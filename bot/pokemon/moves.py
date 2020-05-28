from typing import Union
import json


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
    "all adjacent foes", "all adjacent Pok\u00e9mon", "all foes", "all Pok\u00e9mon", "any adjacent ally", "the user", \
    "the user and all allies"
statusConditions = poisoned, badlyPoisoned, burned, paralyzed, asleep, frozen, fainted = "Poisoned", "Badly poisoned", \
    "Burned", "Paralyzed", "Asleep", "Frozen", "Fainted"


class StatChange:
    """Chances should be the percentage value, NOT the decimal value. A 10% chance should be input as 10."""
    stat_name_dict = {
        "atk": "Attack", "dfn": "Defense", "spa": "Special Attack", "spd": "Special Defense", "spe": "Speed",
        "eva": "evasion", "acc": "accuracy"
    }
    modifier_strings = [
        "{name}'s {stat} won't go any higher!", "{name}'s {stat} rose!", "{name}'s {stat} rose sharply!",
        "{name}'s {stat} rose drastically!", "{name}'s {stat} severely fell!", "{name}'s {stat} harshly fell!",
        "{name}'s {stat} fell!"
    ]
    numbers = ["zero stages", "one stage", "two stages", "three stages", "three stages", "two stages", "one stage"]

    def __init__(self, chance: float, stages: dict):
        self.chance = chance
        self.stages = {g: j for g, j in stages.items() if j}

    def __bool__(self):
        return bool(self.chance and self.stages)

    def str(self, affected: str):
        if set(self.stages) == {"atk", "dfn", "spa", "spd", "spe"}:
            ret = {f"all the {affected}'s stats": self.stages["atk"]}
        else:
            ret = {f"the {affected}'s {self.stat_name_dict[g]}": j for g, j in self.stages.items()}
        if self.chance == 100:
            return "\n".join(f"{'Raises' if j > 0 else 'Lowers'} {g} by {self.numbers[j]}." for g, j in ret.items())
        return "\n".join(
            f"Has a chance to {'raise' if j > 0 else 'lower'} {g} by {self.numbers[j]}." for g, j in ret.items()
        )

    @staticmethod
    def from_json(setup: list):
        if not setup:
            return StatChange.null()
        if isinstance(setup, StatChange):
            return setup
        if isinstance(setup, list):
            return StatChange(*setup)
        return StatChange.null()

    @staticmethod
    def null():
        return StatChange(0, {})

    @property
    def json(self):
        return [self.chance, self.stages]


class StatusEffect:
    """Like StatChange, chance should be out of 100."""
    def __init__(self, chance: float, effect: str):
        self.chance = chance
        self.effect = effect

    def __bool__(self):
        return bool(self.chance and self.effect)

    def __str__(self):
        effects = {
            burned: "Burn", frozen: "Freeze", paralyzed: "Paralyze", poisoned: "Poison", badlyPoisoned: "Badly poison"
        }
        if self.chance == 100:
            return "Puts the target to sleep." if self.effect == asleep else \
                f"{effects[self.effect]}s the target."
        else:
            return "Has a chance to put the target to sleep." if self.effect == asleep else \
                f"Has a chance to {effects[self.effect].lower()} the target."

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


class ZEffect:
    """A class for the secondary effects of status Z-moves."""

    def __init__(self, typ: Union[str, None], effect: Union[StatChange, bool, str]):
        self.type = typ
        self.effect = effect

    def __bool__(self):
        return bool(self.effect)

    @staticmethod
    def from_json(setup: dict):
        if not setup:
            return ZEffect.null()
        typ, effect = list(setup)[0], list(setup.values())[0]
        if StatChange.from_json(effect):
            return ZEffect(typ, StatChange.from_json(effect))
        return ZEffect(typ, effect)

    @staticmethod
    def null():
        return ZEffect(None, False)

    @property
    def json(self):
        if isinstance(self.effect, StatChange):
            return {self.type: self.effect.json}
        else:
            return {self.type: self.effect}


class Move:
    def __init__(self, name: str, typ: str, category: str, pp: int, pwr: int, accuracy: int, contact: bool,
                 target: str, **kwargs):
        # BASE DATA
        self.name = name
        self.type = typ
        self.category = category
        self.pp = pp
        self.ppc = kwargs.get("ppc", pp)
        self.power = pwr
        self.accuracy = accuracy
        self.priority = kwargs.get("priority", 0)
        self.contact = contact
        self.target = target

        # PT-MC-SN-MM-KR
        self.can_protect = kwargs.get("can_protect", False)
        self.can_magic_coat = kwargs.get("can_magic_coat", False)
        self.can_snatch = kwargs.get("can_snatch", False)
        self.can_mirror_move = kwargs.get("can_mirror_move", False)
        self.can_kings_rock = kwargs.get("can_kings_rock", False)

        if self.category == status:
            self.z_effect = ZEffect.from_json(kwargs.get("z_effect", {}))
        else:
            self.z_effect = ZEffect.null()

        # STAT CHANGES
        if target == user:
            self.user_stat_changes = StatChange.from_json(
                kwargs.get("user_stat_changes", kwargs.get("usc", kwargs.get("target_stat_changes", kwargs.get("tsc"))))
            )
            self.target_stat_changes = StatChange.null()
        else:
            self.user_stat_changes = StatChange.from_json(kwargs.get("user_stat_changes", kwargs.get("usc")))
            self.target_stat_changes = StatChange.from_json(kwargs.get("target_stat_changes", kwargs.get("tsc")))
        self.reset_stats = kwargs.get("reset_stats", False)

        # STATUS EFFECTS / CONDITIONS
        self.status_effect = StatusEffect.from_json(kwargs.get("status_effect"))
        self.flinch = kwargs.get("flinch", 0)
        self.confuse = kwargs.get("confuse", 0)

        # SPECIFIC SINGLE-USE EFFECTS
        self.payday = kwargs.get("payday", False)
        self.fly = kwargs.get("fly", False)
        self.thrash = kwargs.get("thrash", False)
        self.disable = kwargs.get("disable", False)
        self.mist = kwargs.get("mist", False)
        self.counter = kwargs.get("counter", False)
        self.psyshock = kwargs.get("psyshock", False)
        self.false_swipe = kwargs.get("false_swipe", False)
        self.switch = kwargs.get("switch", False)  # switching out. only for system use
        self.leech_seed = kwargs.get("leech_seed", False)
        self.yawn = kwargs.get("yawn", False)
        self.fake_out = kwargs.get("fake_out", False)
        self.dig = kwargs.get("dig", False)
        self.endure = kwargs.get("endure", False)
        self.protect = kwargs.get("protect", False)

        # COMMON ADDITIONAL EFFECTS
        self.absorbent = kwargs.get("absorbent", False)
        self.recoil = kwargs.get("recoil", 0)  # recoil arg should be denominator of fraction: 1/3 recoil > recoil=3
        self.crash = kwargs.get("crash", False)
        self.raised_crit_ratio = kwargs.get("raised_crit_ratio", 0)
        self.force_out = kwargs.get("force_out", False)
        self.binding = kwargs.get("binding", False)
        self.full_heal = kwargs.get("full_heal", False)  # full HP restoration
        self.used_in_succession = kwargs.get("used_in_succession", False)

        # STRIKE / TURN CONTROL
        self.multi2 = kwargs.get("multi2", False)
        self.multi25 = kwargs.get("multi25", False)
        self.two_turn = kwargs.get("two_turn", False)
        self.must_recharge = kwargs.get("must_recharge", kwargs.get("must_rest", False))  # Giga Impact, etc.

        # ABSOLUTE POWER / DAMAGE MODS
        self.ohko = kwargs.get("ohko", False)
        self.exact_damage = kwargs.get("exact_damage", 0)
        self.weight_based = kwargs.get("weight_based", False)  # power dependent on target's weight
        self.level_damage = kwargs.get("level_damage", False)  # does damage equal to user's level

        # SITUATIONAL POWER BOOSTS
        self.stomp = kwargs.get("stomp", False)  # double damage against Minimize
        self.facade = kwargs.get("facade", False)
        self.brine = kwargs.get("brine", False)

        # WEATHER / FIELD MODS
        self.removes_barriers = kwargs.get("removes_barriers", False)  # removes Light Screen / Reflect

        # ACCURACY BYPASSES
        self.can_hit_fly = kwargs.get("can_hit_fly", False)
        self.can_hit_dive = kwargs.get("can_hit_dive", False)
        self.can_hit_dig = kwargs.get("can_hit_dig", False)
        self.hits_in_hail = kwargs.get("hits_in_hail", False)

        # CATEGORIZATIONS
        self.sound_based = kwargs.get("sound_based", False)  # Soundproof is immune
        self.ball_and_bomb = kwargs.get("ball_and_bomb", False)  # Bulletproof is immune
        self.powder_based = kwargs.get("powder_based", False)  # Grass-types, Safety Goggles, and Overcoat are immune
        self.aura_and_pulse = kwargs.get("aura_and_pulse", False)  # boosted by Mega Launcher

    @staticmethod
    def from_json(setup: list):
        return Move(*setup[:-1], **setup[-1])

    @property
    def json(self):
        def fi(s: str):
            return {s: self.__getattribute__(s)} if self.__getattribute__(s) else {}

        kwargs = {
            **({"ppc": self.ppc} if self.ppc != self.pp else {}), **fi("priority"),
            **({"user_stat_changes": self.user_stat_changes.json} if self.user_stat_changes else {}),
            **({"target_stat_changes": self.target_stat_changes.json} if self.target_stat_changes else {}),
            **({"status_effect": self.status_effect.json} if self.status_effect else {}),
            **({"z_effect": self.z_effect.json} if self.z_effect else {}),
            **fi("can_protect"), **fi("can_magic_coat"), **fi("can_snatch"), **fi("can_mirror_move"),
            **fi("can_kings_rock"),
            **fi("flinch"), **fi("confuse"), **fi("absorbent"), **fi("recoil"), **fi("raised_crit_ratio"),
            **fi("multi25"), **fi("payday"), **fi("ohko"), **fi("two_turn"), **fi("reset_stats"), **fi("can_hit_fly"),
            **fi("fly"), **fi("binding"), **fi("stomp"), **fi("multi2"), **fi("crash"), **fi("thrash"),
            **fi("force_out"), **fi("sound_based"), **fi("exact_damage"), **fi("disable"), **fi("mist"),
            **fi("full_heal"), **fi("can_hit_dive"), **fi("hits_in_hail"), **fi("weight_based"), **fi("counter"),
            **fi("level_damage"), **fi("psyshock"), **fi("facade"), **fi("false_swipe"), **fi("switch"),
            **fi("leech_seed"), **fi("must_recharge"), **fi("yawn"), **fi("brine"), **fi("can_hit_dig"),
            **fi("ball_and_bomb"), **fi("powder_based"), **fi("aura_and_pulse"), **fi("removes_barriers"),
            **fi("fake_out"), **fi("dig"), **fi("endure"), **fi("used_in_succession"), **fi("protect")
        }

        return [
            self.name, self.type, self.category, self.pp, self.power, self.accuracy, self.contact, self.target, kwargs
        ]

    def copy(self):
        return Move.from_json(self.json)

    @property
    def accuracy_str(self):
        return f"{self.accuracy}%" if self.accuracy else "—"

    @property
    def power_str(self):
        return self.power if self.power else "—"

    @property
    def description(self):
        ret = []
        if self.two_turn:
            ret.append("- Strikes on the second turn.")
        if self.status_effect:
            ret.append(f"- {self.status_effect}")
        if self.confuse == 100:
            ret.append("- Confuses the target.")
        elif self.confuse:
            ret.append("- May confuse the target.")
        if self.flinch == 100:
            ret.append("- Causes the target to flinch.")
        elif self.flinch:
            ret.append("- May cause the target to flinch.")
        if self.user_stat_changes:
            ret.append("- " + "\n- ".join(self.user_stat_changes.str("user").splitlines()))
        if self.target_stat_changes:
            ret.append("- " + "\n- ".join(self.target_stat_changes.str("target").splitlines()))
        if self.multi2:
            ret.append("- Hits exactly twice.")
        if self.multi25:
            ret.append("- Hits two to five times.")
        if self.absorbent:
            ret.append("- Restores the user's HP by half the damage dealt.")
        if self.recoil:
            ret.append(f"- The user receives 1/{self.recoil} of the damage dealt as recoil.")
        if self.raised_crit_ratio:
            ret.append("- Has a high critical-hit ratio.")
        if self.category != status and not self.accuracy:
            ret.append("- Never misses.")
        if self.ohko:
            ret.append("- One-hit KOs the target if it hits.")
        if self.payday:
            ret.append("- Money is earned after the battle.")
        if self.reset_stats:
            ret.append("- Resets the user's lowered stats.")
        if self.can_hit_fly:
            ret.append("- Can hit targets during Fly.")
        if self.can_hit_dive:
            ret.append("- Can hit targets during Dive.")
        if self.force_out:
            ret.append("- Forces the target to switch out.")
        if self.fly:
            ret.append("- The user flies up high on the first turn, and attacks on the second.")
        if self.binding:
            ret.append("- The target will continue to take damage for four to five turns.")
        if self.stomp:
            ret.append("- Does double damage against a Minimized target.")
        if self.crash:
            ret.append("- If it misses, the user hurts itself.")
        if self.thrash:
            ret.append("- The user rampages for 2-3 turns, then gets confused.")
        if self.exact_damage:
            ret.append(f"- Always does exactly {self.exact_damage} HP damage.")
        if self.disable:
            ret.append("- Disables the last move the target used for four turns.")
        if self.mist:
            ret.append("- Prevents the user and its allies' stats from being lowered for five turns.")
        if self.full_heal:
            ret.append("- Fully restores the user's HP.")
        if self.hits_in_hail:
            ret.append("- Always hits during hailstorms.")
        if self.weight_based:
            ret.append("- The heavier the target, the greater the move's power.")
        if self.counter:
            ret.append("- Counters any physical attack, inflicting double the damage taken.")
        if self.level_damage:
            ret.append("- Does damage equal to the user's level.")
        if self.psyshock:
            ret.append("- Does physical damage.")
        if self.facade:
            ret.append("- If the user is poisoned, paralyzed, or burned, power doubles.")
        if self.false_swipe:
            ret.append("- Leaves the target with at least 1 HP.")
        if self.leech_seed:
            ret.append("- Plants a seed on the target which drains its HP to heal the user.")
        if self.must_recharge:
            ret.append("- The user must rest on the next turn.")
        if self.yawn:
            ret.append("- Lulls the target into falling asleep after the next turn.")
        if self.brine:
            ret.append("- Does double damage against a target with less than 50% HP.")
        if self.can_hit_dig:
            ret.append("- Can hit targets during Dig.")
        if self.removes_barriers:
            ret.append("- Removes Light Screen and Reflect from the target's team.")
        if self.fake_out:
            ret.append("- Only works on the first turn the user is in battle.")
        if self.dig:
            ret.append("- The user burrows underground on the first turn, and attacks on the second.")
        if self.endure:
            ret.append("- The user endures any attack with at least 1 HP.")
        if self.protect:
            ret.append("- Enables the user to evade all attacks.")

        if self.used_in_succession:
            ret.append("- Its chance of failing rises if it is used in succession.")
        if self.z_effect:
            ret.append("- Z-Effect: " + Move("", "", status, 0, 0, 0, False, "", **self.z_effect.json).description[2:])

        if not ret:
            return "- Has no secondary effect."
        return "\n".join(ret)


class PackedMove:
    """Moves are stored in this format in actual Mon objects."""
    def __init__(self, name: str, pp: int, ppc: int = -1):
        if ppc == -1:
            ppc = pp
        self.name = name
        self.pp = pp
        self.ppc = ppc

    @staticmethod
    def from_move(m: Move):
        return PackedMove(m.name, m.pp, m.ppc)

    def unpack(self):
        if self.name in systemMoves:
            ret = systemMoves[self.name].copy()
        else:
            ret = moveDex[self.name].copy()
        ret.pp = self.pp
        ret.ppc = self.ppc
        assert isinstance(ret, Move)
        return ret


with open("moves.json" if __name__ == "__main__" else "pokemon/moves.json", "r") as fp:
    moveDex = {g: Move.from_json(j) for g, j in json.load(fp).items()}


twoTurnTexts = {
    "Razor Wind": "{name} whipped up a whirlwind!",
    "Solar Beam": "{name} absorbed light!"
}


systemMoves = {
    "Switch": Move.from_json(["Switch", None, None, 0, 0, 0, False, None, {"switch": True, "priority": 10}]),
    "Exit": Move.from_json(["Exit", None, None, 0, 0, 0, False, None, {}]),
    "Confused": Move.from_json(["Confused", None, physical, 0, 40, 0, False, None, {"raised_crit_ratio": -100}])
}
