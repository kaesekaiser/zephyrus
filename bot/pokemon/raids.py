from pokemon.teams import *


class TeraRaidDrop:
    def __init__(self, item: str, quantity: int, chance: float):
        self.item = item
        self.quantity = quantity
        self.chance = chance

    def __str__(self):
        if self.chance in ["Guest", "Host"]:
            return f"{self.quantity}x **{self.item}** for {'guests' if self.chance == 'Guest' else 'the host'}"
        elif self.chance == "Once":
            return f"{self.quantity}x **{self.item}** the first time only"
        elif self.chance == 100:
            return f"{self.quantity}x **{self.item}**"
        else:
            return f"{self.quantity}x **{self.item}** ({round(self.chance, 2)}% chance)"

    @staticmethod
    def from_json(js: list):
        return TeraRaidDrop(*js)


class TeraRaid:
    def __init__(self, stars: int, species: str, game: str, battle_level: int, catch_level: int, tera_type: str,
                 ability: str, moves: list[str], hp_actions: list[list], time_actions: list[list],
                 drops: list[TeraRaidDrop]):
        self.stars = stars
        self.species = species
        self.game = game
        self.battle_level = battle_level
        self.catch_level = catch_level
        self.type = tera_type
        self.ability = ability
        self.moves = moves
        self.hp_actions = hp_actions
        self.time_actions = time_actions
        self.drops = drops

    @staticmethod
    def from_json(js: dict, stars: int = 5):
        return TeraRaid(
            stars, js["species"], js["game"], js["battle_level"], js["catch_level"], js["type"],
            js["ability"], js["moves"], js.get("hp_actions", []), js.get("time_actions", []),
            [TeraRaidDrop.from_json(g) for g in js["drops"]]
        )

    @property
    def name(self):
        return f"{self.stars}\u2605 {self.species}"


raids = {
    5: {g: TeraRaid.from_json(j, 5) for g, j in json.load(open("pokemon/data/raids5.json", "r")).items()},
    6: {g: TeraRaid.from_json(j, 6) for g, j in json.load(open("pokemon/data/raids6.json", "r")).items()}
}
