from pokemon.rules import *
from copy import deepcopy as dc


effDescs = {
    "acupressure": "Raises one random stat two stages", "attract": "Causes opposite-gendered mons to become infatuated",
    "bellyDrum": "Halves the user's HP, but maxes out its Attack", "paralyzed": "Paralyzes target",
    "recoil3": "User receives 1/3 of damage dealt as recoil", "recoil4": "User receives 1/4 of damage dealt as recoil",
    "strike25": "Strikes between 2 and 5 times", "falseSwipe": "Leaves target with at least 1 HP",
    "fakeOut": "Moves first and makes target flinch if used on first turn user is in battle; otherwise, fails",
    "mustRest": "User will need a turn to recharge", "judgment": "Takes on the type of the user's held Plate",
    "metronome": "Selects and uses a random move",
    "painSplit": "Splits the target's and user's combined HP between the two",
    "protect": "Protects the user from all attacks for one turn", "halfHealS": "Recovers half the user's total HP",
    "reflectType": "Changes the user's types to match the target's", "revelation": "Takes on the user's primary type",
    "forceOutT": "Forces the target to switch out", "halfHealT": "Recovers half the target's total HP",
    "safeguard": "Protects the user's team against status conditions for five turns",
    "selfDestruct": "If it lands, the user faints", "extraCrit": "Raised critical hit ratio", "splash": "Does nothing",
    "substitute": "Switches the user for a substitute with 25% of its HP", "halfHPC": "Cuts the target's HP in half",
    "confused": "Confuses the target", "transform": "Transforms the user into a copy of the target",
    "weatherBall": "Changes type based on the weather", "yawn": "Makes the target drowsy",
    "burned": "Burns the target", "flinched": "Makes the target flinch",
    "flameBurst": "If attack lands, a bursting flame damages adjacent enemies", "makeSun": "Turns the sunlight harsh",
    "aquaRing": "User regains 1/16 of its HP each turn", "brine": "Does double damage if target is below half health",
    "dive": "User dives on first turn, then resurfaces and attacks on second", "makeRain": "Causes it to rain",
    "thaw": "Thaws frozen targets", "soak": "Turns the target's primary target to Water",
    "absorbent": "User absorbs half of damage dealt", "weightDMG": "Damage increases with target's weight",
    "ingrain": "User regains 1/16 of its HP each turn, but can't be switched out",
    "leechSeed": "User drains 1/8 of target's HP each turn",
    "slept": "Induces sleep on target", "twoTurn": "User charges up on first turn, then attacks on second",
    "synthesis": "Restores HP; amount varies based on weather", "terrE": "Turns the terrain electric",
    "electroBall": "Becomes more powerful the faster the user is than the target",
    "riseUp": "Un-grounds user for five turns", "thunder": "Always hits in rain",
    "forceOutS": "Forces the user to switch out", "allStats": "Raises all the user's stats one stage",
    "rollout": "Attacks five turns in a row, becoming more powerful with each hit", "makeSand": "Whips up a sandstorm",
    "dig": "User digs underground on first turn, then resurfaces and attacks on second",
    "oneHit": "Knocks the target out in one hit", "magnitude": "Power varies between magnitude 4 and 10",
    "canHitDig": "Can hit mons in the semi-invulnerable Dig state",
    "doubleDig": "Does double damage against targets in the semi-invulnerable Dig state",
    "sandTomb": "Entombs the target in a damaging sand vortex for four to five turns",
    "gyroBall": "Becomes more powerful the slower the user is than the target",
    "aegishield": "Switches Aegislash to Shield Forme", "afterYou": "Makes the target move immediately after the user",
    "assist": "Randomly selects and uses a move from allies' movesets",
    "batonPass": "Switches the user out, passing on all stat changes", "bestow": "User gives the target its item",
    "bide": "User endures attacks for two turns, then returns twice the damage taken on the third",
    "bind": "Entraps and damages the target for four to five turns",
    "block": "Prevents the target from escaping", "camouflage": "Changes the user's type based on the environment",
    "captivate": "Lowers opposite-gendered targets' Special Defense by two stages",
    "celebrate": "The mon congratulates you on your special day!", "ignoreStats": "Ignores target's stat changes",
    "conversion": "Changes the user's first type to that of its first move",
    "conversion2": "Changes the user's first type to one that resist's the target's last move",
    "copycat": "Copies the move used immediately before it", "thief": "Steals the target's held item",
    "crushGrip": "Becomes more powerful the more HP the target has left",
    "disable": "Disables target's last move for four turns", "strike2": "Strikes twice",
    "echoed": "Becomes more powerful with each successive use",
    "encore": "Forces the target to use its last move for the next three turns",
    "endeavor": "Reduces the target's HP to equal the user's",
    "endure": "User survives all attacks with at least 1 HP for one turn",
    "entrain": "Turns the target's ability into the user's",
    "facade": "Doubles in power if user is paralyzed, burned, or poisoned",
    "lightScreen": "Halves special damage done to the user's team for five turns",
    "mirrorCoat": "Counters a special attack for double damage",
    "counter": "Counters a physical attack for double damage",
    "psychoShift": "Transfers the user's status condition to the target", "psyshock": "Does physical damage",
    "reflect": "Halves physical damage done to the user's team for five turns",
    "trickRoom": "Slower mons will move earlier for five turns",
    "breakBarrier": "Breaks Light Screen, Reflect, and Aurora Veil",
    "reversal": "Does more damage when user's HP is lower",
    "wakeUp": "Wakes and does double damage to sleeping targets",
    "bounce": "User bounces into the sky on first turn, then attacks on second",
    "canHitFly": "Can hit mons in the semi-invulnerable Fly, Bounce, and Sky Drop states",
    "doubleFly": "Does double damage against targets in the semi-invulnerable Fly, Bounce, or Sky Drop states",
    "fly": "User flies up into the sky on first turn, then attacks on second",
    "hurricane": "Always hits in rain, but accuracy reduced to 50% in sun",
    "mirrorMove": "Uses the last move targeted at the user", "roost": "User lands and restores half its HP",
    "skyDrop": "User takes the target up into the sky on first turn, then slams them down on second",
    "tailwind": "Doubles user's and allies' effective Speed stats for five turns",
    "breakProtect": "Breaks target's Protect", "phantomForce": "User vanishes on first turn, then attacks on second",
    "noEscape": "Prevents the target from switching out", "embargo": "Prevents target from using items for five turns",
    "shadowForce": "User disappears on first turn, then attacks on second", "knockOff": "Knocks target's held item off",
    "pursuit": "Strikes a target for double damage before it switches out",
    "fellStinger": "Raises the user's Attack by three stages if it knocks out its target",
    "infestation": "The target is trapped and infested for four to five turns", "poisoned": "Poisons the target",
    "badPoisoned": "Badly poisons the target", "venoshock": "Does double damage if target is poisoned",
    "terrM": "Turns the terrain misty", "terrG": "Turns the terrain grassy", "terrP": "Turns the terrain weird",
    "setDamage40": "Inflicts exactly 40 damage", "setDamage20": "Inflicts exactly 20 damage",
    "frozen": "Freezes target", "blizzard": "Always hits in hail", "makeHail": "Causes it to hail",
    "vibropunch": "Becomes stronger with each successive hit",
    "auroraVeil": "Halves damage done to the user by physical and special moves for five turns, but can only be used "
                  "in a hailstorm", "helpingHand": "Boosts the power of an ally's move",
    "suckerPunch": "Fails if the target has not selected a physical or special move",
    "hex": "Doubles in power if the target has a status condition", "dreams": "Fails if target is awake",
    "freezeDry": "Super effective against the Water type", "triAttack": "Burns, paralyzes, or freezes the target",
    "burnUp": "Burns away the user's Fire type",
    "telekinesis": "Levitates the target for three turns, making it easier to hit",
    "guardSplit": "Averages the user's defensive stats with the target's",
    "psychUp": "Copies the target's stat changes onto the user", "trick": "Switches the user's and the target's items",
    "payback": "Doubles in power if the target has already moved", "foresight": "Makes a Ghost-type target vulnerable "
    "to Normal and Fighting moves, and negates the target's evasion stat",
    "wideGuard": "Protects the user's team from multi-target moves",
    "toxicSpikes": "Lays toxic spikes around the opponent team's feet, poisoning mons that switch into battle",
    "rapidSpin": "Eliminates binding moves, Leech Seed, and entry hazards from the user",
    "stockpile": "The user stores up power to be used through either Spit Up or Swallow; can be used up to three times",
    "spitUp": "The user spits up its stockpile in the form of an attack; the greater the stockpile, the higher the "
              "attack's power",
    "swallow": "The user swallows its stockpile to restore HP; the greater the stockpile, the greater the HP restored",
    "fullHeal": "Fully restores the user's UP", "rest": "The user falls asleep for two turns",
    "belch": "Fails if the user has not eaten a Berry at some point in the battle",
    "nightmare": "Afflicts a sleeping target with a nightmare, causing it to lose 1/4 of its maximum HP each turn",
    "round": "Doubles in power if another mon has used this move in the same turn",
    "destinyBond": "If the user is knocked out after using this move, the attacker also faints",
    "taunt": "Forces the target to only use attack moves for three turns", "smackDown": "Grounds the target"
}


def scs(s):
    return f"{'Raises' if int(s[4:]) > 0 else 'Lowers'} {'user' if s[3] == 'S' else 'target'}'s " \
           f"{stats[s[:3]]} {nums[abs(int(s[4:]))]} stage{'s' if abs(int(s[4:])) > 1 else ''}"


class Move:
    def __init__(self, typ: str, category: str, power: int, acc: int, effs: list, target: str,
                 priority: int, name: str, pp: int, z: str=None):
        self.type = typ
        self.category = category
        self.power = power
        self.acc = acc
        self.effs = {g.split("|")[0]: (int(g.split("|")[1]) if "|" in g else 100) for g in list(effs)}
        self.target = target
        self.priority = priority
        self.name = name
        self.z = z
        self.pp = pp
        self.ppc = dc(self.pp)

    def eas(self):
        return ("\n\n" +
                "\n".join([f"{effDescs[g].format(self.effs[g]) if g in effDescs else scs(g)}."
                           f"{f' ({self.effs[g]}% chance)' if g in self.effs and self.effs[g] not in [100, 0] else ''}"
                           for g in self.effs if g in effDescs or isEff(g)])) if len(self.effs) > 0 else ""

    def sd(self):
        return {"s": self.name,
                "d": f"**Type:** {self.type} | **Category:** {self.category} | **PP:** {self.pp}\n"
                f"**Power:** {'—' if self.power == 0 else self.power} | "
                f"**Accuracy:** {'—' if self.acc == 1000 else self.acc}%"
                f"{f' | **Priority:** {signed(self.priority)}' if self.priority != 0 else ''}"
                f"{self.eas()}"}

    def __str__(self):
        return f"-= {self.name.upper()} =-\n{self.sd()['d']}"

    def zPower(self):
        if self.category == status:
            return 0
        if self.name == "Mega Drain":
            return 120
        if self.name == "Core Enforcer":
            return 140
        if self.name in ["Weather Ball", "Hex"]:
            return 160
        if self.name == "Flying Press":
            return 170
        if self.name == "Gear Grind":
            return 180
        if self.name == "V-create":
            return 220
        return 100 if self.power < 60 else 120 if self.power < 70 else 140 if self.power < 80 else\
            160 if self.power < 90 else 175 if self.power < 100 else 180 if self.power < 110 else\
            185 if self.power < 120 else 190 if self.power < 130 else 195 if self.power < 140 else 200


movedict = {
    # NORMAL
    "Acupressure": Move(normal, status, 0, 1000, ["acupressure"], user, 0, "Acupressure", 30, "crtS2"),
    "After You": Move(normal, status, 0, 1000, ["afterYou"], anyAdjMon, 0, "After You", 15, "speS1"),
    "Assist": Move(normal, status, 0, 1000, ["assist"], user, 0, "Assist", 20, "turnsZ"),
    "Attract": Move(normal, status, 0, 100, ["attract"], anyAdjMon, 0, "Attract", 15, "resetStats"),
    "Barrage": Move(normal, physical, 15, 85, ["strike25"], anyAdjMon, 0, "Barrage", 20),
    "Baton Pass": Move(normal, status, 0, 1000, ["batonPass"], user, 0, "Baton Pass", 40, "resetStats"),
    "Belly Drum": Move(normal, status, 0, 1000, ["bellyDrum"], user, 0, "Belly Drum", 10, "fullHeal"),
    "Bestow": Move(normal, status, 0, 1000, ["bestow"], anyAdjMon, 0, "Bestow", 15, "speS2"),
    # "Bide": Move(normal, physical, var, 1000, ["bide"], user, 1, "Bide", 10),
    "Bind": Move(normal, physical, 15, 85, ["bind", "contact"], anyAdjMon, 0, "Bind", 20),
    "Block": Move(normal, status, 0, 1000, ["block"], anyAdjMon, 0, "Block", 5, "defS1"),
    "Body Slam": Move(normal, physical, 85, 100, ["paralyzed|30", "contact"], anyAdjMon, 0, "Body Slam", 15),
    "Boomburst": Move(normal, special, 140, 100, [], allAdjMon, 0, "Boomburst", 10),
    "Camouflage": Move(normal, status, 0, 1000, ["camouflage"], user, 0, "Camouflage", 20, "evaS1"),
    "Captivate": Move(normal, status, 0, 100, ["captivate"], allAdjFoe, 0, "Captivate", 20, "spdS2"),
    "Celebrate": Move(normal, status, 0, 1000, ["celebrate"], user, 0, "Celebrate", 40, "allStats"),
    "Chip Away": Move(normal, physical, 70, 100, ["ignoreStats", "contact"], anyAdjMon, 0, "Chip Away", 20),
    "Comet Punch": Move(normal, physical, 18, 85, ["strike25", "contact"], anyAdjMon, 0, "Comet Punch", 15),
    "Confide": Move(normal, status, 0, 1000, ["spaT-1"], anyAdjMon, 0, "Confide", 20, "spdS1"),
    "Constrict": Move(normal, physical, 10, 100, ["speT-1|10", "contact"], anyAdjMon, 0, "Constrict", 35),
    "Conversion": Move(normal, status, 0, 1000, ["conversion"], user, 0, "Conversion", 30, "allStats"),
    "Conversion 2": Move(normal, status, 0, 1000, ["conversion2"], anyAdjMon, 0, "Conversion", 30, "fullHeal"),
    "Copycat": Move(normal, status, 0, 1000, ["copycat"], user, 0, "Copycat", 20, "accS1:turnsZ"),
    "Covet": Move(normal, physical, 60, 100, ["thief", "contact"], anyAdjMon, 0, "Covet", 25),
    "Crush Claw": Move(normal, physical, 75, 95, ["defT-1|50", "contact"], anyAdjMon, 0, "Crush Claw", 10),
    "Crush Grip": Move(normal, physical, var, 100, ["crushGrip", "contact"], anyAdjMon, 0, "Crush Grip", 5),
    "Cut": Move(normal, physical, 50, 95, ["contact"], anyAdjMon, 0, "Cut", 30),
    "Defense Curl": Move(normal, status, 0, 1000, ["defS1"], user, 0, "Defense Curl", 40, "accS1"),
    "Disable": Move(normal, status, 0, 1000, ["disable"], anyAdjMon, 0, "Disable", 20, "resetStats"),
    "Dizzy Punch": Move(normal, physical, 70, 100, ["confused|20", "contact"], anyAdjMon, 0, "Dizzy Punch", 10),
    "Double Hit": Move(normal, physical, 35, 90, ["strike2", "contact"], anyAdjMon, 0, "Double Hit", 10),
    "Double Slap": Move(normal, physical, 15, 85, ["strike25", "contact"], anyAdjMon, 0, "Double Slap", 10),
    "Double Team": Move(normal, status, 0, 1000, ["evaS1"], user, 0, "Double Team", 15, "resetStats"),
    "Double-Edge": Move(normal, physical, 120, 100, ["recoil3", "contact"], anyAdjMon, 0, "Double-Edge", 15),
    "Echoed Voice": Move(normal, special, 40, 100, ["echoed"], anyAdjMon, 0, "Echoed Voice", 15),
    "Egg Bomb": Move(normal, physical, 100, 75, [], anyAdjMon, 0, "Egg Bomb", 10),
    "Encore": Move(normal, status, 0, 100, ["encore"], anyAdjMon, 0, "Encore", 5, "speS1"),
    "Endeavor": Move(normal, physical, var, 100, ["endeavor"], anyAdjMon, 0, "Endeavor", 5),
    "Endure": Move(normal, status, 0, 1000, ["endure"], user, 4, "Endure", 10, "resetStats"),
    "Entrainment": Move(normal, status, 0, 100, ["entrainment"], anyAdjMon, 0, "Entrainment", 15, "spdS1"),
    "Explosion": Move(normal, physical, 250, 100, ["selfDestruct"], allAdjMon, 0, "Explosion", 5),
    "Extreme Speed": Move(normal, physical, 80, 100, ["contact"], anyAdjMon, 2, "Extreme Speed", 5),
    "Facade": Move(normal, physical, 70, 100, ["facade"], anyAdjMon, 0, "Facade", 20),
    "Fake Out": Move(normal, physical, 40, 100, ["fakeOut", "contact"], anyAdjMon, 3, "Fake Out", 10),
    "False Swipe": Move(normal, physical, 40, 100, ["falseSwipe", "contact"], anyAdjMon, 0, "False Swipe", 40),
    "Feint": Move(normal, physical, 30, 100, ["breakProtect"], anyAdjMon, 2, "Feint", 10),
    "Flail": Move(normal, physical, var, 100, ["reversal", "contact"], anyAdjMon, 0, "Flail", 10),
    "Focus Energy": Move(normal, status, 0, 1000, ["crtS2"], user, 0, "Focus Energy", 30),
    "Foresight": Move(normal, status, 0, 1000, ["foresight"], anyAdjMon, 0, "Foresight", 40, "crtS2"),
    "Fury Swipes": Move(normal, physical, 15, 80, ["strike25", "contact"], anyAdjMon, 0, "Fury Swipes", 15),
    "Giga Impact": Move(normal, physical, 150, 100, ["mustRest", "contact"], anyAdjMon, 0, "Giga Impact", 5),
    "Growl": Move(normal, status, 0, 100, ["atkT-1"], allAdjFoe, 0, "Growl", 40, "defS1"),
    "Helping Hand": Move(normal, status, 0, 1000, ["helpingHand"], anyAdjAlly, 0, "Helping Hand", 20, "resetStats"),
    "Hyper Beam": Move(normal, special, 150, 100, ["mustRest"], anyAdjMon, 0, "Hyper Beam", 5),
    "Judgment": Move(normal, special, 100, 100, ["judgment"], anyAdjMon, 0, "Judgment", 10),
    "Metronome": Move(normal, status, 0, 1000, ["metronome"], user, 0, "Metronome", 10),
    "Minimize": Move(normal, status, 0, 1000, ["evaS2", "minimize"], user, 0, "Minimize", 10, "resetStats"),
    "Pain Split": Move(normal, status, 0, 1000, ["painSplit"], anyAdjMon, 0, "Pain Split", 20, "defS1"),
    "Pound": Move(normal, physical, 40, 100, ["contact"], anyAdjMon, 0, "Pound", 35),
    "Protect": Move(normal, status, 0, 1000, ["protect"], user, 4, "Protect", 10, "resetStats"),
    "Psych Up": Move(normal, status, 0, 1000, ["psychUp"], anyAdjMon, 0, "Psych Up", 10, "fullHeal"),
    "Quick Attack": Move(normal, physical, 40, 100, ["contact"], anyAdjMon, 1, "Quick Attack", 30),
    "Rapid Spin": Move(normal, physical, 20, 100, ["rapidSpin", "contact"], anyAdjMon, 0, "Rapid Spin", 40),
    "Recover": Move(normal, status, 0, 1000, ["halfHealS"], user, 0, "Recover", 10, "resetStats"),
    "Reflect Type": Move(normal, status, 0, 100, ["reflectType"], anyAdjMon, 0, "Reflect Type", 15, "spaS1"),
    "Revelation Dance": Move(normal, special, 90, 100, ["revelation"], anyAdjMon, 0, "Revelation Dance", 15),
    "Roar": Move(normal, status, 0, 1000, ["forceOutT"], anyAdjMon, -6, "Roar", 20, "defS1"),
    "Round": Move(normal, special, 60, 100, ["round"], anyAdjMon, 0, "Round", 15),
    "Safeguard": Move(normal, status, 0, 1000, ["safeguard"], allAlly, 0, "Safeguard", 25, "speS1"),
    "Self-Destruct": Move(normal, physical, 200, 100, ["selfDestruct"], anyAdjMon, 0, "Self-Destruct", 5),
    "Slack Off": Move(normal, status, 0, 1000, ["halfHealS"], user, 0, "Slack Off", 10),
    "Slash": Move(normal, physical, 70, 100, ["extraCrit", "contact"], anyAdjMon, 0, "Slash", 20),
    "Smokescreen": Move(normal, status, 0, 100, ["accT-1"], anyAdjMon, 0, "Smokescreen", 20, "evaS1"),
    "Spit Up": Move(normal, special, var, 100, ["spitUp"], anyAdjMon, 0, "Spit Up", 10),
    "Splash": Move(normal, status, 0, 1000, ["splash"], anyAdjMon, 0, "Splash", 40, "atkS3"),
    "Stockpile": Move(normal, status, 0, 1000, ["stockpile", "defS1", "spdS1"], user, 0, "Stockpile", 20),
    "Strength": Move(normal, physical, 80, 100, ["contact"], anyAdjMon, 0, "Strength", 15),
    "Substitute": Move(normal, status, 0, 1000, ["substitute"], user, 0, "Substitute", 10, "resetStats"),
    "Super Fang": Move(normal, physical, 1, 90, ["contact", "halfHPC"], anyAdjMon, 0, "Super Fang", 10),
    "Swagger": Move(normal, status, 0, 85, ["atkT2", "confused"], anyAdjMon, 0, "Swagger", 15, "resetStats"),
    "Swallow": Move(normal, status, 0, 1000, ["swallow"], user, 0, "Swallow", 10),
    "Swords Dance": Move(normal, status, 0, 1000, ["atkS2"], user, 0, "Swords Dance", 20, "resetStats"),
    "Tackle": Move(normal, physical, 50, 100, ["contact"], anyAdjMon, 0, "Tackle", 35),
    "Tail Whip": Move(normal, status, 0, 100, ["defT-1"], anyAdjMon, 0, "Tail Whip", 30, "atkS1"),
    "Tri Attack": Move(normal, special, 80, 100, ["triAttack|20"], anyAdjMon, 0, "Tri Attack", 10),
    "Transform": Move(normal, status, 0, 1000, ["transform"], anyAdjMon, 0, "Transform", 10, "fullHeal"),
    "Weather Ball": Move(normal, special, 50, 100, ["weatherBall"], anyAdjMon, 0, "Weather Ball", 10),
    "Yawn": Move(normal, status, 0, 1000, ["yawn"], anyAdjMon, 0, "Yawn", 10, "speS1"),

    # FIRE
    "Blast Burn": Move(fire, special, 150, 90, ["mustRest"], anyAdjMon, 0, "Blast Burn", 5),
    "Burn Up": Move(fire, special, 130, 100, ["burnUp"], anyAdjMon, 0, "Burn Up", 5),
    "Ember": Move(fire, special, 40, 100, ["burned|10"], anyAdjMon, 0, "Ember", 25),
    "Fire Blast": Move(fire, special, 110, 85, ["burned|10"], anyAdjMon, 0, "Fire Blast", 5),
    "Fire Fang": Move(fire, physical, 65, 95, ["burned|10", "flinched|10", "contact"], anyAdjMon, 0, "Fire Fang", 15),
    "Fire Punch": Move(fire, physical, 75, 100, ["burned|10", "contact"], anyAdjMon, 0, "Fire Punch", 15),
    "Flame Burst": Move(fire, special, 70, 100, ["flameBurst"], anyAdjMon, 0, "Flame Burst", 15),
    "Flamethrower": Move(fire, special, 90, 100, ["burned|10"], anyAdjMon, 0, "Flamethrower", 15),
    "Flare Blitz": Move(fire, physical, 120, 100, ["burned|10", "recoil3", "contact"], anyAdjMon, 0, "Flare Blitz", 15),
    "Heat Wave": Move(fire, special, 95, 90, ["burned|10"], allAdjFoe, 0, "Heat Wave", 10),
    "Lava Plume": Move(fire, special, 80, 100, ["burned|30"], allAdjMon, 0, "Lava Plume", 15),
    "Overheat": Move(fire, special, 130, 90, ["spaS-2"], anyAdjMon, 0, "Overheat", 5),
    "Sunny Day": Move(fire, status, 0, 1000, ["makeSun"], user, 0, "Sunny Day", 5, "speS1"),
    "Will-O-Wisp": Move(fire, status, 0, 75, ["burned"], anyAdjMon, 0, "Will-O-Wisp", 15, "atkS1"),

    # WATER
    "Aqua Jet": Move(water, physical, 40, 100, ["contact"], anyAdjMon, 1, "Aqua Jet", 20),
    "Aqua Ring": Move(water, status, 0, 1000, ["aquaRing"], user, 0, "Aqua Ring", 20, "defS1"),
    "Aqua Tail": Move(water, physical, 90, 100, ["contact"], anyAdjMon, 0, "Aqua Tail", 10),
    "Brine": Move(water, special, 65, 100, ["brine"], anyAdjMon, 0, "Brine", 10),
    "Dive": Move(water, physical, 80, 100, ["contact", "dive"], anyAdjMon, 0, "Dive", 10),
    "Hydro Cannon": Move(water, special, 150, 90, ["mustRest"], anyAdjMon, 0, "Hydro Cannon", 5),
    "Hydro Pump": Move(water, special, 110, 80, [], anyAdjMon, 0, "Hydro Pump", 5),
    "Muddy Water": Move(water, special, 90, 85, ["accT-1|30"], anyAdjMon, 0, "Muddy Water", 10),
    "Rain Dance": Move(water, status, 0, 1000, ["makeRain"], user, 0, "Rain Dance", 10, "speS1"),
    "Scald": Move(water, special, 80, 100, ["burned|30", "thaw"], anyAdjMon, 0, "Scald", 15),
    "Soak": Move(water, status, 0, 100, ["soak"], anyAdjMon, 0, "Soak", 20, "spaS1"),
    "Surf": Move(water, special, 90, 100, [], allAdjMon, 0, "Surf", 15),
    "Water Gun": Move(water, special, 40, 100, [], anyAdjMon, 0, "Water Gun", 25),
    "Water Pulse": Move(water, special, 60, 100, ["confused|20"], anyAdjMon, 0, "Water Pulse", 20),
    "Waterfall": Move(water, physical, 80, 100, ["flinched|20", "contact"], anyAdjMon, 0, "Waterfall", 15),

    # GRASS
    "Absorb": Move(grass, special, 20, 100, ["absorbent"], anyAdjMon, 0, "Absorb", 25),
    "Bullet Seed": Move(grass, physical, 25, 100, ["strike25"], anyAdjMon, 0, "Bullet Seed", 30),
    "Energy Ball": Move(grass, special, 90, 100, ["spdT-1|10"], anyAdjMon, 0, "Energy Ball", 10),
    "Frenzy Plant": Move(grass, special, 150, 90, ["mustRest"], anyAdjMon, 0, "Frenzy Plant", 5),
    "Giga Drain": Move(grass, special, 75, 100, ["absorbent"], anyAdjMon, 0, "Giga Drain", 10),
    "Grass Knot": Move(grass, physical, var, 100, ["weightDMG", "contact"], anyAdjMon, 0, "Grass Knot", 20),
    "Grassy Terrain": Move(grass, status, 0, 1000, ["terrG"], user, 0, "Grassy Terrain", 10),
    "Ingrain": Move(grass, status, 0, 1000, ["ingrain"], user, 0, "Ingrain", 20, "spdS1"),
    "Leaf Blade": Move(grass, physical, 90, 100, ["contact"], anyAdjMon, 0, "Leaf Blade", 15),
    "Leaf Storm": Move(grass, special, 130, 90, ["spaS-2"], anyAdjMon, 0, "Leaf Storm", 5),
    "Leech Seed": Move(grass, status, 0, 90, ["leechSeed"], anyAdjMon, 0, "Leech Seed", 10, "resetStats"),
    "Mega Drain": Move(grass, special, 40, 100, ["absorbent"], anyAdjMon, 0, "Mega Drain", 15),
    "Power Whip": Move(grass, physical, 120, 85, ["contact"], anyAdjMon, 0, "Power Whip", 10),
    "Sleep Powder": Move(grass, status, 0, 75, ["slept", "powder"], anyAdjMon, 0, "Sleep Powder", 15, "speS1"),
    "Solar Beam": Move(grass, special, 120, 100, ["twoTurn"], anyAdjMon, 0, "Solar Beam", 10),
    "Solar Blade": Move(grass, physical, 125, 100, ["twoTurn", "contact"], anyAdjMon, 0, "Solar Blade", 10),
    "Spore": Move(grass, status, 0, 100, ["slept", "powder"], anyAdjMon, 0, "Spore", 15, "resetStats"),
    "Synthesis": Move(grass, status, 0, 1000, ["synthesis"], user, 0, "Synthesis", 5, "resetStats"),
    "Tera Drain": Move(grass, special, 100, 100, ["absorbent"], anyAdjMon, 0, "Tera Drain", 5),
    "Vine Whip": Move(grass, physical, 45, 100, ["contact"], anyAdjMon, 0, "Vine Whip", 25),
    "Wood Hammer": Move(grass, physical, 120, 100, ["recoil3"], anyAdjMon, 0, "Wood Hammer", 15),

    # ELECTRIC
    "Charge Beam": Move(electric, special, 50, 90, ["spaS1|70"], anyAdjMon, 0, "Charge Beam", 10),
    "Discharge": Move(electric, special, 80, 100, ["paralyzed|30"], anyAdjMon, 0, "Discharge", 15),
    "Electric Terrain": Move(electric, status, 0, 1000, ["terrE"], user, 0, "Electric Terrain", 10, "speS1"),
    "Electro Ball": Move(electric, special, var, 100, ["electroBall"], anyAdjMon, 0, "Electro Ball", 10),
    "Magnet Rise": Move(electric, status, 0, 1000, ["riseUp"], user, 0, "Magnet Rise", 10, "evaS1"),
    "Nuzzle": Move(electric, physical, 20, 100, ["paralyzed", "contact"], anyAdjMon, 0, "Nuzzle", 20),
    "Thunder": Move(electric, special, 110, 70, ["paralyzed|30", "thunder", "canHitFly"], anyAdjMon, 0, "Thunder", 10),
    "Thunder Fang": Move(electric, physical, 65, 95, ["paralyzed|10", "flinched|10", "contact"], anyAdjMon, 0,
                         "Thunder Fang", 15),
    "Thunder Punch": Move(electric, physical, 75, 100, ["paralyzed|10", "contact"], anyAdjMon, 0, "Thunder Punch", 15),
    "Thunder Shock": Move(electric, special, 40, 100, ["paralyzed|10"], anyAdjMon, 0, "Thunder Shock", 30),
    "Thunder Wave": Move(electric, status, 0, 90, ["paralyzed"], anyAdjMon, 0, "Thunder Wave", 20, "spdS1"),
    "Thunderbolt": Move(electric, special, 90, 100, ["paralyzed|10"], anyAdjMon, 0, "Thunderbolt", 15),
    "Volt Switch": Move(electric, special, 70, 100, ["forceOutS", "contact"], anyAdjMon, 0, "Volt Switch", 20),
    "Volt Tackle": Move(electric, physical, 120, 100, ["recoil3", "contact"], anyAdjMon, 0, "Volt Tackle", 15),
    "Wild Charge": Move(electric, physical, 90, 100, ["recoil4", "contact"], anyAdjMon, 0, "Wild Charge", 15),

    # ROCK
    "Accelerock": Move(rock, physical, 40, 100, ["contact"], anyAdjMon, 1, "Accelerock", 20),
    "Ancient Power": Move(rock, special, 60, 100, ["allStats|10"], anyAdjMon, 0, "Ancient Power", 5),
    "Power Gem": Move(rock, special, 80, 100, [], anyAdjMon, 0, "Power Gem", 20),
    "Rock Blast": Move(rock, physical, 25, 90, ["strike25"], anyAdjMon, 0, "Rock Blast", 10),
    "Rock Polish": Move(rock, status, 0, 1000, ["speS2"], user, 0, "Rock Polish", 20),
    "Rock Slide": Move(rock, physical, 75, 90, ["flinched|30"], anyAdjMon, 0, "Rock Slide", 10),
    "Rock Throw": Move(rock, physical, 50, 90, [], anyAdjMon, 0, "Rock Throw", 15),
    "Rollout": Move(rock, physical, 30, 90, ["rollout", "contact"], anyAdjMon, 0, "Rollout", 20),
    "Sandstorm": Move(rock, status, 0, 1000, ["makeSand"], user, 0, "Sandstorm", 10, "speS1"),
    "Smack Down": Move(rock, physical, 50, 100, ["smackDown"], anyAdjMon, 0, "Smack Down", 15),
    "Stone Edge": Move(rock, physical, 100, 80, ["extraCrit"], anyAdjMon, 0, "Stone Edge", 5),
    "Wide Guard": Move(rock, status, 0, 1000, ["wideGuard"], anyAdjMon, 3, "Wide Guard", 10, "defS1"),

    # GROUND
    "Bone Rush": Move(ground, physical, 25, 90, ["strike25"], anyAdjMon, 0, "Bone Rush", 10),
    "Bulldoze": Move(ground, physical, 60, 100, ["speT-1"], allAdjMon, 0, "Bulldoze", 20),
    "Dig": Move(ground, physical, 80, 100, ["dig", "contact"], anyAdjMon, 0, "Dig", 10),
    "Earthquake": Move(ground, physical, 100, 100, ["doubleDig"], allAdjMon, 0, "Earthquake", 10),
    "Earth Power": Move(ground, special, 90, 100, ["spdT-1|10"], anyAdjMon, 0, "Earth Power", 10),
    "Fissure": Move(ground, physical, 0, 30, ["oneHit", "canHitDig"], anyAdjMon, 0, "Fissure", 5),
    "Magnitude": Move(ground, physical, var, 100, ["magnitude", "doubleDig"], allAdjMon, 0, "Magnitude", 30),
    "Mud-Slap": Move(ground, special, 20, 100, ["accT-1"], anyAdjMon, 0, "Mud-Slap", 10),
    "Sand Attack": Move(ground, status, 0, 100, ["accT-1"], anyAdjMon, 0, "Sand Attack", 15, "evaS1"),
    "Sand Tomb": Move(ground, physical, 35, 85, ["sandTomb"], anyAdjMon, 0, "Sand Tomb", 15),
    "Stomping Tantrum": Move(ground, physical, 75, 100, ["stompingTantrum", "contact"], anyAdjMon, 0,
                             "Stomping Tantrum", 10),

    # STEEL
    "Autotomize": Move(steel, status, 0, 1000, ["speS2"], user, 0, "Autotomize", 15, "resetStats"),
    "Bullet Punch": Move(steel, physical, 40, 100, ["contact"], anyAdjMon, 1, "Bullet Punch", 30),
    "Flash Cannon": Move(steel, special, 80, 100, [], anyAdjMon, 0, "Flash Cannon", 10),
    "Gyro Ball": Move(steel, physical, var, 100, ["gyroBall", "contact"], anyAdjMon, 0, "Gyro Ball", 5),
    "Iron Defense": Move(steel, status, 0, 1000, ["defS2"], user, 0, "Iron Defense", 15, "resetStats"),
    "Iron Head": Move(steel, physical, 80, 100, ["flinched|30", "contact"], anyAdjMon, 0, "Iron Head", 15),
    "Iron Tail": Move(steel, physical, 100, 75, ["defT-1|30", "contact"], anyAdjMon, 0, "Iron Tail", 15),
    "King's Shield": Move(steel, status, 0, 1000, ["protect", "aegishield"], user, 4,
                          "King's Shield", 10, "resetStats"),
    "Magnet Bomb": Move(steel, physical, 60, 1000, [], anyAdjMon, 0, "Magnet Bomb", 20),
    "Metal Claw": Move(steel, physical, 50, 95, ["contact", "atkS1|10"], anyAdjMon, 0, "Metal Claw", 35),
    "Steel Wing": Move(steel, physical, 70, 90, ["defS1|10", "contact"], anyAdjMon, 0, "Steel Wing", 25),

    # PSYCHIC
    "Agility": Move(psychic, status, 0, 1000, ["speS2"], user, 0, "Agility", 30, "resetStats"),
    "Amnesia": Move(psychic, status, 0, 1000, ["spdS2"], user, 0, "Amnesia", 20, "resetStats"),
    "Calm Mind": Move(psychic, status, 0, 1000, ["spaS1", "spdS1"], user, 0, "Calm Mind", 20, "resetStats"),
    "Confusion": Move(psychic, special, 50, 100, ["confused|10"], anyAdjMon, 0, "Confusion", 25),
    "Dream Eater": Move(psychic, special, 100, 100, ["absorbent", "dreams"], anyAdjMon, 0, "Dream Eater", 15),
    "Extrasensory": Move(psychic, special, 80, 100, ["flinched|10"], anyAdjMon, 0, "Extrasensory", 20),
    "Guard Split": Move(psychic, status, 0, 1000, ["guardSplit"], anyAdjMon, 0, "Guard Split", 10, "speS1"),
    "Heart Stamp": Move(psychic, physical, 60, 100, ["flinched|30", "contact"], anyAdjMon, 0, "Heart Stamp", 25),
    "Hypnosis": Move(psychic, status, 0, 60, ["slept"], anyAdjMon, 0, "Hypnosis", 20, "speS1"),
    "Light Screen": Move(psychic, status, 0, 1000, ["lightScreen"], user, 0, "Light Screen", 30, "spdS1"),
    "Mirror Coat": Move(psychic, status, 0, 1000, ["mirrorCoat"], user, -5, "Mirror Coat", 20),
    "Psychic": Move(psychic, special, 90, 100, ["spdT-1|10"], anyAdjMon, 0, "Psychic", 10),
    "Psycho Shift": Move(psychic, status, 0, 100, ["psychoShift"], anyAdjMon, 0, "Psycho Shift", 10, "spaS2"),
    "Psyshock": Move(psychic, special, 80, 100, ["psyshock"], anyAdjMon, 0, "Psyshock", 10),
    "Reflect": Move(psychic, status, 0, 1000, ["reflect"], user, 0, "Reflect", 20, "defS1"),
    "Rest": Move(psychic, status, 0, 1000, ["rest", "fullHeal"], user, 0, "Rest", 10, "resetStats"),
    "Telekinesis": Move(psychic, status, 0, 1000, ["telekinesis"], anyAdjMon, 0, "Telekinesis", 15, "spaS1"),
    "Trick": Move(psychic, status, 0, 1000, ["trick"], anyAdjMon, 0, "Trick", 10, "speS2"),
    "Trick Room": Move(psychic, status, 0, 1000, ["trickRoom"], user, -7, "Trick Room", 5, "accS1"),

    # FIGHTING
    "Aura Sphere": Move(fighting, special, 80, 1000, [], anyAdjMon, 0, "Aura Sphere", 20),
    "Brick Break": Move(fighting, physical, 75, 100, ["breakBarrier", "contact"], anyAdjMon, 0, "Brick Break", 15),
    "Close Combat": Move(fighting, physical, 120, 100, ["defS-1", "spdS-1", "contact"], anyAdjMon, 0,
                         "Close Combat", 5),
    "Counter": Move(fighting, status, 0, 100, ["counter", "contact"], user, -5, "Counter", 20),
    "Cross Chop": Move(fighting, physical, 100, 80, ["extraCrit", "contact"], anyAdjMon, 0, "Cross Chop", 5),
    "Detect": Move(fighting, status, 0, 1000, ["protect"], user, 4, "Detect", 10, "resetStats"),
    "Dynamic Punch": Move(fighting, physical, 100, 50, ["confused", "contact"], anyAdjMon, 0, "Dynamic Punch", 5),
    "Focus Blast": Move(fighting, special, 120, 70, ["spdT-1|10"], anyAdjMon, 0, "Focus Blast", 5),
    "Karate Chop": Move(fighting, physical, 50, 100, ["extraCrit", "contact"], anyAdjMon, 0, "Karate Chop", 25),
    "Mach Punch": Move(fighting, physical, 40, 100, ["contact"], anyAdjMon, 1, "Mach Punch", 30),
    "Reversal": Move(fighting, physical, var, 100, ["reversal", "contact"], anyAdjMon, 0, "Reversal", 15),
    "Sacred Sword": Move(fighting, physical, 90, 100, ["ignoreStats", "contact"], anyAdjMon, 0, "Sacred Sword", 15),
    "Vacuum Wave": Move(fighting, special, 40, 100, [], anyAdjMon, 1, "Vacuum Wave", 30),
    "Wake-Up Slap": Move(fighting, physical, 65, 100, ["wakeUp", "contact"], anyAdjMon, 100, "Wake-Up Slap", 10),

    # FLYING
    "Aerial Ace": Move(flying, physical, 60, 1000, ["contact"], anyAdjMon, 0, "Aerial Ace", 20),
    "Aeroblast": Move(flying, special, 100, 95, ["extraCrit"], anyAdjMon, 0, "Aeroblast", 5),
    "Air Slash": Move(flying, special, 75, 95, ["flinched|10"], anyAdjMon, 0, "Air Slash", 15),
    "Bounce": Move(flying, physical, 85, 85, ["bounce", "contact", "paralyzed|30"], anyAdjMon, 0, "Bounce", 5),
    "Brave Bird": Move(flying, physical, 120, 100, ["recoil3", "contact"], anyAdjMon, 0, "Brave Bird", 15),
    "Feather Dance": Move(flying, status, 0, 1000, ["atkT-2"], anyAdjMon, 0, "Feather Dance", 15, "defS1"),
    "Fly": Move(flying, physical, 90, 100, ["fly", "contact"], anyAdjMon, 0, "Fly", 15),
    "Gust": Move(flying, special, 40, 100, ["doubleFly"], anyAdjMon, 0, "Gust", 35),
    "Hurricane": Move(flying, special, 110, 70, ["confused|30", "canHitFly", "hurricane"], anyAdjMon, 0,
                      "Hurricane", 10),
    "Mirror Move": Move(flying, status, 0, 1000, ["mirrorMove"], anyAdjMon, 0, "Mirror Move", 20, "atkS2:turnsZ"),
    "Roost": Move(flying, status, 0, 1000, ["roost"], user, 0, "Roost", 10, "resetStats"),
    "Sky Drop": Move(flying, physical, 60, 100, ["skyDrop", "contact"], anyAdjMon, 0, "Sky Drop", 10),
    "Tailwind": Move(flying, status, 0, 1000, ["tailwind"], user, 0, "Tailwind", 15, "crtS2"),

    # GHOST
    "Confuse Ray": Move(ghost, status, 0, 100, ["confused"], anyAdjMon, 0, "Confuse Ray", 10, "spaS1"),
    "Destiny Bond": Move(ghost, status, 0, 1000, ["destinyBond"], user, 0, "Destiny Bond", 5),
    "Hex": Move(ghost, special, 65, 100, ["hex"], anyAdjMon, 0, "Hex", 10),
    "Nightmare": Move(ghost, status, 0, 100, ["nightmare", "dreams"], anyAdjMon, 0, "Nightmare", 15),
    "Ominous Wind": Move(ghost, special, 60, 100, ["allStats|10"], anyAdjMon, 0, "Ominous Wind", 5),
    "Phantom Force": Move(ghost, physical, 90, 100, ["phantomForce", "contact", "breakProtect"], anyAdjMon, 0,
                          "Phantom Force", 10),
    "Shadow Ball": Move(ghost, special, 80, 100, ["spdT-1|20"], anyAdjMon, 0, "Shadow Ball", 15),
    "Shadow Bone": Move(ghost, physical, 85, 100, ["defT-1|20"], anyAdjMon, 0, "Shadow Bone", 10),
    "Shadow Claw": Move(ghost, physical, 70, 100, ["extraCrit", "contact"], anyAdjMon, 0, "Shadow Claw", 15),
    "Shadow Force": Move(ghost, physical, 120, 100, ["shadowForce", "contact"], anyAdjMon, 0, "Shadow Force", 5),
    "Shadow Sneak": Move(ghost, physical, 40, 100, ["contact"], anyAdjMon, 1, "Shadow Sneak", 30),
    "Spirit Shackle": Move(ghost, physical, 80, 100, ["noEscape"], anyAdjMon, 0, "Spirit Shackle", 10),

    # DARK
    "Bite": Move(dark, physical, 60, 100, ["flinched|30", "contact"], anyAdjMon, 0, "Bite", 25),
    "Brutal Swing": Move(dark, physical, 60, 100, ["contact"], allAdjMon, 0, "Brutal Swing", 20),
    "Crunch": Move(dark, physical, 80, 100, ["defT-1|20", "contact"], anyAdjMon, 0, "Crunch", 15),
    "Dark Pulse": Move(dark, special, 80, 100, ["flinched|20"], anyMon, 0, "Dark Pulse", 15),
    "Embargo": Move(dark, status, 0, 1000, ["embargo"], anyAdjMon, 0, "Embargo", 15),
    "Feint Attack": Move(dark, physical, 60, 1000, ["contact"], anyAdjMon, 0, "Feint Attack", 20),
    "Flatter": Move(dark, status, 0, 1000, ["spaT1", "confused"], anyAdjMon, 0, "Flatter", 15, "spdS1"),
    "Knock Off": Move(dark, physical, 65, 100, ["knockOff", "contact"], anyAdjMon, 0, "Knock Off", 20),
    "Nasty Plot": Move(dark, status, 0, 1000, ["spaS2"], user, 0, "Nasty Plot", 20, "resetStats"),
    "Night Slash": Move(dark, physical, 70, 100, ["extraCrit", "contact"], anyAdjMon, 0, "Night Slash", 15),
    "Payback": Move(dark, physical, 50, 100, ["payback", "contact"], anyAdjMon, 0, "Payback", 10),
    "Pursuit": Move(dark, physical, 40, 100, ["pursuit", "contact"], anyAdjMon, 0, "Pursuit", 20),
    "Snarl": Move(dark, special, 55, 95, ["spaT-1"], allAdjFoe, 0, "Snarl", 15),
    "Sucker Punch": Move(dark, physical, 70, 100, ["suckerPunch", "contact"], anyAdjMon, 1, "Sucker Punch", 5),
    "Taunt": Move(dark, status, 0, 100, ["taunt"], anyAdjMon, 0, "Taunt", 20),
    "Thief": Move(dark, physical, 60, 100, ["thief", "contact"], anyAdjMon, 0, "Thief", 25),

    # BUG
    "Bug Buzz": Move(bug, special, 90, 100, ["spdT-1|10"], anyAdjMon, 0, "Bug Buzz", 10),
    "Fell Stinger": Move(bug, physical, 50, 100, ["fellStinger", "contact"], anyAdjMon, 0, "Fell Stinger", 25),
    "Infestation": Move(bug, special, 20, 100, ["infestation"], anyAdjMon, 0, "Infestation", 20),
    "Leech Life": Move(bug, special, 80, 100, ["absorbent", "contact"], anyAdjMon, 0, "Leech Life", 10),
    "Megahorn": Move(bug, physical, 120, 85, ["contact"], anyAdjMon, 0, "Megahorn", 10),
    "Pin Missile": Move(bug, physical, 25, 95, ["strike25"], anyAdjMon, 0, "Pin Missile", 20),
    "Silver Wind": Move(bug, special, 60, 100, ["allStats|10"], anyAdjMon, 0, "Silver Wind", 5),
    "Twineedle": Move(bug, physical, 25, 100, ["strike2", "poisoned|20"], anyAdjMon, 0, "Twineedle", 20),
    "U-turn": Move(bug, physical, 70, 100, ["forceOutS", "contact"], anyAdjMon, 0, "U-turn", 20),
    "X-Scissor": Move(bug, physical, 80, 100, ["contact"], anyAdjMon, 0, "X-Scissor", 15),

    # POISON
    "Acid Armor": Move(poison, status, 0, 100, ["defS2"], user, 0, "Acid Armor", 20, "resetStats"),
    "Acid Spray": Move(poison, special, 40, 100, ["spdT-2"], anyAdjMon, 0, "Acid Spray", 20),
    "Belch": Move(poison, special, 120, 90, ["belch"], anyAdjMon, 0, "Belch", 10),
    "Gunk Shot": Move(poison, special, 120, 80, ["poisoned|30"], anyAdjMon, 0, "Gunk Shot", 5),
    "Poison Gas": Move(poison, status, 0, 90, ["poisoned"], anyAdjMon, 0, "Poison Gas", 40, "defS1"),
    "Poison Jab": Move(poison, physical, 80, 100, ["poisoned|30", "contact"], anyAdjMon, 0, "Poison Jab", 20),
    "Sludge": Move(poison, special, 65, 100, ["poisoned|30"], anyAdjMon, 0, "Sludge", 20),
    "Sludge Bomb": Move(poison, special, 90, 100, ["poisoned|30"], anyAdjMon, 0, "Sludge Bomb", 10),
    "Sludge Wave": Move(poison, special, 95, 100, ["poisoned|10"], allAdjMon, 0, "Sludge Wave", 10),
    "Toxic": Move(poison, status, 0, 90, ["badPoisoned"], anyAdjMon, 0, "Toxic", 10, "defS1"),
    "Toxic Spikes": Move(poison, status, 0, 1000, ["toxicSpikes"], allFoe, 0, "Toxic Spikes", 20, "defS1"),
    "Venoshock": Move(poison, special, 65, 100, ["venoshock"], anyAdjMon, 0, "Venoshock", 10),

    # FAIRY
    "Baby-Doll Eyes": Move(fairy, status, 0, 100, ["atkT-1"], anyAdjMon, 1, "Baby-Doll Eyes", 30, "defS1"),
    "Dazzling Gleam": Move(fairy, special, 80, 100, [], allAdjFoe, 0, "Dazzling Gleam", 10),
    "Disarming Voice": Move(fairy, special, 40, 1000, [], anyAdjMon, 0, "Disarming Voice", 15),
    "Misty Terrain": Move(fairy, status, 0, 1000, ["terrM"], user, 0, "Misty Terrain", 10, "spdS1"),
    "Moonblast": Move(fairy, special, 95, 100, ["spaT-1|30"], anyAdjMon, 0, "Moonblast", 15),
    "Nature's Madness": Move(fairy, special, 1, 90, ["halfHPC"], anyAdjMon, 0, "Nature's Madness", 10),
    "Sweet Kiss": Move(fairy, status, 0, 75, ["confused"], anyAdjMon, 0, "Sweet Kiss", 10, "spaS1"),

    # DRAGON
    "Dragon Claw": Move(dragon, physical, 80, 100, ["contact"], anyAdjMon, 0, "Dragon Claw", 15),
    "Dragon Dance": Move(dragon, status, 0, 1000, ["atkS1", "speS1"], user, 0, "Dragon Dance", 20, "resetStats"),
    "Dragon Hammer": Move(dragon, physical, 90, 100, ["contact"], anyAdjMon, 0, "Dragon Hammer", 15),
    "Dragon Pulse": Move(dragon, special, 85, 100, [], anyMon, 0, "Dragon Pulse", 10),
    "Dragon Rage": Move(dragon, special, 0, 100, ["setDamage40"], anyAdjMon, 0, "Dragon Rage", 10),
    "Dragon Rush": Move(dragon, physical, 100, 75, ["flinched|20", "contact", "stomp"], anyAdjMon, 0,
                        "Dragon Rush", 10),
    "Dragon Tail": Move(dragon, physical, 60, 90, ["forceOutT", "contact"], anyAdjMon, -6, "Dragon Tail", 10),
    "Twister": Move(dragon, special, 40, 100, ["flinched|20", "doubleFly"], anyAdjMon, 0, "Twister", 20),

    # ICE
    "Aurora Veil": Move(ice, status, 0, 1000, ["auroraVeil"], user, 0, "Aurora Veil", 20, "speS1"),
    "Blizzard": Move(ice, special, 110, 70, ["frozen|10", "blizzard"], allAdjFoe, 0, "Blizzard", 5),
    "Deep Freeze": Move(ice, status, 0, 100, ["frozen"], anyAdjMon, 0, "Deep Freeze", 10, "spaS1"),
    "Freeze-Dry": Move(ice, special, 70, 100, ["freezeDry", "frozen|10"], anyAdjMon, 0, "Freeze-Dry", 20),
    "Frost Breath": Move(ice, special, 60, 90, ["allCrit"], anyAdjMon, 0, "Frost Breath", 10),
    "Hail": Move(ice, status, 0, 1000, ["makeHail"], user, 0, "Hail", 10, "speS1"),
    "Ice Ball": Move(ice, physical, 30, 90, ["rollout", "contact"], anyAdjMon, 0, "Ice Ball", 20),
    "Ice Beam": Move(ice, special, 90, 100, ["frozen|10"], anyAdjMon, 0, "Ice Beam", 10),
    "Ice Fang": Move(ice, physical, 65, 95, ["frozen|10", "flinched|10", "contact"], anyAdjMon, 0, "Ice Fang", 15),
    "Ice Punch": Move(ice, physical, 75, 100, ["frozen|10", "contact"], anyAdjMon, 0, "Ice Punch", 15),
    "Ice Shard": Move(ice, physical, 40, 100, [], anyAdjMon, 1, "Ice Shard", 30),
    "Icicle Spear": Move(ice, physical, 25, 100, ["strike25"], anyAdjMon, 0, "Icicle Spear", 30),

    # CUSTOM
    "Infinifuck": Move(typeless, physical, 10**30, 1000, [], anyMon, 0, "Infinifuck", 60),
    "Nearfuck": Move(typeless, physical, 10**30, 1000, ["falseSwipe"], anyMon, 0, "Nearfuck", 60),
    "Quick Gift": Move(typeless, status, 0, 1000, ["halfHealT"], anyMon, 6, "Quick Gift", 60, "halfHealS"),
    "Quick Heal": Move(typeless, status, 0, 1000, ["halfHealS"], user, 6, "Quick Heal", 60, "resetStats"),
    "Vibropunch": Move(typeless, special, 20, 1000, ["vibropunch", "psyshock"], anyAdjMon, 1, "Vibropunch", 60),
}
confusedMove = Move(typeless, physical, 40, 1000, ["func"], anyAdjMon, 0, "don't print", 1)
lowerMoves = {g.lower(): g for g in movedict}
nameLength = max([len(m.name) for m in movedict.values()])
if nameLength != 16:
    print([g for g in movedict if len(g) > 16], nameLength, sep="\n")


def lengthen(s):
    return s + " " * (nameLength - len(s))


def getMove(s: str, ppd: int=0):
    ret = dc(movedict[lowerMoves[s.lower()]])
    ret.ppc -= ppd
    return ret


if __name__ == "__main__":
    for mod in movedict:
        if type(movedict[mod]) == Move:
            print(movedict[mod].sd())
            print()
