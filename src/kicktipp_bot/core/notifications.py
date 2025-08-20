"""Notification module for sending webhooks and alerts."""

import requests
from datetime import datetime
from typing import List, Tuple, Optional
import logging

from ..config import Config


logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages different types of notifications for game tips."""

    def __init__(self):
        self.zapier_enabled = Config.ZAPIER_URL is not None
        self.ntfy_enabled = all([
            Config.NTFY_URL,
            Config.NTFY_USERNAME,
            Config.NTFY_PASSWORD
        ])
        self.webhook_enabled = Config.WEBHOOK_URL is not None

    def send_all_notifications(
        self,
        game_time: datetime,
        home_team: str,
        away_team: str,
        quotes: List[str],
        tip: Tuple[int, int]
    ) -> None:
        """Send all configured notifications."""
        try:
            if self.zapier_enabled:
                self._send_zapier_webhook(
                    game_time, home_team, away_team, quotes, tip)

            if self.ntfy_enabled:
                self._send_ntfy_notification(
                    game_time, home_team, away_team, quotes, tip)

            if self.webhook_enabled:
                self._send_webhook_notification(
                    game_time, home_team, away_team, quotes, tip)

        except Exception as e:
            logger.error(f"Error sending notifications: {e}")

    def _send_zapier_webhook(
        self,
        game_time: datetime,
        home_team: str,
        away_team: str,
        quotes: List[str],
        tip: Tuple[int, int]
    ) -> None:
        """Send notification to Zapier webhook."""
        try:
            payload = {
                'date': game_time.isoformat(),
                'team1': home_team,
                'team2': away_team,
                'quoteteam1': quotes[0] if len(quotes) > 0 else '',
                'quotedraw': quotes[1] if len(quotes) > 1 else '',
                'quoteteam2': quotes[2] if len(quotes) > 2 else '',
                'tipteam1': tip[0],
                'tipteam2': tip[1]
            }

            response = requests.post(
                Config.ZAPIER_URL,
                data=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Zapier webhook sent successfully")

        except requests.RequestException as e:
            logger.error(f"Failed to send Zapier webhook: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending Zapier webhook: {e}")

    def _send_ntfy_notification(
        self,
        game_time: datetime,
        home_team: str,
        away_team: str,
        quotes: List[str],
        tip: Tuple[int, int]
    ) -> None:
        """Send notification via ntfy service."""
        try:
            title = f"{home_team} - {away_team} tipped {tip[0]}:{tip[1]}"
            message = f"Time: {game_time.strftime('%d.%m.%y %H:%M')}\nQuotes: {quotes}"

            headers = {
                "X-Title": title.encode('utf-8'),
                "Content-Type": "text/plain; charset=utf-8"
            }

            response = requests.post(
                Config.NTFY_URL,
                auth=(Config.NTFY_USERNAME, Config.NTFY_PASSWORD),
                data=message.encode('utf-8'),
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Ntfy notification sent successfully")

        except requests.RequestException as e:
            logger.error(f"Failed to send ntfy notification: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending ntfy notification: {e}")

    def _send_webhook_notification(
        self,
        game_time: datetime,
        home_team: str,
        away_team: str,
        quotes: List[str],
        tip: Tuple[int, int]
    ) -> None:
        """Send notification to generic webhook."""
        try:
            data = {
                "home_team": home_team,
                "away_team": away_team,
                "quotes": quotes,
                "tip": list(tip),
                "time": game_time.strftime('%d.%m.%y %H:%M'),
                "timestamp": game_time.isoformat()
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(
                Config.WEBHOOK_URL,
                json=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Generic webhook sent successfully")

        except requests.RequestException as e:
            logger.error(f"Failed to send generic webhook: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending generic webhook: {e}")
