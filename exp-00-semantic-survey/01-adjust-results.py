import requests
import pandas as pd
import numpy as np

surveyDataFD = open('./dset.json', 'r')

data = surveyDataFD.read()

data = data.replace('\'','\"')

surveyDataFD.close()

convoData = open('./dset-fixed.json', 'w')

convoData.writelines(data)

convoData.flush()
convoData.close()