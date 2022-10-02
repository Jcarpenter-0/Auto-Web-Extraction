import pandas as pd

fileName = 'non-spatial-debug.csv'

experiments = pd.read_csv(fileName)

# Group the experiments based on the ID
tests = dict()

for rowIDX, row in experiments.iterrows():

    keys = row.keys()
    vals = row.values

    rowDF = pd.DataFrame(columns=keys, data=[vals])

    testID = row['TestID']

    if testID in tests.keys():
        tests[testID] = tests[testID].append(rowDF)
    else:
        tests[testID] = rowDF

groupedExperiments = pd.DataFrame()

for testID in tests.keys():

    testDataFrame = tests[testID]

    configRow = testDataFrame.iloc[0].copy()

    del configRow['Website']
    del configRow['Overall-Page-Avg-Distance']
    del configRow['Overall-Page-STD-Distance']
    del configRow['Overall-Page-Ratio-Distance']
    del configRow['Overall-Page-Avg-TI']
    del configRow['Overall-Page-STD-TI']
    del configRow['Overall-Page-Ratio-TI']
    del configRow['Overall-Page-Avg-TD']
    del configRow['Overall-Page-STD-TD']
    del configRow['Overall-Page-Ratio-TD']
    del configRow['Final-Clustering-Size-Percentile']
    del configRow['Final-Clustering-Ratio-Size']
    del configRow['Final-Clustering-Avg-Size']
    del configRow['Final-Clustering-STD-Size']
    del configRow['Final-Clustering-Ratio-Distance']
    del configRow['Final-Clustering-Avg-Distance']
    del configRow['Final-Clustering-STD-Distance']


    configRow['Match-Accuracy'] = testDataFrame.groupby('TestID')['Match-Accuracy'].mean()[0]
    configRow['Time-Taken(S)'] = testDataFrame.groupby('TestID')['Time-Taken(S)'].mean()[0]
    configRow['Data-To-Noise'] = testDataFrame.groupby('TestID')['Data-To-Noise'].mean()[0]

    groupedExperiments = groupedExperiments.append(configRow)


groupedExperiments.to_csv('./grouped-experiments-{}'.format(fileName), index=False)

print()