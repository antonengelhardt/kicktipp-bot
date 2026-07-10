"""Game model for representing football matches and calculating betting tips."""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class Game:
    """Represents a football game with teams, betting quotes, and tip calculation logic."""

    home_team: str
    away_team: str
    quotes: List[str]
    game_time: datetime
    _validated_quotes: List[float] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        """Validate and process data after initialization."""
        self.home_team = self.home_team.strip()
        self.away_team = self.away_team.strip()
        self._validated_quotes = self._validate_quotes(self.quotes)

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

    def calculate_tip(
        self,
        home_quote: Optional[float] = None,
        away_quote: Optional[float] = None,
        allow_draw: bool = True
    ) -> Tuple[int, int]:
        """
        Calculate betting tip based on the quotes.

        Args:
            home_quote: Quote for home team win (uses self._validated_quotes[0] if None)
            away_quote: Quote for away team win (uses self._validated_quotes[2] if None)
            allow_draw: Whether equal-score predictions are allowed

        Returns:
            Tuple of (home_goals, away_goals) prediction
        """
        home_quote, away_quote = self._get_effective_win_quotes(
            home_quote, away_quote)
        tip = self._calculate_base_tip(home_quote, away_quote)

        if not allow_draw:
            return self.resolve_draw_tip(tip, home_quote, away_quote)

        return tip

    def resolve_draw_tip(
        self,
        tip: Tuple[int, int],
        home_quote: Optional[float] = None,
        away_quote: Optional[float] = None
    ) -> Tuple[int, int]:
        """Resolve a draw prediction into a one-goal win based on win quotes."""
        if tip[0] != tip[1]:
            return tip

        home_quote, away_quote = self._get_effective_win_quotes(
            home_quote, away_quote)

        if home_quote <= away_quote:
            return tip[0] + 1, tip[1]

        return tip[0], tip[1] + 1

    def _get_effective_win_quotes(
        self,
        home_quote: Optional[float],
        away_quote: Optional[float]
    ) -> Tuple[float, float]:
        """Return explicit home/away win quotes, falling back to validated values."""
        if home_quote is None:
            home_quote = self._validated_quotes[0]
        if away_quote is None:
            away_quote = self._validated_quotes[2]
        return home_quote, away_quote

    @staticmethod
    def _calculate_base_tip(home_quote: float, away_quote: float) -> Tuple[int, int]:
        """Create a raw tip from home/away quotes before draw-rule adjustments."""
        # Calculate quote difference (negative = home team more likely to win)
        quote_difference = home_quote - away_quote

        # Add randomness for more realistic scores
        random_goal = random.randint(0, 1)

        # Lower coefficient for very unequal games to avoid extreme scores
        coefficient = 0.3 if abs(quote_difference) > 7 else 0.75

        if abs(quote_difference) < 0.25:
            # Very close match - predict draw-like result
            return random_goal, random_goal

        if quote_difference < 0:
            # Home team favored
            home_goals = max(0, round(-quote_difference * coefficient)) + random_goal
            return home_goals, random_goal

        # Away team favored
        away_goals = max(0, round(quote_difference * coefficient)) + random_goal
        return random_goal, away_goals

    def __str__(self) -> str:
        """String representation of the game."""
        return f"{self.home_team} vs {self.away_team} at {self.game_time.strftime('%d.%m.%y %H:%M')}"
