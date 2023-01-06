import pandas as pd
import glob
import numpy as np

import context.formats.html
import context.mappings
import extraction_process
import exp_tools

webSites = glob.glob('../dataset/raw-webpages/*.csv')

# =================================
# Testing Ranges ~ the hyper parameters
# =================================

adaptiveClusteringRange = [False]
clusterRatioThresholdRange = [0.50]
subclusterRadiusRange = [3]
TDBoostRange = [1,10]
TIBoostRange = [1,1000]
subClusterXBoostRange = [1.0]
subClusterYBoostRange = [1]

totalTests = len(webSites) * len(adaptiveClusteringRange) * len(clusterRatioThresholdRange) * len(subclusterRadiusRange) * len(TDBoostRange) * len(TIBoostRange) * len(subClusterXBoostRange) * len(subClusterYBoostRange)

timesTaken = []
labelAccuracies = []
dataAccuracies = []
matchAccuracies = []
noiseRatios = []

debugDF = pd.DataFrame()

actualTests = 0
currentTest = 1

for website in webSites:
    for adaptiveClustering in adaptiveClusteringRange:
        for clusterRatioThreshold in clusterRatioThresholdRange:
            for subclusterRadius in subclusterRadiusRange:
                for TDBoost in TDBoostRange:
                    for TIBoost in TIBoostRange:
                        for subClusterXBoost in subClusterXBoostRange:
                            for subClusterYBoost in subClusterYBoostRange:

                                try:

                                    webSiteName = website.split('/')[-1]

                                    print(webSiteName)

                                    answerKey = pd.read_csv('../dataset/webpage-field-annotations/{}'.format(webSiteName))

                                    rawData = pd.read_csv(website)

                                    elements = context.formats.html.ParseFromDataFrameToList(rawData)

                                    resultingDataClusters, timeTaken, debugInfo = extraction_process.GrabBest(elements,
                                                                                                              adaptiveClusterDistance=adaptiveClustering,
                                                                                                              clusterRatioThreshold=clusterRatioThreshold,
                                                                                                              subClusterDistancePercentile=subclusterRadius,
                                                                                                              tDboost=TDBoost,
                                                                                                              tIboost=TIBoost,
                                                                                                              subclusterXBoost=subClusterXBoost,
                                                                                                              subclusterYBoost=subClusterYBoost)

                                    debugInfo.insert(0, 'Website', webSiteName)

                                    if len(answerKey) > 0:
                                        print()

                                    outcome = exp_tools.CheckScrapeAnswers2(resultingDataClusters, answerKey)

                                    resultingDataClusters.to_csv('./debugging-output/{}-cluster.csv'.format(webSiteName), index=False)

                                    print(outcome)

                                    timeTakenSeconds = timeTaken/1000000

                                    print('Time Taken:{} seconds ~ {}'.format(timeTakenSeconds, webSiteName))

                                    timesTaken.append(timeTakenSeconds)
                                    #labelAccuracies.append(outcome['Label-Accuracy'])
                                    #dataAccuracies.append(outcome['Data-Accuracy'])
                                    matchAccuracies.append(outcome['Match-Accuracy'])
                                    noiseRatios.append(outcome['Data-To-Noise'])

                                    debugInfo.insert(1, 'Match-Accuracy', outcome['Match-Accuracy'])
                                    debugInfo.insert(2, 'Data-To-Noise', outcome['Data-To-Noise'])
                                    debugInfo.insert(2, 'Time-Taken(S)', timeTakenSeconds)
                                    debugInfo['TestID'] = [
                                        '{}{}{}{}{}{}{}'.format(adaptiveClustering, clusterRatioThreshold, subclusterRadius,
                                                                TDBoost, TIBoost, subClusterXBoost, subClusterYBoost)]

                                    debugDF = debugDF.append(debugInfo)

                                    print('===================== {}/{}'.format(currentTest, totalTests))
                                    actualTests += 1
                                except Exception as ex:
                                    print('{} had error {}'.format(website, ex))
                                finally:
                                    currentTest += 1


print('================================')
print('Time Taken: avg {} seconds across {}/{} websites'.format(np.mean(timesTaken), actualTests,len(webSites)))
print('Avg: Label ACC {} Data ACC {} Match ACC {} Data/Noise Ratio {}'.format(np.mean(labelAccuracies),
                                                                       np.mean(dataAccuracies),
                                                                       np.mean(matchAccuracies),
                                                                       np.mean(noiseRatios)))

debugDF.to_csv('./debug.csv', index=False)