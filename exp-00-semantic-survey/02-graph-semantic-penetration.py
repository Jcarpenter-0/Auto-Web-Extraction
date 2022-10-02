import requests
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt


dataFD = open('./dset-fixed.json', 'r')
rawData = json.load(dataFD)
dataFD.close()

# Need to get the averages per website
LangOccurencesByWebsite = {}

for website in rawData.keys():

    for lang in rawData[website].keys():
        if lang not in LangOccurencesByWebsite:
            LangOccurencesByWebsite[lang] = []

        LangOccurencesByWebsite[lang].append(rawData[website][lang])

macroDF = pd.DataFrame()
for lang in LangOccurencesByWebsite.keys():
    macroDF[lang] = LangOccurencesByWebsite[lang]

print(len(macroDF))
ax = macroDF.boxplot(figsize=(13, 6), fontsize=18, color=dict(boxes='black', whiskers='black', medians='black', caps='black'), showfliers=False)
ax.set_ylabel('Occurrences By Website', fontsize=18)
ax.set_xlabel('Language', fontsize=16)
plt.xticks(rotation=0, fontsize=20)
plt.yticks(range(0,22,2), fontsize=20)
plt.title('', fontsize=0)
plt.suptitle('')
plt.tight_layout()

plt.savefig('./lang-penetration.jpg')
plt.close()
