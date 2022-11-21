import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def getLowestQuote(team1, team2):
     """Returns the lowest quote of the given teams"""
    try:
        if sys.argv[1] == 'headless':
            driver = webdriver.Chrome(
                options=set_chrome_options())  # for docker
        elif sys.argv[1] == 'local':
            driver = webdriver.Chrome()  # for local
    except IndexError:
        print('Debug Mode\n')
        driver = webdriver.Chrome()  # debug
        
def set_chrome_options() -> None:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return chrome_options
