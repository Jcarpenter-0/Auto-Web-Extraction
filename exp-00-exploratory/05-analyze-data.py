import glob
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

# https://stackoverflow.com/questions/55260842/adjust-spacing-on-x-axis-in-python-boxplots

siteDataFilePaths = glob.glob('./output-conference-data/*.csv')

pointcolor = 'black'
# typical 48
fontSize = 24
figW = 12
figH = 12
lineWidth = 4
xRot = 25

# Want to get the overall demographics of the sites
macroDF = pd.DataFrame()
reportDF = pd.DataFrame()

siteNames = []

print('Sites {}'.format(len(siteDataFilePaths)))

# For the clustering value
distanceMod = 0.07

for sitePath in siteDataFilePaths:

    siteDF = pd.read_csv(sitePath)

    siteName = sitePath.split('/')[-1].replace('.csv','').replace('-','.')

    siteNames.append(siteName)

    # Add to full macro for high level generalization
    siteDF['Site-Name'] = siteName

    macroDF = macroDF.append(siteDF)

    subreport = pd.DataFrame()

    #
    numberOfLinks = len(siteDF[siteDF['TagName'] == 'a'])
    siteElements = siteDF[['RenderedX','RenderedY','TagIndex','TagDepth']]
    avgDist = np.mean(pdist(siteElements))

    subreport['Site-Name'] = [siteName]
    subreport['Average-InnerHtml-Size'] = ['{}+-{}'.format(np.average(siteDF['Len']), np.std(siteDF['Len']))]
    subreport['Number-Of-Elements'] = [siteDF.shape[0]]
    subreport['Number-Of-Links'] = [numberOfLinks]
    subreport['Link-To-Element-Ratio'] = round(subreport['Number-Of-Links']/siteDF.shape[0], 4)
    subreport['Average-Distance'] = [avgDist]

    # Do phenomenon clustering
    try:
        clustering = DBSCAN(eps=avgDist * distanceMod, min_samples=2).fit(siteElements)

        clusterLabels = np.unique(clustering.labels_)

        # If more than 1 cluster or more counted as "having phenomenon"
        subreport['Cluster-Count'] = [len(clusterLabels)]
    except:
        subreport['Cluster-Count'] = [0]

    reportDF = reportDF.append(subreport)

    # Graph tag index vs tag depth
    ax = siteDF.plot(figsize=(figW, figH), fontsize=fontSize, x='TagIndex',y='TagDepth', legend=False, color=pointcolor, lw=lineWidth)
    #ax = siteDF.plot.scatter(figsize=(figW, figH), fontsize=fontSize, x='TagIndex', y='TagDepth', legend=False, c=pointcolor)
    ax.set_ylabel('Tag Depth', fontsize=fontSize)
    ax.set_xlabel('Tag Index', fontsize=fontSize)
    plt.title('{}'.format(siteName), fontsize=fontSize)
    #plt.legend(prop={"size": fontSize})

    plt.savefig('./output-website-graphs/{}-lineplot-tag-depth-tag-index.jpg'.format(siteName))
    plt.close()

reportDF = reportDF.reset_index()
reportDF = reportDF.drop(['index'], axis=1)

reportDF.to_csv('./report.csv',index=False)

macroDF = macroDF.reset_index()
macroDF = macroDF.drop(['index'], axis=1)

# Graph InnerHtml size and element counts
print(len(macroDF))
print('avg {}'.format(macroDF['Len'].mean()))
ax = macroDF.boxplot(column=['Len'],figsize=(figW, figH), fontsize=fontSize, color=pointcolor, showfliers=False)
#ax = macroDF.boxplot(column=['Len'],figsize=(figW, figH), fontsize=fontSize, by='Site-Name', color=pointcolor, showfliers=True)

ax.set_ylabel('Size of InnerHtml', fontsize=fontSize)
ax.set_xlabel('', fontsize=0)
#plt.title('{}'.format(''), fontsize=fontSize)
plt.xticks(rotation=xRot, fontsize=fontSize * 0)
plt.title('', fontsize=0)
plt.suptitle('')
plt.tight_layout()
#plt.show()
plt.savefig('./output-website-graphs/boxplots-innerHtml.jpg')
plt.close()

ax = macroDF.boxplot(column=['TagDepth'],figsize=(figW, figH), fontsize=fontSize, by='Site-Name', color=pointcolor)
ax.set_ylabel('Tag Depth', fontsize=fontSize)
ax.set_xlabel('Sites', fontsize=fontSize)
plt.xticks(rotation=xRot)
plt.title('', fontsize=0)
plt.suptitle('')

plt.savefig('./output-website-graphs/boxplots-tagDepth.jpg')
plt.close()

# Clustering analysis
# https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
# https://scikit-learn.org/stable/modules/generated/sklearn.cluster.OPTICS.html

