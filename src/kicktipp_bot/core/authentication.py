"""Authentication module for Kicktipp login functionality."""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from ..config import Config
from ..utils.selenium_utils import SeleniumUtils

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication failures."""
    pass


class Authenticator:
    """Handles user authentication for Kicktipp."""

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def login(self) -> None:
        """Perform login to Kicktipp."""
        if not Config.EMAIL or not Config.PASSWORD:
            raise AuthenticationError("Email and password must be configured")

        logger.info("Starting login process...")

        try:
            # Navigate to login page
            logger.debug("Navigating to login page")
            self.driver.get(Config.LOGIN_URL)

            # Wait for page to load
            if not SeleniumUtils.wait_for_page_load(self.driver):
                raise AuthenticationError("Login page failed to load")

            # Enter credentials
            self._enter_credentials()

            # Submit login form
            self._submit_login()

            # Verify login success
            self._verify_login()

            logger.info("Login completed successfully")

        except AuthenticationError:
            raise
        except WebDriverException as e:
            raise AuthenticationError(f"WebDriver error during login: {e}")
        except Exception as e:
            raise AuthenticationError(f"Unexpected error during login: {e}")

    def _enter_credentials(self) -> None:
        """Enter email and password in the login form."""
        logger.debug("Entering login credentials")

        # Find email field
        email_field = SeleniumUtils.safe_find_element(self.driver, By.ID, "kennung")
        if not email_field:
            raise AuthenticationError("Could not find email input field")

        # Find password field
        password_field = SeleniumUtils.safe_find_element(self.driver, By.ID, "passwort")
        if not password_field:
            raise AuthenticationError("Could not find password input field")

        # Enter credentials
        if not SeleniumUtils.safe_send_keys(email_field, Config.EMAIL, "email field"):
            raise AuthenticationError("Failed to enter email")

        if not SeleniumUtils.safe_send_keys(password_field, Config.PASSWORD, "password field"):
            raise AuthenticationError("Failed to enter password")

        logger.debug("Credentials entered successfully")

    def _submit_login(self) -> None:
        """Submit the login form."""
        logger.debug("Submitting login form")

        submit_button = SeleniumUtils.safe_find_element(self.driver, By.NAME, "submitbutton")
        if not submit_button:
            raise AuthenticationError("Could not find login submit button")

        if not SeleniumUtils.safe_click(submit_button, "login submit button"):
            raise AuthenticationError("Failed to click login submit button")

    def _verify_login(self) -> None:
        """Verify that login was successful."""
        logger.debug("Verifying login success")

        try:
            current_url = self.driver.current_url
            if current_url == Config.BASE_URL:
                logger.info("Login verification successful")
            else:
                raise AuthenticationError(f"Login failed - redirected to: {current_url}")
        except WebDriverException as e:
            raise AuthenticationError(f"Could not verify login status: {e}")

    def accept_terms_and_conditions(self) -> None:
        """Accept terms and conditions if the dialog appears."""
        logger.debug("Checking for terms and conditions dialog")

        # Try to find and click the accept button
        accept_button = SeleniumUtils.safe_find_element(
            self.driver,
            By.XPATH,
            '//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]',
            timeout=3  # Short timeout since this may not exist
        )

        if accept_button:
            if SeleniumUtils.safe_click(accept_button, "terms and conditions accept button"):
                logger.info("Accepted terms and conditions")
            else:
                logger.warning("Found terms dialog but failed to click accept button")
        else:
            logger.debug("No terms and conditions dialog found")
