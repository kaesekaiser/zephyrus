import json
from re import sub, search
from typing import Union
from pyquery import PyQuery
from random import choice


types = normal, water, fire, grass, electric, ground, rock, steel, ice, ghost, dark, fighting, flying, bug, poison, \
    fairy, dragon, psychic = "Normal", "Water", "Fire", "Grass", "Electric", "Ground", "Rock", "Steel", "Ice", \
    "Ghost", "Dark", "Fighting", "Flying", "Bug", "Poison", "Fairy", "Dragon", "Psychic"


class Form:
    def __init__(self, hp: int, atk: int, dfn: int, spa: int, spd: int, spe: int, type1, type2,
                 height: float, weight: float, name: str=""):
        self.hp = hp
        self.atk = atk
        self.dfn = dfn
        self.spa = spa
        self.spd = spd
        self.spe = spe
        self.type1 = type1
        self.type2 = type2
        self.height = height
        self.weight = weight
        self.name = name

    @property
    def json(self):
        return [self.hp, self.atk, self.dfn, self.spa, self.spd, self.spe, self.type1, self.type2, self.height,
                self.weight, self.name]


formes = ["Attack", "Defense", "Speed", "Altered", "Origin", "Land", "Sky", "Incarnate", "Therian", "Aria",
          "Pirouette", "Blade", "Shield", "10%", "50%", "Complete"]
formAts = {
    "Mega": "Mega {}",
    "Mega X": "Mega {} X",
    "Mega Y": "Mega {} Y",
    "Alolan": "Alolan {}",
    "Black": "Black {}",
    "White": "White {}",
    "Ash": "Ash-{}",
    "Confined": "{} Confined",
    "Unbound": "{} Unbound",
    "Dusk Mane": "Dusk Mane {}",
    "Dawn Wings": "Dawn Wings {}",
    "Ultra": "Ultra {}",
    "Red-Striped": "Red-Striped {}",
    "Blue-Striped": "Blue-Striped {}"
}


class Species:
    def __init__(self, name, *forms: Form):
        self.name = name
        self.forms = {g.name: g for g in forms}

    def get_form_name(self, s: str):
        if not s:
            return list(self.forms)[0]
        for g in self.forms:
            if fix(g) == fix(s):
                return g
        else:
            raise ValueError("Form not found.")

    @property
    def json(self):
        return [self.name, *[g.json for g in self.forms.values()]]


class Mon:
    def __init__(self, spc: Union[Species, str], **kwargs):
        if isinstance(spc, str):
            self.species = natDex[spc]
        else:
            self.species = spc
        self.givenForm = kwargs.get("form", "")
        self.form = self.species.forms[self.species.get_form_name(self.givenForm)]
        self.type1 = self.form.type1  # need to be changeable bc of moves like Soak
        self.type2 = self.form.type2

    @property
    def dex_no(self):
        return list(natDex).index(self.species.name) + 1

    @property
    def generation(self):
        return [g for g in range(8) if self.dex_no <= generationBounds[g]][-1]

    @property
    def form_names(self):
        return [Mon(self.species, form=g).full_name for g in natDex[self.species.name].forms]

    @property
    def types(self):
        return tuple(g for g in [self.type1, self.type2] if g)

    @property
    def base_stats(self):
        return self.form.hp, self.form.atk, self.form.dfn, self.form.spa, self.form.spd, self.form.spe

    @property
    def full_name(self):
        if not self.form.name:
            return self.species.name
        if self.form.name in formes:
            return f"{self.species.name} ({self.form.name} Forme)"
        elif self.species.name == "Vivillon":
            return f"{self.species.name} ({self.form.name} Pattern)"
        elif self.species.name in ["Flabébé", "Floette", "Florges"]:
            return f"{self.species.name} ({self.form.name} Flower)"
        elif self.species.name == "Oricorio":
            return f"{self.species.name} ({self.form.name} Style)"
        elif self.species.name in ["Pumpkaboo", "Gourgeist"]:
            return f"{self.form.name} Size {self.species.name}"
        elif self.species.name == "Wormadam":
            return f"{self.form.name} Cloak {self.species.name}"
        elif self.species.name in ["Silvally", "Arceus"]:
            return f"{self.species.name} ({self.form.name}-type)"
        elif self.species.name == "Furfrou":
            return f"{self.species.name} ({self.form.name} Trim)"
        return formAts.get(self.form.name, "{} (" + self.form.name + " Form)").format(self.species.name)


with open("stats.json" if __name__ == "__main__" else "pokemon/stats.json", "r") as file:
    natDex = {g: Species(j[0], *[Form(*k) for k in j[1:]]) for g, j in json.load(file).items()}


with open("dex.json" if __name__ == "__main__" else "pokemon/dex.json", "r") as file:
    dexEntries = json.load(file)


with open("species.json" if __name__ == "__main__" else "pokemon/species.json", "r") as file:
    species = json.load(file)


def fix(s: str, joiner: str="-"):
    return sub(f"{joiner}+", joiner, sub(f"[^a-z0-9{joiner}]+", "", sub("\s+", joiner, s.lower().replace("é", "e"))))


fixedDex = {fix(g): g for g in natDex}


def read_url(url: str):
    return str(PyQuery(url, {'title': 'CSS', 'printable': 'yes'}))


imgLink = "https://img.pokemondb.net/artwork/vector/{}.png"
dexLink = "https://pokemondb.net/pokedex/{}"
generationBounds = [0, 151, 251, 386, 493, 649, 721, 809]
gameGenerations = {
    "Red": 1, "Blue": 1, "Yellow": 1, "Gold": 2, "Silver": 2, "Crystal": 2, "Ruby": 3, "Sapphire": 3, "Emerald": 3,
    "FireRed": 3, "LeafGreen": 3, "Diamond": 4, "Pearl": 4, "Platinum": 4, "HeartGold": 4, "SoulSilver": 4,
    "Black": 5, "White": 5, "Black 2": 5, "White 2": 5, "X": 6, "Y": 6, "Omega Ruby": 6, "Alpha Sapphire": 6,
    "Sun": 7, "Moon": 7, "Ultra Sun": 7, "Ultra Moon": 7
}


class Dex:
    def __init__(self, name: str):
        self.name = name
        self.dex = {g: j for g, j in list(natDex.items())[:generationBounds[gameGenerations[name]]]}

    def __len__(self):
        return len(self.dex)

    def __getitem__(self, item: Union[int, str]):
        if isinstance(item, int):
            return self.dex[list(self.dex)[(item - 1) % len(self.dex)]]
        return self.dex[item]

    def __contains__(self, item):
        return item in self.dex


gameDexes = {g: Dex(g) for g in gameGenerations}


def image(m: Mon):
    if m.form.name:
        if m.species.name == "Minior" and m.form == "Core":
            suffix = "-" + choice(["orange", "yellow", "green", "blue", "indigo", "purple"]) + "-core"
        else:
            suffix = "-" + fix(m.form.name)
    else:
        suffix = ""
    return imgLink.format(fix(m.species.name) + suffix)


if __name__ == "__main__":
    species = {}
    for i in natDex:
        try:
            species[i] = search(r"(?<=<td>)[^<>]+\sPokémon(?=</td>\n)", read_url(dexLink.format(fix(i))))\
                .group(0)
        except AttributeError:
            print(f"NOT FOUND FOR {i}")
            continue
        print(i, species[i])
    with open("species.json", "w") as file:
        json.dump(species, file, indent=4)
