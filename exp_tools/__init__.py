import json
from difflib import SequenceMatcher

import pandas as pd


# https://stackoverflow.com/questions/17388213/find-the-similarity-metric-between-two-strings

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def CheckScrapeAnswers2(data:pd.DataFrame, answerKey:pd.DataFrame) -> dict:
    """Given a csv (dataframe) of labeled field answers, will match against what was found on a few criteria:
    """

    statsDict = dict()

    # Label accuracy,
    dataLabels = list(data['Label'])
    keyLabels = list(answerKey['Label'])

    foundLabels = 0

    for labelIndex, keyLabel in enumerate(keyLabels):

        for dataLabelIndex, dataLabel in enumerate(dataLabels):

            # If the data item is found, remove from list, break loop
            if keyLabel in dataLabel:
                foundLabels += 1
                dataLabels.pop(dataLabelIndex)

    #statsDict['Label-Accuracy'] = foundLabels/len(keyLabels)

    # Data accuracy,
    foundData = 0
    matchedData = 0

    remainingData = data.copy()
    del remainingData['clusterID']
    remainingData = remainingData.reset_index(drop=True)

    for rowIDX, keyDataElement in answerKey.iterrows():

        matched = False

        for row2IDX, dataElement in remainingData.iterrows():

            # If the data item is found, remove from list, break loop
            if keyDataElement['Value'] == dataElement['Value']:
                foundData += 1

                # Also check if the label is matched correctly
                if keyDataElement['Label'] in dataElement['Label']:
                    matchedData += 1
                    matched = True
                    remainingData = remainingData.drop(row2IDX)
                    break

                #break

        if matched is False:
            pass
            #print('Could not Match {}'.format(keyDataElement))

    #statsDict['Data-Accuracy'] = foundData/len(answerKey)

    statsDict['Match-Accuracy'] = matchedData/len(answerKey)

    # Noise, match accuracy/len(data)
    statsDict['Data-To-Noise'] = matchedData/len(data)

    return statsDict

