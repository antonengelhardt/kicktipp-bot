import os
import sys
from datetime import datetime
from datetime import timedelta
from time import sleep
import requests

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from game import Game

# Constants
BASE_URL = "https://www.kicktipp.de/"
LOGIN_URL = "https://www.kicktipp.de/info/profil/login/"
RUN_EVERY_X_MINUTES = os.getenv("KICKTIPP_RUN_EVERY_X_MINUTES") or 60
EMAIL = os.getenv("KICKTIPP_EMAIL")
PASSWORD = os.getenv("KICKTIPP_PASSWORD")
NAME_OF_COMPETITION = os.getenv("KICKTIPP_NAME_OF_COMPETITION")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")
ZAPIER_URL = os.getenv("ZAPIER_URL")
TIME_UNTIL_GAME = os.getenv("KICKTIPP_HOURS_UNTIL_GAME") != None and timedelta(
    hours=int(os.getenv("KICKTIPP_HOURS_UNTIL_GAME"))) or timedelta(hours=2)
NTFY_URL = os.getenv("NTFY_URL")
NTFY_USERNAME = os.getenv("NTFY_USERNAME")
NTFY_PASSWORD = os.getenv("NTFY_PASSWORD")
HOME_ASSISTANT_WEBHOOK_URL = os.getenv("HOME_ASSISTANT_WEBHOOK_URL")


def tip_all_games():

    # create driver
    driver = create_driver()

    # login
    login(driver)

    # entry form
    driver.get(F"https://www.kicktipp.de/{NAME_OF_COMPETITION}/tippabgabe")

    # accept AGB
    sleep(5)
    accept_agbs(driver)

    # get number of rows
    games_count = len(driver.find_elements(
        by=By.CLASS_NAME, value="datarow"))

    # iterate over rows of the form
    for i in range(1, games_count):
        try:
            tip_game(driver, i)

        except NoSuchElementException:
            # try to accept AGB again
            accept_agbs(driver)

            tip_game(driver, i)

            # and then try next row
            continue
    sleep(0.1)

    # submit all tips
    driver.find_element(by=By.NAME, value="submitbutton").click()

    try:
        if sys.argv[1] == '--local':
            print("Sleeping for 20secs to see the result - Debug Mode\n")
            sleep(20)
    except IndexError:
        pass

    driver.quit()


def create_driver():
    if CHROMEDRIVER_PATH is not None:
        print('Custom Chrome Driver Path\n')
        driver = webdriver.Chrome(CHROMEDRIVER_PATH)  # for local

    try:
        if sys.argv[1] == '--headless':
            print('Headless Mode\n')
            driver = webdriver.Chrome(
                options=set_chrome_options())  # for docker

    except IndexError:
        print('Debug Mode\n')
        driver = webdriver.Chrome()  # debug

    return driver


def login(driver):

    print("Logging in...")

    # login
    driver.get(LOGIN_URL)

    # enter email
    driver.find_element(by=By.ID, value="kennung").send_keys(EMAIL)

    # enter password
    driver.find_element(by=By.ID, value="passwort").send_keys(PASSWORD)

    # send login
    driver.find_element(by=By.NAME, value="submitbutton").click()

    if driver.current_url == BASE_URL:
        print("Logged in!\n")
    else:
        print("Login failed!\n")


def tip_game(driver, i):

    # time of game, if empty, use previous row's time
    for j in range(i, 0, -1):
        xpath_row = '//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(j) + ']'
        try:
            time = datetime.strptime(
                driver.find_element(
                    by=By.XPATH, value=xpath_row + '/td[1]').get_property('innerHTML'),
                '%d.%m.%y %H:%M')
            if time is not None:
                break
        except ValueError:
            continue

    # if time is still None, use current time
    if time is None:
        print("Time not found, using current time as default.")
        time = datetime.now()

    # xpath to row
    xpath_row = '//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']'

    # get Team names
    home_team = driver.find_element(
        by=By.XPATH, value=xpath_row + '/td[2]').get_attribute('innerHTML')
    away_team = driver.find_element(
        by=By.XPATH, value=xpath_row + '/td[3]').get_attribute('innerHTML')

    # print time and team names
    print(home_team + " - " + away_team)
    print("Time: " + str(time.strftime('%d.%m.%y %H:%M')))

    # find entry fields. if not found, the game is over
    try:
        home_tip_entry = driver.find_element(by=By.XPATH,
                                             value=xpath_row + '/td[4]/input[2]')
        away_tip_entry = driver.find_element(by=By.XPATH,
                                             value=xpath_row + '/td[4]/input[3]')
    except NoSuchElementException:
        # print out the tipped game
        print("Game is over: " + driver.find_element(
            by=By.XPATH, value=xpath_row + '/td[4]').get_attribute('innerHTML').replace(":", " - ") + "\n")
        return

    # only continue if the game is not tipped yet
    if home_tip_entry.get_attribute('value') != "" and away_tip_entry.get_attribute('value') != "":
        print("Game already tipped: " + driver.find_element(
            by=By.XPATH, value=xpath_row + '/td[4]/input[2]').get_attribute('value') + " - " + driver.find_element(
            by=By.XPATH, value=xpath_row + '/td[4]/input[3]').get_attribute('value') + "\n")
        return

    # time until start of game
    time_until_game = time - datetime.now()
    print("Time until game: " + str(time_until_game))

    # only tip if game starts in less than defined time
    if time_until_game > TIME_UNTIL_GAME:

        print("Game starts in more than ", TIME_UNTIL_GAME, ". Skipping...\n")

    else:
        print("Game starts in less than ", TIME_UNTIL_GAME, ". Tipping...")

        # find quotes
        quotes_raw = driver.find_element(
            by=By.XPATH, value=xpath_row + '/td[5]/a').get_property('innerHTML')

        quotes_sanitized = quotes_raw.replace("Quote: ", "")
        if quotes_sanitized.find("/"):
            quotes = quotes_sanitized.split(" / ")
        elif quotes_sanitized.find(" | "):
            quotes = quotes_sanitized.split(" | ")
        else:
            print("Quotes not found")
            return

        # create game object
        game = Game(home_team, away_team, quotes, time)

        # print quotes
        print("Quotes:" + str(quotes))

        # calculate tips bases on quotes and print them
        tip = game.calculate_tip(float(quotes[0]), float(quotes[2]))
        print("Tip: " + str(tip), "\n")

        # send tips
        home_tip_entry.send_keys(tip[0])
        away_tip_entry.send_keys(tip[1])

        # custom webhook to zapier
        send_zapier_webhook(time, home_team, away_team, quotes, tip)

        # ntfy notification
        send_ntfy_notification(time, home_team, away_team, quotes, tip)

        send_home_assistant_notification(
            time, home_team, away_team, quotes, tip)


def send_zapier_webhook(time, home_team, away_team, quotes, tip):
    if ZAPIER_URL is not None:
        try:
            payload = {
                'date': time,
                'team1': home_team,
                'team2': away_team,
                'quoteteam1': quotes[0],
                'quotedraw': quotes[1],
                'quoteteam2': quotes[2],
                'tipteam1': tip[0],
                'tipteam2': tip[1]}
            files = []
            headers = {}

            requests.post(ZAPIER_URL, headers=headers,
                          data=payload, files=files)
        except IndexError:
            pass


def send_ntfy_notification(time, home_team, away_team, quotes, tip):
    if NTFY_URL is not None and NTFY_USERNAME is not None and NTFY_PASSWORD is not None:
        try:
            data = f"Time: {time.strftime('%d.%m.%y %H:%M')}\nQuotes: {quotes}"

            headers = {
                "X-Title": f"{home_team} - {away_team} tipped {tip[0]}:{tip[1]}",
            }

            # utf-8 encode headers
            headers = {k: v.encode('utf-8') for k, v in headers.items()}

            requests.post(NTFY_URL, auth=(
                NTFY_USERNAME, NTFY_PASSWORD), data=data, headers=headers)

        except IndexError:
            pass


def send_home_assistant_notification(time, home_team, away_team, quotes, tip):
    if HOME_ASSISTANT_WEBHOOK_URL is not None:
        try:
            data = {
                "home_team": home_team,
                "away_team": away_team,
                "quotes": quotes,
                "tip": tip,
                "time": time.strftime('%d.%m.%y %H:%M')
            }

            headers = {
                "Content-Type": "application/json",
            }

            requests.post(HOME_ASSISTANT_WEBHOOK_URL,
                          json=data, headers=headers)

        except IndexError:
            pass


def accept_agbs(driver):
    try:
        driver.find_element(
            by=By.XPATH, value='//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]').click()
    except NoSuchElementException:
        pass


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
        if EMAIL is None or PASSWORD is None or NAME_OF_COMPETITION is None:
            print("Please set the environment variables KICKTIPP_EMAIL, KICKTIPP_PASSWORD and KICKTIPP_NAME_OF_COMPETITION")
            exit(1)

        now = datetime.now().strftime('%d.%m.%y %H:%M')
        print(now + ": The script will execute now!\n")

        try:
            tip_all_games()
        except Exception as e:
            print(str(e) + "\n")

        print(
            now + f": The script has finished. Sleeping for {RUN_EVERY_X_MINUTES} minutes\n")
        sleep(int(RUN_EVERY_X_MINUTES) * 60)
