import glob
import pandas as pd
from selenium import webdriver
import context.formats.html
import context.sources

IgnoreExtensions = ['cn', 'ru', 'jp', 'hk', 'in', 'de', 'fr', 'it', 'tw', 'sg', 'mx', 'tr', 'br', 'la', 'ar', 'ir', 'co', 've', 'pl']

topNDF = pd.read_csv('./input-general-websites/top-1000000.csv', header=None)

screenShot = False

siteReport = pd.DataFrame()

holdSites = glob.glob('./output-website-data/holds/*.csv')
holdNames = []

for holdPath in holdSites:
    holdNames.append(holdPath.split('/')[-1])

def ParseWebSite(row):

    siteURL = row[1]
    siteExtension = siteURL.split('.')[-1]
    siteName = siteURL.replace('.', '-').replace('/', '-').replace('#', '-').replace(':', '-')
    siteFileName = siteName + '.csv'

    if siteFileName not in holdNames:

        if siteExtension not in IgnoreExtensions:


            print(siteURL)
            try:
                # Setup Headless
                fireFoxOptions = webdriver.FirefoxOptions()
                fireFoxOptions.headless = True

                # Call web page
                browser = webdriver.Firefox(options=fireFoxOptions)

                # Navigate to the site
                if 'http' not in siteURL:
                    siteElements, siteElementsDF, listSiteElements = context.formats.html.ParseWebPage('https://www.{}'.format(siteURL), browser)

                else:
                    siteElements, siteElementsDF, listSiteElements = context.formats.html.ParseWebPage(siteURL, browser)

                if screenShot:
                    # take a screenshot
                    browser.save_screenshot("./output-website-data/{}.png".format(siteName))

                print('Closing')
                browser.close()
                browser.quit()

                siteElements.to_csv('./output-website-data/{}.csv'.format(siteName), index=None)
            except Exception as ex:
                print('EX {}'.format(ex))
                if browser is not None:
                    browser.close()
                    browser.quit()


topNDF.apply(lambda x : ParseWebSite(x), axis=1)

siteReport.to_csv('./site-survey-links.csv', index=False)

print('Done')
