from pokemon.moves import *


sun, rain, snow, sandstorm = "Harsh sunlight", "Heavy rain", "Snow", "Sandstorm"


class Field:
    """
    A class for storing battlefield data like weather, Gravity, Trick Room, etc. outside of the Battle class,
    which is defined later down the line.
    """

    def __init__(self):
        self.weather = None
        self.trick_room = False
