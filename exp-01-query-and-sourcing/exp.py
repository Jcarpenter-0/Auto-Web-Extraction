# Included for running in cmd
import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../')
# ===========================

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


#pagefilter = None

pagefilter = context.sources.filtrations.SimpleFiltration()

depthFilter = None

#depthFilter = context.sources.filtrations.StatisticalFiltrationAndTokenSelection()

endFilter = None

#endFilter = context.sources.filtrations.StatisticalFiltrationAndTokenSelection()

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


        # Evaluate at Depth Level
        #if evaluator is not None:
            #nextDepthLinks = evaluator.EvaluateDepth(nextDepthLinks, depth, nDepth)
            #pass

        # Filtering at Depth Level
        if depthFilter is not None:
            # Pass nextDepthLinks to the filter
            originalDepthSize = len(nextDepthLinks)

            nextDepthLinks = depthFilter.SelectLinks(nextDepthLinks, evaluator, depth, nDepth)

            print('Depth Filter {} to {}: d={}'.format(originalDepthSize, len(nextDepthLinks), originalDepthSize-len(nextDepthLinks)))

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
    #if evaluator is not None:
        #finalLinksDF = evaluator.EvaluateTotal(finalLinksDF, nDepth, nDepth)

    # Total level filtering
    if endFilter is not None:
        # Pass nextDepthLinks to the filter
        originalEndSize = len(finalLinksDF)

        finalLinksDF = endFilter.SelectLinks(finalLinksDF, evaluator, nDepth, nDepth)

        print('Final Filter {} to {} = d={}'.format(originalEndSize, len(finalLinksDF), originalEndSize-len(finalLinksDF)))

    timeEnd = datetime.datetime.now()

    timeDelta = timeEnd - timeStart

    tokenDF = pd.DataFrame()

    tokenDF['Token'] = evaluator.TokenOccurences.keys()
    tokenDF['Count'] = evaluator.TokenOccurences.values()

    tokenDF.to_csv('./ses-{}-depth-{}-tokens.csv'.format(len(searchEngines),nDepth), index=False)

    checksDF = pd.DataFrame()

    checksDF['Token'] = list(evaluator.DomainChecks)

    checksDF.to_csv('./ses-{}-depth-{}-check-tokens.csv'.format(len(searchEngines),nDepth), index=False)

    print('Links found {} took {} seconds ~ {} minutes ~ {} hours'.format(len(finalLinksDF), timeDelta.seconds, timeDelta.seconds/60, timeDelta.seconds/60/60))

    finalLinksDF.to_csv('./ses-{}-depth-{}-links-{}-time-{}.csv'.format(len(searchEngines),nDepth, len(finalLinksDF), timeDelta.seconds), index=False)

