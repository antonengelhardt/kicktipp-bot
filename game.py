import random

""" This class represents a game with the home team, away team, quotes and time """


class Game:

    """ Constructor for the game class """

    def __init__(self, home_team, away_team, quotes, time):
        self.home_team = home_team
        self.away_team = away_team
        self.quotes = quotes
        self.time = time

    def calculate_tip(self, home, away):
        """ Calculates the tip based on the quotes """

        # if negative the home team is more likely to win
        difference_home_and_away = home - away

        # generate random number between 0 and 1
        one_more_goal = round(random.uniform(0, 1))

        # depending on the quotes, the factor is derived to decrease the tip for very unequal games
        coefficient = 0.3 if round(abs(difference_home_and_away)) > 7 else 0.75

        # calculate tips
        if abs(difference_home_and_away) < 0.25:
            return one_more_goal, one_more_goal
        else:
            if difference_home_and_away < 0:
                return round(-difference_home_and_away * coefficient) + one_more_goal, one_more_goal
            elif difference_home_and_away > 0:
                return one_more_goal, round(difference_home_and_away * coefficient) + one_more_goal
            else:
                return one_more_goal, one_more_goal
