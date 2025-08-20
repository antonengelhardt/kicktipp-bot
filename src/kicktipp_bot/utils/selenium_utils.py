"""Utility functions for safe Selenium operations with robust error handling."""

import logging
from time import sleep
from typing import Optional, List, Callable, Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementNotInteractableException,
    WebDriverException
)

logger = logging.getLogger(__name__)


class SeleniumUtils:
    """Utility class for safe Selenium operations."""

    DEFAULT_TIMEOUT = 10
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_DELAY = 1

    @staticmethod
    def safe_find_element(
        driver: WebDriver,
        by: By,
        value: str,
        timeout: int = DEFAULT_TIMEOUT,
        retry_count: int = DEFAULT_RETRY_COUNT
    ) -> Optional[WebElement]:
        """
        Safely find a single element with retry logic.

        Args:
            driver: WebDriver instance
            by: Locator strategy (By.ID, By.XPATH, etc.)
            value: Locator value
            timeout: Maximum wait time in seconds
            retry_count: Number of retry attempts

        Returns:
            WebElement if found, None otherwise
        """
        for attempt in range(retry_count):
            try:
                wait = WebDriverWait(driver, timeout)
                element = wait.until(
                    EC.presence_of_element_located((by, value)))
                logger.debug(f"Element found: {by}='{value}'")
                return element

            except TimeoutException:
                logger.warning(
                    f"Element not found (attempt {attempt + 1}/{retry_count}): {by}='{value}'")
                if attempt < retry_count - 1:
                    sleep(SeleniumUtils.DEFAULT_RETRY_DELAY)

            except WebDriverException as e:
                logger.error(
                    f"WebDriver error finding element {by}='{value}': {e}")
                if attempt < retry_count - 1:
                    sleep(SeleniumUtils.DEFAULT_RETRY_DELAY)
                else:
                    break

        logger.error(
            f"Failed to find element after {retry_count} attempts: {by}='{value}'")
        return None

    @staticmethod
    def safe_find_elements(
        driver: WebDriver,
        by: By,
        value: str,
        timeout: int = DEFAULT_TIMEOUT
    ) -> List[WebElement]:
        """
        Safely find multiple elements.

        Args:
            driver: WebDriver instance
            by: Locator strategy
            value: Locator value
            timeout: Maximum wait time in seconds

        Returns:
            List of WebElements (empty list if none found)
        """
        try:
            wait = WebDriverWait(driver, timeout)
            elements = wait.until(
                EC.presence_of_all_elements_located((by, value)))
            logger.debug(f"Found {len(elements)} elements: {by}='{value}'")
            return elements

        except TimeoutException:
            logger.warning(f"No elements found: {by}='{value}'")
            return []

        except WebDriverException as e:
            logger.error(
                f"WebDriver error finding elements {by}='{value}': {e}")
            return []

    @staticmethod
    def safe_click(element: WebElement, element_name: str = "element") -> bool:
        """
        Safely click an element with retry logic.

        Args:
            element: WebElement to click
            element_name: Name for logging purposes

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(SeleniumUtils.DEFAULT_RETRY_COUNT):
            try:
                element.click()
                logger.debug(f"Successfully clicked {element_name}")
                return True

            except ElementNotInteractableException as e:
                logger.warning(
                    f"Element not interactable (attempt {attempt + 1}): {element_name}")
                # Add debugging information about the element
                try:
                    is_displayed = element.is_displayed()
                    is_enabled = element.is_enabled()
                    tag_name = element.tag_name
                    logger.debug(
                        f"Element debug - displayed: {is_displayed}, enabled: {is_enabled}, tag: {tag_name}")
                except Exception as debug_e:
                    logger.debug(
                        f"Could not get element debug info: {debug_e}")

                if attempt < SeleniumUtils.DEFAULT_RETRY_COUNT - 1:
                    sleep(SeleniumUtils.DEFAULT_RETRY_DELAY)

            except StaleElementReferenceException:
                logger.warning(
                    f"Stale element reference (attempt {attempt + 1}): {element_name}")
                return False  # Element needs to be re-found

            except WebDriverException as e:
                logger.error(f"Error clicking {element_name}: {e}")
                if attempt < SeleniumUtils.DEFAULT_RETRY_COUNT - 1:
                    sleep(SeleniumUtils.DEFAULT_RETRY_DELAY)

        logger.error(
            f"Failed to click {element_name} after {SeleniumUtils.DEFAULT_RETRY_COUNT} attempts")
        return False

    @staticmethod
    def safe_send_keys(element: WebElement, keys: str, element_name: str = "element") -> bool:
        """
        Safely send keys to an element.

        Args:
            element: WebElement to send keys to
            keys: Keys to send
            element_name: Name for logging purposes

        Returns:
            True if successful, False otherwise
        """
        try:
            element.clear()
            element.send_keys(keys)
            logger.debug(f"Successfully sent keys to {element_name}")
            return True

        except ElementNotInteractableException:
            logger.error(f"Element not interactable: {element_name}")
            return False

        except StaleElementReferenceException:
            logger.error(f"Stale element reference: {element_name}")
            return False

        except WebDriverException as e:
            logger.error(f"Error sending keys to {element_name}: {e}")
            return False

    @staticmethod
    def safe_get_attribute(element: WebElement, attribute: str, element_name: str = "element") -> Optional[str]:
        """
        Safely get an attribute from an element.

        Args:
            element: WebElement to get attribute from
            attribute: Attribute name
            element_name: Name for logging purposes

        Returns:
            Attribute value if successful, None otherwise
        """
        try:
            value = element.get_attribute(attribute)
            logger.debug(
                f"Got attribute '{attribute}' from {element_name}: {value}")
            return value

        except StaleElementReferenceException:
            logger.error(
                f"Stale element reference getting attribute: {element_name}")
            return None

        except WebDriverException as e:
            logger.error(
                f"Error getting attribute '{attribute}' from {element_name}: {e}")
            return None

    @staticmethod
    def safe_get_text(element: WebElement, element_name: str = "element") -> Optional[str]:
        """
        Safely get text from an element.

        Args:
            element: WebElement to get text from
            element_name: Name for logging purposes

        Returns:
            Element text if successful, None otherwise
        """
        try:
            text = element.text
            logger.debug(f"Got text from {element_name}: {text}")
            return text

        except StaleElementReferenceException:
            logger.error(
                f"Stale element reference getting text: {element_name}")
            return None

        except WebDriverException as e:
            logger.error(f"Error getting text from {element_name}: {e}")
            return None

    @staticmethod
    def wait_for_page_load(driver: WebDriver, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """
        Wait for page to fully load.

        Args:
            driver: WebDriver instance
            timeout: Maximum wait time in seconds

        Returns:
            True if page loaded, False otherwise
        """
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script(
                    "return document.readyState") == "complete"
            )
            logger.debug("Page loaded successfully")
            return True

        except TimeoutException:
            logger.warning(f"Page load timeout after {timeout} seconds")
            return False

        except WebDriverException as e:
            logger.error(f"Error waiting for page load: {e}")
            return False

    @staticmethod
    def retry_operation(
        operation: Callable,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_delay: int = DEFAULT_RETRY_DELAY,
        operation_name: str = "operation"
    ) -> Any:
        """
        Retry an operation with exponential backoff.

        Args:
            operation: Function to retry
            retry_count: Number of retry attempts
            retry_delay: Base delay between retries
            operation_name: Name for logging purposes

        Returns:
            Operation result if successful, None otherwise
        """
        last_exception = None

        for attempt in range(retry_count):
            try:
                result = operation()
                if attempt > 0:
                    logger.info(
                        f"{operation_name} succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{retry_count}): {e}")

                if attempt < retry_count - 1:
                    delay = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.debug(
                        f"Retrying {operation_name} in {delay} seconds...")
                    sleep(delay)

        logger.error(
            f"{operation_name} failed after {retry_count} attempts. Last error: {last_exception}")
        return None
