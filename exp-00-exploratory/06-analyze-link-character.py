import pandas as pd
from selenium import webdriver
import context.formats.html
import context.sources


siteDF = pd.read_csv('./input-general-websites/top-10.csv', header=None)

siteReport = pd.DataFrame()

# Setup Headless
fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.headless = True

# Call web page
browser = webdriver.Firefox(options=fireFoxOptions)

siteNames = []
siteLinks = []
siteLinkLens = []
siteInDegs = []
siteOutDegs = []

for idx, site in siteDF.iterrows():

    print('{}/{}'.format(idx+1, len(siteDF)))

    url = site[1]
    siteNames.append(url)

    if 'http' not in url:
        subLinks, inDeg, outDeg, passed = context.sources.AssessWebPage(browser, 'https://www.{}'.format(url))

        siteLinks.append(subLinks)
        siteLinkLens.append(len(subLinks))
        siteInDegs.append(inDeg)
        siteOutDegs.append(outDeg)

    else:
        subLinks, inDeg, outDeg, passed = context.sources.AssessWebPage(browser, url)
        siteLinks.append(subLinks)
        siteLinkLens.append(len(subLinks))
        siteInDegs.append(inDeg)
        siteOutDegs.append(outDeg)

siteReport['Site-Name'] = siteNames
siteReport['Links'] = siteLinks
siteReport['Link-Count'] = siteLinkLens
siteReport['In-Degrees'] = siteInDegs
siteReport['Out-Degrees'] = siteOutDegs
siteReport['I/O Ratio'] = siteReport['Out-Degrees']/siteReport['In-Degrees']

browser.quit()

siteReport.to_csv('./site-survey-links.csv', index=False)
