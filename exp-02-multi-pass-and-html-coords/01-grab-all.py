import json
import pandas as pd
import numpy as np
import glob
import exp_tools
import datetime
import context.formats.html
import context.broad_context

siteDataPaths = glob.glob('../exp-00-exploratory/output-conference-data/*.csv')

evaluationApproach = context.formats.html.DataToLabelEvaluationHeuristic()

times = []
dataAccuracies = []
labelAccuracies = []
noiseRatios = []
matchAccuracies = []

for siteDataPath in siteDataPaths:

    siteName = siteDataPath.split('/')[-1].split('.')[-2]
    print('Processing {}'.format(siteDataPath))

    siteElements = pd.read_csv(siteDataPath)
    siteElementsList = context.formats.html.ParseFromDataFrameToList(siteElements)

    timeStart = datetime.datetime.now()

    # Data Cleanup Step ~ Just splitting pieces
    tempList = context.formats.html.CleanupElementSubsplittingSpecifics(siteElementsList)
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

    times.append(timeDelta.microseconds)

    print(finalReport)

    # Check against answers
    with open('./answers/{}.json'.format(siteName),'r') as answerFile:
        truData = json.load(answerFile)

        data = exp_tools.CheckAnswers(truData, fields)

        print(data)

        noiseRatios.append(data['noise'])
        dataAccuracies.append(data['data-capture'])
        labelAccuracies.append(data['label-capture'])
        matchAccuracies.append(data['match-correctness'])


# Produce Report
print('Grab All: Time {} (ms)| Noise-To-Data {} % | Label-Accuracy {} % | Data-Accuracy {} % | Match-Accuracy {} %'.format(np.mean(times)/1000,
                                                                                                                           np.mean(noiseRatios),
                                                                                                                           np.mean(labelAccuracies),
                                                                                                                           np.mean(dataAccuracies),
                                                                                                                           np.mean(matchAccuracies)))
