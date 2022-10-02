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
