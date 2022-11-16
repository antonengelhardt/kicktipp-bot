import os
import random
import sys
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Constants

BASE_URL = "https://www.kicktipp.de"
LOGIN_URL = "https://www.kicktipp.de/info/profil/login"
EMAIL = os.getenv("KICKTIPP_EMAIL")
PASSWORD = os.getenv("KICKTIPP_PASSWORD")
NAME_OF_COMPETITION = os.getenv("KICKTIPP_NAME_OF_COMPETITION")
CHROMEDRIVER_PATH = "/Applications/chromedriver"


def execute():

    # create driver
    if sys.argv[1] == 'headless':
        driver = webdriver.Chrome(options=set_chrome_options())  # for docker
    elif sys.argv[1] == 'local':
        driver = webdriver.Chrome(CHROMEDRIVER_PATH)  # for local

    # login
    driver.get(LOGIN_URL)

    # enter email
    driver.find_element(by=By.ID, value="kennung").send_keys(EMAIL)

    # enter password
    driver.find_element(by=By.ID, value="passwort").send_keys(PASSWORD)

    # send login
    driver.find_element(by=By.NAME, value="submitbutton").click()

    # accept AGB
    try:
        driver.find_element(
            by=By.XPATH, value='//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]').click()
    except NoSuchElementException:
        pass

    # entry form
    driver.get(F"https://www.kicktipp.de/{NAME_OF_COMPETITION}/tippabgabe")

    count = driver.find_elements(by=By.CLASS_NAME, value="datarow").__len__()

    # iterate over rows of the form
    for i in range(1, count + 1):
        try:
            # find entry, enter if empty
            homeTipEntry = driver.find_element(by=By.XPATH,
                                               value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[4]/input[2]')
            awayTipEntry = driver.find_element(by=By.XPATH,
                                               value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[4]/input[3]')

            # only calc tip and enter, when not entered already
            if homeTipEntry.get_attribute('value') == '' and awayTipEntry.get_attribute('value') == '':

                # find quotes
                quotes = driver.find_element(
                    by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[5]/a').get_property('innerHTML').split(sep=" / ")

                # get Team names
                homeTeam = driver.find_element(
                    by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[2]').get_attribute('innerHTML')
                awayTeam = driver.find_element(
                    by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[3]').get_attribute('innerHTML')

                # print quotes and team names
                print(homeTeam + " - " + awayTeam +
                      "\nQuotes:" + str(quotes))

                # calculate tips bases on quotes and print them
                tip = calculate_tip(float(quotes[0]), float(quotes[1]), float(quotes[2]))
                print("Tip:" + str(tip))
                print()

                homeTipEntry.send_keys(tip[0])
                awayTipEntry.send_keys(tip[1])

              # submit all tips

        except NoSuchElementException:
            continue
    sleep(0.1)

    #submit all tips
    driver.find_element(by=By.NAME, value="submitbutton").submit()

    if sys.argv[1] == 'local':
        sleep(20)

    try:
        print("Total bet: " + driver.find_element(by=By.XPATH,
              value='//*[@id="kicktipp-content"]/div[2]/div[2]/a/div/div[1]/div[1]/div[1]/div[2]/span[2]'))
    except NoSuchElementException:
        pass

    driver.quit()


def calculate_tip(home, draw, away):
    """ Calculates the tip based on the quotes"""

    # if negative the home team is more likely to win
    differenceHomeAndAway = home - away

    # generate random number between 0 and 1
    onemore = round(random.uniform(0, 1))

    # depending on the quotes, the factor is derived to decrease the tip for very unequal games
    coefficient = 0.3 if round(abs(differenceHomeAndAway)) > 7 else 0.75

    # calculate tips
    if abs(differenceHomeAndAway) < 0.25:
        return onemore, onemore
    else:
        if differenceHomeAndAway < 0:
            return round(-differenceHomeAndAway * coefficient) + onemore, onemore
        elif differenceHomeAndAway > 0:
            return onemore, round(differenceHomeAndAway * coefficient) + onemore
        else:
            return onemore, onemore


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


if __name__ == '__main__':
    while True:
        print("The script will execute now")
        execute()
        print("The script has finished. Sleeping for 1 hour")
        sleep(60*60)
