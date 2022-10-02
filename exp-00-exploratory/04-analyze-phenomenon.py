import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ===========================================================
#
# ===========================================================

websiteStats = pd.read_csv('./report.csv')

#plot the occurrences of clusters
ax = websiteStats.boxplot(column=['Cluster-Count'],figsize=(6, 6), fontsize=18, color=dict(boxes='black', whiskers='black', medians='black', caps='black'), showfliers=False)
ax.set_ylabel('Cluster Occurrences By Website', fontsize=18)
ax.set_xlabel('', fontsize=0)
plt.xticks(rotation=0, fontsize=0)
plt.yticks(fontsize=20)
plt.title('Phenomenon Occurrence', fontsize=20)
plt.suptitle('')
plt.tight_layout()

plt.savefig('./cluster-count.jpg')
plt.close()

