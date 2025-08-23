"""
Kicktipp Bot - Automated football betting tips based on odds analysis.

This script automatically logs into Kicktipp, analyzes betting odds for upcoming games,
calculates optimal tips, and submits them while sending notifications.
"""

import logging
import sys
from datetime import datetime
from time import sleep
import sentry_sdk
import os

from .config import Config
from .webdriver.webdriver_manager import WebDriverManager
from .core.authentication import Authenticator, AuthenticationError
from .core.game_tipper import GameTipper, GameTippingError
from .core.notifications import NotificationManager
from .health import health_status, health_monitor


def setup_logging(debug_mode: bool = False) -> None:
    """Setup logging configuration."""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    log_format = '%(asctime)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt='%H:%M:%S',
        force=True  # Override any existing configuration
    )

    # Set logging level for all kicktipp_bot modules
    logging.getLogger('kicktipp_bot').setLevel(log_level)

    # Reduce selenium logging noise
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


class KicktippBot:
    """Main bot class that orchestrates the tipping process."""

    def __init__(self):
        self.driver = None
        self.authenticator = None
        self.game_tipper = None
        self.notification_manager = NotificationManager()

    def run(self) -> None:
        """Execute the complete tipping process."""
        try:
            # Update health status
            health_status.heartbeat()

            # Initialize WebDriver
            self.driver = WebDriverManager.create_driver()
            logger.info("WebDriver initialized successfully")

            # Initialize authenticator
            self.authenticator = Authenticator(self.driver)

            # Login
            self.authenticator.login()

            # Initialize game tipper
            self.game_tipper = GameTipper(
                self.driver, self.notification_manager)

            # Process all games
            self.game_tipper.tip_all_games()

            # Record successful run
            health_status.record_successful_run()
            logger.info("Tipping process completed successfully")

        except AuthenticationError as e:
            health_status.record_failed_run(f"Authentication failed: {e}")
            logger.error(f"Authentication failed: {e}")
            raise
        except GameTippingError as e:
            health_status.record_failed_run(f"Game tipping failed: {e}")
            logger.error(f"Game tipping failed: {e}")
            raise
        except Exception as e:
            health_status.record_failed_run(f"Unexpected error: {e}")
            logger.error(f"Unexpected error during tipping process: {e}")
            raise
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")


def run_bot() -> None:
    """Run a single bot execution cycle."""
    bot = KicktippBot()
    bot.run()


def main() -> None:
    """Main entry point for the Kicktipp bot."""
    # Check for debug mode
    debug_mode = len(sys.argv) > 1 and '--debug' in sys.argv
    if debug_mode:
        logger.info("Debug mode enabled - detailed logging active")

    # Setup logging with appropriate level
    setup_logging(debug_mode)

    # Get logger after setup
    logger = logging.getLogger(__name__)

    # Validate configuration
    if not Config.validate_required_config():
        logger.error("Missing required configuration. Please set KICKTIPP_EMAIL, "
                     "KICKTIPP_PASSWORD and KICKTIPP_NAME_OF_COMPETITION environment variables")
        sys.exit(1)

    logger.info("Kicktipp Bot starting...")
    logger.info(f"Configuration: Competition={Config.NAME_OF_COMPETITION}, "
                f"Run interval={Config.RUN_EVERY_X_MINUTES}min, "
                f"Tip threshold={Config.TIME_UNTIL_GAME}")

    if os.getenv("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            send_default_pii=True,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )

        logger.info("Sentry initialized successfully")

    # Start health monitoring
    health_monitor.start_health_server()
    health_status.heartbeat()

    try:
        while True:
            try:
                current_time = datetime.now().strftime('%d.%m.%y %H:%M')
                logger.info(f"{current_time}: Starting tipping cycle")

                # Update heartbeat
                health_status.heartbeat()

                # Run the bot
                run_bot()

                logger.info("Tipping cycle completed successfully")

                # Send heartbeat notification if configured
                health_monitor.send_heartbeat_notification()

            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during tipping cycle: {e}", exc_info=True)

            # Sleep until next cycle
            sleep_minutes = Config.RUN_EVERY_X_MINUTES
            if sleep_minutes == 0:
                logger.info("Repetition time is 0, shutting down")
                return
            next_run = datetime.now().timestamp() + sleep_minutes * 60
            logger.info(
                f"Sleeping for {sleep_minutes} minutes until next cycle at {next_run}")
            while (remaining := next_run - datetime.now().timestamp()) > 0:
                sleep(min(10, remaining))


    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        # Stop health monitoring
        health_monitor.stop_health_server()
        logger.info("Bot shutdown complete")


if __name__ == '__main__':
    main()
