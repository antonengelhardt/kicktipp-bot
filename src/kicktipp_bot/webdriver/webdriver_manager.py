"""WebDriver management module for browser automation."""

import logging
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

from ..config import Config

logger = logging.getLogger(__name__)


class WebDriverManager:
    """Manages WebDriver creation and configuration."""

    @staticmethod
    def create_driver() -> WebDriver:
        """Create and configure a WebDriver instance based on arguments and configuration."""
        # Check for custom chrome driver path
        if Config.CHROMEDRIVER_PATH is not None:
            logger.info('Using custom Chrome Driver path')
            return webdriver.Chrome(Config.CHROMEDRIVER_PATH)

        # Check for headless mode
        if WebDriverManager._is_headless_mode():
            logger.info('Running in headless mode')
            return webdriver.Chrome(options=WebDriverManager._get_headless_options())

        # Default mode
        return webdriver.Chrome()

    @staticmethod
    def _is_headless_mode() -> bool:
        """Check if the script should run in headless mode."""
        return len(sys.argv) > 1 and '--headless' in sys.argv

    @staticmethod
    def _get_headless_options() -> Options:
        """Configure Chrome options for headless browser operation."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-setuid-sandbox")

        return chrome_options
