"""Game model for representing football matches and calculating betting tips."""

import random
from datetime import datetime
from typing import List, Tuple, Union


class Game:
    """Represents a football game with teams, betting quotes, and tip calculation logic."""

    def __init__(self, home_team: str, away_team: str, quotes: List[str], game_time: datetime):
        """
        Initialize a Game instance.

        Args:
            home_team: Name of the home team
            away_team: Name of the away team
            quotes: List of betting quotes [home_win, draw, away_win]
            game_time: DateTime when the game starts
        """
        self.home_team = home_team.strip()
        self.away_team = away_team.strip()
        self.quotes = self._validate_quotes(quotes)
        self.game_time = game_time

    def _validate_quotes(self, quotes: List[str]) -> List[float]:
        """
        Validate and convert quotes to float values.

        Args:
            quotes: List of quote strings

        Returns:
            List of float quotes

        Raises:
            ValueError: If quotes are invalid
        """
        if len(quotes) != 3:
            raise ValueError(f"Expected 3 quotes, got {len(quotes)}")

        try:
            return [float(quote) for quote in quotes]
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid quote values: {quotes}") from e

    def calculate_tip(self, home_quote: Union[float, None] = None, away_quote: Union[float, None] = None) -> Tuple[int, int]:
        """
        Calculate betting tip based on the quotes.

        Args:
            home_quote: Quote for home team win (uses self.quotes[0] if None)
            away_quote: Quote for away team win (uses self.quotes[2] if None)

        Returns:
            Tuple of (home_goals, away_goals) prediction
        """
        if home_quote is None:
            home_quote = self.quotes[0]
        if away_quote is None:
            away_quote = self.quotes[2]

        # Calculate quote difference (negative = home team more likely to win)
        quote_difference = home_quote - away_quote

        # Add randomness for more realistic scores
        random_goal = random.randint(0, 1)

        # Adjust coefficient based on how unequal the match is
        # Lower coefficient for very unequal games to avoid extreme scores
        coefficient = 0.3 if abs(quote_difference) > 7 else 0.75

        # Calculate tips based on quote difference
        if abs(quote_difference) < 0.25:
            # Very close match - predict draw-like result
            return random_goal, random_goal
        elif quote_difference < 0:
            # Home team favored
            home_goals = max(
                0, round(-quote_difference * coefficient)) + random_goal
            away_goals = random_goal
            return home_goals, away_goals
        else:
            # Away team favored
            home_goals = random_goal
            away_goals = max(
                0, round(quote_difference * coefficient)) + random_goal
            return home_goals, away_goals

    def __str__(self) -> str:
        """String representation of the game."""
        return f"{self.home_team} vs {self.away_team} at {self.game_time.strftime('%d.%m.%y %H:%M')}"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (f"Game(home_team='{self.home_team}', away_team='{self.away_team}', "
                f"quotes={self.quotes}, game_time='{self.game_time}')")
