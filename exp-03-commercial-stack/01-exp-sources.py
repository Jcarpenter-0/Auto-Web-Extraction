from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver
import extraction_process


# Setup the browser
pageLoadTimeoutInSeconds = 20
pageScriptTimeoutInSeconds = 3
pageSleepTimeInSeconds = 2
fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.headless = True
browser = webdriver.Firefox(options=fireFoxOptions)
browser.set_page_load_timeout(pageLoadTimeoutInSeconds)
browser.set_script_timeout(pageScriptTimeoutInSeconds)

getAnswers = False
Answers = ['https://www.nintendo.com/store/games/coming-soon/', 'https://www.nintendo.com/store/games/new-releases/']

if getAnswers:
    for answer in Answers:
        print('Getting Answer {}'.format(answer))
        elementList, elementDF = extraction_process.AnalyzeWebPage(browser,answer,pageWait=pageLoadTimeoutInSeconds)

        outputName = answer.split('//')[-1].replace('/','-')
        outputName = outputName + 'site.csv'
        elementDF.to_csv(outputName, index=False)


# Get the URLs
#linksDF, seconds = extraction_process.HF(browser, 'What games for Nintendo Switch are coming out this month?',                                         maxDepth=2)

linksDF, seconds = extraction_process.SETS(browser, 'What games for Nintendo Switch are coming out this month?')

browser.quit()

# Check if answer is in the final
targetURLs = linksDF['TargetURL'].values

correctAnswers = 0
for Answer in Answers:
    if Answer in targetURLs:
        correctAnswers += 1

noise = correctAnswers/len(linksDF)

print('Accuracy {} ({}/{}) noise-to-data Ratio {} ~ {} seconds'.format(correctAnswers/len(Answers),
                                                              correctAnswers,
                                                              correctAnswers,
                                                              noise, seconds))



