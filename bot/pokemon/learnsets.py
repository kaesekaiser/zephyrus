import json


full_game_names = {
    "RB": "Red/Blue",
    "Y": "Yellow",
    "GS": "Gold/Silver",
    "C": "Crystal",
    "RS": "Ruby/Sapphire",
    "FRLG": "FireRed/LeafGreen",
    "E": "Emerald",
    "DP": "Diamond/Pearl",
    "Pt": "Platinum",
    "HGSS": "HeartGold/SoulSilver",
    "BW": "Black/White",
    "BW2": "Black 2/White 2",
    "XY": "X/Y",
    "ORAS": "Omega Ruby/Alpha Sapphire",
    "SM": "Sun/Moon",
    "USUM": "Ultra Sun/Ultra Moon",
    "LGPE": "Let's Go Pikachu/Eevee",
    "SwSh": "Sword/Shield",
    "BDSP": "Brilliant Diamond/Shining Pearl",
    "LA": "Legends: Arceus",
    "SV": "Scarlet/Violet"
}


class Learnset:
    def __init__(self, **kwargs):
        self.level = kwargs.get("level", [])
        self.evo = kwargs.get("evo", [])
        self.prior = kwargs.get("prior", [])
        self.reminder = kwargs.get("reminder", [])
        self.egg = kwargs.get("egg", [])
        self.tm = kwargs.get("tm", {})

    def __bool__(self):
        return bool(self.all_moves)

    def __contains__(self, item):
        return (item in self.all_level_up_moves) or (item in self.evo) or (item in self.prior) or \
            (item in self.reminder) or (item in self.egg) or (item in self.all_tm_moves)

    def __str__(self):
        ret = ""
        if self.level:
            ret += "By level:\n"
            ret += "\n".join(f"{k}: {v}" for k, v in self.level)

        if self.evo:
            ret += f"\n\nOn evolution:\n{', '.join(self.evo)}"

        if self.prior:
            ret += f"\n\nBy a prior evolution:\n{', '.join(self.prior)}"

        if self.reminder:
            ret += f"\n\nBy reminder:\n{', '.join(self.reminder)}"

        if self.egg:
            ret += f"\n\nEgg moves:\n{', '.join(self.egg)}"

        if self.tm:
            ret += f"\n\nBy TM:\n"
            ret += "\n".join(f"{k}: {v}" for k, v in self.tm.items())

        return ret.strip("\n")

    @property
    def all_moves(self):
        return list(set(self.all_level_up_moves + self.evo + self.prior + self.reminder + self.egg + self.all_tm_moves))

    @property
    def all_level_up_moves(self):
        return [g[1] for g in self.level] if self.level else []

    @property
    def all_tm_moves(self):
        return list(self.tm.values())

    @property
    def json(self):
        ret = {}
        if self.level:
            ret["level"] = self.level
        if self.evo:
            ret["evo"] = self.evo
        if self.prior:
            ret["prior"] = self.prior
        if self.reminder:
            ret["reminder"] = self.reminder
        if self.egg:
            ret["egg"] = self.egg
        if self.tm:
            ret["tm"] = self.tm
        return ret

    @staticmethod
    def from_json(js: dict):
        return Learnset(
            level=js.get("level", []),
            evo=js.get("evo", []),
            prior=js.get("prior", []),
            reminder=js.get("reminder", []),
            egg=js.get("egg", []),
            tm=js.get("tm", {})
        )

    def methods_for(self, move: str) -> dict:
        return {
            "level": ([g[0] for g in self.level if g[1] == move][0]) if move in self.all_level_up_moves else 0,
            "evo": (move in self.evo),
            "prior": (move in self.prior),
            "reminder": (move in self.reminder),
            "egg": (move in self.egg),
            "tm": ([k for k, v in self.tm.items() if v == move][0]) if move in self.all_tm_moves else None
        }


with open("pokemon/learnsets.json", "r") as fp:
    learnsets = {k: {j: Learnset.from_json(g) for j, g in v.items()} for k, v in json.load(fp).items()}
