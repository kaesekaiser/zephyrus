from typing import Union


types = normal, fire, water, electric, grass, ice, fighting, poison, ground, flying, psychic, bug, rock, ghost, \
    dragon, dark, steel, fairy = "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", \
    "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
typeColors = {
    normal: "A8A878", fire: "F08030", water: "6890F0", grass: "78C850", electric: "F8D030", rock: "B8A038",
    ground: "E0C068", steel: "B8B8D0", psychic: "F85888", fighting: "C03028", flying: "A890F0", ghost: "705898",
    dark: "705848", bug: "A8B820", poison: "A040A0", fairy: "EE99AC", dragon: "7038F8", ice: "98D8D8"
}
categories = physical, special, status = "Physical", "Special", "Status"
targets = anyAdjFoe, anyAdj, anyMon, userOrAdjAlly, allAdjFoe, allAdj, allFoe, allMon, anyAdjAlly, user, userAllAlly = \
    "any adjacent foe", "any adjacent Pok\u00e9mon", "any Pok\u00e9mon", "the user or an adjacent ally", \
    "all adjacent foes", "all adjacent Pok\u00e9mon", "all foes", "all Pok\u00e9", "any adjacent ally", "the user", \
    "the user and all allies"
statusConditions = poisoned, badlyPoisoned, burned, paralyzed, asleep, frozen = "Poisoned", "Badly poisoned", \
    "Burned", "Paralyzed", "Asleep", "Frozen"


class StatChange:
    stat_name_dict = {
        "atk": "Attack", "dfn": "Defense", "spa": "Special Attack", "spd": "Special Defense", "spe": "Speed",
        "eva": "evasion", "acc": "accuracy"
    }
    modifier_strings = [
        "{name}'s {stat} won't go any higher!", "{name}'s {stat} rose!", "{name}'s {stat} rose sharply!",
        "{name}'s {stat} rose drastically!", "{name}'s {stat} severely fell!", "{name}'s {stat} harshly fell!",
        "{name}'s {stat} fell!"
    ]

    def __init__(self, chance: float, stages: dict):
        self.chance = chance
        self.stages = {g: j for g, j in stages.items() if j}

    @staticmethod
    def from_json(setup: list):
        if not setup:
            return StatChange.null()
        return StatChange(*setup)

    @staticmethod
    def null():
        return StatChange(0, {})

    @property
    def json(self):
        return [self.chance, self.stages]


class StatusEffect:
    def __init__(self, chance: float, effect: str):
        self.chance = chance
        self.effect = effect

    @staticmethod
    def from_json(setup: list):
        if not setup:
            return StatusEffect.null()
        return StatusEffect(*setup)

    @staticmethod
    def null():
        return StatusEffect(0, "")

    @property
    def json(self):
        return [self.chance, self.effect]


class Move:
    def __init__(self, name: str, typ: str, category: str, pp: int, pwr: Union[str, int], accuracy: int, contact: bool,
                 can_protect: bool, can_magic_coat: bool, can_snatch: bool, can_mirror_move: bool, can_kings_rock: bool,
                 target: str, **kwargs):
        self.name = name
        self.type = typ
        self.category = category
        self.pp = pp
        self.ppc = kwargs.get("ppc", pp)
        self.power = pwr
        self.accuracy = accuracy
        self.priority = kwargs.get("priority", 0)
        self.contact = contact
        self.can_protect = can_protect
        self.can_magic_coat = can_magic_coat
        self.can_snatch = can_snatch
        self.can_mirror_move = can_mirror_move
        self.can_kings_rock = can_kings_rock
        self.target = target
        self.user_stat_changes = StatChange.from_json(kwargs.get("user_stat_changes") if target != user else [])
        self.target_stat_changes = StatChange.from_json(kwargs.get("target_stat_changes"))
        self.status_effect = StatusEffect.from_json(kwargs.get("status_effects"))
        self.flinch = kwargs.get("flinch", False)

    @staticmethod
    def from_json(setup: list):
        return Move(*setup[:-1], **setup[-1])

    @property
    def json(self):
        kwargs = {
            **({"ppc": self.ppc} if self.ppc != self.pp else {}),
            **({"priority": self.priority} if self.priority else {}),
            **({"user_stat_changes": self.user_stat_changes.json} if self.user_stat_changes else {}),
            **({"target_stat_changes": self.target_stat_changes.json} if self.target_stat_changes else {}),
            **({"status_effect": self.status_effect.json} if self.status_effect else {}),
            **({"flinch": self.flinch} if self.flinch else {})
        }

        return [
            self.name, self.type, self.category, self.pp, self.power, self.accuracy, self.contact, self.can_protect,
            self.can_magic_coat, self.can_snatch, self.can_mirror_move, self.can_kings_rock, self.target, kwargs
        ]
