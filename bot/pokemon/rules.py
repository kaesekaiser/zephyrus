from math import floor, ceil
from random import choices, sample

status, physical, special = "Status", "Physical", "Special"
anyAdjFoe, anyAdjMon, anyMon, allAdjFoe, allAdjMon, allFoe, allMon, anyAlly, user, allAlly, anyAdjAlly =\
    ("any adjacent foe", "any adjacent mon", "any mon", "all adjacent foes", "all adjacent mons", "all foes",
     "all mons", "any ally", "user", "all allies", "any adjacent ally")
var = "varies"
stats = {"atk": "Attack", "def": "Defense", "spa": "Special Attack", "spd": "Special Defense", "spe": "Speed",
         "eva": "evasion", "acc": "accuracy", "crt": "critical hit ratio"}
nums = ["zero", "one", "two", "three", "four", "five", "six"]
genDict = ["", "♀", "♂"]

normal = "Normal"
fire = "Fire"
water = "Water"
grass = "Grass"
electric = "Electric"
rock = "Rock"
ground = "Ground"
steel = "Steel"
psychic = "Psychic"
fighting = "Fighting"
flying = "Flying"
ghost = "Ghost"
dark = "Dark"
bug = "Bug"
poison = "Poison"
fairy = "Fairy"
dragon = "Dragon"
ice = "Ice"
typeless = "???"

colors = {
    normal: "A8A878", fire: "F08030", water: "6890F0", grass: "78C850", electric: "F8D030", rock: "B8A038",
    ground: "E0C068", steel: "B8B8D0", psychic: "F85888", fighting: "C03028", flying: "A890F0", ghost: "705898",
    dark: "705848", bug: "A8B820", poison: "A040A0", fairy: "EE99AC", dragon: "7038F8", ice: "98D8D8",
    typeless: "000000"
}

superEffective = {
    normal: (), fire: (grass, bug, steel, ice), water: (fire, rock, ground), grass: (water, rock, ground),
    electric: (flying, water), rock: (fire, flying, bug, ice), ground: (fire, rock, steel, poison, electric),
    steel: (rock, ice, fairy), psychic: (fighting, poison), fighting: (rock, steel, ice, dark, normal),
    flying: (grass, bug, fighting), ghost: (ghost, psychic), dark: (psychic, ghost), bug: (grass, psychic, dark),
    poison: (grass, fairy), fairy: (dragon, fighting, dark), dragon: (dragon, ), ice: (ground, grass, flying, dragon),
    typeless: ()
}
notVeryEffective = {
    normal: (steel, rock), fire: (fire, water, rock, dragon), water: (water, grass, dragon),
    grass: (grass, bug, flying, steel, fire, dragon, poison), electric: (dragon, grass, electric),
    rock: (fighting, steel, ground), ground: (bug, grass), steel: (steel, fire, water, electric),
    psychic: (psychic, steel), fighting: (psychic, flying, bug, fairy, poison), flying: (rock, steel, electric),
    ghost: (dark, ), dark: (fighting, dark, fairy), bug: (fighting, steel, fairy, poison, ghost, fire, flying),
    poison: (poison, ground, rock, ghost), fairy: (poison, steel, fire), dragon: (steel, ),
    ice: (fire, ice, steel, water), typeless: ()
}
ineffective = {
    normal: (ghost, ), fire: (), water: (), grass: (), electric: (ground, ), rock: (), ground: (flying, ),
    psychic: (dark, ), fighting: (ghost, ), flying: (), ghost: (normal, ), dark: (), bug: (), poison: (steel, ),
    steel: (), fairy: (), dragon: (fairy, ), ice: (), typeless: ()
}


def strType(t):
    se = f"**Super effective against:** {', '.join(superEffective[t])}\n" if len(superEffective[t]) > 0 else ""
    nve = f"**Not very effective against:** {', '.join(notVeryEffective[t])}\n" if len(notVeryEffective[t]) > 0 else ""
    ne = f"**Does not affect:** {', '.join(ineffective[t])}\n" if len(ineffective[t]) > 0 else ""
    resists = [g for g in notVeryEffective if t in notVeryEffective[g]]
    re = f"**Resistant to:** {', '.join(resists)}\n" if len(resists) > 0 else ""
    weak = [g for g in superEffective if t in superEffective[g]]
    we = f"**Weak to:** {', '.join(weak)}\n" if len(weak) > 0 else ""
    immune = [g for g in ineffective if t in ineffective[g]]
    me = f"**Immune to:** {', '.join(immune)}" if len(immune) > 0 else ""
    return "".join([se, nve, ne, "\n", re, we, me])


def eff(a, d):
    if a not in superEffective:
        return -10
    if d is None:
        return 1
    return 0 if d in ineffective[a] else 2 if d in superEffective[a] else 0.5 if d in notVeryEffective[a] else 1


def scal(n, level=100, ev=0, iv=0):
    return floor((2 * n + iv + floor(ev / 4)) * level / 100) + 5


def hcal(n, level=100, ev=0, iv=0):
    return floor((2 * n + iv + floor(ev / 4)) * level / 100) + level + 10


def cap(s, sep=" "):
    return sep.join([g.capitalize() for g in s.split(sep)])


def pokeround(n):  # Game Freak rounds down on .5?????
    return ceil(n) if n % 1 > 0.5 else floor(n)


def threeDig(n):
    return str(n) if n >= 100 else "0" + str(n) if n >= 10 else "00" + str(n)


def signed(n):
    return f"+{str(n)}" if n > 0 else str(n)


def sign(n):
    return -1 if n < 0 else 1


def isEff(s):
    try:
        int(s[4:])
    except ValueError:
        return False
    else:
        return s[:3] in stats and s[3] in "ST"


def product(l):
    ret = 1
    for i in l:
        ret *= i
    return ret


def weighted_sample(l: iter, weight: callable, k=1):
    weights = [weight(g) for g in l]
    indices = list(range(len(l)))
    ret = []
    while len(ret) < k:
        add = choices(indices, weights=[weights[n] for n in indices], k=1)[0]
        ret.append(l[add])
        indices.remove(add)
    return ret
