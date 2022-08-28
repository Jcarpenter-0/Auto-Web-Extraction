import pandas as pd
import datetime
from urllib.parse import urlparse
from typing import List
from typing import Dict

import nltk
#nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')

from selenium.webdriver.remote.webdriver import WebDriver

import context.broad_context
import context
import context.sources.filtrations
import context.formats.html

# ======================================================================================================================
#
# ======================================================================================================================


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
            './hf-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines), 1, len(finalLinksDF),
                                                            timeDelta.seconds), index=False)



    return finalLinksDF, timeDelta.seconds


def SETS(browser:WebDriver, query:str, pageLoadTime:int=10) -> (pd.DataFrame, float):
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

        for depth in range(1, 1 + 1):

            nextDepthLinks = pd.DataFrame()

            for rowIDX, row in currentLinksDF.iterrows():
                pageStartTime = datetime.datetime.now()

                trgURL = row['TargetURL']

                siteLinks, pageEval = evaluator.EvaluatePage(browser, row, depth, 1, pageLoadTime)
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
                        siteLinks = pagefilter.SelectLinks(siteLinks, evaluator, depth, 1)

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

        # Select only the upper end
        finalLinksDF = finalLinksDF[finalLinksDF['Value'] > 0]

        # Take non-plurals (set aside plurals if you wish to do more exploration)
        finalLinksDF = finalLinksDF[finalLinksDF['IsPathPlural'] == False]

        generatedQueries = set()

        # For each non-plural, take the path, and humanize it, then do a search engine result on it, add top n (~10) to new linkset
        subQueryIDX = 0

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

            endPathSet = set(endPath.split(' '))

            if endPath in generatedQueries:
                # Skip, we already queried this
                pass
            else:
                generatedQueries.add(endPath)

                # Idea is that a query should be about specifics here, hence the minimum size heuristic
                if len(endPath) > 3:

                    print('Querying {}/{} on {}'.format(subQueryIDX, len(finalLinksDF), endPath))

                    # Add the query to the path checks?
                    oldPathChecks = evaluator.PathChecks.copy()
                    oldDomainChecks = evaluator.DomainChecks.copy()

                    evaluator.DomainChecks.update(endPathSet)
                    evaluator.PathChecks.update(endPathSet)

                    for se in searchEngines:

                        try:
                            subLinksDF = se.Query(browser, endPath, linkLimit=100, paginationLimit=0,
                                                  linkEvaluator=evaluator)

                            if len(subLinksDF) > 0:
                                subLinksDF = subLinksDF[subLinksDF['Explored'] == False]
                                subLinksDF = subLinksDF[subLinksDF['Value'] > 0]
                                subLinksDF = subLinksDF[subLinksDF['IsQuerier'] == False]
                                subLinksDF = subLinksDF[subLinksDF['DomainIgnore'] == False]
                                subLinksDF = subLinksDF[subLinksDF['IsFragment'] == False]
                                subLinksDF = subLinksDF[subLinksDF['MimetypeIgnore'] == False]
                                subLinksDF = subLinksDF[subLinksDF['IsPathPlural'] == False]
                                subLinksDF = subLinksDF.reset_index()
                                subLinksDF = subLinksDF.drop(['index'], axis=1)

                                actuallyFinalLinksDF = actuallyFinalLinksDF.append(subLinksDF, ignore_index=True)
                        except Exception as ex:
                            print('{} failed, skipping'.format(se))

                    # Restore old path checks
                    evaluator.PathChecks.clear()
                    evaluator.DomainChecks.clear()

                    evaluator.PathChecks = oldPathChecks
                    evaluator.DomainChecks = oldDomainChecks


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
            './ses-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines), 1, len(actuallyFinalLinksDF),
                                                            timeDelta.seconds), index=False)
    timeEnd = datetime.datetime.now()

    timeDelta = timeEnd - timeStart

    return finalLinksDF, timeDelta.seconds


def AnalyzeWebPage(browser:WebDriver, url:str, pageWait:float=1.5) -> (list, pd.DataFrame):
    """Produce a datasheet of DOM coordinate capable HTML page data"""

    siteElements, siteElementsObjectsDF, listSiteElements = context.formats.html.ParseWebPage(url, browser, pageWait=pageWait)

    return (listSiteElements, siteElements)


def GrabAll(webData:List[context.formats.html.Element]) -> (pd.DataFrame, float):
    """"""

    evaluationApproach = context.formats.html.DataToLabelEvaluationHeuristic()

    timeStart = datetime.datetime.now()

    # Data Cleanup Step ~ Just splitting pieces
    tempList = context.formats.html.CleanupElementSubsplittingSpecifics(webData)
    tempList = context.formats.html.Cleanup_RecursiveInnerHTMLRemover(tempList)
    tempList = context.formats.html.CleanupTagDumping(tempList)

    # Boost some values, make them as or more important than the spatial values
    for element in tempList:
        element.TagDepth = element.TagDepth * 10000
        element.TagIndex = element.TagIndex * 1000

    # Per-Format
    fields = dict()

    for format in context.broad_context.AllPrimitives:
        subFormatList = context.formats.html.Cleanup_GeneralMatchSplitting(tempList, format)
        subFormatList = context.formats.html.Cleanup_DuplicateRemoval(subFormatList)
        tst1 = context.formats.html.EvaluateDataAgainstFormats(subFormatList, format)

        dataCandidates = list(tst1[tst1['Element-Match'] > 0]['Element-Object'].values)
        labelCandidates = list(tst1[tst1['Element-Match'] <= 0]['Element-Object'].values)
        tst2 = context.formats.html.EvaluateDataRelationships(dataCandidates, labelCandidates, evaluationApproach)

        for element in tst2.keys():
            valu, label = tst2[element][0]

            try:
                # Remove the label from the overall pool
                tempList.remove(label)
            except:
                pass

            try:
                # Remove the data from the overall pool
                tempList.remove(element)
            except:
                pass

            if len(label.InnerHTML) > 1:

                if label.InnerHTML in fields.keys():
                    fields[label.InnerHTML].append(element.InnerHTML)
                else:
                    fields[label.InnerHTML] = [element.InnerHTML]

    fields = context.formats.CleanupWhiteSpaces(fields)

    finalReport = pd.DataFrame()

    finalReport['Field'] = fields.keys()
    finalReport['Value'] = fields.values()

    timeEnd = datetime.datetime.now()

    timeDelta = timeEnd - timeStart

    return finalReport, timeDelta.seconds


def GrabSome(webData:List[context.formats.html.Element], contextFields:list) -> (pd.DataFrame, float):
    """"""

    contextFields.sort(key=lambda x: x.DataTypeIndex)

    dataTypeFormatsGroups = []

    currentGroup = None
    currentGroupValues = []

    # Group all the datatypes together
    for fieldDefinition in contextFields:

        if currentGroup is None:
            currentGroup = fieldDefinition.DataTypeIndex
            currentGroupValues.append(fieldDefinition)
        else:
            if currentGroup != fieldDefinition.DataTypeIndex:
                dataTypeFormatsGroups.append(currentGroupValues)
                currentGroup = fieldDefinition.DataTypeIndex
                currentGroupValues = [fieldDefinition]
            else:
                currentGroupValues.append(fieldDefinition)

    HueristicEval = context.formats.html.DataToLabelEvaluationHeuristic()
    LabelEval = context.formats.html.LabelToDataEvaluationHeuristic()

    timeStart = datetime.datetime.now()

    # Data Cleanup Step ~ Just splitting pieces
    tempList = context.formats.html.CleanupElementSubsplittingSpecifics(webData)
    tempList = context.formats.html.Cleanup_RecursiveInnerHTMLRemover(tempList)
    tempList = context.formats.html.CleanupTagDumping(tempList)

    # Boost some values, make them as or more important than the spatial values
    for element in tempList:
        element.TagDepth = element.TagDepth * 10000
        element.TagIndex = element.TagIndex * 1000

    # Per each field definition group by data type, hew the data down into a almost atomic form, then look for matching
    fields = dict()

    for fieldDefinitionGroup in dataTypeFormatsGroups:

        allDataFormats = context.formats.html.GetAllFormats(fieldDefinitionGroup)

        # Get the data candidates (the ones that match the format)
        subFormatList = context.formats.html.Cleanup_GeneralMatchSplitting(tempList, allDataFormats)
        subFormatList = context.formats.html.Cleanup_DuplicateRemoval(subFormatList)
        tst1 = context.formats.html.EvaluateDataAgainstFormats(subFormatList, allDataFormats)

        dataCandidates = list(tst1[tst1['Element-Match'] > 0]['Element-Object'].values)
        labelCandidates = list(tst1[tst1['Element-Match'] <= 0]['Element-Object'].values)

        dataCandidatesAndEvals = dict()

        for dataCandidate in dataCandidates:
            dataCandidatesAndEvals[dataCandidate] = 0

        # for each field inside this group, look for labels among the label candidates
        for fieldDefinition in fieldDefinitionGroup:

            evaluatedData = dict()

            subLabelCandidates = None

            if len(fieldDefinition.LabelFormats) > 0:
                # Use label formats to find label candidates
                subLabelCandidates = context.formats.html.EvaluateDataAgainstFormats(labelCandidates, fieldDefinition.LabelFormats)
                subLabelCandidates = list(subLabelCandidates[subLabelCandidates['Element-Match'] > 0]['Element-Object'].values)

            if len(fieldDefinition.Behaviors) > 0:
                # Use behaviors to further filter the data candidates
                for behavior in fieldDefinition.Behaviors:
                    for dataCandidate in dataCandidatesAndEvals.keys():
                        dataCandidatesAndEvals[dataCandidate] += behavior.Evaluate(dataCandidate.InnerHTML)

            # Boost the data around the labels (by inverse of distance)
            if subLabelCandidates is not None and len(subLabelCandidates) > 0:
                for sublabelCandidate in subLabelCandidates:
                    for dataCandidate in dataCandidatesAndEvals.keys():
                        dataCandidatesAndEvals[dataCandidate] += LabelEval.Evaluate(sublabelCandidate, dataCandidate)

            # sort and present the data with evals
            combo = sorted(dataCandidatesAndEvals.items(), key=lambda x: x[1], reverse=False)

            # Select top N occurences and closest
            selectedData = combo[0:fieldDefinition.Ocurrences]

            for selectedElement, score in selectedData:

                # remove from considerations of others?

                if subLabelCandidates is not None and len(subLabelCandidates) > 0:
                    altLabel = subLabelCandidates[0]

                    if altLabel.InnerHTML in fields.keys():
                        fields[altLabel.InnerHTML].append(selectedElement.InnerHTML)
                    else:
                        fields[altLabel.InnerHTML] = [selectedElement.InnerHTML]
                else:

                    if fieldDefinition.FieldName in fields.keys():
                        fields[fieldDefinition.FieldName].append(selectedElement.InnerHTML)
                    else:
                        fields[fieldDefinition.FieldName] = [selectedElement.InnerHTML]


    fields = context.formats.CleanupWhiteSpaces(fields)
    finalReport = pd.DataFrame()

    finalReport['Field'] = fields.keys()
    finalReport['Value'] = fields.values()

    timeEnd = datetime.datetime.now()
    timeDelta = timeEnd - timeStart

    return finalReport, timeDelta.seconds


def GrabBest(webData:List[context.formats.html.Element]) -> (pd.DataFrame, float):
    """Enrich coordinates, do primitive subsplitting"""

    timeStart = datetime.datetime.now()

    # Data Cleanup Step ~ Just splitting pieces
    tempList = context.formats.html.CleanupElementSubsplittingSpecifics(webData)
    tempList = context.formats.html.Cleanup_RecursiveInnerHTMLRemover(tempList)
    tempList = context.formats.html.CleanupTagDumping(tempList)

    # Boost some values, make them as or more important than the spatial values
    for element in tempList:
        element.TagDepth = element.TagDepth * 10000
        element.TagIndex = element.TagIndex * 1000

    # Do the primitive splitting
    tempList2 = tempList.copy()
    for element in tempList2:
        # pop out old entry, replace with extension of the new list
        oldIndex = tempList.index(element)

        tempList.extend(context.formats.html.Cleanup_GeneralMatchSplittingSingle(element,context.broad_context.AllPrimitives))

        del tempList[oldIndex]

    # Do String assignment (parts of speech)
    for element in tempList:

        element.InnerHTML

        element.TextDemographics = []


    # Do the clustering
    clusterLabels = []

    # For each cluster approach, try to resolve the relationships or the labels for label-less data
    for clusterLabel in clusterLabels:
        pass

    # =======================

    timeEnd = datetime.datetime.now()
    timeDelta = timeEnd - timeStart

    return (None, timeDelta)