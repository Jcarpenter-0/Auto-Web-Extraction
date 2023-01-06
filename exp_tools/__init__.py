import json
from difflib import SequenceMatcher

import pandas as pd


# https://stackoverflow.com/questions/17388213/find-the-similarity-metric-between-two-strings

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def CheckScrapeAnswers2(data:pd.DataFrame, answerKey:pd.DataFrame) -> dict:
    """Given a csv (dataframe) of labeled field answers, will match against what was found on a few criteria:
    """

    # Load in the answer keys, and unpack them for a "per-data item" cross-off approach
    answerKeyUnpacked = []
    for rowIdx, answerRow in answerKey.iterrows():
        # only need to check against the data item and the label
        dataItems = answerRow['field-value'].split('|')
        for dataItem in dataItems:
            if 'label-type' == 'Label-Less':
                answerKeyUnpacked.append((dataItem, answerRow['parse-primitive']))
            else:
                answerKeyUnpacked.append((dataItem, answerRow['label-html-text']))

    totalAnswerDataFields = len(answerKeyUnpacked)

    matches = 0

    # Go through each data item found by the system, and if a full match, delete from the answerKey
    for rowIdx, dataRow in data.iterrows():
        for answerIdx, answerField in enumerate(answerKeyUnpacked):
            if answerField[0] in dataRow['Value'] and answerField[1] in dataRow['Label']:
                matches += 1
                del answerKeyUnpacked[answerIdx]
                break

    # Noise, Match-Accuracy
    statsDict = dict()
    statsDict['Match-Accuracy'] = matches/totalAnswerDataFields
    statsDict['Data-To-Noise'] = matches/len(data)

    return statsDict

