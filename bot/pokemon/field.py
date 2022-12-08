from pokemon.moves import *


weather_start = {
    sun: "The sunlight turned harsh!", rain: "It started to rain!",
    hail: "It started to hail!", sandstorm: "A sandstorm kicked up!"
}
weather_continue = {
    sun: "The sunlight is strong.", rain: "Rain continues to fall.",
    hail: "Hail continues to fall.", sandstorm: "The sandstorm rages."
}
weather_end = {
    sun: "The sunlight faded.", rain: "The rain stopped.",
    hail: "The hail stopped.", sandstorm: "The sandstorm subsided."
}


class Field:
    """
    A class for storing battlefield data like weather, Gravity, Trick Room, etc. outside of the Battle class,
    which is defined later down the line.
    """

    def __init__(self):
        self.weather = None
        self.weather_timer = 0
        self.trick_room = 0

    @property
    def status_screen(self):
        ret = []
        if self.weather:
            ret.append(f"- {self.weather}")
        if self.trick_room:
            ret.append("- Trick Room active")
        return "\n".join(ret) if ret else "*All is normal.*"
