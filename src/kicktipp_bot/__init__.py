"""
Kicktipp Bot - Automated football betting tips based on odds analysis.

This package provides automated betting tip calculation and submission
for the Kicktipp platform.
"""

# Import main classes for easy access
from .config import Config
from .models.game import Game

# Import core functionality
from .core.authentication import Authenticator, AuthenticationError
from .core.game_tipper import GameTipper, GameTippingError
from .core.notifications import NotificationManager

# Import utilities
from .utils.selenium_utils import SeleniumUtils
from .webdriver.webdriver_manager import WebDriverManager

__all__ = [
    "Config",
    "Game",
    "Authenticator",
    "AuthenticationError",
    "GameTipper",
    "GameTippingError",
    "NotificationManager",
    "SeleniumUtils",
    "WebDriverManager",
]
