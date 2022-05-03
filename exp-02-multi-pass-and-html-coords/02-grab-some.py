import json
import pandas as pd
import numpy as np
import glob
import exp_tools
import datetime
import context.formats.html
import context.academic_conference

siteDataPaths = glob.glob('../exp-00-exploratory/output-conference-data/*.csv')

HueristicEval = context.formats.html.DataToLabelEvaluationHeuristic()
LabelEval = context.formats.html.LabelToDataEvaluationHeuristic()

times = []
dataAccuracies = []
labelAccuracies = []
noiseRatios = []
matchAccuracies = []

# Prepping the context a bit
# Sort the field defininitions in order of data type (to avoid atomicity problem)
context.academic_conference.conferenceFields.sort(key=lambda x: x.DataTypeIndex)

dataTypeFormatsGroups = []

currentGroup = None
currentGroupValues = []

# Group all the datatypes together
for fieldDefinition in context.academic_conference.conferenceFields:

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

# Examine each site

for siteDataPath in siteDataPaths:

    siteName = siteDataPath.split('/')[-1].split('.')[-2]
    print('Processing {}'.format(siteDataPath))
    print('{}'.format(siteName))

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
print('Grab Some: Time {} (ms)| Noise-To-Data {} % | Label-Accuracy {} % | Data-Accuracy {} % | Match-Accuracy {} %'.format(np.mean(times)/1000,
                                                                                                                           np.mean(noiseRatios),
                                                                                                                           np.mean(labelAccuracies),
                                                                                                                           np.mean(dataAccuracies),
                                                                                                                           np.mean(matchAccuracies)))

