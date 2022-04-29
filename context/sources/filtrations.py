import pandas as pd
import context.sources.evaluations
# the place to filter links

# ======================================================================================================================
# Filtration approaches, for deciding based on evaluated links/pages, what should stay and what should go
# ======================================================================================================================


class FiltrationApproach():

    def __init__(self):
        """"""

    def SelectLinks(self, candidateLinks:pd.DataFrame, evaluationApproach:context.sources.evaluations.EvaluationModule, currentDepth:int, maxDepth:int) -> pd.DataFrame:
        """Given a set of links with criteria of evaluations, make calls return a refined list of links"""
        return NotImplementedError

    def SelectLinksAtDepth(self):
        return NotImplementedError

    def SelectLinksAtEnd(self):
        return NotImplementedError


# ======================================================================================================================
# Simple Filtration
# ======================================================================================================================


class SimpleFiltration(FiltrationApproach):

    def __init__(self):
        """Expand searching on relative value, then contract on domain on 2nd to last step, then finally expand"""
        super().__init__()
        self.DomainCrunch = True

    def SelectLinks(self, candidateLinks:pd.DataFrame, evaluationApproach:context.sources.evaluations.EvaluationModule, currentDepth:int, maxDepth:int) -> pd.DataFrame:

        newLinks = candidateLinks.copy()

        # any flags hit for these booleans, start dropping
        newLinks = newLinks[newLinks['Explored'] == False]
        newLinks = newLinks[newLinks['TotalIgnore'] == False]
        newLinks = newLinks[newLinks['TotalSubsetIgnore'] == False]
        newLinks = newLinks[newLinks['DomainSubsetIgnore'] == False]
        newLinks = newLinks[newLinks['DirIgnore'] == False]
        newLinks = newLinks[newLinks['DirSubsetIgnore'] == False]
        newLinks = newLinks[newLinks['EndPathIgnore'] == False]
        newLinks = newLinks[newLinks['EndPathSubsetIgnore'] == False]

        return newLinks


# ======================================================================================================================
# Quantile Filtering
# ======================================================================================================================

class StatisticalFiltrationAndTokenSelection(FiltrationApproach):

    def __init__(self):
        """Given an evaluation, select percentiles, take take top performers, add tokens to overall occurrences, take lowest occurence tokens, then reevaluate for final prune"""
        super().__init__()
        self.DomainCrunch = True

    def SelectLinks(self, candidateLinks:pd.DataFrame, evaluationApproach:context.sources.evaluations.EvaluationModule, currentDepth:int, maxDepth:int) -> pd.DataFrame:

        tokenEvaluator:context.sources.evaluations.CustomEvaluation = evaluationApproach

        newLinks = candidateLinks.copy()

        # remove bad performers
        badLinks = newLinks[newLinks['Value'] < 0]

        newLinks = newLinks[newLinks['Value'] >= 0]

        #cutOff = newLinks['Value'].quantile(0.25)

        #print('Filter Cutoff {}'.format(cutOff))
        cutOff = 0

        # get the "good performers"
        goodLinks = newLinks[newLinks['Value'] >= cutOff]

        allSeenTokensDF = pd.DataFrame()

        allSeenTokensDF['Token'] = tokenEvaluator.TokenOccurences.keys()
        allSeenTokensDF['Count'] = tokenEvaluator.TokenOccurences.values()

        macroTokenCuttoff = allSeenTokensDF['Count'].quantile(0.75)

        # lower occurence tokens from entire set
        subTokensDF = allSeenTokensDF[allSeenTokensDF['Count'] <= macroTokenCuttoff]

        #print('Macro Token Cuttoff {}'.format(macroTokenCuttoff))

        subTokens = set(subTokensDF['Token'].values)

        # Add the tokens of the good performers to the domains (to aid in seeking specific data sources)
        # Only add the good tokens that also "don't occur frequently" overall
        goodLinksTokenGroupsPath = goodLinks['EndPath']

        for row in goodLinksTokenGroupsPath:
            for token in row:
                if len(token) > 2:
                    if token in subTokens:
                        tokenEvaluator.DomainChecks.add(token)

        # Add the poor tokens to the path discs (to aid in removing lower order links)
        badLinkTokenGroupsPath = badLinks['EndPath']

        for row in badLinkTokenGroupsPath:
            for token in row:
                if len(token) > 2:
                    tokenEvaluator.PathDiscs.add(token)

        badLinkTokenGroupsDirs = badLinks['Dirs']
        for row in badLinkTokenGroupsDirs:
            for token in row:
                if len(token) > 2:
                    tokenEvaluator.DirDiscs.add(token)

        newLinks = tokenEvaluator.EvaluateDepth(None, newLinks, currentDepth, maxDepth)

        # Now take the remaining upper performers as the filter
        newLinks = newLinks[newLinks['Value'] > 0]

        newLinks = newLinks.reset_index()
        newLinks = newLinks.drop(['index'], axis=1)

        return newLinks

