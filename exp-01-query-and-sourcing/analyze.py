import pandas as pd
import glob
from urllib.parse import urlparse

# ======================================================================================================================
# Check if the found links contained the links we "know" are right
# ======================================================================================================================

dataFiles = glob.glob('./test-*-*/ses-*-depth-*-links-*-time-*.csv')

answerLinksDF = pd.read_csv('./answer-links.csv')
totalNumberOfAnswers = len(answerLinksDF)
answerCollection = answerLinksDF['Valid-Links'].apply(lambda x: x.split(','))


def AnswerCheck(row, answerField) -> bool:
    for answerGroup in answerField:
        if row['TargetURL'] in answerGroup:
            #print('{} Matched {}'.format(row['TargetURL'], answerGroup))
            return True

    return False


for dataFile in dataFiles:
    links = pd.read_csv(dataFile)

    totalNumberOfLinks = len(links)

    testCaseOutcomes = pd.DataFrame()

    testCaseOutcomes['Outcome'] = links.apply(lambda x : AnswerCheck(x, answerCollection), axis=1)

    totalNumberOfAnswersFound = len(testCaseOutcomes[testCaseOutcomes['Outcome'] == True])

    noiseToAnswerRatio = totalNumberOfAnswersFound/totalNumberOfLinks
    accuracy = totalNumberOfAnswersFound/totalNumberOfAnswers

    print('Accuracy {} ({}/{}) noise-to-data Ratio {}. {}'.format(accuracy, totalNumberOfAnswersFound, totalNumberOfAnswers, noiseToAnswerRatio, dataFile))

