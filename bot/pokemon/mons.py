import random
from functions import can_int, none_list, snip
from pokemon.field import *
from pokemon.learnsets import *
from pyquery import PyQuery
from math import floor, log, ceil


def add_sign(n: float | int) -> str:
    if n > 0:
        return f"+{n}"
    else:
        return str(n)


def rebase(n: str | int, fro: int, to: int, min_length: int = 0) -> str:
    base_order = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    n = "".join(list(reversed(str(n))))
    n = sum([base_order.index(n[g]) * fro ** g for g in range(len(n))])
    if not n:
        return "0".rjust(min_length, "0")
    ret = "".join(reversed([base_order[(n % (to ** (g + 1))) // (to ** g)] for g in range(int(log(n + 0.5, to)) + 1)]))
    return ret.rjust(min_length, "0")


def decimal(n: str, fro: int) -> int:
    return int(rebase(n, fro, 10))


def product(ls: iter) -> float:
    ret = 1
    for item in ls:
        ret *= item
    return ret


class Form:
    def __init__(self, hp: int, atk: int, dfn: int, spa: int, spd: int, spe: int, type1, type2,
                 height: float, weight: float, name: str = ""):
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

    @staticmethod
    def null():
        return Form(0, 0, 0, 0, 0, 0, None, None, 0, 0)

    @staticmethod
    def from_str(s: str):
        """Assumes validity."""
        def convert_to_type(st: str):
            st = st.title()
            if st == "None":
                return None
            else:
                if st not in types:
                    raise ValueError(f"Invalid type {st}.")
                return st

        s = s.split()
        return Form(
            *list(map(int, s[:6])), *list(map(convert_to_type, s[6:8])), *list(map(float, s[8:10])),
            name="" if len(s) < 11 else s[10] if len(s) == 11 else " ".join(s[10:])
        )

    @property
    def json(self):
        return [self.hp, self.atk, self.dfn, self.spa, self.spd, self.spe, self.type1, self.type2, self.height,
                self.weight, self.name]


formes = ["Attack", "Defense", "Speed", "Altered", "Origin", "Land", "Sky", "Incarnate", "Therian", "Aria",
          "Pirouette", "Blade", "Shield", "10%", "50%", "Complete"]
form_name_styles = {
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
    "Blue-Striped": "Blue-Striped {}",
    "White-Striped": "White-Striped {}",
    "Bloodmoon": "Bloodmoon {}"
}
castform_weathers = {sun: "Sunny", rain: "Rainy", hail: "Snowy"}


form_shortcuts = {
    "a": "Alolan",
    "alola": "Alolan",
    "g": "Galarian",
    "galar": "Galarian",
    "h": "Hisuian",
    "hisui": "Hisuian",
    "p": "Paldean",
    "paldea": "Paldean"
}


class Species:
    def __init__(self, name: str, catch_rate: int, forms: list[Form]):
        self.name = name
        self.forms = {g.name: g for g in forms}
        self.catch_rate = catch_rate

    @staticmethod
    def null():
        return Species("NULL", 0, [Form.null()])

    @staticmethod
    def from_json(js: dict):
        return Species(js["name"], js["catch_rate"], [Form(*g) for g in js["forms"]])

    def add_form(self, fm: Form):
        self.forms[fm.name] = fm

    def remove_form(self, fm: Form):
        del self.forms[fm.name]

    @property
    def notable_forms(self):
        """Forms which change the actual stats of the mon, not just appearance (e.g. Vivillon) or type (e.g. Arceus)."""
        return {
            g: j for g, j in self.forms.items()
            if j.json[:6] != list(self.forms.values())[0].json[:6]
            or j.name in ["Alolan", "Galarian", "Hisuian", "Paldean"]
        }

    def get_form_name(self, s: str):
        if isinstance(s, int):
            return list(self.forms)[s]
        if (not s) or (s.lower() == "base"):
            return list(self.forms)[0]
        if s.lower() == "random":
            return random.choice(list(self.forms))
        for g in self.forms:
            if fix(g) == fix(s):
                return g
            if form_shortcuts.get(fix(s)) == g:
                return g
        else:
            raise ValueError("Form not found.")

    @property
    def json(self):
        return {"name": self.name, "catch_rate": self.catch_rate, "forms": [g.json for g in self.forms.values()]}


class Evolution:
    def __init__(self, into: str, **kwargs):
        self.into = into
        self.reqs = kwargs

    @staticmethod
    def from_json(js: dict):
        return Evolution(**js)

    @staticmethod
    def null():
        return Evolution("NONE")

    @property
    def method(self):
        return self["method"]

    @property
    def first_method(self) -> dict:
        if self["multiple"]:
            return self["multiple"][0]
        return self.reqs

    def __getitem__(self, item):
        return self.reqs.get(item)

    def __eq__(self, other):
        return isinstance(other, Evolution) and (self.into == other.into)

    def __bool__(self):
        return self.into != "NONE"

    def read_out(self, using_gerund: bool):
        if self["multiple"]:
            return "; or, ".join(Evolution(self.into, **g).read_out(using_gerund) for g in self["multiple"])

        if self.method == "specific":
            return self["by"] if using_gerund else self["desc"]

        if self.method == "level":
            if self["level"]:
                ret = f"at level {self['level']}" if using_gerund else f"Level {self['level']}"
            else:
                ret = "upon levelling up" if using_gerund else "Level up"
        elif self.method == "friendship":
            ret = ("upon levelling" if using_gerund else "Level") + " up with high friendship"
        elif self.method == "trade":
            ret = "when traded" if using_gerund else "Trade"
        elif self.method == "use":
            ret = ("with" if using_gerund else "Use") + \
                  f" a{'n' if self['item'][0].lower() in 'aeiou' else ''} {self['item']}"
        elif self.method == "steps":
            ret = ("after walking" if using_gerund else "Walk") + " 1000 steps using the Let's Go feature"
        elif self.method == "move":
            ret = ("after using" if using_gerund else "Use") + f" {self['move']}"
        else:
            return "Not known"

        if self["special_req"]:
            ret += f" {self['special_req']}"

        if self["holding"]:
            ret += f" while holding a{'n' if self['holding'][0].lower() in 'aeiou' else ''} {self['holding']}"
        if self["knowing"]:
            ret += f" while knowing {self['knowing']}"

        if self["location"]:
            ret += f" in {self['location']}"
        if self["time"]:
            ret += f" at {self['time']}"
        if self["gender"]:
            ret += f" ({self['gender']})"
        if self["game"]:
            ret += f" (in {self['game']})"

        return ret

    def sentence(self, preposition: str = "into"):
        if self.into == "NONE":
            return "Does not evolve."
        if self.into == "Shedinja":
            return f"A **{self.into}** appears in the player's party {self.read_out(True)}."
        return f"Evolves {preposition} **{self.into}** {self.read_out(True)}."

    @property
    def phrase(self):
        if self.into == "NONE":
            return "Does not evolve"
        return self.read_out(False)


with open("pokemon/data/evolutions.json", "r") as fp:
    evolutions = {g: [Evolution.from_json(k) for k in j] for g, j in json.load(fp).items()}


natures = [
    'Hardy', 'Lonely', 'Adamant', 'Naughty', 'Brave',
    'Bold', 'Docile', 'Impish', 'Lax', 'Relaxed',
    'Modest', 'Mild', 'Bashful', 'Rash', 'Quiet',
    'Calm', 'Gentle', 'Careful', 'Quirky', 'Sassy',
    'Timid', 'Hasty', 'Jolly', 'Naive', 'Serious'
]
ability_descriptions = json.load(open("pokemon/data/ability_descriptions.json"))
abilities = list(ability_descriptions.keys())
berries = [
    'Aguav Berry', 'Apicot Berry', 'Aspear Berry', 'Babiri Berry', 'Belue Berry', 'Bluk Berry', 'Charti Berry',
    'Cheri Berry', 'Chesto Berry', 'Chilan Berry', 'Chople Berry', 'Coba Berry', 'Colbur Berry', 'Cornn Berry',
    'Custap Berry', 'Durin Berry', 'Enigma Berry', 'Figy Berry', 'Ganlon Berry', 'Grepa Berry', 'Haban Berry',
    'Hondew Berry', 'Iapapa Berry', 'Jaboca Berry', 'Kasib Berry', 'Kebia Berry', 'Kee Berry', 'Kelpsy Berry',
    'Lansat Berry', 'Leppa Berry', 'Liechi Berry', 'Lum Berry', 'Mago Berry', 'Magost Berry', 'Maranga Berry',
    'Micle Berry', 'Nanab Berry', 'Nomel Berry', 'Occa Berry', 'Oran Berry', 'Pamtre Berry', 'Passho Berry',
    'Payapa Berry', 'Pecha Berry', 'Persim Berry', 'Petaya Berry', 'Pinap Berry', 'Pomeg Berry', 'Qualot Berry',
    'Rabuta Berry', 'Rawst Berry', 'Razz Berry', 'Rindo Berry', 'Roseli Berry', 'Rowap Berry', 'Salac Berry',
    'Shuca Berry', 'Silver Razz Berry', 'Sitrus Berry', 'Spelon Berry', 'Starf Berry', 'Tamato Berry', 'Tanga Berry',
    'Wacan Berry', 'Watmel Berry', 'Wepear Berry', 'Wiki Berry', 'Yache Berry'
]
status_berries = {
    "Aspear Berry": [frozen], "Cheri Berry": [paralyzed], "Chesto Berry": [asleep],
    "Pecha Berry": [poisoned, badly_poisoned], "Rawst Berry": [burned],
    "Lum Berry": [frozen, paralyzed, asleep, poisoned, badly_poisoned, burned]
}
drives = ['Burn Drive', 'Chill Drive', 'Douse Drive', 'Shock Drive']
gems = [f"{g} Gem" for g in types]
mega_stones = {
    'Abomasite': 'Abomasnow', 'Absolite': 'Absol', 'Aerodactylite': 'Aerodactyl', 'Aggronite': 'Aggron',
    'Alakazite': 'Alakazam', 'Altarianite': 'Altaria', 'Ampharosite': 'Ampharos', 'Audinite': 'Audino',
    'Banettite': 'Banette', 'Beedrillite': 'Beedrill', 'Blastoisinite': 'Blastoise', 'Blazikenite': 'Blaziken',
    'Cameruptite': 'Camerupt', 'Charizardite X': 'Charizard', 'Charizardite Y': 'Charizard', 'Diancite': 'Diancie',
    'Galladite': 'Gallade', 'Garchompite': 'Garchomp', 'Gardevoirite': 'Gardevoir', 'Gengarite': 'Gengar',
    'Glalitite': 'Glalie', 'Gyaradosite': 'Gyarados', 'Heracronite': 'Heracross', 'Houndoominite': 'Houndoom',
    'Kangaskhanite': 'Kangaskhan', 'Latiasite': 'Latias', 'Latiosite': 'Latios', 'Lopunnite': 'Lopunny',
    'Lucarionite': 'Lucario', 'Manectite': 'Manectric', 'Mawilite': 'Mawile', 'Medichamite': 'Medicham',
    'Metagrossite': 'Metagross', 'Mewtwonite X': 'Mewtwo', 'Mewtwonite Y': 'Mewtwo', 'Pidgeotite': 'Pidgeot',
    'Pinsirite': 'Pinsir', 'Sablenite': 'Sableye', 'Salamencite': 'Salamence', 'Sceptilite': 'Sceptile',
    'Scizorite': 'Scizor', 'Sharpedonite': 'Sharpedo', 'Slowbronite': 'Slowbro', 'Steelixite': 'Steelix',
    'Swampertite': 'Swampert', 'Tyranitarite': 'Tyranitar', 'Venusaurite': 'Venusaur'
}
memories = [f"{g} Memory" for g in types]
plates = {
    'Draco Plate': 'Dragon', 'Dread Plate': 'Dark', 'Earth Plate': 'Ground', 'Fist Plate': 'Fighting',
    'Flame Plate': 'Fire', 'Icicle Plate': 'Ice', 'Insect Plate': 'Bug', 'Iron Plate': 'Steel',
    'Meadow Plate': 'Grass', 'Mind Plate': 'Psychic', 'Pixie Plate': 'Fairy', 'Sky Plate': 'Flying',
    'Splash Plate': 'Water', 'Spooky Plate': 'Ghost', 'Stone Plate': 'Rock', 'Toxic Plate': 'Poison',
    'Zap Plate': 'Electric'
}
type_enhancers = {
    'Black Belt': 'Fighting', 'Black Glasses': 'Dark', 'Charcoal': 'Fire', 'Dragon Fang': 'Dragon',
    'Hard Stone': 'Rock', 'Magnet': 'Electric', 'Metal Coat': 'Steel', 'Miracle Seed': 'Grass',
    'Mystic Water': 'Water', 'Never-Melt Ice': 'Ice', 'Poison Barb': 'Poison', 'Sharp Beak': 'Flying',
    'Silk Scarf': 'Normal', 'Silver Powder': 'Bug', 'Soft Sand': 'Ground', 'Spell Tag': 'Ghost',
    'Twisted Spoon': 'Psychic'
}
type_z_crystals = {
    'Buginium Z': {'req': 'Bug', 'move': 'Savage Spin-Out'},
    'Darkinium Z': {'req': 'Dark', 'move': 'Black Hole Eclipse'},
    'Dragonium Z': {'req': 'Dragon', 'move': 'Devastating Drake'},
    'Electrium Z': {'req': 'Electric', 'move': 'Gigavolt Havoc'},
    'Fairium Z': {'req': 'Fairy', 'move': 'Twinkle Tackle'},
    'Fightinium Z': {'req': 'Fighting', 'move': 'All-Out Pummeling'},
    'Firium Z': {'req': 'Fire', 'move': 'Inferno Overdrive'},
    'Flyinium Z': {'req': 'Flying', 'move': 'Supersonic Skystrike'},
    'Ghostium Z': {'req': 'Ghost', 'move': 'Never-Ending Nightmare'},
    'Grassium Z': {'req': 'Grass', 'move': 'Bloom Doom'},
    'Groundium Z': {'req': 'Ground', 'move': 'Tectonic Rage'},
    'Icium Z': {'req': 'Ice', 'move': 'Subzero Slammer'},
    'Normalium Z': {'req': 'Normal', 'move': 'Breakneck Blitz'},
    'Poisonium Z': {'req': 'Poison', 'move': 'Acid Downpour'},
    'Psychium Z': {'req': 'Psychic', 'move': 'Shattered Psyche'},
    'Rockium Z': {'req': 'Rock', 'move': 'Continental Crush'},
    'Steelium Z': {'req': 'Steel', 'move': 'Corkscrew Crash'},
    'Waterium Z': {'req': 'Water', 'move': 'Hydro Vortex'}
}
mon_z_crystals = {
    'Aloraichium Z': {'req': ['Raichu-Alolan'], 'start': 'Thunderbolt', 'move': 'Stoked Sparksurfer'},
    'Decidium Z': {'req': ['Decidueye'], 'start': 'Spirit Shackle', 'move': 'Thousand Arrow Raid'},
    'Eevium Z': {'req': ['Eevee'], 'start': 'Last Resort', 'move': 'Extreme Evoboost'},
    'Incinium Z': {'req': ['Incineroar'], 'start': 'Darkest Lariat', 'move': 'Malicious Moonsault'},
    'Kommonium Z': {'req': ['Kommo-o'], 'start': 'Clanging Scales', 'move': 'Clangorous Soulblaze'},
    'Lunalium Z': {
        'req': ['Lunala', 'Necrozma-Dawn Wings'], 'start': 'Moongeist Beam', 'move': 'Menacing Moonraze Maelstrom'
    },
    'Lycanium Z': {'req': ['Lycanroc'], 'start': 'Stone Edge', 'move': 'Splintered Stormshards'},
    'Marshadium Z': {'req': ['Marshadow'], 'start': 'Spectral Thief', 'move': 'Soul-Stealing 7-Star Strike'},
    'Mewnium Z': {'req': ['Mew'], 'start': 'Psychic', 'move': 'Genesis Supernova'},
    'Mimikium Z': {'req': ['Mimikyu'], 'start': 'Play Rough', 'move': "Let's Snuggle Forever"},
    'Pikashunium Z': {'req': ['Pikachu-Cap'], 'start': 'Thunderbolt', 'move': '10,000,000 Volt Thunderbolt'},
    'Pikanium Z': {'req': ['Pikachu'], 'start': 'Volt Tackle', 'move': 'Catastropika'},
    'Primarium Z': {'req': ['Primarina'], 'start': 'Sparkling Aria', 'move': 'Oceanic Operetta'},
    'Snorlium Z': {'req': ['Snorlax'], 'start': 'Giga Impact', 'move': 'Pulverizing Pancake'},
    'Solganium Z': {
        'req': ['Solgaleo', 'Necrozma-Dusk Mane'], 'start': 'Sunsteel Strike', 'move': 'Searing Sunraze Smash'
    },
    'Tapunium Z': {
        'req': ['Tapu Koko', 'Tapu Lele', 'Tapu Fini', 'Tapu Bulu']
    },
    'Ultranecrozium Z': {'req': ['Necrozma-Ultra'], 'start': 'Photon Geyser', 'move': 'Light That Burns The Sky'}
}
z_crystals = [*type_z_crystals.keys(), *mon_z_crystals.keys()]
held_items = [
    'No Item',
    *berries, *drives, *gems, *mega_stones, *memories, *plates, *type_enhancers, *z_crystals,
    'Ability Shield', 'Absorb Bulb', 'Adamant Orb', 'Adrenaline Orb', 'Air Balloon', 'Amulet Coin', 'Armor Fossil',
    'Assault Vest', 'Berry Sweet', 'Big Root', 'Binding Band', 'Black Sludge', 'Blunder Policy', 'Booster Energy',
    'Bottle Cap', 'Bright Powder', 'Cell Battery', 'Chipped Pot', 'Choice Band', 'Choice Scarf', 'Choice Specs',
    'Claw Fossil', 'Clear Amulet', 'Clover Sweet', 'Cover Fossil', 'Covert Cloak', 'Cracked Pot', 'Damp Rock',
    'Dawn Stone', 'Deep Sea Scale', 'Deep Sea Tooth', 'Destiny Knot', 'Dome Fossil', 'Dragon Scale', 'Dubious Disc',
    'Dusk Stone', 'Eject Button', 'Eject Pack', 'Electirizer', 'Electric Seed', 'Eviolite', 'Expert Belt',
    'Fire Stone', 'Flame Orb', 'Float Stone', 'Flower Sweet', 'Focus Band', 'Focus Sash', 'Fossilized Bird',
    'Fossilized Dino', 'Fossilized Drake', 'Fossilized Fish', 'Full Incense', 'Galarica Cuff', 'Galarica Wreath',
    'Gold Bottle Cap', 'Grassy Seed', 'Grip Claw', 'Griseous Orb', 'Heat Rock', 'Heavy-Duty Boots', 'Helix Fossil',
    'Hi-tech Earbuds', 'Ice Stone', 'Icy Rock', 'Iron Ball', "King's Rock", 'Lagging Tail', 'Lax Incense',
    'Leaf Stone', 'Leek', 'Leftovers', 'Life Orb', 'Light Ball', 'Light Clay', 'Loaded Dice', 'Love Sweet',
    'Luck Incense', 'Lucky Egg', 'Lucky Punch', 'Luminous Moss', 'Lustrous Orb', 'Macho Brace', 'Magmarizer',
    'Mental Herb', 'Metal Powder', 'Metronome', 'Mirror Herb', 'Misty Seed', 'Moon Stone', 'Muscle Band',
    'Odd Incense', 'Oval Stone', 'Plume Fossil', 'Power Anklet', 'Power Band', 'Power Belt', 'Power Bracer',
    'Power Herb', 'Power Lens', 'Power Weight', 'Prism Scale', 'Protective Pads', 'Protector', 'Psychic Seed',
    'Punching Glove', 'Pure Incense', 'Quick Claw', 'Quick Powder', 'Rare Bone', 'Razor Claw', 'Razor Fang',
    'Reaper Cloth', 'Red Card', 'Ribbon Sweet', 'Ring Target', 'Rock Incense', 'Rocky Helmet', 'Room Service',
    'Root Fossil', 'Rose Incense', 'Sachet', 'Safety Goggles', 'Scope Lens', 'Sea Incense', 'Shed Shell', 'Shell Bell',
    'Shiny Stone', 'Skull Fossil', 'Smooth Rock', 'Snowball', 'Soul Dew', 'Star Sweet', 'Sticky Barb',
    'Strawberry Sweet', 'Sun Stone', 'Sweet Apple', 'Tart Apple', 'Terrain Extender', 'Thick Club', 'Throat Spray',
    'Thunder Stone', 'Toxic Orb', 'Upgrade', 'Utility Umbrella', 'Water Stone', 'Wave Incense', 'Weakness Policy',
    'Whipped Dream', 'White Herb', 'Wide Lens', 'Wise Glasses', 'Zoom Lens'
]
weather_extenders = {
    sun: "Heat Rock", rain: "Damp Rock", hail: "Icy Rock", snow: "Icy Rock", sandstorm: "Smooth Rock"
}
poke_ball_types = [
    "beast", "cherish", "dive", "dream", "dusk", "fast", "friend", "great", "heal", "heavy", "level", "love", "lure",
    "luxury", "master", "moon", "nest", "net", "park", "poke", "premier", "quick", "repeat", "safari", "sport",
    "timer", "ultra"
]


gender_ratios = {
    "male": [
        'Nidoran-M', 'Nidorino', 'Nidoking', 'Hitmonlee', 'Hitmonchan', 'Tauros', 'Hitmontop', 'Volbeat', 'Mothim',
        'Gallade', 'Throh', 'Sawk', 'Rufflet', 'Braviary', 'Impidimp', 'Morgrem', 'Grimmsnarl', 'Tyrogue', 'Latios',
        'Tornadus', 'Thundurus', 'Landorus', 'Ursaluna-Bloodmoon', 'Greninja-Ash', 'Okidogi', 'Munkidori',
        'Fezandipiti', 'Basculegion-Male', 'Indeedee-Male', 'Oinkologne-Male', 'Meowstic-Male'
    ],
    "1:7": [
        'Bulbasaur', 'Ivysaur', 'Venusaur', 'Charmander', 'Charmeleon', 'Charizard', 'Squirtle', 'Wartortle',
        'Blastoise', 'Eevee', 'Vaporeon', 'Jolteon', 'Flareon', 'Omanyte', 'Omastar', 'Kabuto', 'Kabutops',
        'Aerodactyl', 'Snorlax', 'Chikorita', 'Bayleef', 'Meganium', 'Cyndaquil', 'Quilava', 'Typhlosion', 'Totodile',
        'Croconaw', 'Feraligatr', 'Togetic', 'Espeon', 'Umbreon', 'Treecko', 'Grovyle', 'Sceptile', 'Torchic',
        'Combusken', 'Blaziken', 'Mudkip', 'Marshtomp', 'Swampert', 'Lileep', 'Cradily', 'Anorith', 'Armaldo',
        'Relicanth', 'Turtwig', 'Grotle', 'Torterra', 'Chimchar', 'Monferno', 'Infernape', 'Piplup', 'Prinplup',
        'Empoleon', 'Cranidos', 'Rampardos', 'Shieldon', 'Bastiodon', 'Combee', 'Lucario', 'Togekiss', 'Leafeon',
        'Glaceon', 'Snivy', 'Servine', 'Serperior', 'Tepig', 'Pignite', 'Emboar', 'Oshawott', 'Dewott', 'Samurott',
        'Pansage', 'Simisage', 'Pansear', 'Simisear', 'Panpour', 'Simipour', 'Tirtouga', 'Carracosta', 'Archen',
        'Archeops', 'Zorua', 'Zoroark', 'Chespin', 'Quilladin', 'Chesnaught', 'Fennekin', 'Braixen', 'Delphox',
        'Froakie', 'Frogadier', 'Greninja', 'Tyrunt', 'Tyrantrum', 'Amaura', 'Aurorus', 'Sylveon', 'Rowlet', 'Dartrix',
        'Decidueye', 'Litten', 'Torracat', 'Incineroar', 'Popplio', 'Brionne', 'Primarina', 'Salandit', 'Grookey',
        'Thwackey', 'Rillaboom', 'Scorbunny', 'Raboot', 'Cinderace', 'Sobble', 'Drizzile', 'Inteleon', 'Sprigatito',
        'Floragato', 'Meowscarada', 'Fuecoco', 'Crocalor', 'Skeledirge', 'Quaxly', 'Quaxwell', 'Quaquaval', 'Togepi',
        'Munchlax', 'Riolu', 'Kubfu', 'Urshifu'
    ],
    "1:3": [
        'Growlithe', 'Arcanine', 'Abra', 'Kadabra', 'Alakazam', 'Machop', 'Machoke', 'Machamp', 'Electabuzz', 'Magmar',
        'Makuhita', 'Hariyama', 'Electivire', 'Magmortar', 'Timburr', 'Gurdurr', 'Conkeldurr', 'Elekid', 'Magby'
    ],
    "3:1": [
        'Clefairy', 'Clefable', 'Vulpix', 'Ninetales', 'Jigglypuff', 'Wigglytuff', 'Snubbull', 'Granbull', 'Corsola',
        'Skitty', 'Delcatty', 'Luvdisc', 'Glameow', 'Purugly', 'Minccino', 'Cinccino', 'Gothita', 'Gothorita',
        'Gothitelle', 'Oricorio', 'Comfey', 'Cursola', 'Cleffa', 'Igglybuff', 'Azurill'
    ],
    "7:1": ['Litleo', 'Pyroar'],
    "female": [
        'Nidoran-F', 'Chansey', 'Kangaskhan', 'Jynx', 'Miltank', 'Blissey', 'Illumise', 'Wormadam', 'Vespiquen',
        'Froslass', 'Petilil', 'Lilligant', 'Vullaby', 'Mandibuzz', 'Flabébé', 'Floette', 'Florges', 'Salazzle',
        'Bounsweet', 'Steenee', 'Tsareena', 'Hatenna', 'Hattrem', 'Hatterene', 'Milcery', 'Alcremie', 'Tinkatink',
        'Tinkatuff', 'Tinkaton', 'Ogerpon', 'Basculegion-Female', 'Indeedee-Female', 'Oinkologne-Female',
        'Meowstic-Female', 'Nidorina', 'Nidoqueen'
    ],
    "genderless": [
        'Magnemite', 'Magneton', 'Voltorb', 'Electrode', 'Staryu', 'Starmie', 'Porygon', 'Porygon2', 'Shedinja',
        'Lunatone', 'Solrock', 'Baltoy', 'Claydol', 'Beldum', 'Metang', 'Metagross', 'Bronzor', 'Bronzong', 'Magnezone',
        'Porygon-Z', 'Rotom', 'Phione', 'Manaphy', 'Klink', 'Klang', 'Klinklang', 'Cryogonal', 'Golett', 'Golurk',
        'Carbink', 'Minior', 'Dhelmise', 'Sinistea', 'Polteageist', 'Falinks', 'Tandemaus', 'Maushold', 'Ditto',
        'Articuno', 'Zapdos', 'Moltres', 'Mewtwo', 'Mew', 'Unown', 'Raikou', 'Entei', 'Suicune', 'Lugia', 'Ho-Oh',
        'Celebi', 'Regirock', 'Regice', 'Registeel', 'Kyogre', 'Groudon', 'Rayquaza', 'Jirachi', 'Deoxys', 'Uxie',
        'Mesprit', 'Azelf', 'Dialga', 'Palkia', 'Regigigas', 'Giratina', 'Darkrai', 'Shaymin', 'Arceus', 'Victini',
        'Cobalion', 'Terrakion', 'Virizion', 'Reshiram', 'Zekrom', 'Kyurem', 'Keldeo', 'Meloetta', 'Genesect',
        'Xerneas', 'Yveltal', 'Zygarde', 'Diancie', 'Hoopa', 'Volcanion', 'Type: Null', 'Silvally', 'Tapu Koko',
        'Tapu Lele', 'Tapu Bulu', 'Tapu Fini', 'Cosmog', 'Cosmoem', 'Solgaleo', 'Lunala', 'Nihilego', 'Buzzwole',
        'Pheromosa', 'Xurkitree', 'Celesteela', 'Kartana', 'Guzzlord', 'Necrozma', 'Magearna', 'Marshadow', 'Poipole',
        'Naganadel', 'Stakataka', 'Blacephalon', 'Zeraora', 'Meltan', 'Melmetal', 'Dracozolt', 'Arctozolt', 'Dracovish',
        'Arctovish', 'Zacian', 'Zamazenta', 'Eternatus', 'Zarude', 'Regieleki', 'Regidrago', 'Glastrier', 'Spectrier',
        'Calyrex', 'Gimmighoul', 'Gholdengo', 'Great Tusk', 'Brute Bonnet', 'Sandy Shocks', 'Scream Tail',
        'Flutter Mane', 'Slither Wing', 'Roaring Moon', 'Iron Treads', 'Iron Moth', 'Iron Hands', 'Iron Jugulis',
        'Iron Thorns', 'Iron Bundle', 'Iron Valiant', 'Ting-Lu', 'Chien-Pao', 'Wo-Chien', 'Chi-Yu', 'Koraidon',
        'Miraidon', 'Walking Wake', 'Iron Leaves', 'Poltchageist', 'Sinistcha'
    ]
}
gender_ratio_lookup = {j: k for k, v in gender_ratios.items() for j in v}
gender_differences = [
    "Venusaur", "Butterfree", "Rattata", "Raticate", "Pikachu", "Raichu", "Zubat", "Golbat", "Gloom", "Vileplume",
    "Kadabra", "Alakazam", "Doduo", "Dodrio", "Hypno", "Rhyhorn", "Rhydon", "Goldeen", "Seaking", "Scyther",
    "Magikarp", "Gyarados", "Eevee", "Meganium", "Ledyba", "Ledian", "Xatu", "Sudowoodo", "Politoed", "Aipom", "Wooper",
    "Quagsire", "Murkrow", "Wobbuffet", "Girafarig", "Gligar", "Steelix", "Scizor", "Heracross", "Sneasel",
    "Sneasel-Hisuian", "Ursaring", "Piloswine", "Octillery", "Houndoom", "Donphan", "Torchic", "Combusken", "Blaziken",
    "Beautifly", "Dustox", "Ludicolo", "Nuzleaf", "Shiftry", "Meditite", "Medicham", "Roselia", "Gulpin", "Swalot",
    "Numel", "Camerupt", "Cacturne", "Milotic", "Relicanth", "Starly", "Staravia", "Staraptor", "Bidoof", "Bibarel",
    "Kricketot", "Kricketune", "Shinx", "Luxio", "Luxray", "Roserade", "Combee", "Pachirisu", "Buizel", "Floatzel",
    "Ambipom", "Gible", "Gabite", "Garchomp", "Hippopotas", "Hippowdon", "Croagunk", "Toxicroak", "Finneon", "Lumineon",
    "Snover", "Abomasnow", "Weavile", "Rhyperior", "Tangrowth", "Mamoswine", "Unfezant", "Frillish", "Jellicent",
    "Pyroar"  # Meowstic, Indeedee, Basculegion, Oinkologne not included because the genders are separate forms
]


weather_speed_abilities = {
    sun: "Chlorophyll", rain: "Swift Swim", hail: "Slush Rush", snow: "Slush Rush", sandstorm: "Sand Rush"
}


class BareMiniMon:
    """A lightweight class containing purely biological data about a mon. Used for dex browsing primarily."""
    def __init__(self, spc: Species | str, **kwargs):
        if isinstance(spc, str):
            self.species = nat_dex[spc]
        else:
            self.species = spc
        self.form = self.species.forms[self.species.get_form_name(kwargs.get("form"))]
        self.type1 = self.form.type1  # need to be changeable bc of moves like Soak
        self.type2 = self.form.type2
        self.gender = "unknown"
        if kwargs.get("randomize_gender"):
            self.randomize_gender()
        else:
            if isinstance(kwargs.get("gender"), int):  # pass 1 for female, and 0 for male (or default)
                if kwargs.get("gender") == 1:
                    self.set_gender("female")
                elif self.default_gender != "random":
                    self.set_gender(self.default_gender)
                else:
                    self.set_gender("male")
            else:
                self.set_gender(kwargs.get("gender", self.default_gender))
        self.shiny = bool(kwargs.get("shiny", False))

    @staticmethod
    def null():
        return BareMiniMon(Species.null())

    def __bool__(self):
        return self.species.name != "NULL"

    @property
    def dex_no(self):
        try:
            return nat_dex_order.index(self.species.name) + 1
        except ValueError:
            return len(nat_dex) + 1

    @property
    def generation(self):
        if self.form.name.startswith("Galarian") or self.form.name.startswith("Hisuian") or \
                (self.species.name == "Basculin" and self.form.name == "White-Striped"):
            return 8
        if self.form.name.startswith("Paldean") or \
                (self.species.name == "Tauros" and self.form.name in ["Combat", "Aqua", "Blaze"]):
            return 9
        return [g + 1 for g in range(9) if self.dex_no > generation_bounds[g]][-1]

    @property
    def walker_pack(self) -> list:
        return [self.dex_no, list(self.species.forms).index(self.form.name), self.gender, self.shiny]

    @property
    def walker_key(self) -> int:
        pack = self.walker_pack
        return round(pack[0] + pack[1] * 1100 + (pack[2] == "female") * 33000 + pack[3] * 66000)

    @staticmethod
    def from_walker_pack(pack: list):
        return BareMiniMon(nat_dex_order[pack[0] - 1], form=pack[1], gender=pack[2], shiny=pack[3])

    @staticmethod
    def from_walker_key(key: int):
        return BareMiniMon.from_walker_pack([key % 1100, (key % 33000) // 1100, (key % 66000) // 33000, key // 66000])

    @property
    def bulbapedia(self):
        return f"https://bulbapedia.bulbagarden.net/wiki/{bulba_format(self.species.name)}_(Pok\u00e9mon\\)"

    @property
    def serebii(self):
        return f"https://serebii.net/pokedex-sv/{self.dex_no}.shtml"

    @property
    def pokemondb(self):
        return f"https://pokemondb.net/pokedex/{fix(self.species.name)}"

    @property
    def image_suffix(self):
        if self.species.name == "Unown":
            if self.form.name == "Question":
                return "-qm"
            elif self.form.name == "Exclamation":
                return "-em"
            else:
                return f"-{self.form.name.lower()}"
        elif self.species.name == "Maushold":
            if self.form.name == "Three":
                return "-family3"
            else:
                return "-family4"
        else:
            if self.form.name and self.species.name != "Dudunsparce":
                return f"-{fix(self.form.name)}"
            else:
                return ""

    @property
    def home_sprite(self):
        fem = "-f" if (self.species.name in gender_differences) and (self.gender == "female") else ""
        if self.species.name in ["Unown", "Maushold"]:
            saf = fix(self.species.name) + self.image_suffix
        else:
            saf = fix(self.overworld_saf)
        if self.shiny:
            return f"https://img.pokemondb.net/sprites/home/shiny/2x/{saf}{fem}.jpg"
        else:
            return f"https://img.pokemondb.net/sprites/home/normal/2x/{saf}{fem}.jpg"

    @property
    def dex_image(self):
        if self.generation == 9:
            return f"https://img.pokemondb.net/sprites/scarlet-violet/normal/" \
                   f"{fix(self.species.name) + self.image_suffix}.png"
        if self.generation == 8:
            return f"https://img.pokemondb.net/artwork/large/{fix(self.species.name) + self.image_suffix}.jpg"
        return img_link.format(fix(self.species.name) + self.image_suffix)

    @property
    def shiny_indicator(self):
        return " :sparkles:" if self.shiny else ""

    @property
    def form_names(self):
        return [Mon(self.species, form=g).full_name for g in nat_dex[self.species.name].forms]

    @property
    def types(self):
        return (self.type1, self.type2) if self.type2 else (self.type1, )

    @property
    def types_with_none(self):  # primarily used for dex searching
        return tuple(str(g) for g in [self.type1, self.type2])

    @property
    def gender_ratio(self):
        return gender_ratio_lookup.get(self.species_and_form, gender_ratio_lookup.get(self.species.name, "1:1"))

    @property
    def default_gender(self):
        return self.gender_ratio if self.gender_ratio in ["genderless", "male", "female"] else "random"

    def randomize_gender(self):
        if self.gender_ratio == self.default_gender:
            self.set_gender(self.default_gender)
        else:
            if random.random() < int(self.gender_ratio[0]) / (int(self.gender_ratio[0]) + int(self.gender_ratio[2])):
                self.set_gender("female")
            else:
                self.set_gender("male")

    def set_gender(self, gender: str):
        self.gender = gender
        if "Male" in self.species.forms and "Female" in self.species.forms:
            self.form = self.species.forms.get(self.gender.title(), self.species.forms["Male"])

    @property
    def base_stats(self):
        return self.form.hp, self.form.atk, self.form.dfn, self.form.spa, self.form.spd, self.form.spe

    @property
    def bst(self):
        return sum(self.base_stats)

    @property
    def height(self):
        return self.form.height

    @property
    def weight(self):
        return self.form.weight

    @property
    def name(self):
        return self.species.name

    @property
    def species_and_form(self):
        if not self.form.name:
            return self.species.name
        else:
            return f"{self.species.name}-{'-'.join(self.form.name.split())}"

    @property
    def overworld_saf(self):
        """Display name for multi-form mons who can only appear in one form outside of battle. Unchanged for most."""
        if self.species.name in [
            "Aegislash", "Wishiwashi", "Minior", "Mimikyu", "Eiscue", "Morpeko", "Gimmighoul", "Palafin"
        ]:
            return self.species.name
        return self.species_and_form

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
        elif self.species.name in ["Burmy", "Wormadam"]:
            return f"{self.species.name} ({self.form.name} Cloak)"
        elif self.species.name in ["Silvally", "Arceus"]:
            return f"{self.species.name} ({self.form.name}-type)"
        elif self.species.name == "Furfrou":
            return f"{self.species.name} ({self.form.name} Trim)"
        elif self.species.name == "Squawkabilly":
            return f"{self.species.name} ({self.form.name} Plumage)"
        elif self.species.name == "Tauros":
            return f"{self.species.name} ({self.form.name} Breed)"
        elif self.species.name == "Eiscue":
            return f"{self.species.name} ({self.form.name} Face)"
        elif self.species.name == "Maushold":
            return f"{self.species.name} (Family of {self.form.name})"
        return form_name_styles.get(self.form.name, "{} (" + self.form.name + " Form)").format(self.species.name)

    @property
    def raw_legal_abilities(self):
        if self.species_and_form in legal_abilities:
            return legal_abilities[self.species_and_form]
        return legal_abilities[self.species.name]

    @property
    def legal_abilities(self):
        return [g for g in self.raw_legal_abilities if g]

    @property
    def regular_abilities(self):
        return [g for g in self.raw_legal_abilities[:2] if g]

    @property
    def hidden_ability(self):
        return self.raw_legal_abilities[2] if self.raw_legal_abilities[2] else None

    @property
    def special_event_ability(self):
        return self.raw_legal_abilities[3] if self.raw_legal_abilities[3] else None

    @property
    def evolutions(self) -> dict[str, Evolution]:
        return {g.into: g for g in evolutions.get(self.species_and_form, evolutions.get(self.species.name, []))}

    @property
    def accessible_evolutions(self) -> dict[str, Evolution]:
        return {g: j for g, j in self.evolutions.items() if (j["gender"] is None or self.gender == j["gender"])}

    @property
    def evolves_from(self):
        if (evo_from := [g for g, j in evolutions.items() for k in j
                         if k.into == self.species.name or k.into == self.species_and_form]):
            return get_saf(evo_from[0])
        else:
            return BareMiniMon.null()

    @property
    def evolved_by(self) -> Evolution:
        """Uses the Evolution.into attribute to store the species-and-form this mon evolved from."""
        if (evo_from := [Evolution(g, **k.reqs) for g, j in evolutions.items() for k in j
                         if k.into == self.species.name or k.into == self.species_and_form]):
            return evo_from[0]
        else:
            return Evolution.null()

    @property
    def baby_form(self) -> str:
        if self.evolves_from:
            if self.evolves_from.evolves_from:
                return self.evolves_from.evolves_from.species_and_form
            return self.evolves_from.species_and_form
        return self.species_and_form

    def get_learnset(self, gen: str = "SV") -> Learnset:
        if gen not in learnsets:
            raise ValueError(f"No such generation {gen}.")
        if self.species_and_form in learnsets[gen]:
            return learnsets[gen][self.species_and_form]
        if self.species.name in learnsets[gen]:
            return learnsets[gen][self.species.name]
        return Learnset()

    def can_learn(self, move: str, gen: str = "SV"):
        return move in self.get_learnset(gen)

    def eff(self, typ: str):
        if typ:
            return product(effectiveness[typ].get(g, 1) for g in self.types)
        else:
            return 1

    def evolve(self, evo: Evolution):
        new_mon = get_saf(evo.into)
        self.species = new_mon.species
        if not evo.reqs.get("preserve_form"):
            self.form = new_mon.form
        self.set_gender(self.gender)  # in case only the evolved species has gendered forms (eg Basculin -> Basculegion)


class Mon(BareMiniMon):
    """The wieldiest of unwieldy classes."""

    def __init__(self, spc: Species | str, **kwargs):
        super().__init__(spc, **kwargs)
        self.nickname = kwargs.get("nickname", None)
        self.type3 = None  # can be added thru moves like Forest's Curse
        self.level = kwargs.get("level", kwargs.get("lvl", 100))
        self.nature = kwargs.get("nature", "Hardy")
        self.iv = kwargs.get("iv", [0, 0, 0, 0, 0, 0])
        self.ev = kwargs.get("ev", [0, 0, 0, 0, 0, 0])
        self.ability = kwargs.get("ability", kwargs.get("abil", "No Ability"))
        self.held_item = kwargs.get("held_item", kwargs.get("item", "No Item"))
        self.tera_type = kwargs.get("tera_type", kwargs.get("tera", self.type1))
        self.activating_tera = False
        self.terastallized = kwargs.get("terastallized", False)

        self.stat_stages = kwargs.get(
            "stat_stages", {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0, "eva": 0, "acc": 0, "crt": 0}
        )
        self.hpc = self.hp - kwargs.get("dmg", 0)
        self.status_condition = kwargs.get("status_condition", None)
        self.stat_con_time = kwargs.get("sct", 0)
        self.confused = kwargs.get("confused", False)
        self.confusion_time = kwargs.get("confusion_time", 0) if self.confused else 0
        self.flinching = kwargs.get("flinching", False)
        self.raised_crit_ratio = 0
        self.moves = []
        for move in kwargs.get("moves", []):
            self.add_move(move)
        self.selection = None  # normally a PackedMove
        self.last_used = None  # normally a str (move name)
        self.has_activated_ability = False  # for abilities which only activate once per switch-in (e.g. Gen 9 Protean)
        self.just_manually_switched = False  # Speed Boost doesn't activate if a mon was just manually switched in

        # all of these are effects that take multiple turns to transpire and which need to be damage-controlled by
        # having more than two states, and I'd rather use multiple booleans than an int
        # the first variable is set to True immediately upon move use; the second is set at the end of that turn
        self.charging = False  # charging a two-turn attack of any kind
        self.has_charged = False
        self.resting = False  # resting after certain moves like Hyper Beam
        self.has_rested = False
        self.drowsy = False
        self.almost_drowsy = False  # triggers falling asleep at the end of the turn
        self.flying = False  # Fly / Bounce
        self.has_flown = False
        self.digging = False  # Dig
        self.has_dug = False

        self.seeded = False
        self.minimized = False
        self.enduring = False  # reset to False at the end of every turn; set to True upon use of Endure
        self.protecting = False  # same as above
        self.successive_uses = 0  # successive uses of Protect, Detect, Endure, etc.
        self.bound = False
        self.bind_timer = 0
        self.binding_banded = False
        self.thrashing = False  # Thrash, Outrage, etc.
        self.thrash_counter = 0
        self.raging = False
        self.curled_up = False
        self.focused_energy = False

        self.team_position = kwargs.get("pos", 0)
        # STARTS AT 1. set to 0 if not in a team. used as a hash, and does not change after being added to a team.

        self.team_id = None

    @staticmethod
    def null():
        return Mon(Species.null())

    def __eq__(self, other):
        if isinstance(other, Mon):
            return self.pack == other.pack
        elif isinstance(other, dict):
            return self.pack == other

    @property
    def pack(self):
        """A JSON-like object that stores the crucial, non-volatile data for a mon. Mons are reduced to their `pack`
        when in the team."""
        return {
            "spc": self.species, "form": self.form.name, "level": self.level, "nature": self.nature, "iv": self.iv,
            "ev": self.ev, "ability": self.ability, "item": self.held_item, "dmg": round(self.hp - self.hpc),
            "status_condition": self.status_condition, "moves": self.moves, "tera": self.tera_type,
            "terastallized": self.terastallized, "pos": self.team_position, "nickname": self.nickname,
            "gender": self.gender, "shiny": self.shiny
        }

    @staticmethod
    def unpack(pack: dict):
        """Given a mon's `pack`, returns a fully-fledged Mon object for use in battle."""
        return Mon(**pack)

    @staticmethod
    def from_bare(bm: BareMiniMon):
        return Mon(bm.species, form=bm.form, gender=bm.gender, shiny=bm.shiny)

    def key(self, compressed: bool = True):
        """An alphanumerical string which contains the defining data for a mon in compressed form. It's a password."""
        moves = [list(battle_moves).index(g.name) + 1 for g in self.moves]
        if len(moves) < 4:
            moves.extend([0] * (4 - len(moves)))
        ret = f"{rebase(self.dex_no - 1, 10, 32, 2)}" \
              f"{rebase(list(self.species.forms).index(self.form.name), 10, 32, 1)}" \
              f"{rebase(self.level, 10, 32, 2)}" \
              f"{rebase(['male', 'female', 'genderless', 'random'].index(self.gender), 10, 32, 1)}" \
              f"{rebase(types.index(self.tera_type), 10, 32, 1)}" \
              f"{rebase(self.nati, 10, 32, 1)}" \
              f"{''.join(rebase(g, 10, 32) for g in self.iv)}" \
              f"{rebase(''.join(rebase(g, 10, 16, 2) for g in self.ev), 16, 32, 10)}" \
              f"{rebase(abilities.index(self.ability), 10, 32, 2)}" \
              f"{rebase(held_items.index(self.held_item) + 512 * self.shiny, 10, 32, 2)}" \
              f"{''.join(rebase(g, 10, 32, 2) for g in moves)}"
        if compressed:
            return rebase(ret, 32, 62)
        else:
            return ret

    @staticmethod
    def from_key(key: str, is_decompressed: bool = False):
        if is_decompressed:
            decompressed_key = key
        else:
            decompressed_key = rebase(key, 62, 32, 36)
        spc = nat_dex_order[decimal(decompressed_key[0:2], 32)]
        moves = [decimal(g, 32) for g in snip(decompressed_key[28:], 2)]
        item = decimal(decompressed_key[26:28], 32)
        if item >= 512:
            item = item - 512
            shiny = True
        else:
            shiny = False
        return Mon.unpack({
            "spc": spc,
            "form": list(nat_dex[spc].forms)[decimal(decompressed_key[2], 32)],
            "level": decimal(decompressed_key[3:5], 32),
            "gender": ["male", "female", "genderless", "random"][decimal(decompressed_key[5], 32)],
            "tera": types[decimal(decompressed_key[6], 32)],
            "nature": natures[decimal(decompressed_key[7], 32)],
            "iv": [decimal(g, 32) for g in decompressed_key[8:14]],
            "ev": [decimal(rebase(decompressed_key[14:24], 32, 16, 12)[g*2:g*2+2], 16) for g in range(6)],
            "ability": abilities[decimal(decompressed_key[24:26], 32)],
            "item": held_items[item],
            "moves": [list(battle_moves)[g - 1] for g in moves if g],
            "shiny": shiny
        })

    def add_move(self, move: Move | PackedMove | str):
        if isinstance(move, Move):
            self.moves.append(move.pack)
        elif isinstance(move, PackedMove):
            self.moves.append(move)
        elif isinstance(move, str):
            try:
                move = [g for g in battle_moves.values() if g.name.lower() == move.lower()][0]
            except IndexError:
                raise ValueError(f"Invalid move name '{move}'.")
            self.moves.append(move.pack)

    def set_nickname(self, nickname: str):
        if (not nickname) or (fix(nickname) == fix(self.species.name)) or (nickname.lower() == "none"):
            self.nickname = None
        else:
            self.nickname = nickname

    @property
    def types(self):
        return (self.tera_type, ) if self.terastallized else self.original_types

    @property
    def original_types(self):
        return tuple(g for g in [self.type1, self.type2, self.type3] if g)

    @property
    def name(self):
        return self.nickname if self.nickname else self.species.name

    @property
    def nickname_and_species(self):
        return self.species_and_form if not self.nickname else f"{self.nickname} ({self.species_and_form})"

    @property
    def nati(self):
        return natures.index(self.nature)

    @property
    def nature_effects(self):
        stat_names = list(six_stats.values())
        if self.nati % 5 == self.nati // 5:
            return "no effect"
        return f"+{stat_names[self.nati // 5 + 1]}, -{stat_names[self.nati % 5 + 1]}"

    def stat_level(self, stat, add: int = 0):
        n = 3 if stat in ["eva", "acc"] else 2
        change = max(min(self.stat_stages[stat] + add, 6), -6)
        return (n + (0 if change <= 0 else change)) / (n - (0 if change >= 0 else change))

    @property
    def hp(self):
        """Maximum HP; current HP is ``Mon.hpc``"""
        if self.species.name == "Shedinja":
            return 1
        return floor((2 * self.form.hp + self.iv[0] + floor(self.ev[0] / 4)) * self.level / 100) + self.level + 10

    @property
    def atk_base(self):
        return floor(
            (floor((2 * self.form.atk + self.iv[1] + floor(self.ev[1] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.nati // 5 == 0) - 0.1 * (self.nati % 5 == 0))
        )

    @property
    def atk_without_sc(self):
        return round(
            self.atk_base *
            (2 if self.species.name == "Pikachu" and self.held_item == "Light Ball" else 1) *
            (1.5 if self.ability == "Gust" and self.status_condition is not None else 1)
        )

    @property
    def atk(self):
        return round(self.atk_without_sc * self.stat_level("atk"))

    @property
    def dfn_base(self):
        return floor(
            (floor((2 * self.form.dfn + self.iv[2] + floor(self.ev[2] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.nati // 5 == 1) - 0.1 * (self.nati % 5 == 1))
        )

    @property
    def dfn_without_sc(self):
        return round(
            self.dfn_base
        )

    @property
    def dfn(self):
        return round(self.dfn_without_sc * self.stat_level("def"))

    @property
    def spa_base(self):
        return floor(
            (floor((2 * self.form.spa + self.iv[3] + floor(self.ev[3] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.nati // 5 == 2) - 0.1 * (self.nati % 5 == 2))
        )

    @property
    def spa_without_sc(self):
        return round(
            self.spa_base *
            (2 if self.species.name == "Pikachu" and self.held_item == "Light Ball" else 1)
        )

    @property
    def spa(self):
        return round(self.spa_without_sc * self.stat_level("spa"))

    @property
    def spd_base(self):
        return floor(
            (floor((2 * self.form.spd + self.iv[4] + floor(self.ev[4] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.nati // 5 == 3) - 0.1 * (self.nati % 5 == 3))
        )

    @property
    def spd_without_sc(self):
        return round(
            self.spd_base
        )

    @property
    def spd(self):
        return round(self.spd_without_sc * self.stat_level("spd"))

    @property
    def spe_base(self):
        return floor(
            (floor((2 * self.form.spe + self.iv[5] + floor(self.ev[5] / 4)) * self.level / 100) + 5) *
            (1 + 0.1 * (self.nati // 5 == 4) - 0.1 * (self.nati % 5 == 4))
        )

    @property
    def spe_without_sc(self):
        return round(
            self.spe_base * (0.5 if self.status_condition == paralyzed else 1)
        )

    @property
    def spe(self):
        return round(self.spe_without_sc * self.stat_level("spe"))

    @property
    def stats(self):
        return self.hp, self.atk_base, self.dfn_base, self.spa_base, self.spd_base, self.spe_base

    @property
    def eva(self):
        return self.stat_level("eva")

    @property
    def acc(self):
        return self.stat_level("acc")

    @property
    def crt(self):
        return self.stat_stages["crt"] + (self.ability == "Super Luck") + self.raised_crit_ratio + \
            2 * self.focused_energy

    @property
    def can_move(self):
        return not (self.resting or self.charging or self.flying or self.digging or self.thrashing)

    def hp_display(self, include_exact: bool = True):
        if include_exact:
            return f"{self.hpc}/{self.hp} HP ({max(round(100 * self.hpc / self.hp), 1 if self.hpc else 0)}%)"
        else:
            return f"{max(round(100 * self.hpc / self.hp), 1 if self.hpc else 0)}% HP"

    def stats_display(self, include_stat_changes: bool = True):
        if include_stat_changes:
            return f"{self.atk} Atk / {self.dfn} Def / {self.spa} SpA / {self.spd} SpD / {self.spe} Spe"
        else:
            return f"{self.atk_base} Atk / {self.dfn_base} Def / {self.spa_base} SpA / " \
                   f"{self.spd_base} SpD / {self.spe_base} Spe"

    @property
    def battle_status(self):
        ret = []
        if self.confused:
            ret.append("- Confused")
        if self.charging:
            ret.append(f"- Charging {self.selection.name}")
        if self.resting:
            ret.append("- Resting")
        if self.drowsy:
            ret.append("- Drowsy")
        if self.flying:
            ret.append("- Flying up high")
        if self.digging:
            ret.append("- Digging underground")
        if self.seeded:
            ret.append("- Seeded by Leech Seed")
        if self.bound:
            ret.append(f"- Bound by {self.bound}")

        if any(self.stat_stages.values()):
            if ret:
                ret.append("")
            for k, v in self.stat_stages.items():
                if v:
                    ret.append(f"{add_sign(v)} {StatChange.stat_name_dict[k]} (x{round(self.stat_level(k), 2)})")

        return "\n".join(ret)

    @property
    def status_emoji(self):
        return "fainted" if self.hpc <= 0 else \
            "".join(self.status_condition.split()).lower() if self.status_condition else ""

    @property
    def full_stat_breakdown(self):
        return f"**Nature:** {self.nature} ({self.nature_effects})\n" \
            f"**EVs:** {none_list([str(g) + ' ' + six_stat_names[n] for n, g in enumerate(self.ev) if g], ' / ')}\n" \
            f"**IVs:** {none_list([str(g) + ' ' + six_stat_names[n] for n, g in enumerate(self.iv) if g], ' / ')}\n" \
            f"**Base:** {' / '.join(str(g) + ' ' + six_stat_names[n] for n, g in enumerate(self.base_stats))}\n" \
            f"**Stats:** {' / '.join(str(g) + ' ' + six_stat_names[n] for n, g in enumerate(self.stats))}"

    def apply(self, stat: StatChange | StatusEffect):
        ret = {}
        if random.random() < stat.chance / 100:
            if isinstance(stat, StatChange):
                for k, v in stat.stages.items():
                    change = max(-6, min(6, self.stat_stages[k] + v)) - self.stat_stages[k]
                    self.stat_stages[k] += change
                    ret[k] = -20 if not change and v < 1 else 20 if not change and v > 1 else change
            else:
                if not self.status_condition:
                    self.status_condition = stat.effect
                    self.stat_con_time = random.randrange(1, 4)
                    ret[0] = {
                        asleep: "{name} fell asleep!",
                        burned: "{name} was burned!",
                        frozen: "{name} was frozen solid!",
                        paralyzed: "{name} was paralyzed!",
                        poisoned: "{name} was poisoned!",
                        badly_poisoned: "{name} was badly poisoned!"
                    }[stat.effect]
        return ret

    def change_form(self, form_name: str):
        try:
            form_name = self.species.get_form_name(form_name)
        except ValueError:
            return
        else:
            if form_name == self.form.name:
                return
            self.givenForm = form_name
            self.form = self.species.forms[form_name]
            self.type1 = self.form.type1
            self.type2 = self.form.type2
            return f"{self.name} changed form!"

    def terastallize(self):
        self.terastallized = True

    def has_move(self, move_name: str | int) -> int:
        """If the mon knows a move by the given name, returns the position (1-4) in its move list which it occupies."""
        if isinstance(move_name, int):
            return move_name
        ret = [n for n, g in enumerate(self.moves) if g.name.lower() == move_name.lower()]
        return 0 if not ret else (ret[0] + 1)

    def retrieve_move(self, move_name: str) -> PackedMove:
        try:  # first, try for one of the 'system moves' - switching out, exiting, using an item
            return [j.pack for g, j in system_moves.items() if fix(g) == fix(move_name)][0]
        except IndexError:
            try:  # then, try for one of the mon's learned moves
                return [g for g in self.moves if fix(g.name) == fix(move_name)][0]
            except IndexError:
                try:  # finally, try for any move. this will eventually be removed.
                    return [PackedMove(g.name, 1) for g in battle_moves.values() if fix(g.name) == fix(move_name)][0]
                except IndexError:
                    return PackedMove.null()


nat_dex = {g: Species.from_json(j) for g, j in json.load(open("pokemon/data/mons.json", "r")).items()}
nat_dex_order = list(nat_dex)


starters = [
    "Bulbasaur", "Charmander", "Squirtle", "Chikorita", "Cyndaquil", "Totodile", "Treecko", "Torchic", "Mudkip",
    "Turtwig", "Chimchar", "Piplup", "Snivy", "Tepig", "Oshawott", "Chespin", "Fennekin", "Froaxie",
    "Rowlet", "Litten", "Popplio", "Grookey", "Scorbunny", "Sobble", "Sprigatito", "Fuecoco", "Quaxly"
]


effectiveness = json.load(open("pokemon/data/eff.json", "r"))
legal_abilities = json.load(open("pokemon/data/abilities.json", "r"))


fixed_dex = {fix(g): g for g in nat_dex}
species_and_forms = {
    fix(Mon(g.name, form=j).species_and_form): BareMiniMon(g, form=j) for g in nat_dex.values() for j in g.forms
}


def get_saf(species_and_form: str, allow_name_only: bool = True) -> BareMiniMon:
    """Assumes that the given species_and_form is correct. Throws KeyError if not."""
    if fix(species_and_form) in species_and_forms:
        return species_and_forms[fix(species_and_form)]
    if fix(species_and_form).endswith("-random"):
        return BareMiniMon(fixed_dex[fix(species_and_form)[:-7]], form="random")
    if allow_name_only:
        return BareMiniMon(fixed_dex[fix(species_and_form)])


fixed_move_names = {fix(g): g for g in wiki_moves}


def read_url(url: str):
    return str(PyQuery(url, {'title': 'CSS', 'printable': 'yes'}))


img_link = "https://img.pokemondb.net/artwork/vector/{}.png"
dex_link = "https://pokemondb.net/pokedex/{}"
generation_bounds = [0, 151, 251, 386, 493, 649, 721, 809, 905, 1012]
game_generations = {
    "Red": 1, "Blue": 1, "Yellow": 1, "Gold": 2, "Silver": 2, "Crystal": 2, "Ruby": 3, "Sapphire": 3, "Emerald": 3,
    "FireRed": 3, "LeafGreen": 3, "Diamond": 4, "Pearl": 4, "Platinum": 4, "HeartGold": 4, "SoulSilver": 4,
    "Black": 5, "White": 5, "Black 2": 5, "White 2": 5, "X": 6, "Y": 6, "Omega Ruby": 6, "Alpha Sapphire": 6,
    "Sun": 7, "Moon": 7, "Ultra Sun": 7, "Ultra Moon": 7, "Sword": 8, "Shield": 8, "Brilliant Diamond": 8,
    "Shining Pearl": 8, "Scarlet": 9, "Violet": 9
}


def image(mon: BareMiniMon):
    if mon.form.name and mon.species.name != "Dudunsparce":
        if mon.species_and_form == "Minior-Core":
            suffix = "-" + random.choice(["orange", "yellow", "green", "blue", "indigo", "purple"]) + "-core"
        elif mon.species.name == "Maushold":
            suffix = {"Three": "-family3", "Four": "-family4"}[mon.form.name]
        elif mon.species_and_form == "Tinkaton-Ideal":
            return "https://cdn.discordapp.com/attachments/582754042527088694/1047738638454231162/tinkaton.png"
        else:
            suffix = "-" + fix(mon.form.name)
    else:
        suffix = ""
    if mon.generation == 9:
        return f"https://img.pokemondb.net/sprites/scarlet-violet/normal/{fix(mon.species.name) + suffix}.png"
    if mon.generation == 8:
        return f"https://img.pokemondb.net/artwork/large/{fix(mon.species.name) + suffix}.jpg"
    return img_link.format(fix(mon.species.name) + suffix)


def stat_change_text(mon: Mon, stat: str, change: int):
    """Creates the display text for a stat change - 'x sharply fell', etc."""
    ret = "{name}'s {stat} won't go any lower!" if change == -20 else \
        "{name}'s {stat} won't go any higher!" if change == 20 else \
        StatChange.modifier_strings[max(-3, min(3, change))]
    return ret.format(name=mon.name, stat=StatChange.stat_name_dict[stat])


exemplary_mons = {}
for sp in nat_dex.values():
    assert isinstance(sp, Species)
    if sp.name not in ["Arceus", "Silvally", "Meltan", "Melmetal"]:
        for form in sp.forms.values():
            exemplary_mons[frozenset([form.type1, form.type2])] = \
                exemplary_mons.get(frozenset([form.type1, form.type2]), []) + [f"{sp.name} {form.name}".strip()]


def add_new_mon(species: Species):
    nat_dex[species.name] = species
    fixed_dex[fix(species.name)] = species.name
    for fm in species.forms:
        mon = BareMiniMon(species.name, form=fm)
        species_and_forms[fix(mon.species_and_form)] = mon
    rewrite_mons()


def rewrite_mons():
    with open("pokemon/data/mons.json", "w") as f:
        json.dump({k: v.json for k, v in nat_dex.items()}, f, indent=4)


def rewrite_abilities():
    with open("pokemon/data/abilities.json", "w") as f:
        json.dump({k: legal_abilities[k] for k in sorted(list(legal_abilities))}, f, indent=4)


def find_mon(s: str | int | None, **kwargs) -> BareMiniMon | Mon:
    """Use **kwargs to pass additional arguments to the Mon.__init__() statement."""
    if kwargs.get("use_bare"):
        return_class = BareMiniMon
    else:
        return_class = Mon

    if isinstance(s, BareMiniMon):
        return s

    if can_int(s) or isinstance(s, int):
        if int(s) < 1 or int(s) > len(nat_dex):
            raise commands.CommandError(f"Use a dex number between 1 and {len(nat_dex)}.")
        return return_class(list(nat_dex.keys())[int(s) - 1], **kwargs)
    if s is None or s.lower() == "null":
        return return_class.null()

    if ret := species_and_forms.get(fix(s)):
        return return_class(ret.species.name, form=ret.form.name, **kwargs)

    for mon in nat_dex:
        if set(fix(mon).split("-")) <= set(fix(s).split("-")) or alpha_fix(mon) == alpha_fix(s):
            ret = mon
            break
    else:
        if fix(s) == "nidoran":
            ret = "Nidoran-F"
        else:
            if kwargs.get("fail_silently") or kwargs.get("return_on_fail"):
                return kwargs.get("return_on_fail", return_class.null())
            else:
                guess = best_guess(fix(s), list(fixed_dex))
                raise commands.CommandError(f"`{s}` not found. Did you mean {fixed_dex[guess]}?")

    other_info = "-".join(g for g in fix(s).split("-") if g not in fix(ret).split("-"))
    try:
        return return_class(ret, form=nat_dex[ret].get_form_name(other_info), **kwargs)
    except ValueError:
        return return_class(ret, **kwargs)


class CatchRate:
    def __init__(self, ball_type: str, mon: Mon, **kwargs):
        self.ball_type = ball_type
        self.mon = mon
        self.hp_percentage = kwargs.get("hp_percentage", kwargs.get("hp", 100))
        self.player_mon = kwargs.get("player_mon", Mon("Bulbasaur", gender="female"))
        self.is_dark_grass = kwargs.get("is_dark_grass", kwargs.get("grass", False))
        self.is_fishing = kwargs.get("is_fishing", kwargs.get("fishing", False))
        self.is_surfing = kwargs.get("is_surfing", kwargs.get("surfing", False))
        self.dex_caught = kwargs.get("dex_caught", kwargs.get("dex", 10))
        self.has_all_badges = kwargs.get("has_all_badges", kwargs.get("badges", True))
        self.caught_previously = kwargs.get("caught_previously", kwargs.get("repeat", False))
        self.turn = kwargs.get("turn", 1)
        self.is_night = kwargs.get("is_night", kwargs.get("dark", False))

    @property
    def multiplicative_ball_bonus(self):
        if self.ball_type == "great":
            return 1.5
        if self.ball_type == "ultra":
            return 2
        if self.ball_type == "level":
            return 8 if self.player_mon.level >= 4 * self.mon.level else \
                4 if self.player_mon.level >= 2 * self.mon.level else \
                2 if self.player_mon.level > self.mon.level else 1
        if self.ball_type == "lure":
            return 4 if self.is_fishing else 1
        if self.ball_type == "moon":
            return 4 if self.mon.species.name in [
                "Nidoran-F", "Nidorina", "Nidoqueen", "Nidoran-M", "Nidorino", "Nidoking", "Cleffa", "Clefairy",
                "Clefable", "Igglybuff", "Jigglypuff", "Wigglytuff", "Skitty", "Delcatty", "Munna", "Musharna"
            ] else 1
        if self.ball_type == "love":
            return 8 if (
                self.mon.species.name == self.player_mon.species.name and
                (
                    (self.mon.gender == "female" and self.player_mon.gender == "male") or
                    (self.mon.gender == "male" and self.player_mon.gender == "female")
                )
            ) else 1
        if self.ball_type == "fast":
            return 4 if self.mon.form.spe >= 100 else 1
        if self.ball_type == "net":
            return 3.5 if (bug in self.mon.types or water in self.mon.types) else 1
        if self.ball_type == "nest":
            return (floor((41 - self.mon.level) * 4096 / 10) / 4096) if self.mon.level < 30 else 1
        if self.ball_type == "repeat":
            return 3.5 if self.caught_previously else 3
        if self.ball_type == "timer":
            return min(4, 1 + (self.turn - 1) * 1229 / 4096)
        if self.ball_type == "dive":
            return 3.5 if (self.is_fishing or self.is_surfing) else 1
        if self.ball_type == "dusk":
            return 3 if self.is_night else 1
        if self.ball_type == "quick":
            return 5 if self.turn == 1 else 1
        if self.ball_type == "dream":
            return 4 if self.mon.status_condition == asleep else 1
        if self.ball_type == "beast":
            return 5 if self.mon.species.name in [
                "Nihilego", "Buzzwole", "Pheromosa", "Xurkitree", "Celesteela", "Kartana", "Guzzlord", "Poipole",
                "Naganadel", "Stakataka", "Blacephalon"
            ] else 410/4096
        return 1

    @property
    def additive_ball_bonus(self):
        if self.ball_type == "heavy":
            return -20 if self.mon.weight < 100 else 0 if self.mon.weight < 200 else \
                20 if self.mon.weight < 300 else 30
        return 1

    @property
    def dark_grass_modifier(self):
        if not self.is_dark_grass:
            return 1
        return 1229/4096 if self.dex_caught < 30 else 2048/4096 if self.dex_caught <= 150 else \
            2867/4096 if self.dex_caught <= 300 else 3277 if self.dex_caught <= 450 else \
            3686/4096 if self.dex_caught <= 600 else 1

    @property
    def status_bonus(self):
        return 2.5 if self.mon.status_condition in [asleep, frozen] else \
            1.5 if self.mon.status_condition is not None else 1

    @property
    def badge_modifier(self):
        return 410/4096 if (not self.has_all_badges) and (self.mon.level > self.player_mon.level) else 1

    @property
    def level_bonus(self):
        return max(1, (30 - self.mon.level) / 10)

    @property
    def a(self) -> int:
        return floor(
            (3 * self.mon.hp - 2 * (self.hp_percentage / 100 * self.mon.hp)) * self.dark_grass_modifier *
            max(1, min(255, self.mon.species.catch_rate + self.additive_ball_bonus))
            * self.multiplicative_ball_bonus / (3 * self.mon.hp) *
            self.status_bonus * self.badge_modifier * self.level_bonus
        )

    @property
    def shake_check_odds_out_of_65536(self) -> int:
        if self.ball_type in ["master", "park"]:
            return 65536
        return floor(65535 / (255 / self.a) ** 0.1875)

    @property
    def shake_check_chance(self) -> float:
        if self.ball_type in ["master", "park"]:
            return 1
        return floor(self.shake_check_odds_out_of_65536) / 65536

    @property
    def critical_capture_odds_out_of_256(self) -> int:
        multiplier = 2.5 if self.dex_caught > 600 else 2 if self.dex_caught > 450 else 1.5 if self.dex_caught > 300 \
            else 1 if self.dex_caught > 150 else 0.5 if self.dex_caught > 30 else 0
        return floor(self.a * multiplier / 6)

    @property
    def critical_capture_chance(self) -> float:
        return self.critical_capture_odds_out_of_256 / 256

    @property
    def capture_chance(self) -> float:
        return min(
            (self.critical_capture_chance * self.shake_check_chance) + \
            ((1 - self.critical_capture_chance) * self.shake_check_chance ** 4),
            1
        )

    def shake_check(self) -> bool:
        return random.randint(0, 65536) < self.shake_check_odds_out_of_65536

    def chance_after_throws(self, n: int) -> float:
        return 1 - (1 - self.capture_chance) ** n

    @property
    def throws_for_95_percent_capture(self) -> int:
        if self.capture_chance == 1:
            return 1
        return ceil(log(0.05, 1 - self.capture_chance))
