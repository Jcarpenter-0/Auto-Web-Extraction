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

# Get the URLs
linksDF, seconds = extraction_process.HF(browser, 'What games for Nintendo Switch are coming out this month?')

# Check if answer is in the final
Answer = ''

print('')


