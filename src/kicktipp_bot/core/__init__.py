"""Core functionality modules for Kicktipp Bot."""

from .authentication import Authenticator, AuthenticationError
from .game_tipper import GameTipper, GameTippingError
from .notifications import NotificationManager

__all__ = [
    "Authenticator",
    "AuthenticationError",
    "GameTipper",
    "GameTippingError",
    "NotificationManager",
]
