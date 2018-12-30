from pokemon.treemons import *
from random import randrange, choices
sun, rain, snow, sandstorm = "Harsh sunlight", "Heavy rain", "Snow", "Sandstorm"
castForms = {sun: fire, rain: water, snow: ice}
failed = "But it failed!"


def move_effectiveness(m: Move, d: Mon):
    def single_effect(move, mon, which):
        typ = mon.types()[which]
        if typ == ghost and mon.foreseen and move.type in [normal, fighting]:
            return 1
        if "freezeDry" in m.effs and typ == water:
            return 2
        return eff(m.type, typ)
    return single_effect(m, d, 0) * single_effect(m, d, 1)


def crit_chance(n):
    return 0.0416667 if n == 0 else 0.125 if n == 1 else 0.5 if n == 2 else 1


class Team:
    def __init__(self, name: str, *mons: Mon, author=None):
        self.name = name
        names = [g.name for g in mons]
        for i in range(len(mons)):
            if mons[i].name in names[:i]:
                mons[i].name += " " + str(names[:i].count(mons[i].name) + 1)
        self.mons = {g.name: g.pack() for g in mons}
        self.active = list(self.mons)[0]
        self.author = author

    def __str__(self):
        return self.name + "\n" + "\n".join([str(m) for m in self.mons])

    def __getitem__(self, item):
        return self.mons[item]


class Battle:
    def __init__(self, team1: Team, team2: Team):
        self.teams = {team1.name: team1, team2.name: team2}
        self.teamNames = list(self.teams)
        for j in self.teams:
            for i in self.teams[j].mons:
                try:
                    self.teams[j].mons[i]["team"] = j
                except IndexError:
                    pass
        self.weather = None
        self.weatherTime = 0
        self.trickRoom = 0
        self.desc = []
        self.turnNo = 1
        self.p = Mon(**self.get_active(0))
        self.o = Mon(**self.get_active(1))

    def get_active(self, n: int):
        return self.teams[self.teamNames[n]][self.teams[self.teamNames[n]].active]

    def pressure(self):
        return self.p.ability == "Pressure" or self.o.ability == "Pressure"

    @staticmethod
    def damcalc(a: int, d: int, m: Move, l: int):
        return floor(floor(floor(2 * l / 5 + 2) * m.power * a / d / 50) + 2)

    def atkc(self, mon: Mon):
        ret = mon.stat_level("atk")
        if self.weather == sun and mon.ability == "Flower Gift":
            ret *= 1.5
        return ret

    def defc(self, mon: Mon):
        ret = mon.stat_level("def")
        return ret

    def spac(self, mon: Mon):
        ret = mon.stat_level("spa")
        if self.weather == sun and mon.ability == "Solar Power":
            ret *= 1.5
        return ret

    def spdc(self, mon: Mon):
        ret = mon.stat_level("spd")
        if self.weather == sun and mon.ability == "Flower Gift":
            ret *= 1.5
        return ret

    def spec(self, mon: Mon):
        ret = mon.stat_level("spe")
        if self.weather == sun and mon.ability == "Chlorophyll":
            ret *= 2
        if self.weather == rain and mon.ability == "Swift Swim":
            ret *= 2
        if self.weather == snow and mon.ability == "Slush Rush":
            ret *= 2
        if self.weather == sandstorm and mon.ability == "Sand Rush":
            ret *= 2
        if mon.condit == paralyzed:
            ret /= 2
        return ret

    def damage_amt(self, a: Mon, d: Mon, m: Move, r: int, c: bool = False):  # this is basically ripped from Showdown
        effectiveness = move_effectiveness(m, d)
        if "setDamage40" in m.effs:
            return 0 if effectiveness == 0 else 40
        if "setDamage20" in m.effs:
            return 0 if effectiveness == 0 else 20
        if "endeavor" in m.effs:
            return d.hpc - a.hpc
        if "halfHPC" in m.effs:
            return floor(d.hpc / 2)
        if "psyshock" in m.effs:
            attack, defense = self.spac(a), self.defc(d)
        elif m.category == physical:
            attack, defense = self.atkc(a), self.defc(d)
        elif m.category == special:
            attack, defense = self.spac(a), self.spdc(d)
        else:
            attack, defense = 0, 1
        dam = self.damcalc(attack, defense, m, a.level)
        if c:
            self.desc.append("A critical hit!")
            dam = floor(dam * (2 if a.ability == "Sniper" else 1.5))
        if m.type in a.types():
            adap = 2 if a.ability == "Adaptability" else 1.5
        else:
            adap = 1
        dam = floor(pokeround(floor(dam * r / 100) * adap) * effectiveness)
        if self.weather == rain:
            dam = floor(dam * (1.5 if m.type == water else 0.5 if m.type == fire else 1))
        elif self.weather == sun:
            dam = floor(dam * (1.5 if m.type == fire else 0.5 if m.type == water else 1))
        if a.condit == burned and a.ability != "Guts" and m.category == physical and "facade" not in m.effs:
            dam = floor(dam / 2)
        return pokeround(max([1, dam]))

    def inhibitors(self, a: Mon):
        if a.resting:
            self.desc.append(f"{a.name} is recharging!")
            a.resting = False
            return False
        if a.condit == frozen:
            self.desc.append(f"{a.name} is frozen solid!")
            return False
        return True

    def but_it_failed(self, a: Mon, d: Mon, m: Move):
        if "protect" in m.effs and random() >= 1 / min([729, 3 ** a.protectCount]):
            self.desc.append(failed)
            return False
        if "aquaRing" in m.effs and a.aquaRing:
            self.desc.append(f"{a.name} is already affected by Aqua Ring!")
            return False
        if "endeavor" in m.effs and a.hpc >= d.hpc:
            self.desc.append(failed)
            return False
        if "stockpile" in m.effs and a.stockpile == 3:
            self.desc.append(failed)
            return False
        if "swallow" in m.effs or "spitUp" in m.effs:
            if a.stockpile == 0:
                self.desc.append(failed)
                return False
        if "makeSun" in m.effs and self.weather == sun:
            self.desc.append(failed)
            return False
        if "makeRain" in m.effs and self.weather == rain:
            self.desc.append(failed)
            return False
        if "makeHail" in m.effs and self.weather == snow:
            self.desc.append(failed)
            return False
        if "makeSand" in m.effs and self.weather == sandstorm:
            self.desc.append(failed)
            return False
        return True

    def power_mods(self, a: Mon, d: Mon, m: Move):
        ret = []
        if a.ability == "Technician" and m.power <= 60:
            ret.append(1.5)
            self.desc.append(a.print_abil())
        if a.ability == "Flare Boost" and a.condit == burned and m.category == special:
            ret.append(1.5)
            self.desc.append(a.print_abil())
        if a.ability == "Toxic Boost" and a.condit in [poisoned, badPoisoned] and m.category == physical:
            ret.append(1.5)
            self.desc.append(a.print_abil())
        if d.ability == "Heatproof" and m.type == fire:
            ret.append(0.5)
            self.desc.append(d.print_abil())
        if d.switching and "pursuit" in m.effs:
            ret.append(2)
        if a.failed and "stompingTantrum" in m.effs:
            ret.append(2)
        return product(ret)

    def attack(self, a: Mon, d: Mon, m: Move):
        if not self.inhibitors(a):
            a.failed = False
            return
        self.desc.append(f"{a.name} used {m.name}!")
        m.ppc -= 1 + self.pressure()
        if "weatherBall" in m.effs:
            m.type = fire if self.weather == sun else ice if self.weather == snow else water if self.weather == rain\
                else rock if self.weather == sandstorm else normal
        if not self.but_it_failed(a, d, m):
            a.failed = True
            return
        if random() > m.acc / 100 * a.stat_level("acc") / d.stat_level("eva"):
            self.desc.append(f"{a.name}'s attack missed!")
            a.failed = False
            return
        if "mustRest" in m.effs:
            a.resting = True
        if d.protecting and "breakProtect" not in m.effs:
            self.desc.append(f"{d.name} protected itself!")
            a.failed = False
            return
        if move_effectiveness(m, d) == 0:
            self.desc.append(f"It doesn't affect {d.name}...")
            a.failed = True
            return
        if m.power == var:
            if "crushGrip" in m.effs:
                m.power = 120 * d.hpc / d.hp
            elif "electroBall" in m.effs:
                rat = self.spec(d) / self.spec(a)
                m.power = 40 if rat > 1 else 60 if rat > 0.5 else 80 if rat > 0.3333 else 120 if rat > 0.25 else 150
            elif "gyroBall" in m.effs:
                m.power = 25 * self.spec(d) / self.spec(a)
            elif "magnitude" in m.effs:
                m.power = choices([10, 30, 50, 70, 90, 110, 150], weights=[5, 10, 20, 30, 20, 10, 5])[0]
                self.desc.append(f"Magnitude {[10, 30, 50, 70, 90, 110, 150].index(m.power) + 4}!")
            elif "reversal" in m.effs:
                rat = a.hpc / a.hp
                m.power = 100 if rat < 0.0417 else 150 if rat < 0.1042 else 100 if rat < 0.2083 else\
                    80 if rat < 0.3542 else 40 if rat < 0.6875 else 20
            elif "spitUp" in m.effs:
                m.power = 100 * a.stockpile
            elif "weightDMG" in m.effs:
                m.power = 20 if d.weight < 10 else 40 if d.weight < 25 else 60 if d.weight < 50 else\
                    80 if d.weight < 100 else 100 if d.weight < 200 else 120
        m.power = max([1, pokeround(m.power * self.power_mods(a, d, m))])
        a.failed = False
        if move_effectiveness(m, d) > 1 and m.category != status:
            self.desc.append("It's super effective!")
        if move_effectiveness(m, d) < 1 and m.category != status:
            self.desc.append("It's not very effective...")
        if "strike2" in m.effs:
            strikes = 2
        elif "strike25" in m.effs:
            strikes = choices([2, 3, 4, 5], weights=[2, 2, 1, 1])[0]
        else:
            strikes = 1
        for strike in range(strikes):
            if m.category != status:
                r = randrange(85, 101)
                c = random() < crit_chance(a.statStages["crt"] + (1 if "extraCrit" in m.effs else 0))
                dam = self.damage_amt(a, d, m, r, c)
                self.dmg(d, dam, swipe="falseSwipe" in m.effs)
                if "recoil3" in m.effs:
                    self.dmg(a, int(floor(dam / 3)), "recoil damage")
                if d.hpc <= 0:
                    return
                if "contact" in m.effs:
                    self.contact(a, d)
                if d.hpc <= 0 or a.hpc <= 0:
                    return
                if "absorbent" in m.effs:
                    a.hpc += floor(dam / 2)
            for effect in m.effs:
                if random() < m.effs[effect] / 100:
                    self.move_effects(a, d, effect)
                elif m.category == status:
                    self.desc.append(failed)
        return

    def contact(self, a: Mon, d: Mon):
        if d.ability == "Static":
            if random() < 0.3 and a.condit is None:
                self.desc.append(f"{d.print_abil()}\n{a.name} was paralyzed!")
                a.condit = paralyzed

    def move_effects(self, a: Mon, d: Mon, e: str):
        if isEff(e):
            if e[3] == "S":
                self.stat_change(a, e)
            else:
                self.stat_change(d, e)
        if e == "stockpile":
            a.stockpile += 1
            self.desc.append(f"{a.name} stockpiled {a.stockpile}!")
        if e == "swallow":
            self.heal(a, int(floor({1: 0.25, 2: 0.5, 3: 1}[a.stockpile] * a.hp)))
            self.stat_change(a, f"defS{-a.stockpile}")
            self.stat_change(a, f"spdS{-a.stockpile}")
            a.stockpile = 0
        if e == "spitUp":
            self.stat_change(a, f"defS{-a.stockpile}")
            self.stat_change(a, f"spdS{-a.stockpile}")
            a.stockpile = 0
        if e == "halfHealS":
            self.heal(a, round(a.hp / 2))
        if e == "halfHealT":
            self.heal(d, round(d.hp / 2))
        if e == "selfDestruct":
            a.hpc = 0
        if e == "makeSun" and self.weather != sun:
            self.desc.append("The sunlight turned harsh!")
            self.weather = sun
            self.weatherTime = 8 if a.heldItem == "Heat Rock" else 5
        if e == "makeRain" and self.weather != rain:
            self.desc.append("It started to rain!")
            self.weather = rain
            self.weatherTime = 8 if a.heldItem == "Damp Rock" else 5
        if e == "makeSand" and self.weather != sandstorm:
            self.desc.append("A sandstorm kicked up!")
            self.weather = sandstorm
            self.weatherTime = 8 if a.heldItem == "Smooth Rock" else 5
        if e == "makeHail" and self.weather != snow:
            self.desc.append("It started to hail!")
            self.weather = snow
            self.weatherTime = 8 if a.heldItem == "Icy Rock" else 5
        if e == "protect":
            self.desc.append(f"{a.name} protected itself!")
            a.protecting = True
            a.protectCount += 1
        if e == "aquaRing":
            self.desc.append(f"{a.name} surrounded itself in a veil of water!")
            a.aquaRing = True
        if e == "painSplit":
            if a.hpc == d.hpc or a.hpc == d.hpc + 1:
                return self.desc.append("But nothing happened!")
            self.desc.append("The battlers shared their pain!")
            n = (a.hpc + d.hpc) / 2
            if a.hpc > d.hpc:
                self.heal(d, int(floor(n) - d.hpc))
                self.dmg(a, int(a.hpc - ceil(n)))
            else:
                self.heal(a, int(ceil(n) - a.hpc))
                self.dmg(d, int(d.hpc - floor(n)))

    def stat_change(self, mon: Mon, change: str):
        which, how = change[:3], int(change[4:])
        signs = {-1: ("fell", "lower"), 1: ("rose", "higher")}
        severity = {-3: "severely fell", -2: "harshly fell", -1: "fell",
                    1: "rose", 2: "rose sharply", 3: "rose drastically"}
        if mon.ability == "Contrary":
            how = -how
        if abs(mon.statStages[which] + how) > 6:
            how = sign(how) * (abs(mon.statStages[which]) - 6)
        if mon.statStages[which] == 6 * sign(how):
            return self.desc.append(f"{mon.name}'s {stats[which]} won't go any {signs[sign(how)][1]}!")
        mon.statStages[which] += how
        return self.desc.append(f"{mon.name}'s {stats[which]} {severity[how]}!")

    def heal(self, mon: Mon, n: int, s: str="HP"):
        if mon.hpc == 0:
            return
        start = mon.hpc
        mon.hpc += n
        if mon.hpc > mon.hp:
            mon.hpc = mon.hp
        self.desc.append(f"{mon.name} regained {mon.hpc - start} {s}!")

    def dmg(self, mon: Mon, n: int, s: str="damage", swipe=False):
        if mon.hpc == 0:
            return
        start = mon.hpc
        mon.hpc -= n
        if swipe:
            if mon.hpc < 1:
                mon.hpc = 1
        else:
            if mon.hpc < 0:
                mon.hpc = 0
                mon.condit = fainted
        self.desc.append(f"{mon.name} took {start - mon.hpc} {s}!")

    def priority(self, p: Mon, o: Mon, mp: Move, mo: Move):
        if p.switching is not None:
            return "o" if "pursuit" in mo.effs else "p"
        if o.switching is not None:
            return "p" if "pursuit" in mp.effs else "o"
        if mo.priority > mp.priority:
            return "o"
        if mp.priority > mo.priority:
            return "p"
        if mp.priority == mo.priority:
            if self.spec(p) > self.spec(o):
                return "p" if self.trickRoom == 0 else "o"
            if self.spec(o) > self.spec(p):
                return "o" if self.trickRoom == 0 else "p"
            if self.spec(o) == self.spec(p):
                return choice(("o", "p"))
