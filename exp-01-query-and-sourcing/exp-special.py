# Included for running in cmd
import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../')
# ===========================

from urllib.parse import urlparse
import datetime
from selenium import webdriver
import pandas as pd
import context.sources
import context.sources.evaluations
import context.sources.filtrations

# ======================================================================================================================
# Setup the context
# ======================================================================================================================

queries = ['Top Computer Networking Academic Research Conferences 2022']
# aggregate up to n depth on the links
nDepth = 1
pageLoadTimeoutInSeconds = 20
pageScriptTimeoutInSeconds = 3
pageSleepTimeInSeconds = 2

totalIgnores = {}

domainChecks = set()
domainDics = set()
domainIgnores = {'googleadservices', 'youtube', 'youtu', 'twitter','facebook', 'linkedin', 'job', 'jobs', 'advertising','addons','translate'}

dirChecks = {'Computer', 'Networking', 'Networks', 'Conferences', 'Network', 'Conference', '2022', '22', 'Top', 'Science'}
dirDics = {'search','journal','news'}
dirIgnores = {'editor', 'press-release', 'award', 'certification','about','advertising','communities'
    ,'professional','job','membership','auth','it-services','support','careers'}

pathChecks = {'Computer', 'Networking', 'Networks', 'Conferences', 'Network', 'Conference', '2022', '22', 'Top', 'Science', 'symposium'}
pathDiscs = {'search','organize','insider'}
pathIgnores = {'award', 'editor', 'shopping', 'advertising', 'tool', 'store', 'map', 'course', 'flight',
               'product', 'podcast', 'finance', 'login', 'contact', 'subscribe', 'webinar', 'policy', 'subscriptions',
               'magazines','account','sponsorship','volunteering','advertising','job', 'registration','cart','join',
               'login', 'video', 'webinar','faq','sponsor','scholarship','members','jobs'}

mimeChecks = {'html'}
mimeDiscs = set()
mimeIgnores = {'pdf', 'zip', 'rar', 'exe', 'png', 'jpg', 'jpeg', 'docx', 'doc', 'odt', 'txt', 'gif', 'mp3', 'mp4', 'jpeg','xml','7em','cfm','io'}

pageCheck = set()
pageCheck.update(dirChecks)
pageCheck.update(pathChecks)
pageCheck.update(domainChecks)

# Search Engine(s) to use
searchEngines = []
searchEngines.append(context.sources.Google())
searchEngines.append(context.sources.Bing())
searchEngines.append(context.sources.Yahoo())
searchEngines.append(context.sources.DuckDuckGo())


# Evaluator to use
evaluator = context.sources.evaluations.CustomEvaluation(domainChecks=domainChecks, domainDiscs=domainDics, domainIgnores=domainIgnores,
                                                         dirChecks=dirChecks, dirDiscs=dirDics, dirIgnores=dirIgnores,
                                                         pathChecks=pathChecks, pathDiscs=pathDiscs, pathIgnores=pathIgnores,
                                                         mimeChecks=mimeChecks, mimeDiscs=mimeDiscs, mimeIgnores=mimeIgnores, pageChecks=pageCheck)


pagefilter = context.sources.filtrations.SimpleFiltration()

depthFilter = None

endFilter = None

fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.headless = True

# Call web page
browser = webdriver.Firefox(options=fireFoxOptions)

browser.set_page_load_timeout(pageLoadTimeoutInSeconds)
browser.set_script_timeout(pageScriptTimeoutInSeconds)

# =====================================================================================================================
# Apply to the search engines
# =====================================================================================================================
timeStart = datetime.datetime.now()

finalLinksDF = pd.DataFrame()
pageEvals = []

for query in queries:
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

    for depth in range(1,nDepth+1):

        nextDepthLinks = pd.DataFrame()

        for rowIDX, row in currentLinksDF.iterrows():
            pageStartTime = datetime.datetime.now()

            trgURL = row['TargetURL']

            siteLinks, pageEval = evaluator.EvaluatePage(browser, row, depth, nDepth, pageSleepTimeInSeconds)
            pageEval:context.sources.evaluations.PageEvaluation = pageEval
            pageEndTime = datetime.datetime.now()

            pageTime = pageEndTime - pageStartTime

            print('Depth {}/{} Link {}/{} - produced {} links took {} second(s) - from {}'.format(depth, nDepth, rowIDX+1, len(currentLinksDF), len(siteLinks), pageTime.seconds, row['TargetURL']))

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
                    siteLinks = pagefilter.SelectLinks(siteLinks, evaluator, depth, nDepth)

                    print('Filter reduced {} to {} = d={}'.format(originalSize, len(siteLinks), originalSize-len(siteLinks)))

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

        dirs:str = parsedSubURL.path

        endPath = dirs.split('/')[-1]

        endPath = endPath.replace('_','-')

        endPath = endPath.replace('-',' ')

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
                        subLinksDF = se.Query(browser, endPath, linkLimit=100, paginationLimit=0, linkEvaluator=evaluator)

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

    timeEnd = datetime.datetime.now()

    timeDelta = timeEnd - timeStart

    print('Links found {} took {} seconds ~ {} minutes ~ {} hours'.format(len(finalLinksDF), timeDelta.seconds, timeDelta.seconds/60, timeDelta.seconds/60/60))

    finalLinksDF.to_csv('./ses-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines),nDepth, len(finalLinksDF), timeDelta.seconds), index=False)
    actuallyFinalLinksDF.to_csv('./af-ses-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines),nDepth, len(actuallyFinalLinksDF), timeDelta.seconds), index=False)

