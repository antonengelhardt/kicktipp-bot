"""Game tipping module for handling the core betting logic."""

import logging
import sys
from datetime import datetime
from time import sleep
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from ..config import Config
from ..models.game import Game
from .notifications import NotificationManager
from ..utils.selenium_utils import SeleniumUtils

logger = logging.getLogger(__name__)


class GameTippingError(Exception):
    """Custom exception for game tipping failures."""
    pass


class GameTipper:
    """Handles the core game tipping functionality."""

    def __init__(self, driver: WebDriver, notification_manager: NotificationManager):
        self.driver = driver
        self.notification_manager = notification_manager

    def tip_all_games(self) -> None:
        """Process and tip all available games."""
        logger.info("Starting game tipping process")

        try:
            # Navigate to tipping page
            logger.debug("Navigating to tipping page")
            self.driver.get(Config.get_tipp_url())

            # Wait for page to load
            if not SeleniumUtils.wait_for_page_load(self.driver):
                raise GameTippingError("Tipping page failed to load")

            # Additional wait for dynamic content
            sleep(2)

            # Accept terms and conditions if they appear on the tipping page
            self._accept_terms_and_conditions()

            # Get the number of games available
            games_count = self._get_games_count()
            if games_count == 0:
                logger.warning("No games found to process - this could mean:")
                logger.warning("  - No games are available for tipping")
                logger.warning("  - Page structure has changed")
                logger.warning("  - Terms dialog is still blocking content")
                return

            logger.info(f"Found {games_count} games to process")

            # Process each game
            processed_count = 0
            for game_index in range(1, games_count):
                try:
                    if self._process_single_game(game_index):
                        processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing game {game_index}: {e}")
                    # Try to accept terms in case they appeared during processing
                    self._accept_terms_and_conditions()
                    continue

            logger.info(f"Processed {processed_count} games successfully")

            # Submit all tips (button should always be clickable)
            self._submit_all_tips()

            # Debug mode sleep
            if self._is_debug_mode():
                logger.info("Local debug mode - sleeping for 20 seconds to review results")
                sleep(20)

        except GameTippingError:
            raise
        except WebDriverException as e:
            raise GameTippingError(f"WebDriver error during tipping: {e}")
        except Exception as e:
            raise GameTippingError(f"Unexpected error during tipping: {e}")

    def _get_games_count(self) -> int:
        """Get the number of games available for tipping."""
        logger.debug("Counting available games")

        # Try to find the games table first
        table = SeleniumUtils.safe_find_element(self.driver, By.ID, "tippabgabeSpiele")
        if not table:
            logger.warning("Could not find tipping table (tippabgabeSpiele)")
            return 0

        games = SeleniumUtils.safe_find_elements(self.driver, By.CLASS_NAME, "datarow")
        count = len(games)
        logger.debug(f"Found {count} game rows with class 'datarow'")

        # If no datarow elements, try alternative selectors
        if count == 0:
            logger.debug("No 'datarow' elements found, trying alternative selectors")
            # Try finding table rows in the tipping table
            table_rows = SeleniumUtils.safe_find_elements(self.driver, By.XPATH, '//*[@id="tippabgabeSpiele"]//tr')
            logger.debug(f"Found {len(table_rows)} total table rows")

            # Filter out header rows (usually first row)
            if len(table_rows) > 1:
                count = len(table_rows) - 1  # Subtract header row
                logger.debug(f"Adjusted count after removing header: {count}")

        return count

    def _process_single_game(self, game_index: int) -> bool:
        """
        Process a single game for tipping.

        Returns:
            True if game was processed successfully, False otherwise
        """
        logger.debug(f"Processing game {game_index}")
        xpath_row = f'//*[@id="tippabgabeSpiele"]/tbody/tr[{game_index}]'

        # Check if row exists
        if not self._row_exists(xpath_row):
            logger.debug(f"Row {game_index} does not exist, skipping...")
            return False

        # Extract game information
        game_info = self._extract_game_info(game_index)
        if not game_info:
            logger.warning(f"Could not extract game info for game {game_index}")
            return False

        game_time, home_team, away_team = game_info

        logger.info(f"Processing: {home_team} vs {away_team} | Time: {game_time.strftime('%d.%m.%y %H:%M')}")

        # Check if game can be tipped
        tip_fields = self._get_tip_fields(xpath_row)
        if not tip_fields:
            logger.debug(f"Game {game_index} cannot be tipped (likely finished)")
            return False

        home_tip_field, away_tip_field = tip_fields

        # Check if already tipped
        if self._is_already_tipped(home_tip_field, away_tip_field):
            home_val = SeleniumUtils.safe_get_attribute(home_tip_field, 'value', 'home tip field') or ''
            away_val = SeleniumUtils.safe_get_attribute(away_tip_field, 'value', 'away tip field') or ''
            logger.info(f"Game already tipped: {home_val} - {away_val}")
            return False

        # Check timing constraints
        if not self._should_tip_game(game_time):
            return False

        # Extract quotes and calculate tip
        quotes = self._extract_quotes(xpath_row)
        if not quotes:
            logger.warning(f"Could not extract quotes for game {game_index}")
            return False

        logger.debug(f"Quotes: {quotes}")

        try:
            # Create game object and calculate tip
            game = Game(home_team, away_team, quotes, game_time)
            tip = game.calculate_tip()

            logger.info(f"Calculated tip: {tip[0]} - {tip[1]}")

            # Enter the tip
            if not self._enter_tip(home_tip_field, away_tip_field, tip):
                logger.error(f"Failed to enter tip for game {game_index}")
                return False

            # Send notifications
            try:
                self.notification_manager.send_all_notifications(
                    game_time, home_team, away_team, quotes, tip
                )
            except Exception as e:
                logger.warning(f"Failed to send notifications for game {game_index}: {e}")
                # Don't fail the whole process for notification errors

            return True

        except Exception as e:
            logger.error(f"Error processing game {game_index}: {e}")
            return False

    def _row_exists(self, xpath_row: str) -> bool:
        """Check if a game row exists."""
        element = SeleniumUtils.safe_find_element(self.driver, By.XPATH, xpath_row, timeout=3)
        return element is not None

    def _extract_game_info(self, game_index: int) -> Optional[tuple]:
        """Extract game time and team names."""
        try:
            # Find game time (may be in current or previous rows)
            game_time = self._find_game_time(game_index)

            # Get team names
            xpath_row = f'//*[@id="tippabgabeSpiele"]/tbody/tr[{game_index}]'

            home_team_element = SeleniumUtils.safe_find_element(self.driver, By.XPATH, f'{xpath_row}/td[2]')
            if not home_team_element:
                logger.warning(f"Could not find home team for game {game_index}")
                return None

            away_team_element = SeleniumUtils.safe_find_element(self.driver, By.XPATH, f'{xpath_row}/td[3]')
            if not away_team_element:
                logger.warning(f"Could not find away team for game {game_index}")
                return None

            home_team = SeleniumUtils.safe_get_attribute(home_team_element, 'innerHTML', 'home team')
            away_team = SeleniumUtils.safe_get_attribute(away_team_element, 'innerHTML', 'away team')

            if not home_team or not away_team:
                logger.warning(f"Could not extract team names for game {game_index}")
                return None

            return game_time, home_team.strip(), away_team.strip()

        except Exception as e:
            logger.error(f"Error extracting game info for game {game_index}: {e}")
            return None

    def _find_game_time(self, game_index: int) -> datetime:
        """Find the game time, looking backwards through rows if needed."""
        for row_index in range(game_index, 0, -1):
            xpath_row = f'//*[@id="tippabgabeSpiele"]/tbody/tr[{row_index}]'

            time_element = SeleniumUtils.safe_find_element(self.driver, By.XPATH, f'{xpath_row}/td[1]', timeout=2)
            if not time_element:
                continue

            time_text = SeleniumUtils.safe_get_attribute(time_element, 'innerHTML', f'time cell row {row_index}')
            if not time_text:
                continue

            time_text = time_text.strip()
            if time_text:  # Non-empty time cell
                try:
                    return datetime.strptime(time_text, '%d.%m.%y %H:%M')
                except ValueError as e:
                    logger.debug(f"Could not parse time '{time_text}' from row {row_index}: {e}")
                    continue

        # Fallback to current time if no time found
        logger.warning("Could not find game time, using current time as fallback")
        return datetime.now()

    def _get_tip_fields(self, xpath_row: str) -> Optional[tuple]:
        """Get the tip input fields for a game."""
        # Look for tip input fields by their name patterns (more reliable)
        home_tip_field = SeleniumUtils.safe_find_element(self.driver, By.XPATH, f'{xpath_row}//input[contains(@name, "heimTipp")]', timeout=2, retry_count=1)
        away_tip_field = SeleniumUtils.safe_find_element(self.driver, By.XPATH, f'{xpath_row}//input[contains(@name, "gastTipp")]', timeout=2, retry_count=1)

        if home_tip_field and away_tip_field:
            return home_tip_field, away_tip_field
        else:
            # Game is likely over or not available for tipping
            result_element = SeleniumUtils.safe_find_element(self.driver, By.XPATH, f'{xpath_row}/td[4]')
            if result_element:
                result_text = SeleniumUtils.safe_get_attribute(result_element, 'innerHTML', 'game result')
                if result_text:
                    logger.debug(f"Game is over or not available: {result_text.replace(':', ' - ')}")
                else:
                    logger.debug("Game status unknown")
            else:
                logger.debug("Could not find game status element")
            return None

    def _is_already_tipped(self, home_field, away_field) -> bool:
        """Check if the game has already been tipped."""
        home_value = SeleniumUtils.safe_get_attribute(home_field, 'value', 'home tip field') or ''
        away_value = SeleniumUtils.safe_get_attribute(away_field, 'value', 'away tip field') or ''
        return bool(home_value and away_value)

    def _should_tip_game(self, game_time: datetime) -> bool:
        """Check if the game should be tipped based on timing."""
        time_until_game = game_time - datetime.now()
        logger.debug(f"Time until game: {time_until_game}")

        if time_until_game > Config.TIME_UNTIL_GAME:
            logger.info(f"Game starts in more than {Config.TIME_UNTIL_GAME}. Skipping...")
            return False

        logger.info(f"Game starts in less than {Config.TIME_UNTIL_GAME}. Proceeding with tip...")
        return True

    def _extract_quotes(self, xpath_row: str) -> Optional[list]:
        """Extract betting quotes from the game row."""
        quotes_element = SeleniumUtils.safe_find_element(self.driver, By.XPATH, f'{xpath_row}/td[5]/a')
        if not quotes_element:
            logger.warning("Could not find quotes element")
            return None

        quotes_raw = SeleniumUtils.safe_get_attribute(quotes_element, 'innerHTML', 'quotes element')
        if not quotes_raw:
            logger.warning("Could not extract quotes content")
            return None

        # Clean up the quotes text
        quotes_text = quotes_raw.replace("Quote: ", "").strip()

        # Split quotes (try different separators)
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

    def _enter_tip(self, home_field, away_field, tip: tuple) -> bool:
        """
        Enter the calculated tip into the form fields.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Enter home team tip
            if not SeleniumUtils.safe_send_keys(home_field, str(tip[0]), "home tip field"):
                logger.error("Failed to enter home team tip")
                return False

            # Enter away team tip
            if not SeleniumUtils.safe_send_keys(away_field, str(tip[1]), "away tip field"):
                logger.error("Failed to enter away team tip")
                return False

            logger.info(f"Successfully entered tip: {tip[0]} - {tip[1]}")
            return True

        except Exception as e:
            logger.error(f"Unexpected error entering tip: {e}")
            return False

    def _submit_all_tips(self) -> None:
        """Submit all entered tips."""
        logger.info("Submitting tips form")

        # Wait a moment for any dynamic updates to the form
        sleep(1)

        submit_button = SeleniumUtils.safe_find_element(self.driver, By.NAME, "submitbutton")
        if not submit_button:
            logger.error("Could not find submit button with name 'submitbutton'")
            raise GameTippingError("Submit button not found")

        logger.debug("Found submit button, attempting to click")

        # Try to scroll the button into view first
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            sleep(0.5)  # Brief pause after scrolling
            logger.debug("Scrolled submit button into view")
        except Exception as e:
            logger.debug(f"Could not scroll to submit button: {e}")

        # Try regular click first
        if SeleniumUtils.safe_click(submit_button, "submit button"):
            logger.info("Tips form submitted successfully")
        else:
            # Fallback to JavaScript click
            logger.info("Regular click failed, trying JavaScript click")
            try:
                self.driver.execute_script("arguments[0].click();", submit_button)
                logger.info("Tips form submitted successfully via JavaScript")
            except Exception as e:
                logger.error(f"Both regular and JavaScript clicks failed: {e}")
                raise GameTippingError("Failed to submit tips form")

    def _is_debug_mode(self) -> bool:
        """Check if running in debug mode."""
        try:
            return len(sys.argv) > 1 and '--debug' in sys.argv
        except IndexError:
            return False

    def _accept_terms_and_conditions(self) -> None:
        """Accept terms and conditions if the dialog appears on the tipping page."""
        logger.debug("Checking for terms and conditions dialog")

        # Look for SourcePoint iframe (where the terms dialog actually is)
        iframe = SeleniumUtils.safe_find_element(
            self.driver,
            By.CSS_SELECTOR,
            'iframe[id*="sp_message_iframe"]',
            timeout=3
        )

        if iframe:
            try:
                # Switch to iframe and find accept button
                self.driver.switch_to.frame(iframe)
                sleep(1)  # Brief wait for iframe content

                accept_button = SeleniumUtils.safe_find_element(
                    self.driver,
                    By.XPATH,
                    '//button[contains(text(), "Akzeptieren")]',
                    timeout=2
                )

                if accept_button and SeleniumUtils.safe_click(accept_button, "terms accept button"):
                    logger.info("Terms and conditions accepted successfully")

                # Always switch back to main content
                self.driver.switch_to.default_content()

            except Exception as e:
                logger.warning(f"Error handling terms dialog: {e}")
                # Ensure we switch back to main content
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass
        else:
            logger.debug("No terms dialog found - may already be accepted")


