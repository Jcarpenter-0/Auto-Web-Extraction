import datetime
from selenium import webdriver
import pandas as pd
import context.sources
import context.sources.evaluations
import context.sources.filtrations


link = 'https://research.com/conference/ccnc-2022-ieee-consumer-communications-and-networking-conference'

urlDF = pd.DataFrame()

urlDF['TargetURL'] = [link]

pageLoadTimeoutInSeconds = 10
pageScriptTimeoutInSeconds = 3

domainChecks = set()
domainDics = set()
domainIgnores = {'googleadservices', 'youtube', 'allconferencealert','startupstash','job','advertising', 'support'}

dirChecks = {'Computer', 'Networking', 'Networks', 'Conferences', 'Network', 'Conference', '2022', '22', 'Top', 'Science'}
dirDics = {'search', 'news', 'calendar','newsletter','journal'}
dirIgnores = {'editor','about', 'advertising','communities','professional','job','membership'}

pathChecks = {'Computer', 'Networking', 'Networks', 'Conferences', 'Network', 'Conference', '2022', '22', 'Top', 'Science', 'symposium'}
pathDiscs = {'search', 'news', 'editor','subscriptions','calendar','tool', 'organize','insider'}
pathIgnores = {'#', 'shopping', 'store', 'map', 'course', 'flight', 'product', 'podcast', 'finance', 'login', 'contact', 'subscribe', 'webinar', 'policy', 'subscriptions','magazines','account','sponsorship','volunteering','advertising','job', 'registration','cart','join','newsletter'}

mimeChecks = {'html'}
mimeDiscs = set()
mimeIgnores = {'pdf', 'video', 'image', 'book', 'mail', 'zip', 'rar', 'exe', 'png', 'jpg', 'jpeg','docx','doc','odt','txt'}

pageCheck = set()
pageCheck.update(dirChecks)
pageCheck.update(pathChecks)
pageCheck.update(domainChecks)


evaluator = context.sources.evaluations.CustomEvaluation(domainChecks=domainChecks, domainDiscs=domainDics, domainIgnores=domainIgnores,
                                                         dirChecks=dirChecks, dirDiscs=dirDics, dirIgnores=dirIgnores,
                                                         pathChecks=pathChecks, pathDiscs=pathDiscs, pathIgnores=pathIgnores,
                                                         mimeChecks=mimeChecks, mimeDiscs=mimeDiscs, mimeIgnores=mimeIgnores, pageChecks=pageCheck)



fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.headless = True

# Call web page
browser = webdriver.Firefox(options=fireFoxOptions)

browser.set_page_load_timeout(pageLoadTimeoutInSeconds)
browser.set_script_timeout(pageScriptTimeoutInSeconds)


siteLinks, pageEval = evaluator.EvaluatePage(browser, urlDF.iloc[0], 0, 0, 5)

originalSize = len(siteLinks)

siteLinks = siteLinks[siteLinks['DomainIgnore'] == False]
siteLinks = siteLinks[siteLinks['IsQuerier'] == False]
siteLinks = siteLinks[siteLinks['IsFragment'] == False]
siteLinks = siteLinks[siteLinks['MimetypeIgnore'] == False]
siteLinks = siteLinks[siteLinks['Explored'] == False]

print('Site Links {} vs {}'.format(len(siteLinks), originalSize))

browser.quit()
