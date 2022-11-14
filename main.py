import os
import random
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Constants

BASE_URL = "https://www.kicktipp.de"
LOGIN_URL = "https://www.kicktipp.de/info/profil/login"
EMAIL = os.getenv("KICKTIPP_EMAIL")
PASSWORD = os.getenv("KICKTIPP_PASSWORD")
NAME_OF_COMPETITION = os.getenv("KICKTIPP_NAME_OF_COMPETITION")
CHROMEDRIVER_PATH = "/Applications/chromedriver"
# DAY_OF_EXECUTION = os.getenv("DAY_OF_EXECUTION")  # wednesday
DAY_OF_EXECUTION = 0


def execute():

    # create driver
    driver = webdriver.Chrome(CHROMEDRIVER_PATH)
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
    
    # select competition
    driver.find_element(
        by=By.PARTIAL_LINK_TEXT, value=str(NAME_OF_COMPETITION)).click()

    # select entry item
    driver.find_element(
        by=By.XPATH, value='//*[@id="navigation"]/div[5]/a').click()

    sleep(0.1)

    # iterate over rows of the form
    for i in range(1, 10):
        sleep(0.1)
        # find quotes
        quotes = driver.find_element(
            by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[5]/a')
        content = quotes.get_property('innerHTML')
        # split quotes by seperator
        splitted = str.split(content, sep=' / ')

        # get Team names
        homeTeam = driver.find_element(
            by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[2]').get_attribute('innerHTML')
        awayTeam = driver.find_element(
            by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[3]').get_attribute('innerHTML')

        # print quotes and team names
        print(homeTeam + " - " + awayTeam + "\nQuotes:" + str(splitted))

        # calculate tips bases on quotes and print them
        tip = calculate_tip(float(splitted[0]), float(
            splitted[1]), float(splitted[2]))
        print("Tip:" + str(tip))
        print()

        try:
        # find entry, clear it and enter tip
            homeTipEntry = driver.find_element(by=By.XPATH,
                                           value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[4]/input[2]')
            homeTipEntry.clear()
            homeTipEntry.send_keys(tip[0])
        except NoSuchElementException:
            pass


        try:
        # find entry, clear it and enter tip
            awayTipEntry = driver.find_element(by=By.XPATH,
                                           value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[4]/input[3]')
            awayTipEntry.clear()
            awayTipEntry.send_keys(tip[1])
        except NoSuchElementException:
            pass
    # submit all tips
    driver.find_element(by=By.NAME, value="submitbutton").click()

    # sleep to display browser
    sleep(10)


def calculate_tip(home, draw, away) -> (int, int):
    """ Calculates the tip based on the quotes"""

    # if negative the home team is more likely to win
    differenceHomeAndAway = home - away

    # generate random number between 0 and 1
    onemore = round(random.uniform(0, 1))

    # depending on the quotes, the factor is derived to decrease the tip for very unequal games
    coefficient = 0.3 if differenceHomeAndAway > 8 else 0.9

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


if __name__ == '__main__':
    while True:
        now = datetime.now()
        formatted = now.strftime("%w")
        
        if formatted == str(DAY_OF_EXECUTION):
            print("The Script will execute now!")
            execute()
            sleep(60 * 60 * 24)  # sleep for 24 hours

        print(datetime.now().strftime("%d-%m-%y") + ": Sleeping! Day of week is " +
              formatted + " and day of execution is " + str(DAY_OF_EXECUTION))
        sleep(30)
