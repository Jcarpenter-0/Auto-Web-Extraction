import pandas as pd
import datetime
from urllib.parse import urlparse
from typing import List
from typing import Dict
from scipy.spatial.distance import pdist
from scipy.spatial.distance import euclidean
from difflib import SequenceMatcher

import nltk
import nltk.tokenize
#nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')

from PyDictionary import PyDictionary
dictionary=PyDictionary()

import spacy
from spacy import displacy
from collections import Counter

# If missing, run in command line "spacy download en_core_web_sm" :https://stackoverflow.com/questions/54334304/spacy-cant-find-model-en-core-web-sm-on-windows-10-and-python-3-5-3-anacon
# May need to run this from /usr/bin/python* for whatever python environment running, as /usr/bin/python3 -m spacy download en_core_web_sm

langModel = spacy.load('en_core_web_sm')
#import en_core_web_sm
#nlp = en_core_web_sm.load()

from selenium.webdriver.remote.webdriver import WebDriver
from sklearn.cluster import DBSCAN
from sklearn.cluster import OPTICS
import numpy as np

import context.broad_context
import context
import context.sources.filtrations
import context.formats.html
import context.mappings
import context.formats

# ======================================================================================================================
#
# ======================================================================================================================


def MF(browser:WebDriver, query:str, maxDepth:int=0, pageLoadTime:int=10, pageFilter:context.sources.filtrations.FiltrationApproach=None) -> (pd.DataFrame, float):
    """Get Links using minimal filtering"""
    # split the query for the checks
    checks = set(query.split(' '))

    # Search Engine(s) to use
    searchEngines = []
    searchEngines.append(context.sources.Google())
    searchEngines.append(context.sources.Bing())
    searchEngines.append(context.sources.Yahoo())
    searchEngines.append(context.sources.DuckDuckGo())

    # Evaluator to use
    evaluator = context.sources.evaluations.CustomEvaluation(domainDiscs=context.broad_context.DomainDics,
                                                             domainIgnores=context.broad_context.DomainIgnores,
                                                             dirChecks=checks, dirDiscs=context.broad_context.DirDics,
                                                             dirIgnores=context.broad_context.DirIgnores,
                                                             pathChecks=checks, pathDiscs=context.broad_context.PathDiscs,
                                                             pathIgnores=context.broad_context.PathIgnores,
                                                             mimeChecks=context.broad_context.MimeChecks, mimeDiscs=context.broad_context.MimeDiscs,
                                                             mimeIgnores=context.broad_context.MimeIgnores, pageChecks=checks)

    depthFilter = None

    endFilter = None

    # =====================================================================================================================
    # Apply to the search engines
    # =====================================================================================================================
    timeStart = datetime.datetime.now()

    finalLinksDF = pd.DataFrame()
    pageEvals = []

    for se in searchEngines:
        subLinksDF = se.Query(browser, query, linkLimit=100, paginationLimit=0, linkEvaluator=evaluator)
        finalLinksDF = finalLinksDF.append(subLinksDF, ignore_index=True)

    finalLinksDF['Depth'] = [0] * len(finalLinksDF)
    finalLinksDF = finalLinksDF[finalLinksDF['IsQuerier'] == False]
    finalLinksDF = finalLinksDF[finalLinksDF['Explored'] == False]
    finalLinksDF = finalLinksDF[finalLinksDF['IsFragment'] == False]
    finalLinksDF = finalLinksDF.reset_index()
    finalLinksDF = finalLinksDF.drop(['index'], axis=1)

    print('Depth 0 : {} SE(s) produced {} link(s)'.format(len(searchEngines), len(finalLinksDF)))

    # ====================================================================================================================
    # Do n-depth link exploration
    # ====================================================================================================================

    currentLinksDF = finalLinksDF.copy()

    try:

        for depth in range(1, maxDepth + 1):

            nextDepthLinks = pd.DataFrame()

            for rowIDX, row in currentLinksDF.iterrows():
                pageStartTime = datetime.datetime.now()

                siteLinks, pageEval = evaluator.EvaluatePage(browser, row, depth, depth, pageLoadTime)
                pageEval: context.sources.evaluations.PageEvaluation = pageEval
                pageEndTime = datetime.datetime.now()

                pageTime = pageEndTime - pageStartTime

                print('Depth {}/{} Link {}/{} - produced {} links took {} second(s) - from {}'.format(depth, maxDepth,
                                                                                                      rowIDX + 1,
                                                                                                      len(currentLinksDF),
                                                                                                      len(siteLinks),
                                                                                                      pageTime.seconds,
                                                                                                      row['TargetURL']))

                originalSize = len(siteLinks)

                if pageEval is not None:
                    pageEvals.append(pageEval.ToDF())

                if len(siteLinks) > 0:

                    siteLinks['Depth'] = [depth] * len(siteLinks)

                    # Do filtering
                    siteLinks = siteLinks[siteLinks['DomainIgnore'] == False]
                    siteLinks = siteLinks[siteLinks['IsQuerier'] == False]
                    siteLinks = siteLinks[siteLinks['IsFragment'] == False]
                    siteLinks = siteLinks[siteLinks['MimetypeIgnore'] == False]
                    siteLinks = siteLinks[siteLinks['Explored'] == False]

                    # Filtering at Page Level
                    if pageFilter is not None:
                        siteLinks = pageFilter.SelectLinks(siteLinks, evaluator, depth, maxDepth)

                        print('Filter reduced {} to {} = d={}'.format(originalSize, len(siteLinks),
                                                                      originalSize - len(siteLinks)))

                    finalLinksDF = finalLinksDF.append(siteLinks, ignore_index=True)

                    nextDepthLinks = nextDepthLinks.append(siteLinks, ignore_index=True)

            # Evaluate at Depth Level
            # if evaluator is not None:
            # nextDepthLinks = evaluator.EvaluateDepth(nextDepthLinks, depth, nDepth)
            # pass

            # Filtering at Depth Level
            if depthFilter is not None:
                # Pass nextDepthLinks to the filter
                originalDepthSize = len(nextDepthLinks)

                nextDepthLinks = depthFilter.SelectLinks(nextDepthLinks, evaluator, depth, maxDepth)

                print('Depth Filter {} to {}: d={}'.format(originalDepthSize, len(nextDepthLinks),
                                                           originalDepthSize - len(nextDepthLinks)))

            currentLinksDF = nextDepthLinks

    except KeyboardInterrupt:
        print('Interupt')
    except Exception as ex:
        print(ex)
        raise ex
    finally:
        browser.quit()

        # Now at the end, join the page evals
        if len(pageEvals) > 0:
            pageEvalsDF = pd.concat(pageEvals, axis=0)

            finalLinksDF = finalLinksDF.join(pageEvalsDF.set_index('URL'), on="TargetURL", how='left')

        # Total Level evaluations
        # if evaluator is not None:
        # finalLinksDF = evaluator.EvaluateTotal(finalLinksDF, nDepth, nDepth)

        # Total level filtering
        if endFilter is not None:
            # Pass nextDepthLinks to the filter
            originalEndSize = len(finalLinksDF)

            finalLinksDF = endFilter.SelectLinks(finalLinksDF, evaluator, maxDepth, maxDepth)

            print('Final Filter {} to {} = d={}'.format(originalEndSize, len(finalLinksDF),
                                                        originalEndSize - len(finalLinksDF)))

        timeEnd = datetime.datetime.now()

        timeDelta = timeEnd - timeStart

        print('Links found {} took {} seconds ~ {} minutes ~ {} hours'.format(len(finalLinksDF), timeDelta.seconds,
                                                                              timeDelta.seconds / 60,
                                                                              timeDelta.seconds / 60 / 60))

        # finalLinksDF.to_csv('./ses-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines),nDepth, len(finalLinksDF), timeDelta.seconds), index=False)
        finalLinksDF.to_csv(
            './mf-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines), maxDepth, len(finalLinksDF),
                                                            timeDelta.seconds), index=False)

    return finalLinksDF, timeDelta.seconds

def HF(browser:WebDriver, query:str, maxDepth:int=0, pageLoadTime:int=10) -> (pd.DataFrame, float):
    """Get Links using heuristic filtering"""

    # split the query for the checks
    checks = set(query.split(' '))

    # Search Engine(s) to use
    searchEngines = []
    searchEngines.append(context.sources.Google())
    searchEngines.append(context.sources.Bing())
    searchEngines.append(context.sources.Yahoo())
    searchEngines.append(context.sources.DuckDuckGo())

    # Evaluator to use
    evaluator = context.sources.evaluations.CustomEvaluation(domainDiscs=context.broad_context.DomainDics,
                                                             domainIgnores=context.broad_context.DomainIgnores,
                                                             dirChecks=checks, dirDiscs=context.broad_context.DirDics,
                                                             dirIgnores=context.broad_context.DirIgnores,
                                                             pathChecks=checks, pathDiscs=context.broad_context.PathDiscs,
                                                             pathIgnores=context.broad_context.PathIgnores,
                                                             mimeChecks=context.broad_context.MimeChecks, mimeDiscs=context.broad_context.MimeDiscs,
                                                             mimeIgnores=context.broad_context.MimeIgnores, pageChecks=checks)


    pagefilter = context.sources.filtrations.SimpleFiltration()

    depthFilter = None

    endFilter = None

    # =====================================================================================================================
    # Apply to the search engines
    # =====================================================================================================================
    timeStart = datetime.datetime.now()

    finalLinksDF = pd.DataFrame()
    pageEvals = []

    for se in searchEngines:
        subLinksDF = se.Query(browser, query, linkLimit=100, paginationLimit=0, linkEvaluator=evaluator)
        finalLinksDF = finalLinksDF.append(subLinksDF, ignore_index=True)

    finalLinksDF['Depth'] = [0] * len(finalLinksDF)
    finalLinksDF = finalLinksDF[finalLinksDF['IsQuerier'] == False]
    finalLinksDF = finalLinksDF[finalLinksDF['Explored'] == False]
    finalLinksDF = finalLinksDF[finalLinksDF['IsFragment'] == False]
    finalLinksDF = finalLinksDF.reset_index()
    finalLinksDF = finalLinksDF.drop(['index'], axis=1)

    print('Depth 0 : {} SE(s) produced {} link(s)'.format(len(searchEngines), len(finalLinksDF)))

    # ====================================================================================================================
    # Do n-depth link exploration
    # ====================================================================================================================

    currentLinksDF = finalLinksDF.copy()

    try:

        for depth in range(1, maxDepth + 1):

            nextDepthLinks = pd.DataFrame()

            for rowIDX, row in currentLinksDF.iterrows():
                pageStartTime = datetime.datetime.now()

                siteLinks, pageEval = evaluator.EvaluatePage(browser, row, depth, depth, pageLoadTime)
                pageEval: context.sources.evaluations.PageEvaluation = pageEval
                pageEndTime = datetime.datetime.now()

                pageTime = pageEndTime - pageStartTime

                print('Depth {}/{} Link {}/{} - produced {} links took {} second(s) - from {}'.format(depth, maxDepth,
                                                                                                      rowIDX + 1,
                                                                                                      len(currentLinksDF),
                                                                                                      len(siteLinks),
                                                                                                      pageTime.seconds,
                                                                                                      row['TargetURL']))

                originalSize = len(siteLinks)

                if pageEval is not None:
                    pageEvals.append(pageEval.ToDF())

                if len(siteLinks) > 0:

                    siteLinks['Depth'] = [depth] * len(siteLinks)

                    # Do filtering
                    siteLinks = siteLinks[siteLinks['DomainIgnore'] == False]
                    siteLinks = siteLinks[siteLinks['IsQuerier'] == False]
                    siteLinks = siteLinks[siteLinks['IsFragment'] == False]
                    siteLinks = siteLinks[siteLinks['MimetypeIgnore'] == False]
                    siteLinks = siteLinks[siteLinks['Explored'] == False]

                    # Filtering at Page Level
                    if pagefilter is not None:
                        siteLinks = pagefilter.SelectLinks(siteLinks, evaluator, depth, maxDepth)

                        print('Filter reduced {} to {} = d={}'.format(originalSize, len(siteLinks),
                                                                      originalSize - len(siteLinks)))

                    finalLinksDF = finalLinksDF.append(siteLinks, ignore_index=True)

                    nextDepthLinks = nextDepthLinks.append(siteLinks, ignore_index=True)

            # Evaluate at Depth Level
            # if evaluator is not None:
            # nextDepthLinks = evaluator.EvaluateDepth(nextDepthLinks, depth, nDepth)
            # pass

            # Filtering at Depth Level
            if depthFilter is not None:
                # Pass nextDepthLinks to the filter
                originalDepthSize = len(nextDepthLinks)

                nextDepthLinks = depthFilter.SelectLinks(nextDepthLinks, evaluator, depth, maxDepth)

                print('Depth Filter {} to {}: d={}'.format(originalDepthSize, len(nextDepthLinks),
                                                           originalDepthSize - len(nextDepthLinks)))

            currentLinksDF = nextDepthLinks

    except KeyboardInterrupt:
        print('Interupt')
    except Exception as ex:
        print(ex)
        raise ex
    finally:
        browser.quit()

        # Now at the end, join the page evals
        if len(pageEvals) > 0:
            pageEvalsDF = pd.concat(pageEvals, axis=0)

            finalLinksDF = finalLinksDF.join(pageEvalsDF.set_index('URL'), on="TargetURL", how='left')

        # Total Level evaluations
        # if evaluator is not None:
        # finalLinksDF = evaluator.EvaluateTotal(finalLinksDF, nDepth, nDepth)

        # Total level filtering
        if endFilter is not None:
            # Pass nextDepthLinks to the filter
            originalEndSize = len(finalLinksDF)

            finalLinksDF = endFilter.SelectLinks(finalLinksDF, evaluator, maxDepth, maxDepth)

            print('Final Filter {} to {} = d={}'.format(originalEndSize, len(finalLinksDF),
                                                        originalEndSize - len(finalLinksDF)))

        timeEnd = datetime.datetime.now()

        timeDelta = timeEnd - timeStart

        print('Links found {} took {} seconds ~ {} minutes ~ {} hours'.format(len(finalLinksDF), timeDelta.seconds,
                                                                              timeDelta.seconds / 60,
                                                                              timeDelta.seconds / 60 / 60))

        # finalLinksDF.to_csv('./ses-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines),nDepth, len(finalLinksDF), timeDelta.seconds), index=False)
        finalLinksDF.to_csv(
            './hf-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines), maxDepth, len(finalLinksDF),
                                                            timeDelta.seconds), index=False)



    return finalLinksDF, timeDelta.seconds


def SETS(browser:WebDriver, query:str, maxDepth:int=1, pageLoadTime:int=10) -> (pd.DataFrame, float):
    """Get Links using Search Engine Token Subquerying"""

    # split the query for the checks
    checks = set(query.split(' '))

    # Search Engine(s) to use
    searchEngines = []
    searchEngines.append(context.sources.Google())
    searchEngines.append(context.sources.Bing())
    searchEngines.append(context.sources.Yahoo())
    searchEngines.append(context.sources.DuckDuckGo())

    # Evaluator to use
    evaluator = context.sources.evaluations.CustomEvaluation(domainDiscs=context.broad_context.DomainDics,
                                                             domainIgnores=context.broad_context.DomainIgnores,
                                                             dirChecks=checks, dirDiscs=context.broad_context.DirDics,
                                                             dirIgnores=context.broad_context.DirIgnores,
                                                             pathChecks=checks, pathDiscs=context.broad_context.PathDiscs,
                                                             pathIgnores=context.broad_context.PathIgnores,
                                                             mimeChecks=context.broad_context.MimeChecks, mimeDiscs=context.broad_context.MimeDiscs,
                                                             mimeIgnores=context.broad_context.MimeIgnores, pageChecks=checks)


    pagefilter = context.sources.filtrations.SimpleFiltration()

    depthFilter = None

    endFilter = None

    # =====================================================================================================================
    # Apply to the search engines
    # =====================================================================================================================
    timeStart = datetime.datetime.now()

    finalLinksDF = pd.DataFrame()
    pageEvals = []

    for se in searchEngines:
        subLinksDF = se.Query(browser, query, linkLimit=100, paginationLimit=0, linkEvaluator=evaluator)
        finalLinksDF = finalLinksDF.append(subLinksDF, ignore_index=True)

    finalLinksDF['Depth'] = [0] * len(finalLinksDF)
    finalLinksDF = finalLinksDF[finalLinksDF['IsQuerier'] == False]
    finalLinksDF = finalLinksDF[finalLinksDF['Explored'] == False]
    finalLinksDF = finalLinksDF[finalLinksDF['IsFragment'] == False]
    finalLinksDF = finalLinksDF.reset_index()
    finalLinksDF = finalLinksDF.drop(['index'], axis=1)

    print('Depth 0 : {} SE(s) produced {} link(s)'.format(len(searchEngines), len(finalLinksDF)))

    # Just for the last phase
    actuallyFinalLinksDF = pd.DataFrame()

    # ====================================================================================================================
    # Do n-depth link exploration
    # ====================================================================================================================

    currentLinksDF = finalLinksDF.copy()

    try:
        for depth in range(1,maxDepth + 1):

            nextDepthLinks = pd.DataFrame()

            for rowIDX, row in currentLinksDF.iterrows():
                pageStartTime = datetime.datetime.now()

                siteLinks, pageEval = evaluator.EvaluatePage(browser, row, depth, maxDepth, pageLoadTime)
                pageEval: context.sources.evaluations.PageEvaluation = pageEval
                pageEndTime = datetime.datetime.now()

                pageTime = pageEndTime - pageStartTime

                print('Depth {}/{} Link {}/{} - produced {} links took {} second(s) - from {}'.format(depth, 1,
                                                                                                      rowIDX + 1,
                                                                                                      len(currentLinksDF),
                                                                                                      len(siteLinks),
                                                                                                      pageTime.seconds,
                                                                                                      row['TargetURL']))

                originalSize = len(siteLinks)

                if pageEval is not None:
                    pageEvals.append(pageEval.ToDF())

                if len(siteLinks) > 0:

                    siteLinks['Depth'] = [depth] * len(siteLinks)

                    # Do filtering
                    siteLinks = siteLinks[siteLinks['DomainIgnore'] == False]
                    siteLinks = siteLinks[siteLinks['IsQuerier'] == False]
                    siteLinks = siteLinks[siteLinks['IsFragment'] == False]
                    siteLinks = siteLinks[siteLinks['MimetypeIgnore'] == False]
                    siteLinks = siteLinks[siteLinks['Explored'] == False]

                    # Filtering at Page Level
                    if pagefilter is not None:
                        siteLinks = pagefilter.SelectLinks(siteLinks, evaluator, depth, maxDepth)

                        print('Filter reduced {} to {} = d={}'.format(originalSize, len(siteLinks),
                                                                      originalSize - len(siteLinks)))

                    finalLinksDF = finalLinksDF.append(siteLinks, ignore_index=True)

                    nextDepthLinks = nextDepthLinks.append(siteLinks, ignore_index=True)

            currentLinksDF = nextDepthLinks

        # Now at the end, join the page evals
        if len(pageEvals) > 0:
            pageEvalsDF = pd.concat(pageEvals, axis=0)

            finalLinksDF = finalLinksDF.join(pageEvalsDF.set_index('URL'), on="TargetURL", how='left')

        # ======================================================================================================================
        # Do the subsequent search engine pass
        # ======================================================================================================================

        # Select only the paths with at least 1 thing that makes it related
        finalLinksDF = finalLinksDF[finalLinksDF['Value'] > 0]

        # Take non-plurals (set aside plurals if you wish to do more exploration)
        #finalLinksDF = finalLinksDF[finalLinksDF['IsPathPlural'] == False]

        generatedQueries = set()

        # For each non-plural, take the path, and humanize it, then do a search engine result on it, add top n (~10) to new linkset
        subQueryIDX = 0

        tokenOccurrencesFD = open('./token-occurrences.csv', 'w')
        tokenOccurrencesFD.write('Token,Count\n')

        for token in evaluator.TokenOccurences:
            tokenCount = evaluator.TokenOccurences[token]
            tokenOccurrencesFD.write('{},{}\n'.format(token,tokenCount))

        tokenOccurrencesFD.flush()
        tokenOccurrencesFD.close()

        queryTokens = evaluator.TokenOccurences.copy()

        evaluator.TokenOccurences.clear()

        evaluator.AlreadyExplored.clear()

        for idx, row in finalLinksDF.iterrows():

            subQueryIDX += 1

            subLink = row['TargetURL']

            parsedSubURL = urlparse(subLink)

            dirs: str = parsedSubURL.path

            endPath = dirs.split('/')[-1]

            endPath = endPath.replace('_', '-')

            endPath = endPath.replace('-', ' ')

            endPath = endPath.replace('.html','')
            endPath = endPath.replace('.php','')
            endPath = endPath.replace('index.html','')

            endPathSet = set(endPath.split(' '))

            if endPath in generatedQueries:
                # Skip, we already queried this
                pass
            else:
                # Idea is that a query should be about specifics here, hence the minimum size heuristic
                if len(endPath.strip()) > 3 and endPath.isdigit() == False and endPath.isdecimal() == False:

                    generatedQueries.add(endPath)

                    # Add the query to the path checks?
                    oldPathChecks = evaluator.PathChecks.copy()
                    oldDomainChecks = evaluator.DomainChecks.copy()

                    evaluator.DomainChecks.update(endPathSet)
                    evaluator.PathChecks.update(endPathSet)

                    for se in searchEngines:

                        try:
                            subLinksDF = se.Query(browser, endPath, linkLimit=100, paginationLimit=0,
                                                  linkEvaluator=evaluator)

                            print('SE {} Queryied {}/{} on {} ~ produced {}'.format(se, subQueryIDX, len(finalLinksDF), endPath, len(subLinksDF)))

                            if len(subLinksDF) > 0:

                                preFilterSize = len(subLinksDF)

                                subLinksDF = subLinksDF[subLinksDF['Explored'] == False]
                                subLinksDF = subLinksDF[subLinksDF['Value'] >= 0]
                                subLinksDF = subLinksDF[subLinksDF['IsQuerier'] == False]
                                subLinksDF = subLinksDF[subLinksDF['DomainIgnore'] == False]
                                subLinksDF = subLinksDF[subLinksDF['IsFragment'] == False]
                                subLinksDF = subLinksDF[subLinksDF['MimetypeIgnore'] == False]
                                subLinksDF = subLinksDF[subLinksDF['IsPathPlural'] == False]
                                subLinksDF = subLinksDF.reset_index()
                                subLinksDF = subLinksDF.drop(['index'], axis=1)

                                postFilterSize = len(subLinksDF)

                                print('SES Subquery Filter {} - {}'.format(preFilterSize, postFilterSize))

                                actuallyFinalLinksDF = actuallyFinalLinksDF.append(subLinksDF, ignore_index=True)
                        except Exception as ex:
                            print('{} failed, skipping {}'.format(se, ex))

                    # Restore old path checks
                    evaluator.PathChecks.clear()
                    evaluator.DomainChecks.clear()

                    evaluator.PathChecks = oldPathChecks
                    evaluator.DomainChecks = oldDomainChecks

        # Take the original query, and then just add tokens to it for query purposes
        tokenAverage = np.percentile(list(queryTokens.values()), 0.75)
        print('Query Token Percentile {} len {}'.format(tokenAverage, len(queryTokens)))

        for tokenIDX, token in enumerate(queryTokens.keys()):

            tokenCount = queryTokens[token]

            if len(token) >= 3 and token.isdigit() == False and token.isdecimal() == False and tokenCount <= tokenAverage:

                newQueryText = query + ' {} home'.format(token)

                generatedQueries.add(newQueryText)

                for se in searchEngines:

                    try:
                        subLinksDF = se.Query(browser, newQueryText, linkLimit=100, paginationLimit=0,
                                              linkEvaluator=evaluator)

                        print('SE {} Queried {}/{} on {} ~ produced {}'.format(se, tokenIDX, len(queryTokens), newQueryText,
                                                                                len(subLinksDF)))

                        if len(subLinksDF) > 0:
                            preFilterSize = len(subLinksDF)

                            subLinksDF = subLinksDF[subLinksDF['Explored'] == False]
                            subLinksDF = subLinksDF[subLinksDF['Value'] >= 0]
                            subLinksDF = subLinksDF[subLinksDF['IsQuerier'] == False]
                            subLinksDF = subLinksDF[subLinksDF['DomainIgnore'] == False]
                            subLinksDF = subLinksDF[subLinksDF['IsFragment'] == False]
                            subLinksDF = subLinksDF[subLinksDF['MimetypeIgnore'] == False]
                            subLinksDF = subLinksDF[subLinksDF['IsPathPlural'] == False]
                            subLinksDF = subLinksDF.reset_index()
                            subLinksDF = subLinksDF.drop(['index'], axis=1)

                            postFilterSize = len(subLinksDF)

                            print('SES Subquery Filter {} - {}'.format(preFilterSize, postFilterSize))

                            actuallyFinalLinksDF = actuallyFinalLinksDF.append(subLinksDF, ignore_index=True)
                    except Exception as ex:
                        print('{} failed, skipping {}'.format(se, ex))

        queryLog = open('./ses-queries.txt', 'w')
        for element in generatedQueries:
            queryLog.write('{}\n'.format(element))

        queryLog.flush()
        queryLog.close()

    except KeyboardInterrupt:
        print('Interupt')
    except Exception as ex:
        print(ex)
        raise ex
    finally:

        browser.quit()

        # include depth 0 and 1's links here ~ note this is additional to basic spec grab
        actuallyFinalLinksDF = actuallyFinalLinksDF.append(finalLinksDF)

        # Drop duplicates
        actuallyFinalLinksDF = actuallyFinalLinksDF.drop_duplicates(['TargetURL'])

        timeEnd = datetime.datetime.now()

        timeDelta = timeEnd - timeStart

        print('Links found {} took {} seconds ~ {} minutes ~ {} hours'.format(len(finalLinksDF), timeDelta.seconds,
                                                                              timeDelta.seconds / 60,
                                                                              timeDelta.seconds / 60 / 60))

        # finalLinksDF.to_csv('./ses-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines),nDepth, len(finalLinksDF), timeDelta.seconds), index=False)
        actuallyFinalLinksDF.to_csv(
            './ses-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines), maxDepth, len(actuallyFinalLinksDF),
                                                            timeDelta.seconds), index=False)
    timeEnd = datetime.datetime.now()

    timeDelta = timeEnd - timeStart

    return finalLinksDF, timeDelta.seconds


def AnalyzeWebPage(browser:WebDriver, url:str, pageWait:float=1.5) -> (list, pd.DataFrame):
    """Produce a datasheet of DOM coordinate capable HTML page data"""

    siteElements, siteElementsObjectsDF, listSiteElements = context.formats.html.ParseWebPage(url, browser, pageWait=pageWait)

    return (listSiteElements, siteElements)


def GrabBest(webData:List[context.formats.html.Element], adaptiveClusterDistance:bool=True,
             clusterDistancePercentile:int=2, subClusterDistancePercentile:int=3,
             xCoordinateBoost:float=1.0, yCoordinateBoost:float=1.0,
             clusterRatioThreshold:float=1.0,
             tDboost:float=10, tIboost:float=1000,
             subclusterXBoost:float=0.5, subclusterYBoost:float=4.0,
             subclustertDBoost:float=1.0, subclustertIBoost:float=1.0) -> (pd.DataFrame, float, pd.DataFrame):
    """Enrich coordinates, do primitive subsplitting, then result in clusters of associated data"""

    timeStart = datetime.datetime.now()

    # Data Cleanup Step ~ Just splitting pieces
    tempList = context.formats.html.CleanupTagDumping(webData)
    tempList = context.formats.html.CleanupElementSubsplittingSpecifics(tempList)
    #tempList = context.formats.html.Cleanup_RecursiveInnerHTMLRemover(tempList)

    # Get average distances of elements in the web page to set stage for Ti,Td boosting?
    vectors = []

    for element in tempList:
        vectors.append(element.GetVector())

    distances = pdist(vectors)
    overallPageAvgDistances = np.mean(distances)
    overallPageSTDDistances = np.std(distances)
    avgDistanceInt = int(overallPageAvgDistances)
    digitCount = len('{}'.format(avgDistanceInt))
    overallPageRatio = overallPageSTDDistances/overallPageAvgDistances

    print('High Level Page Character {} ratio'.format(overallPageRatio))

    # Boost some values, make them as or more important than the spatial values
    for element in tempList:
        element.TagDepth = (element.TagDepth * (10^digitCount)) * tDboost
        element.TagIndex = (element.TagIndex * (10^digitCount)) * tIboost
        element.RenderedX = element.RenderedX * xCoordinateBoost
        element.RenderedY = element.RenderedY * yCoordinateBoost

    # Do the primitive splitting
    tempList2 = tempList.copy()
    for element in tempList2:
        # pop out old entry, replace with extension of the new list
        oldIndex = tempList.index(element)
        tempList.extend(context.formats.html.Cleanup_GeneralMatchSplittingSingle(element,context.formats.AllPrimitives))
        del tempList[oldIndex]

    # Do String assignment (parts of speech)
    for element in tempList:

        # Only do POS if its a string
        if element.Primitive == "String":

            # Do trailing whitespace cleaning
            element.InnerHTML = element.InnerHTML.strip()
            elementProcessingText = element.InnerHTML
            text = nltk.word_tokenize(elementProcessingText)
            textPos = nltk.pos_tag(text)

            newTextPos = []

            posCounts = dict()

            overallTokenCount = len(textPos)
            overallPyDictionaryPOSCount = 0

            secondPOSDemos = dict()

            for textPosElement, Pos in textPos:

                secondPOS = dict()

                # Custom web-heuristic Named-Entity-Recognition (NER)
                #try:
                #    secondPOS = dictionary.meaning(textPosElement).keys()
                #except:
                    #pass

                for key in secondPOS:

                    if key not in secondPOSDemos.keys():
                        secondPOSDemos[key] = 1
                    else:
                        secondPOSDemos[key] += 1

                    overallPyDictionaryPOSCount += 1

                if Pos != textPosElement:
                    newTextPos.append((textPosElement,Pos))

                    if Pos in posCounts.keys():
                        posCounts[Pos] += 1
                    else:
                        posCounts[Pos] = 1

            for posKey in posCounts.keys():
                posCounts[posKey] = posCounts[posKey]/overallTokenCount

            for posKey in secondPOSDemos.keys():
                secondPOSDemos[posKey] = secondPOSDemos[posKey]/overallPyDictionaryPOSCount

            element.PyDictionaryDemographics = secondPOSDemos
            element.NTLKTextDemographics = posCounts

            # if this shows up as an entity, put this to true
            elementEntities = langModel(elementProcessingText)

            if len(elementEntities.ents) > 0:
                element.SpaceyTextDemographics = elementEntities.ents[0].label_

            # Determine if element is named-entity
            entityCounts = 0

            if 'NNP' in element.NTLKTextDemographics.keys():
                entityCounts += 1

            if element.SpaceyTextDemographics is not None:
                entityCounts += 1

            #if len(element.PyDictionaryDemographics.keys()) <= 0:
            #    entityCounts += 1

            # If entirely capitalized, likely a header
            if element.InnerHTML.isupper():
                entityCounts -= 1

            # Proper Noun, "disqualifiers" eg hueristics that would indicate that what we are looking at is NOT a proper noun
            if element.InnerHTML.endswith(':') or element.InnerHTML.endswith('-') or element.InnerHTML.endswith('='):
                # If the innerHTML ends with : it like is something like this (Name: John Doe)
                entityCounts -= 1

            if element.InnerHTML.endswith('.'):
                # is a "sentence" and likely "data"
                entityCounts += 1

            # check capitalization
            textTokens = element.InnerHTML.split(' ')

            capitals = 0
            uncapitals = 0

            for token in textTokens:
                if len(token.strip()) > 1:
                    if token[0].isupper():
                        capitals += 1
                    else:
                        uncapitals += 1

            capitalsPercentage = capitals/len(textTokens)

            if capitalsPercentage < 1.0:
                entityCounts -= 1

            if uncapitals > 0.50:
                entityCounts -= 1

            element.Entity = entityCounts > 0

    # Do the clustering
    vectors = []

    tiCoords = []
    tdCoords = []

    for element in tempList:
        vectors.append(element.GetVector())
        tiCoords.append(element.TagIndex)
        tdCoords.append(element.TagDepth)

    tiMean = np.mean(tiCoords)
    tiSTD = np.std(tiCoords)
    tiRatio = tiSTD/tiMean
    tdMean = np.mean(tdCoords)
    tdSTD = np.std(tdCoords)
    tdRatio = tdSTD/tdMean

    print('Overall Ti Td Characters {} {}'.format(tiSTD/tiMean, tdSTD/tdMean))

    distances = pdist(vectors)

    # this value determines how big the clusters will be, starting small, increase this if the ratio of STD/AVG
    # is greater than 1.0
    currentClusterDistancePercentile = clusterDistancePercentile
    currentClusterSizeRatio = None
    currentClusterSizeAvg = None
    currentClusterSizeSTD = None
    currentClusterDistanceRatio = None
    currentClusterdistanceAvg = None
    currentClusterdistanceSTD = None

    continueNewClustering = True
    clusters = []

    while continueNewClustering:

        clusterDistance = np.percentile(distances, currentClusterDistancePercentile)

        # Approaches for clustering: https://scikit-learn.org/stable/modules/clustering.html
        clustering = DBSCAN(eps=clusterDistance, min_samples=2).fit(vectors)

        clusterLabels = clustering.labels_

        labelUniques = np.unique(clusterLabels)

        clustercount = len(labelUniques)

        # For each cluster approach, try to resolve the relationships or the labels for label-less data
        tempClusters = []

        for clusterLabel in range(-1,clustercount):
            specificCluster = []

            for itemIDX, item in enumerate(clusterLabels):
                if clusterLabel == item:
                    specificCluster.append(tempList[itemIDX])

            tempClusters.append(specificCluster)

        # Overall cluster sizing
        clusterSizes = []
        clusterRatios = []

        for cluster in tempClusters:

            if len(cluster) > 0:

                clusterSizes.append(len(cluster))

                clusterVectors = []

                for element in cluster:
                    clusterVectors.append(element.GetVector())

                clusterDistances = pdist(clusterVectors)
                clusterAvgDistance = np.mean(clusterDistances)
                clusterSTDDistance = np.std(clusterDistances)
                clusterRatio = clusterSTDDistance/clusterAvgDistance

                clusterRatios.append(clusterRatio)

        clusterDistanceRatiosAvg = np.mean(clusterRatios)
        clusterDistanceRatiosSTD = np.std(clusterRatios)
        clusterDistancesRatio = clusterDistanceRatiosSTD/clusterDistanceRatiosAvg
        clusterSizeMeans = np.mean(clusterSizes)
        clusterSizeSTD = np.std(clusterSizes)
        clusterSizeRatio = clusterSizeSTD/clusterSizeMeans

        currentClusterSizeRatio = clusterSizeRatio
        currentClusterSizeAvg = clusterSizeMeans
        currentClusterSizeSTD = clusterSizeSTD
        currentClusterDistanceRatio = clusterDistancesRatio
        currentClusterdistanceAvg = clusterDistanceRatiosAvg
        currentClusterdistanceSTD = clusterDistanceRatiosSTD

        print('Cluster Size Ratio {} - Cluster Distances Ratios {}'.format(clusterSizeRatio, clusterDistancesRatio))

        if adaptiveClusterDistance == True and clusterSizeRatio > clusterRatioThreshold and currentClusterDistancePercentile * 2 < 100:
            # increase the size of the clustering size
            currentClusterDistancePercentile *= 2
        elif adaptiveClusterDistance == False:
            continueNewClustering = False
            clusters = tempClusters
            break
        else:
            # no more need to loop, we have an "adequate size"
            continueNewClustering = False
            clusters = tempClusters
            break

    print('Final Cluster Percentile {}'.format(currentClusterDistancePercentile))

    # ========================================================================
    # Per cluster-operations
    # ========================================================================

    tempList3 = []

    returnDF = pd.DataFrame()

    for clusterID, cluster in enumerate(clusters):
        cleanedCluster = cluster
        tempList3.append(cleanedCluster)

        if len(cleanedCluster) > 0:
            vectors = []

            for element in cleanedCluster:
                # Do any coordinate modifications here for the sub cluster
                # Under-emphasize the Y coordinate (as same line elements (along the X) may be closer than then others)
                element.RenderedX = element.RenderedX * subclusterXBoost
                element.RenderedY = element.RenderedY * subclusterYBoost
                element.TagIndex = element.TagIndex * subclustertIBoost
                element.TagDepth = element.TagDepth * subclustertDBoost

                vectors.append(element.GetVector())

            if len(vectors) <= 0:
                clusterDistances = []
                clusterPercentile = 0
            else:
                clusterDistances = pdist(vectors)
                try:
                    clusterPercentile = np.percentile(clusterDistances, subClusterDistancePercentile)
                except:
                    clusterPercentile = np.mean(clusterDistances)

            #averageClusterDistance = np.mean(clusterDistances)
            #clusterSTD = np.std(clusterDistances)
            #clusterRatio = clusterSTD/averageClusterDistance

            # Higher primitives and propernouns
            dataList = []

            # everything else ~ label candidates
            miscList = []

            for clusterElement in cleanedCluster:

                if len(clusterElement.InnerHTML.strip()) > 0:
                    if clusterElement.Primitive != 'String':
                        dataList.append(clusterElement)
                    elif clusterElement.Entity:
                        dataList.append(clusterElement)
                    else:
                        miscList.append(clusterElement)

            # For each data item, find the possible label as a nearby noun, if none are found, then just take primitives
            clusterDF = pd.DataFrame()

            for dataElementIDX, dataElement in enumerate(dataList):

                elementDF = pd.DataFrame()

                # locate closest "misc"
                closestElement = None
                closestElementDistance = 999999999

                for miscElementIDX, miscElement in enumerate(miscList):
                    distance = euclidean(miscElement.GetVector(), dataElement.GetVector())

                    # Take shortest distance, and distances that fall under the heuristic bound
                    # And hueristic bound for not taking as labels elements less than 3 characters
                    if distance < closestElementDistance and len(miscElement.InnerHTML) >= 3:

                        if distance <= clusterPercentile:
                            # Use the overall average as starting point
                            closestElement = miscElement
                            closestElementDistance = distance

                # If no element found, then we assume label-less and the label as primitive
                if closestElement is None:
                    if dataElement.Primitive == 'String':
                        elementDF['Label'] = ['Name']
                    else:
                        elementDF['Label'] = [dataElement.Primitive]
                else:
                    elementDF['Label'] = [closestElement.InnerHTML]

                elementDF['Value'] = [dataElement.InnerHTML]

                elementDF['Type'] = [dataElement.Primitive]

                elementDF['clusterID'] = [clusterID]

                clusterDF = clusterDF.append(elementDF)

            returnDF = returnDF.append(clusterDF)

    # Drop duplicates in the final DF (duplicates here being same label, same value)
    #returnDF = returnDF.drop_duplicates(subset=['Label','Value','Type'], keep='last')

    # =======================
    timeEnd = datetime.datetime.now()
    timeDelta = timeEnd - timeStart

    print('GB Xboost {} Yboost {} TIboost {} TDboost {} Cluster Ratio Threshold {} Cluster Distance {}'.format(xCoordinateBoost, yCoordinateBoost, tIboost, tDboost, clusterRatioThreshold, currentClusterDistancePercentile))
    print('SC Xboost {} Yboost {} TIboost {} TDboost {} Subcluster Radius Percentile {}'.format(subclusterXBoost, subclusterYBoost, subclustertIBoost, subclustertDBoost, subClusterDistancePercentile))

    miscInfo = pd.DataFrame()

    miscInfo['Overall-Page-Avg-Distance'] = [overallPageAvgDistances]
    miscInfo['Overall-Page-STD-Distance'] = [overallPageSTDDistances]
    miscInfo['Overall-Page-Ratio-Distance'] = [overallPageRatio]
    miscInfo['Overall-Page-Avg-TI'] = [tiMean]
    miscInfo['Overall-Page-STD-TI'] = [tiSTD]
    miscInfo['Overall-Page-Ratio-TI'] = [tiRatio]
    miscInfo['Overall-Page-Avg-TD'] = [tdMean]
    miscInfo['Overall-Page-STD-TD'] = [tdSTD]
    miscInfo['Overall-Page-Ratio-TD'] = [tdRatio]
    miscInfo['Final-Clustering-Size-Percentile'] = [currentClusterDistancePercentile]
    miscInfo['Final-Clustering-Ratio-Size'] = [currentClusterSizeRatio]
    miscInfo['Final-Clustering-Avg-Size'] = [currentClusterSizeAvg]
    miscInfo['Final-Clustering-STD-Size'] = [currentClusterSizeSTD]
    miscInfo['Final-Clustering-Ratio-Distance'] = [currentClusterDistanceRatio]
    miscInfo['Final-Clustering-Avg-Distance'] = [currentClusterdistanceAvg]
    miscInfo['Final-Clustering-STD-Distance'] = [currentClusterdistanceSTD]

    miscInfo['xCoordinateBoost'] = [xCoordinateBoost]
    miscInfo['yCoordinateBoost'] = [yCoordinateBoost]
    miscInfo['tIboost'] = [tIboost]
    miscInfo['tDboost'] = [tDboost]
    miscInfo['clusterRatioThreshold'] = [xCoordinateBoost]
    miscInfo['subclusterXBoost'] = [subclusterXBoost]
    miscInfo['subclusterYBoost'] = [subclusterYBoost]
    miscInfo['subclustertIBoost'] = [subclustertIBoost]
    miscInfo['subclustertDBoost'] = [subclustertDBoost]
    miscInfo['subClusterDistancePercentile'] = [subClusterDistancePercentile]
    miscInfo['adaptiveClusterDistance'] = [adaptiveClusterDistance]

    return (returnDF, timeDelta.microseconds, miscInfo)


def GoogleResolver(browser:WebDriver, query:str) -> (pd.DataFrame, float, pd.DataFrame):
    """Give google a single page intended query, like www2023 abstract deadline. And see if it can get the answer right"""

    # The feature snippet code xpdopen = class or V3FYCf

    # The table answer code ULSxyf a2qDab EyBRub = class

    timeStart = datetime.datetime.now()

    # Apply query
    browser.get('https://www.google.com/search?q={}'.format(query))

    # Check for the tabular array of answer variant
    tabulars = browser.find_elements_by_class_name('ULSxyf a2qDab EyBRub')
    # Check for the snippet variant
    snippets = browser.find_elements_by_class_name('V3FYCf')

    # Process the results into something useful
    if len(snippets) > 0:
        snippet = snippets[0]

        snippetPieces = snippet.text.split('\n')

        # what do the pieces look like here?
        # Snippet requires parsing similar to web page extraction

    timeEnd = datetime.datetime.now()
    timeDelta = timeEnd - timeStart

    # the labeled fields, time taken, and finally, debug full info
    return (None, timeDelta, None)


