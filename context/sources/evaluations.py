import time

import pandas as pd
from selenium import webdriver
from urllib.parse import urlparse
from typing import List
from typing import Dict
import json
import nltk
#nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')

# ======================================================================================================================
# Evaluation approaches, for looking at web pages, and links and providing value judgements
# ======================================================================================================================


class EvaluationModule(object):

    def __int__(self):
        """"""
        return

    def EvaluateLink(self, browserInstance:webdriver, link:str, sourceLink:str, currentDepth:int, maxDepth:int) -> pd.DataFrame:
        """On a per link basis, evaluate"""
        return NotImplementedError

    def EvaluateRichSourceLink(self, browserInstance:webdriver, link:str, sourceLink:pd.Series, currentDepth:int, maxDepth:int) -> pd.DataFrame:
        """Evaluate a dataframe but with a source that was already evaluated"""
        return self.EvaluateLink(browserInstance, link, sourceLink['TargetURL'], currentDepth, maxDepth)

    def EvaluateLinks(self, browserInstance:webdriver, links:pd.DataFrame, currentDepth:int, maxDepth:int) -> pd.DataFrame:
        """Given a set of links, evaluate them"""
        return NotImplementedError

    def EvaluatePage(self, browserInstance:webdriver, urlRow:pd.Series, currentDepth:int, maxDepth:int, pageSleep:int) -> (pd.DataFrame, pd.DataFrame):
        return NotImplementedError

    def EvaluateDepth(self, browserInstance:webdriver, depthLinks:pd.DataFrame, currentDepth:int, maxDepth:int) -> pd.DataFrame:
        return NotImplementedError

    def EvaluateTotal(self, allLinks:pd.DataFrame, currentDepth:int, maxDepth:int) -> pd.DataFrame:
        return NotImplementedError

    def ToLog(self)->str:
        """Convert this structure to formatted json"""
        return NotImplemented


# ======================================================================================================================
# Helper methods
# ======================================================================================================================


def GetHrefFromAnchor(row) -> str:

    linkText = None

    try:
        linkText = row[0].get_attribute('href')
        if linkText is None or 'http' not in linkText:
            raise Exception('No parsable here, or no HTTP')
    except:
        linkText = None

    return linkText


def AnchorsToLinksDF(webElements:list, sourceText:str=None) -> pd.DataFrame:
    """Convert web links to list of str"""
    elementsDF = pd.DataFrame()
    elementsDF['webElements'] = webElements

    linksDF = pd.DataFrame()
    linksDF['TargetURL'] = elementsDF.apply(lambda x : GetHrefFromAnchor(x), axis=1)
    linksDF = linksDF[linksDF['TargetURL'].isnull() == False]
    linksDF['SourceURL'] = [sourceText] * len(linksDF)

    return linksDF


def AnchorsToLinks(webElements:list, sourceText:str=None) -> Dict[str,str]:
    """Convert web links to list of str"""
    subLinks = dict()

    for anchor in webElements:
        try:
            linkText = anchor.get_attribute('href')

            if linkText is not None and 'http' in linkText:
                subLinks[linkText] = sourceText

        except:
            print('Web Element Link Extraction Failure, may not be a big deal.')

    return subLinks


class URLEvaluation():

    def __init__(self, trg:str,
                 totalSubsetMatch:int, totalMatch:int, totalsubsetIgnore:bool,
                 domainSubsetMatch:int, domainMatch:int, domainIgnore:bool, domainSubsetIgnore:bool,
                 dirsSubsetMatch:int, dirsMatch:int, dirIgnore:bool, dirSubsetIgnore:bool,
                 pathSubsetMatch:int, pathMatch:int, endPathIgnore:bool, endPathSubsetIgnore:bool, isFragment:bool,
                 isQuerier:bool, alreadyExplored:bool, overallIgnore:bool,
                 src:str, inDomain:bool, mimeTypeIgnore:bool, mimeTypeEval:int,
                 domains:list, dirs:list, endPath:list, mimeType:str, isPathPlural:bool, dirPlurals:list):
        """"""
        self.TargetURL:str = trg

        self.SourceURL:str = src

        # Total evaluation of this URL
        self.TotalSubsetMatch:int = totalSubsetMatch
        # Match on explicit tokens, no "in" but "equal"
        self.TotalMatch:int = totalMatch

        self.DomainSubsetMatch:int = domainSubsetMatch
        self.DomainMatch:int = domainMatch

        self.DirsSubsetMatch:int = dirsSubsetMatch
        self.DirsMatch:int = dirsMatch

        self.PathSubsetMatch:int = pathSubsetMatch
        self.PathMatch:int = pathMatch

        self.MimetypeMatch:int = mimeTypeEval

        # Evaluation details
        self.IsPathPlural:bool = isPathPlural
        self.DirPluralities:list = dirPlurals
        self.TotalIgnore:bool = overallIgnore
        self.InDomain:bool = inDomain
        self.IsQuerier:bool = isQuerier
        self.IsFragment:bool = isFragment
        self.Explored:bool = alreadyExplored
        self.DomainIgnore:bool = domainIgnore
        self.DirIgnore:bool = dirIgnore
        self.EndPathIgnore:bool = endPathIgnore
        self.MimetypeIgnore:bool = mimeTypeIgnore
        self.TotalSubsetIgnore:bool = totalsubsetIgnore
        self.DomainSubsetIgnore:bool = domainSubsetIgnore
        self.DirSubsetIgnore:bool = dirSubsetIgnore
        self.EndPathSubsetIgnore:bool = endPathSubsetIgnore

        # Data details
        self.Domains:list = domains
        self.Dirs:list = dirs
        self.EndPath:list = endPath
        self.Mimetype:str = mimeType

    def ToDF(self) -> pd.DataFrame:

        dfFormat = pd.DataFrame()

        for key in self.__dict__:
            val = self.__dict__[key]

            dfFormat[key] = [val]

        return dfFormat


class PageEvaluation():

    def __init__(self, url:str, inDegree:int, outDegree:int, pageCheck:int):
        self.URL:str = url
        self.InDegree = inDegree
        self.OutDegree = outDegree
        self.PageCheckEvaluation = pageCheck

    def ToDF(self)->pd.DataFrame:

        dfFormat = pd.DataFrame()

        for key in self.__dict__:
            val = self.__dict__[key]

            dfFormat[key] = [val]

        return dfFormat


def CleanupList(listData:list) -> list:
    """Remove empty elements"""

    newList = list()

    for elem in listData:
        if len(elem) > 0:
            newList.append(elem)

    return newList


def EvaluateListAgainstSet(sourceData:list, targetData:set) -> int:
    """"""

    matches = 0

    # convert to list, to sort by order
    targetDatalist = list(targetData)

    targetDatalist.sort(key=len, reverse=True)

    # do full point comparison
    for compare in sourceData:
        for elem in targetDatalist:
            if compare is not None and elem.lower() == compare.lower():
                matches += 1
                # no sense matching on this again
                break

    return matches


def EvaluateListAgainstSetSubset(sourceData:list, targetData:set) -> int:
    """Check if a value exists in a subset of the string"""
    matches = 0

    # convert to list, to sort by order
    targetDatalist = list(targetData)

    targetDatalist.sort(key=len, reverse=True)

    # do full point comparison
    for compare in sourceData:
        for elem in targetDatalist:
            if compare is not None and elem.lower() in compare.lower():
                matches += 1
                # no sense matching on this again
                break

    return matches


def IsPlural(sentence:str) -> bool:

    isPlural = False

    if len(sentence) > 1:

        simplifiedPathHumanRead = sentence.replace('-', ' ')

        is_noun = lambda pos: pos[:2] == 'NN'

        # Split off the prepositional phrases (need the core subject's plurality)
        preps = [' on ', ' in ', ' about ', ' of ', ' for ']

        for prep in preps:

            try:
                simplifiedPathHumanRead = simplifiedPathHumanRead[:simplifiedPathHumanRead.index(prep)]
                break
            except:
                pass

        tokenized = nltk.word_tokenize(simplifiedPathHumanRead)

        nouns = [word for (word, pos) in nltk.pos_tag(tokenized) if is_noun(pos)]

        if len(nouns) >= 1:
            lastNoun: str = nouns[-1]

            pluralEndings = ['ses', 'es']

            for pluralEnding in pluralEndings:
                if lastNoun.endswith(pluralEnding):
                    isPlural = True
                    break

            # Special case S check
            if isPlural is False and lastNoun.endswith('s') and lastNoun.endswith('ss') == False:
                isPlural = True

    return isPlural


# ======================================================================================================================
# Custom Evaluation - Simple
# ======================================================================================================================


class CustomEvaluation(EvaluationModule):

    def __init__(self, totalChecks:set=set(), totalDiscs:set=set(), totalIgnores:set=set(),
                 domainChecks:set=set(), domainDiscs:set={}, domainIgnores:set=set(),
                 dirChecks:set=set(), dirDiscs:set=set(), dirIgnores:set=set(),
                pathChecks:set=set(), pathDiscs:set=set(), pathIgnores:set=set(),
                mimeChecks:set=set(), mimeDiscs:set=set(), mimeIgnores:set=set(),
                pageChecks:set=set(),
                ):
        """Using simple boolean checks"""
        self.DomainChecks = domainChecks
        self.DomainDiscs = domainDiscs
        self.DomainIgnores = domainIgnores

        self.DirChecks = dirChecks
        self.DirDiscs = dirDiscs
        self.DirIgnores = dirIgnores

        self.PathChecks = pathChecks
        self.PathDiscs = pathDiscs
        self.PathIgnores = pathIgnores

        self.MimeChecks = mimeChecks
        self.MimeDiscs = mimeDiscs
        self.MimeIgnores = mimeIgnores

        self.PageCheck = pageChecks
        self.PageCheck.update(self.DirChecks)
        self.PageCheck.update(self.PathChecks)
        self.PageCheck.update(self.DomainChecks)

        self.TotalChecks = totalChecks
        self.TotalDiscs = totalDiscs
        self.TotalIgnores = totalIgnores

        self.AlreadyExplored = set()
        self.TokenOccurences = dict()


    def ToLog(self) ->str:

        data = json.dumps(self.TokenOccurences, indent=8)

        return data

    def EvaluationFormula(self, row:pd.DataFrame) -> float:
        """For use in evaluating a dataframe, a comprehensive formula for total evaluaton"""

        calculation = row['TotalSubsetMatch'] + row['TotalMatch'] \
                      + (row['DomainSubsetMatch'] * 2) + (row['DomainMatch'] * 10) \
                      + (row['DirsSubsetMatch'] * 0.25) + (row['DirsMatch'] * 0.25) \
                      + (row['PathSubsetMatch'] * 0.25) + (row['PathMatch'] * 0.5)

        return calculation

    def EvaluateLink(self, browserInstance:webdriver, link:str, sourceLink:str, currentDepth:int, maxDepth:int) -> pd.DataFrame:

        parsedURL = urlparse(link)

        explored = False
        if link in self.AlreadyExplored:
            explored = True
        else:
            self.AlreadyExplored.add(link)

        # Check if in the domain as the source
        inDomain = False

        if sourceLink is not None:
            srcURLParse = urlparse(sourceLink)

            if srcURLParse.netloc == parsedURL.netloc:
                inDomain = True

        # ==========================
        # Clean up the overall Path
        # ==========================
        simpllifiedOverallPath = link
        simpllifiedOverallPath = simpllifiedOverallPath.replace('.', '-')
        simpllifiedOverallPath = simpllifiedOverallPath.replace('_', '-')
        simpllifiedOverallPath = simpllifiedOverallPath.replace('/', '-')
        overallPathPieces = simpllifiedOverallPath.split('-')
        overallPathPieces = CleanupList(overallPathPieces)

        # ==========================
        # Cleaning up the net loc ~ turn into a list of domains
        # ==========================
        simplifiedNetLoc = parsedURL.netloc

        simplifiedNetLoc = simplifiedNetLoc.replace('https://', '')
        simplifiedNetLoc = simplifiedNetLoc.replace('http://', '')
        simplifiedNetLoc = simplifiedNetLoc.replace('www.', '')
        endBit = simplifiedNetLoc.split('.')[-1]
        simplifiedNetLoc = simplifiedNetLoc.replace(endBit, '')
        domainPieces = simplifiedNetLoc.split('.')

        domainPieces = CleanupList(domainPieces)

        # ==========================
        # Clean up the path ~ break into parts, the dirs, path, mimetype
        # ==========================
        pathPieces = parsedURL.path.split('/')
        simplifiedPath = pathPieces[-1]

        mimeType = None
        if '.' in simplifiedPath:
            mimeType = simplifiedPath.split('.')[-1]
            simplifiedPath = simplifiedPath.split('.')[-2]
        pathDirs = pathPieces[:-1]
        pathDirs = CleanupList(pathDirs)
        dirTokens = []

        dirPlurals = []

        for pathDir in pathDirs:
            pathDir = pathDir.replace('_','-')
            subTokens = pathDir.split('-')
            dirTokens.extend(subTokens)

            # Process the dir tokens
            subDirPlural = IsPlural(pathDir)

            dirPlurals.append(subDirPlural)

        if len(simplifiedPath) <= 0:
            simplifiedPath = pathPieces[-2]
            #pathPieces = pathPieces[:-1]

        tokenPath = simplifiedPath.replace('_', '-')
        endPathTokens = tokenPath.split('-')
        endPathTokens = CleanupList(endPathTokens)
        #queryPieces = None
        isQuerier = False
        if parsedURL.query is not None and len(parsedURL.query) > 0:
            isQuerier = True
            #queryPieces = None

        isFragment = False

        if parsedURL.fragment is not None and len(parsedURL.fragment) > 0:
            isFragment = True

        # ==========================
        # Check plurality of path
        # ==========================

        isPlural = IsPlural(simplifiedPath)

        # ==========================
        # Conduct the evaluation
        # ==========================
        # Naive path checks
        totalMatch = 0

        totalMatch += EvaluateListAgainstSet(overallPathPieces, self.TotalChecks)
        totalMatch -= EvaluateListAgainstSet(overallPathPieces, self.TotalDiscs)
        totalIgnore = EvaluateListAgainstSet(overallPathPieces, self.TotalIgnores) > 0

        totalSubsetMatch = 0

        totalSubsetMatch += EvaluateListAgainstSetSubset(overallPathPieces, self.TotalChecks)
        totalSubsetMatch -= EvaluateListAgainstSetSubset(overallPathPieces, self.TotalDiscs)
        totalSubsetIgnore = EvaluateListAgainstSetSubset(overallPathPieces, self.TotalIgnores) > 0

        # Domain checks
        domainMatch = 0

        domainMatch += EvaluateListAgainstSet(domainPieces, self.DomainChecks)
        domainMatch -= EvaluateListAgainstSet(domainPieces, self.DomainDiscs)
        domainIgnore = EvaluateListAgainstSet(domainPieces, self.DomainIgnores) > 0

        domainSubsetMatch = 0
        domainSubsetMatch += EvaluateListAgainstSetSubset(domainPieces, self.DomainChecks)
        domainSubsetMatch -= EvaluateListAgainstSetSubset(domainPieces, self.DomainDiscs)
        domainSubsetIgnore = EvaluateListAgainstSetSubset(domainPieces, self.DomainIgnores) > 0

        # Dirs checks
        dirsMatch = 0

        dirsMatch += EvaluateListAgainstSet(pathDirs, self.DirChecks)
        dirsMatch -= EvaluateListAgainstSet(pathDirs, self.DirDiscs)
        dirIgnore = EvaluateListAgainstSet(pathDirs, self.DirIgnores) > 0

        dirsSubsetMatch = 0
        dirsSubsetMatch += EvaluateListAgainstSetSubset(pathDirs, self.DirChecks)
        dirsSubsetMatch -= EvaluateListAgainstSetSubset(pathDirs, self.DirDiscs)
        dirSubsetIgnore = EvaluateListAgainstSetSubset(pathDirs, self.DirIgnores) > 0

        # endPath check
        pathMatch = 0

        pathMatch += EvaluateListAgainstSet(endPathTokens, self.PathChecks)
        pathMatch -= EvaluateListAgainstSet(endPathTokens, self.PathDiscs)
        endPathIgnore = EvaluateListAgainstSet(endPathTokens, self.PathIgnores) > 0

        pathSubsetMatch = 0

        pathSubsetMatch += EvaluateListAgainstSetSubset(endPathTokens, self.PathChecks)
        pathSubsetMatch -= EvaluateListAgainstSetSubset(endPathTokens, self.PathDiscs)
        endPathSubsetIgnore = EvaluateListAgainstSetSubset(endPathTokens, self.PathIgnores) > 0

        # mimetype check
        mimeEval = 0

        mimeEval += EvaluateListAgainstSet([mimeType], self.MimeChecks)
        mimeEval -= EvaluateListAgainstSet([mimeType], self.MimeDiscs)
        mimeIgnore = EvaluateListAgainstSet([mimeType], self.MimeIgnores) > 0

        # All tokens calc
        allTokens = []
        allTokens.extend(endPathTokens)
        allTokens.extend(dirTokens)
        allTokens.extend(domainPieces)

        for element in allTokens:

            isTokenNumber = element.isnumeric()

            if isTokenNumber is False:

                modifiedElement = element.lower()

                modifiedElement.replace('_', '-')

                if len(modifiedElement) > 5:

                    if modifiedElement.endswith('s') and modifiedElement.endswith('ies') is False and modifiedElement.endswith('ss') is False:
                        modifiedElement = modifiedElement[:-1]

                    if modifiedElement.endswith('ed'):
                        modifiedElement = modifiedElement[:-2]

                    if modifiedElement.endswith('ly'):
                        modifiedElement = modifiedElement[:-2]

                    if modifiedElement.endswith('ing'):
                        modifiedElement = modifiedElement[:-3]

                coreToken = modifiedElement

                if coreToken in self.TokenOccurences.keys():
                    self.TokenOccurences[coreToken] += 1
                else:
                    self.TokenOccurences[coreToken] = 1

        # =========================

        linkEval = URLEvaluation(trg=link, src=sourceLink, isQuerier=isQuerier, alreadyExplored=explored, inDomain=inDomain,
                                 totalMatch=totalMatch, totalSubsetMatch=totalSubsetMatch, overallIgnore=totalIgnore, totalsubsetIgnore=totalSubsetIgnore,
                                 domainMatch=domainMatch, domainSubsetMatch=domainSubsetMatch, domainIgnore=domainIgnore, domainSubsetIgnore=domainSubsetIgnore,
                                 dirsMatch=dirsMatch, dirsSubsetMatch=dirsSubsetMatch, dirIgnore=dirIgnore, dirSubsetIgnore=dirSubsetIgnore,
                                 pathMatch=pathMatch, pathSubsetMatch=pathSubsetMatch, endPathIgnore=endPathIgnore, endPathSubsetIgnore=endPathSubsetIgnore,
                                 mimeType=mimeType, dirs=pathDirs, domains=domainPieces, endPath=endPathTokens, isFragment=isFragment,
                                 mimeTypeEval=mimeEval, mimeTypeIgnore=mimeIgnore, isPathPlural=isPlural, dirPlurals=dirPlurals)

        linkDf = linkEval.ToDF()
        linkDf['Value'] = self.EvaluationFormula(linkDf)

        return linkDf

    def EvaluatePage(self, browserInstance:webdriver, urlRow:pd.Series, currentDepth:int, maxDepth:int, pageSleep:int) -> (pd.DataFrame, PageEvaluation):
        """Navigate to the page, get the links from it, eval the page and the links, return a dataframe of links FROM this page, add rows to the incoming Row"""

        inLinks = 0
        outLinks = 0
        pageCheckEval = 0
        linkEvals = pd.DataFrame()

        url = urlRow['TargetURL']

        try:

            browserInstance.get(url)

            time.sleep(pageSleep)

            # Do Page check against, title/page source
            try:
                titleElement = browserInstance.title

                # metaElements = browserInstance.find_elements_by_tag_name('meta')

                #pageSource = browserInstance.page_source

                for check in self.PageCheck:
                    #if check.lower() in pageSource.lower():
                        #pageCheckEval += 1

                    if check.lower() in titleElement.lower():
                        pageCheckEval += 1

                # priceValue.get_attribute("content")

            except Exception as ex:
                print('Page Check Failure: {}'.format(ex))

            try:
                # Get links on this page and path discriminate
                subAnchors = browserInstance.find_elements_by_tag_name('a')
                links = AnchorsToLinksDF(subAnchors, sourceText=url)

                for linkIDX, link in links.iterrows():

                    linkEval = self.EvaluateRichSourceLink(browserInstance, link['TargetURL'], urlRow, currentDepth, maxDepth)

                    inOrOut = linkEval['InDomain'][0]

                    if inOrOut:
                        inLinks += 1
                    else:
                        outLinks += 1

                    linkEvals = linkEvals.append(linkEval, ignore_index=True)
            except Exception as ex1:
                print('Issue with link {} link extraction - {}'.format(url,ex1))

        except Exception as ex:
            print('Issue with link {} - {}'.format(url, ex))
            return pd.DataFrame(), None

        if len(linkEvals) <= 0:
            print('Stop Here')

        return linkEvals, PageEvaluation(url, inLinks, outLinks, pageCheckEval)

    def EvaluateDepth(self, browserInstance:webdriver, depthLinks:pd.DataFrame, currentDepth:int, maxDepth:int) -> pd.DataFrame:

        finalLinks = []

        for idx, rowSeries in depthLinks.iterrows():

            newRow = self.EvaluateLink(browserInstance, rowSeries['TargetURL'], rowSeries['SourceURL'], currentDepth, maxDepth)

            finalLinks.append(newRow)

        finalLinksDF = pd.concat(finalLinks)

        return finalLinksDF
