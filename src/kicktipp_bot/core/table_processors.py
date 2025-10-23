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
            return datetime.now(tz=ZoneInfo('Europe/Berlin'))

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
        """
        Extract betting quotes in the order [1, X, 2].
        Supports both new DOM (div.tippabgabe-quoten > a.quote > spans)
        and legacy format (a.quote-link).
        Returns a list of 3 strings or None if not found.
        """
        # --- New DOM structure ---
        try:
            container = SeleniumUtils.safe_find_element(
                game_row,
                By.XPATH,
                './/div[contains(@class, "tippabgabe-quoten")]'
            )
            if not container:
                # fallback: sometimes quotes are inside td.quoten
                container = SeleniumUtils.safe_find_element(
                    game_row,
                    By.XPATH,
                    './/td[contains(@class, "quoten")]'
                )

            if container:
                anchors = SeleniumUtils.safe_find_elements(
                    container,
                    By.XPATH,
                    './/a[contains(@class, "quote")]'
                )
                if anchors and len(anchors) >= 3:
                    pairs = []
                    for a in anchors:
                        label_el = SeleniumUtils.safe_find_element(
                            a, By.XPATH, './/span[contains(@class, "quote-label")]'
                        )
                        text_el = SeleniumUtils.safe_find_element(
                            a, By.XPATH, './/span[contains(@class, "quote-text")]'
                        )
                        label = SeleniumUtils.safe_get_text(label_el, 'quote label') if label_el else None
                        value = SeleniumUtils.safe_get_text(text_el, 'quote text') if text_el else None
                        if label and value:
                            pairs.append((label.strip(), value.strip()))

                    if pairs:
                        mapping = {lbl: val for (lbl, val) in pairs}
                        ordered = [mapping.get('1'), mapping.get('X'), mapping.get('2')]
                        if all(ordered) and len(ordered) == 3:
                            return ordered
                        else:
                            logger.warning(f"Incomplete quote mapping: {mapping}")
        except Exception as e:
            logger.warning(f"Error parsing quotes (new DOM): {e}")

        # --- Legacy fallback ---
        try:
            quotes_element = SeleniumUtils.safe_find_element(
                game_row, By.XPATH, './/a[contains(@class, "quote-link")]'
            )
            if quotes_element:
                quotes_raw = SeleniumUtils.safe_get_text(quotes_element, 'quotes element')
                if quotes_raw:
                    txt = quotes_raw.replace("Quote: ", "").strip()
                    if " / " in txt:
                        parts = [p.strip() for p in txt.split(" / ")]
                    elif " | " in txt:
                        parts = [p.strip() for p in txt.split(" | ")]
                    else:
                        parts = None

                    if parts and len(parts) == 3:
                        return parts
                    else:
                        logger.warning(f"Could not parse legacy quotes format: {txt}")
        except Exception as e:
            logger.warning(f"Error parsing quotes (legacy DOM): {e}")

        logger.warning("Could not find quotes element in any supported format")
        return None
