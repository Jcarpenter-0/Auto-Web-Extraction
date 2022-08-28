from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver
import extraction_process


pageLoadTimeoutInSeconds = 20
pageScriptTimeoutInSeconds = 3
pageSleepTimeInSeconds = 2
fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.headless = False
browser = webdriver.Firefox(options=fireFoxOptions)
browser.set_page_load_timeout(pageLoadTimeoutInSeconds)
browser.set_script_timeout(pageScriptTimeoutInSeconds)

# parse the labeled data

extraction_process.GrabAll()


