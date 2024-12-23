import json
from discord.ext import commands
from functions import best_guess, fix
from re import sub


def alpha_fix(s: str) -> str:
    return sub(r"[^A-Za-z0-9]", "", fix(s))


def bulba_format(s: str):
    return '_'.join(s.split()).replace("'", "%27")


types = normal, fire, water, electric, grass, ice, fighting, poison, ground, flying, psychic, bug, rock, ghost, \
    dragon, dark, steel, fairy = "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", \
    "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
type_colors = {
    normal: "A8A878", fire: "F08030", water: "6890F0", grass: "78C850", electric: "F8D030", rock: "B8A038",
    ground: "E0C068", steel: "B8B8D0", psychic: "F85888", fighting: "C03028", flying: "A890F0", ghost: "705898",
    dark: "705848", bug: "A8B820", poison: "A040A0", fairy: "EE99AC", dragon: "7038F8", ice: "98D8D8"
}
categories = physical, special, status = "Physical", "Special", "Status"
targets = anyAdjFoe, anyAdj, anyMon, userOrAdjAlly, allAdjFoe, allAdj, allFoe, allMon, anyAdjAlly, user, userAllAlly = \
    "any adjacent foe", "any adjacent Pok\u00e9mon", "any Pok\u00e9mon", "the user or an adjacent ally", \
    "all adjacent foes", "all adjacent Pok\u00e9mon", "all foes", "all Pok\u00e9mon", "any adjacent ally", "the user", \
    "the user and all allies"
status_conditions = poisoned, badly_poisoned, burned, paralyzed, asleep, frozen, fainted = "Poisoned", \
    "Badly poisoned", "Burned", "Paralyzed", "Asleep", "Frozen", "Fainted"
weather_types = sun, rain, hail, sandstorm, snow = "Harsh sunlight", "Rain", "Hail", "Sandstorm", "Snow"
six_stats = {"hp": "HP", "atk": "Atk", "def": "Def", "spa": "SpA", "spd": "SpD", "spe": "Spe"}
six_stat_names = list(six_stats.values())


class StatChange:
    """Chances should be the percentage value, NOT the decimal value. A 10% chance should be input as 10."""
    stat_name_dict = {
        "atk": "Attack", "def": "Defense", "spa": "Special Attack", "spd": "Special Defense", "spe": "Speed",
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
        if set(self.stages) == {"atk", "def", "spa", "spd", "spe"}:
            ret = {f"all the {affected}'s stats": self.stages["atk"]}
        else:
            ret = {f"the {affected}'s {self.stat_name_dict[g]}": j for g, j in self.stages.items()}
        if self.chance == 100:
            return "\n".join(f"{'Raises' if j > 0 else 'Lowers'} {g} by {self.numbers[j]}." for g, j in ret.items())
        return "\n".join(
            f"Has a {self.chance}% chance to {'raise' if j > 0 else 'lower'} {g} by {self.numbers[j]}."
            for g, j in ret.items()
        )

    @staticmethod
    def from_json(setup: list):
        if not setup:
            return StatChange.null()
        if isinstance(setup, StatChange):
            return setup
        if isinstance(setup, list):
            return StatChange(*setup)
        if isinstance(setup, dict):
            return StatChange(100, setup)
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
            burned: "Burn", frozen: "Freeze", paralyzed: "Paralyze", poisoned: "Poison", badly_poisoned: "Badly poison"
        }
        if self.chance == 100:
            return "Puts the target to sleep." if self.effect == asleep else \
                f"{effects[self.effect]}s the target."
        else:
            return f"Has a {self.chance}% chance to put the target to sleep." if self.effect == asleep else \
                f"Has a {self.chance}% chance to {effects[self.effect].lower()} the target."

    @staticmethod
    def from_json(setup: list):
        if not setup:
            return StatusEffect.null()
        if isinstance(setup, str):
            return StatusEffect(100, setup)
        return StatusEffect(*setup)

    @staticmethod
    def null():
        return StatusEffect(0, "")

    @property
    def json(self):
        return [self.chance, self.effect]


class ZEffect:
    """A class for the secondary effects of status Z-moves."""

    def __init__(self, typ: str | None, effect: StatChange | bool | str):
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

        if self.category == status:
            self.z_effect = ZEffect.from_json(kwargs.get("z_effect", kwargs.get("z")))
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
        self.reset_low_stats = kwargs.get("reset_low_stats", False)
        self.reset_target_stats = kwargs.get("reset_target_stats", False)
        self.reset_all_stats = kwargs.get("reset_all_stats", False)

        # STATUS EFFECTS / CONDITIONS
        self.status_effect = StatusEffect.from_json(kwargs.get("status_effect", kwargs.get("status")))
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
        self.leech_seed = kwargs.get("leech_seed", False)
        self.yawn = kwargs.get("yawn", False)
        self.fake_out = kwargs.get("fake_out", False)
        self.dig = kwargs.get("dig", False)
        self.endure = kwargs.get("endure", False)
        self.protect = kwargs.get("protect", False)
        self.growth = kwargs.get("growth", False)
        self.rage = kwargs.get("rage", False)
        self.mimic = kwargs.get("mimic", False)
        self.reflect = kwargs.get("reflect", False)
        self.light_screen = kwargs.get("light_screen", False)
        self.aurora_veil = kwargs.get("aurora_veil", False)
        self.trick_room = kwargs.get("trick_room", False)
        self.belly_drum = kwargs.get("belly_drum", False)
        self.minimize = kwargs.get("minimize", False)
        self.curl = kwargs.get("curl", False)
        self.focus_energy = kwargs.get("focus_energy", False)
        self.metronome = kwargs.get("metronome", False)
        self.dream_eater = kwargs.get("dream_eater", False)
        self.tera_blast = kwargs.get("tera_blast", False)

        # COMMON ADDITIONAL EFFECTS
        self.absorbent = kwargs.get("absorbent", False)
        self.recoil = kwargs.get("recoil", 0)  # recoil arg should be denominator of fraction: 1/3 recoil > recoil=3
        self.crash = kwargs.get("crash", False)
        self.raised_crit_ratio = kwargs.get("raised_crit_ratio", 0)
        self.force_out = kwargs.get("force_out", False)
        self.binding = kwargs.get("binding", False)
        self.full_heal = kwargs.get("full_heal", False)  # full HP restoration
        self.half_heal = kwargs.get("half_heal", False)
        self.used_in_succession = kwargs.get("used_in_succession", False)
        self.add_type = kwargs.get("add_type", None)
        self.change_type = kwargs.get("change_type", None)
        self.ignore_tsc = kwargs.get("ignore_tsc", False)
        self.switch_self = kwargs.get("switch_self", False)
        self.fails_if_cant_switch = kwargs.get("fails_if_cant_switch", False)

        # STRIKE / TURN CONTROL
        self.multi2 = kwargs.get("multi2", False)
        self.multi25 = kwargs.get("multi25", False)
        self.two_turn = kwargs.get("two_turn", False)
        self.must_recharge = kwargs.get("must_recharge", kwargs.get("must_rest", False))  # Giga Impact, etc.
        self.solar = kwargs.get("solar", False)  # Solar Beam + Solar Blade
        self.triple_kick = kwargs.get("triple_kick", False)  # Triple Kick + Triple Axel
        self.population_bomb = kwargs.get("population_bomb", False)

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
        self.weather = kwargs.get("weather", None)

        # ACCURACY BYPASSES
        self.can_hit_fly = kwargs.get("can_hit_fly", False)
        self.can_hit_dive = kwargs.get("can_hit_dive", False)
        self.can_hit_dig = kwargs.get("can_hit_dig", False)
        self.hits_in_hail = kwargs.get("hits_in_hail", False)
        self.hits_in_rain = kwargs.get("hits_in_rain", False)
        self.poison_never_miss = kwargs.get("poison_never_miss", False)

        # CATEGORIZATIONS
        self.sound_based = kwargs.get("sound_based", False)  # Soundproof is immune
        self.ball_and_bomb = kwargs.get("ball_and_bomb", False)  # Bulletproof is immune
        self.powder_based = kwargs.get("powder_based", False)  # Grass-types, Safety Goggles, and Overcoat are immune
        self.aura_and_pulse = kwargs.get("aura_and_pulse", False)  # boosted by Mega Launcher
        self.still_typed = kwargs.get("still_typed", False)  # offensive status moves still affected by type
        self.slicing = kwargs.get("slicing", False)  # Sharpness boosts power

    @staticmethod
    def from_json(setup: list):
        return Move(*setup[:-1], **setup[-1])

    @staticmethod
    def control(name: str):
        return Move(name, "", "", 0, 0, 0, False, "")

    @property
    def pack(self):
        return PackedMove(self.name, self.pp, self.ppc)

    @property
    def json(self):
        basic_args = [
            "priority", "can_protect", "can_magic_coat", "can_snatch", "can_mirror_move", "flinch", "confuse",
            "absorbent", "recoil", "raised_crit_ratio", "multi25", "payday", "ohko", "two_turn", "reset_low_stats",
            "can_hit_fly", "fly", "binding", "stomp", "multi2", "crash", "thrash", "force_out", "sound_based",
            "exact_damage", "disable", "mist", "full_heal", "can_hit_dive", "hits_in_hail", "weight_based", "counter",
            "level_damage", "psyshock", "facade", "false_swipe", "leech_seed", "must_recharge", "yawn", "brine",
            "can_hit_dig", "ball_and_bomb", "powder_based", "aura_and_pulse", "removes_barriers", "fake_out", "dig",
            "used_in_succession", "protect", "growth", "weather", "solar", "still_typed", "hits_in_rain", "endure",
            "poison_never_miss", "rage", "mimic", "tera_blast", "half_heal", "reset_target_stats", "reset_all_stats",
            "add_type", "change_type", "ignore_tsc", "reflect", "light_screen", "aurora_veil", "trick_room",
            "belly_drum", "triple_kick", "population_bomb", "slicing", "switch_self", "fails_if_cant_switch",
            "minimize", "curl", "focus_energy", "metronome", "dream_eater"
        ]

        kwargs = {
            **({"ppc": self.ppc} if self.ppc != self.pp else {}),
            **({"user_stat_changes": self.user_stat_changes.json} if self.user_stat_changes else {}),
            **({"target_stat_changes": self.target_stat_changes.json} if self.target_stat_changes else {}),
            **({"status_effect": self.status_effect.json} if self.status_effect else {}),
            **({"z_effect": self.z_effect.json} if self.z_effect else {}),
            **{g: self.__getattribute__(g) for g in basic_args if self.__getattribute__(g)}
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
        if self.dream_eater:
            ret.append("- Can only be used on sleeping Pok\u00e9mon.")
        if self.two_turn:
            ret.append("- Strikes on the second turn.")
        if self.solar:
            ret.append("- Can be executed in a single turn during harsh sunlight.")
        if self.status_effect:
            ret.append(f"- {self.status_effect}")
        if self.confuse == 100:
            ret.append("- Confuses the target.")
        elif self.confuse:
            ret.append(f"- Has a {self.confuse}% chance to confuse the target.")
        if self.flinch == 100:
            ret.append("- Causes the target to flinch.")
        elif self.flinch:
            ret.append(f"- Has a {self.flinch}% chance to cause the target to flinch.")
        if self.user_stat_changes:
            ret.append("- " + "\n- ".join(self.user_stat_changes.str("user").splitlines()))
        if self.target_stat_changes:
            ret.append("- " + "\n- ".join(self.target_stat_changes.str("target").splitlines()))
        if self.multi2:
            ret.append("- Hits exactly twice.")
        if self.multi25:
            ret.append("- Hits two to five times.")
        if self.triple_kick:
            ret.append(f"- Hits up to three times, with each strike having its own accuracy check. Each successive "
                       f"strike increases in base power by {self.power}.")
        if self.population_bomb:
            ret.append(f"- Hits up to ten times, with each strike having its own accuracy check.")
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
        if self.reset_low_stats:
            ret.append("- Resets the user's lowered stats.")
        if self.reset_target_stats:
            ret.append("- Resets the target's stat changes.")
        if self.reset_all_stats:
            ret.append("- Resets the stat changes of all mons on the field.")
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
        if self.half_heal:
            ret.append("- Restores half the user's HP.")
        if self.hits_in_hail:
            ret.append("- Always hits during hailstorms.")
        if self.hits_in_rain:
            ret.append("- Always hits during rain.")
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
        if self.growth:
            ret.append("- Raises the user's Attack and Special Attack by one stage each, or two stages in sunlight.")
        if self.poison_never_miss:
            ret.append("- Poison-types never miss this move.")
        if self.rage:
            ret.append("- After landing this move once, the user's Attack stat will rise one stage each time it is "
                       "damaged by an attack. This will continue until another move is selected.")
        if self.mimic:
            ret.append("- Copies the target's last used move, which the user may continue using until the battle ends.")
        if self.add_type:
            ret.append(f"- Adds the {self.add_type} type to the target. "
                       f"Fails if the target is already {self.add_type}-type.")
        if self.change_type:
            ret.append(f"- Changes the target to become pure {self.change_type}-type.")
        if self.ignore_tsc:
            ret.append("- Ignores the target's defensive stat changes.")
        if self.reflect:
            ret.append("- For 5 turns, reduces physical damage taken by the mon and its allies by half "
                       "(or one-third in a Double Battle).")
        if self.light_screen:
            ret.append("- For 5 turns, reduces special damage taken by the mon and its allies by half "
                       "(or one-third in a Double Battle).")
        if self.aurora_veil:
            ret.append("- For 5 turns, reduces physical and special damage taken by the mon and its allies by half "
                       "(or one-third in a Double Battle). Can only be used during hail or snow.")
        if self.trick_room:
            ret.append("- For 5 turns, mons with a lower Speed stat will move first within their priority bracket.")
        if self.belly_drum:
            ret.append("- The user loses half its max HP, but maximizes its Attack stat.")
        if self.minimize:
            ret.append("- Minimizes the user, causing them to become more vulnerable to moves such as Stomp.")
        if self.curl:
            ret.append("- The user curls up, making its subsequent Rollout and Ice Ball attacks twice as powerful.")
        if self.focus_energy:
            ret.append("- Raises the user's critical hit rate.")
        if self.tera_blast:
            ret.append("- Changes to the user's Tera type when Terastallized. Becomes a physical move if the user's "
                       "Attack is higher than its Special Attack.")

        if self.weather:
            weather_descriptions = {
                sun: "intense sunlight", rain: "a heavy rain", hail: "a hailstorm", sandstorm: "a sandstorm",
                snow: "snow"
            }
            ret.append(f"- Summons {weather_descriptions[self.weather]} that lasts for five turns.")

        if self.switch_self:
            ret.append("- Switches the user out.")

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

    @staticmethod
    def null():
        return PackedMove("", 0)

    def __bool__(self):
        return bool(self.name)

    def unpack(self):
        if self.name in system_moves:
            ret = system_moves[self.name].copy()
        else:
            ret = battle_moves[self.name].copy()
        ret.pp = self.pp
        ret.ppc = self.ppc
        assert isinstance(ret, Move)
        return ret


battle_moves = {g: Move.from_json(j) for g, j in json.load(open("pokemon/data/moves.json", "r")).items()}


two_turn_texts = {
    "Razor Wind": "{name} whipped up a whirlwind!",
    "Solar Beam": "{name} absorbed light!",
    "Sky Attack": "{name} became cloaked in a harsh light!"
}
no_metronome = [
    'After You', 'Apple Acid', 'Armor Cannon', 'Assist', 'Astral Barrage', 'Aura Wheel', 'Baneful Bunker',
    'Beak Blast', 'Behemoth Bash', 'Behemoth Blade', 'Belch', 'Bestow', 'Blazing Torque', 'Body Press', 'Branch Poke',
    'Breaking Swipe', 'Celebrate', 'Chatter', 'Chilling Water', 'Chilly Reception', 'Clangorous Soul',
    'Collision Course', 'Combat Torque', 'Comeuppance', 'Copycat', 'Counter', 'Covet', 'Crafty Shield', 'Decorate',
    'Destiny Bond', 'Detect', 'Diamond Storm', 'Doodle', 'Double Iron Bash', 'Double Shock', 'Dragon Ascent',
    'Dragon Energy', 'Drum Beating', 'Dynamax Cannon', 'Electro Drift', 'Endure', 'Eternabeam', 'False Surrender',
    'Feint', 'Fiery Wrath', 'Fillet Away', 'Fleur Cannon', 'Focus Punch', 'Follow Me', 'Freeze Shock',
    'Freezing Glare', 'Glacial Lance', 'Grav Apple', 'Helping Hand', 'Hold Hands', 'Hyper Drill', 'Hyperspace Fury',
    'Hyperspace Hole', 'Ice Burn', 'Instruct', 'Jet Punch', 'Jungle Healing', "King's Shield", 'Life Dew',
    'Light of Ruin', 'Make It Rain', 'Magical Torque', 'Mat Block', 'Me First', 'Meteor Assault', 'Mimic',
    'Mind Blown', 'Mirror Coat', 'Mirror Move', 'Moongeist Beam', 'Nature Power', "Nature's Madness", 'Noxious Torque',
    'Obstruct', 'Order Up', 'Origin Pulse', 'Overdrive', 'Photon Geyser', 'Plasma Fists', 'Population Bomb', 'Pounce',
    'Power Shift', 'Precipice Blades', 'Protect', 'Pyro Ball', 'Quash', 'Quick Guard', 'Rage Fist', 'Rage Powder',
    'Raging Bull', 'Raging Fury', 'Relic Song', 'Revival Blessing', 'Ruination', 'Salt Cure', 'Secret Sword',
    'Shed Tail', 'Shell Trap', 'Silk Trap', 'Sketch', 'Sleep Talk', 'Snap Trap', 'Snarl', 'Snatch', 'Snore',
    'Snowscape', 'Spectral Thief', 'Spicy Extract', 'Spiky Shield', 'Spirit Break', 'Spotlight', 'Steam Eruption',
    'Steel Beam', 'Strange Steam', 'Struggle', 'Sunsteel Strike', 'Surging Strikes', 'Switcheroo', 'Techno Blast',
    'Thief', 'Thousand Arrows', 'Thousand Waves', 'Thunder Cage', 'Thunderous Kick', 'Tidy Up', 'Trailblaze',
    'Transform', 'Trick', 'Twin Beam', 'V-create', 'Wicked Blow', 'Wicked Torque', 'Wide Guard'
]


system_moves = {
    "Switch": Move.from_json(["Switch", None, None, 0, 0, 0, False, None, {"switch": True, "priority": 10}]),
    "Team": Move.control("Switch"),
    "Exit": Move.control("Exit"),
    "Confused": Move.from_json(["Confused", None, physical, 0, 40, 0, False, None, {"raised_crit_ratio": -100}]),
    "Status": Move.control("Status"),
    "Terastallize": Move.control("Terastallize"),
    "Tera": Move.control("Terastallize")
}


class WikiMove:
    def __init__(self, **kwargs):
        self.name = kwargs.pop("name")
        self.type = kwargs.pop("type")
        self.category = kwargs.pop("category")
        self.pp = kwargs.pop("pp")
        self.power = kwargs.pop("power")
        self.accuracy = kwargs.pop("accuracy")
        self.description = kwargs.pop("description")

    @property
    def accuracy_str(self):
        return f"{self.accuracy}%" if self.accuracy else "—"

    @property
    def power_str(self):
        return self.power if self.power else "—"

    @property
    def bulbapedia(self):
        return f"https://bulbapedia.bulbagarden.net/wiki/{bulba_format(self.name)}_(move)"

    @property
    def serebii(self):
        return f"https://www.serebii.net/attackdex-sv/{''.join(self.name.lower().split())}.shtml"

    @property
    def pokemondb(self):
        return f"https://pokemondb.net/move/{fix(self.name)}"


wiki_moves = {g: WikiMove(**j) for g, j in json.load(open("pokemon/data/wikimoves.json", "r")).items()}


def find_move(s: str, return_wiki: bool = True, fail_silently: bool = False) -> Move | WikiMove:
    try:
        if return_wiki:
            return [j for g, j in wiki_moves.items() if alpha_fix(g) == alpha_fix(s)][0]
        return [j.copy() for g, j in battle_moves.items() if alpha_fix(g) == alpha_fix(s)][0]
    except IndexError:
        if not fail_silently:
            lis = {fix(g): g for g in (wiki_moves if return_wiki else battle_moves)}
            guess = best_guess(fix(s), list(lis))
            raise commands.CommandError(f"`{s}` not found. Did you mean {lis[guess]}?")
