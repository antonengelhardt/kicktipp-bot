"""Table processing utilities for game tipping."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from ..utils.selenium_utils import SeleniumUtils

logger = logging.getLogger(__name__)


class TimeExtractor:
    """Handles time extraction from table rows."""

    @staticmethod
    def extract_from_rowheader(header_row) -> Optional[datetime]:
        """Extract time from a rowheader element using multiple approaches."""
        try:
            # Approach 1: Look for any td with time-like content
            time_cells = SeleniumUtils.safe_find_elements(
                header_row, By.TAG_NAME, 'td')
            for cell in time_cells:
                time_text = SeleniumUtils.safe_get_text(
                    cell, 'header time cell')
                if time_text and time_text.strip():
                    text = time_text.strip()
                    if TimeExtractor._looks_like_time(text):
                        logger.debug(f"Found time in rowheader cell: '{text}'")
                        return TimeExtractor._parse_time_string(text)

            # Approach 2: Look for specific time-related classes or attributes
            time_element = SeleniumUtils.safe_find_element(
                header_row, By.XPATH, './/td[contains(@class, "time") or contains(text(), ":") or contains(text(), ".")]')
            if time_element:
                time_text = SeleniumUtils.safe_get_text(
                    time_element, 'header time xpath')
                if time_text and time_text.strip():
                    logger.debug(
                        f"Found time via xpath in rowheader: '{time_text.strip()}'")
                    return TimeExtractor._parse_time_string(time_text.strip())

            logger.debug(
                "Could not extract time from rowheader using any method")
            return None

        except Exception as e:
            logger.error(f"Error extracting time from rowheader: {e}")
            return None

    @staticmethod
    def extract_from_datarow(data_row, fallback_time: Optional[datetime] = None) -> datetime:
        """Extract time from a datarow or use fallback time."""
        time_cell = SeleniumUtils.safe_find_element(
            data_row, By.XPATH, './td[1]')
        if time_cell:
            class_attr = SeleniumUtils.safe_get_attribute(
                time_cell, 'class', 'time cell') or ''
            logger.debug(f"Time cell class: '{class_attr}'")

            # Only use if not hidden
            if 'hide' not in class_attr:
                time_text = SeleniumUtils.safe_get_text(
                    time_cell, 'datarow time')
                if time_text and time_text.strip():
                    logger.debug(
                        f"Found visible time in datarow: {time_text.strip()}")
                    return TimeExtractor._parse_time_string(time_text.strip())
            else:
                logger.debug("Time cell is hidden, will use fallback time")

        # Use fallback time or current time
        if fallback_time:
            logger.debug(
                f"Using fallback time: {fallback_time.strftime('%d.%m.%y %H:%M')}")
            return fallback_time
        else:
            logger.warning("No time available, using current time")
            return datetime.now()

    @staticmethod
    def has_visible_time(data_row) -> bool:
        """Check if a datarow has a visible (non-hidden) time cell with content."""
        time_cell = SeleniumUtils.safe_find_element(
            data_row, By.XPATH, './td[1]')
        if time_cell:
            class_attr = SeleniumUtils.safe_get_attribute(
                time_cell, 'class', 'time cell') or ''
            if 'hide' not in class_attr:
                time_text = SeleniumUtils.safe_get_text(
                    time_cell, 'datarow time check')
                return bool(time_text and time_text.strip())
        return False

    @staticmethod
    def _looks_like_time(text: str) -> bool:
        """Check if text looks like a time string."""
        return any(char.isdigit() for char in text) and ('.' in text or ':' in text)

    @staticmethod
    def _parse_time_string(time_text: str) -> datetime:
        """Parse time string into Europe/Berlin aware datetime object using zoneinfo."""
        try:
            naive_dt = datetime.strptime(time_text, '%d.%m.%y %H:%M')
            return naive_dt.replace(tzinfo=ZoneInfo('Europe/Berlin'))
        except ValueError as e:
            logger.warning(f"Could not parse time '{time_text}': {e}")
            return datetime.now(tz=ZoneInfo('Europe/Berlin'))


class TableRowProcessor:
    """Handles processing of table rows and state management."""

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def get_all_table_rows(self):
        """Get all table rows from the tipping table."""
        return SeleniumUtils.safe_find_elements(
            self.driver,
            By.XPATH,
            '//*[@id="tippabgabeSpiele"]/tbody/tr'
        )

    def get_row_safely(self, all_rows, row_index: int):
        """Get a row safely, handling stale element references."""
        try:
            row = all_rows[row_index]
            row_class = SeleniumUtils.safe_get_attribute(
                row, 'class', 'table row') or ''
            return row, row_class
        except Exception as e:
            if 'stale element' in str(e).lower():
                logger.debug(
                    f"Stale element for row {row_index}, re-finding...")
                fresh_rows = self.get_all_table_rows()
                if row_index < len(fresh_rows):
                    row = fresh_rows[row_index]
                    row_class = SeleniumUtils.safe_get_attribute(
                        row, 'class', 'table row') or ''
                    return row, row_class
                else:
                    logger.warning(f"Could not re-find row {row_index}")
                    return None, None
            else:
                raise e


class GameDataExtractor:
    """Handles extraction of game-specific data from table rows."""

    @staticmethod
    def extract_team_name(data_row, column_index: int, team_type: str) -> Optional[str]:
        """Extract team name from a specific column."""
        team_element = SeleniumUtils.safe_find_element(
            data_row, By.XPATH, f'./td[{column_index}]')
        if team_element:
            team_name = SeleniumUtils.safe_get_text(
                team_element, f'{team_type} team')
            if team_name and team_name.strip():
                return team_name.strip()
        return None

    @staticmethod
    def get_tip_fields(game_row) -> Optional[tuple]:
        """Get tip input fields directly from a game row element."""
        home_tip_field = SeleniumUtils.safe_find_element(
            game_row, By.XPATH, './/input[contains(@name, "heimTipp")]')
        away_tip_field = SeleniumUtils.safe_find_element(
            game_row, By.XPATH, './/input[contains(@name, "gastTipp")]')

        if home_tip_field and away_tip_field:
            return home_tip_field, away_tip_field
        else:
            result_element = SeleniumUtils.safe_find_element(
                game_row, By.XPATH, './td[4]')
            if result_element:
                result_text = SeleniumUtils.safe_get_text(
                    result_element, 'game result')
                if result_text:
                    logger.debug(
                        f"Game is over or not available: {result_text}")
            return None

    @staticmethod
    def extract_quotes(game_row) -> Optional[list]:
        """Extract betting quotes directly from a game row element."""
        quotes_element = SeleniumUtils.safe_find_element(
            game_row, By.XPATH, './/a[contains(@class, "quote-link")]')
        if not quotes_element:
            logger.warning("Could not find quotes element")
            return None

        quotes_raw = SeleniumUtils.safe_get_text(
            quotes_element, 'quotes element')
        if not quotes_raw:
            logger.warning("Could not extract quotes content")
            return None

        quotes_text = quotes_raw.replace("Quote: ", "").strip()

        if " / " in quotes_text:
            quotes = quotes_text.split(" / ")
        elif " | " in quotes_text:
            quotes = quotes_text.split(" | ")
        else:
            logger.warning(f"Could not parse quotes format: {quotes_text}")
            return None

        if len(quotes) != 3:
            logger.warning(f"Expected 3 quotes, got {len(quotes)}: {quotes}")
            return None

        return quotes
