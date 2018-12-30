from .events import *
from .lang import *
from random import randrange
traits = ["adaptable", "adventurous", "aloof", "analytical", "arrogant", "artistic", "avaricious", "anxious",
          "belligerent", "boisterous", "bold", "brusque", "clannish", "creative", "curious", "daring", "delicate",
          "devout", "diligent", "diminutive", "duplicitous", "elegant", "enduring", "enterprising", "enthusiastic",
          "fearful", "flamboyant", "gentle", "harmless", "honest", "honorable", "humble", "industrious", "intelligent",
          "kind", "loquacious", "meticulous", "moral", "nimble", "noble", "nomadic", "obsequious", "obsessive",
          "outgoing", "passionate", "passive", "playful", "polite", "possessive", "proud", "regretful", "reliable",
          "resilient", "sedentary", "serious", "solitary", "stoic", "studious", "sturdy", "subtle", "taciturn",
          "tenacious", "thrifty", "timid", "vengeful", "warlike", "wise"]
conquerors = ["Conqueror", "Great", "Magnificent", "Merciful", "Ruthless"]


class Civ:  # base class. does no actual action; ticking is covered by DiscordCiv class in discobot/epitaph.py
    def __init__(self):
        self.stardate = int(randrange(2000, 5000) * randrange(2000, 5000) / 2000)
        self.lastIntervention = self.stardate - 30
        self.birth = self.stardate
        self.language = Language()
        self.name = self.language.word().capitalize()
        self.beast = self.language.word()
        self.city = self.language.name()
        self.conqueror = self.language.name() + " the " + choice(conquerors)
        self.crop = self.language.word()
        self.fish = self.language.word()
        self.pet = self.language.word()
        self.planet = self.language.name()
        self.religion = self.language.word().capitalize()
        self.system = self.language.name()
        self.traits = sample(traits, 3)
        self.knowledge = []
        self.techChance = 1 / 90
        self.extinct = False
        self.victorious = False
        self.eventChances = {"asteroid": 1 / 1000,
                             "volcano": 1 / 1000,
                             "food-illness": 1 / 1000,
                             "gamma-ray-burst": 1 / 3000,
                             "pets": 1 / 1000}
        self.history = [f"History of the {self.name}", ""]

    def vocabize(self, s: str, **vocab: list):
        vocab = {"civ": self.name, "beast": self.beast, "city": self.city, "conqueror": self.conqueror,
                 "crop": self.crop, "fish": self.fish, "pet": self.pet, "planet": self.planet,
                 "religion": self.religion, "system": self.system, "stardate": self.stardate,
                 "trait1": self.traits[0], "trait2": self.traits[1], "trait3": self.traits[2],
                 **{g: choice(vocab[g]) for g in vocab}}
        while "{" in s:
            try:
                s = s.format(**vocab)
            except KeyError as key:
                raise KeyError(f"missing vocab {key}")
        return s

    def contact(self):  # initial text message
        return self.vocabize("We first became aware of the {civ} in {stardate}. They {reside} the {environment} planet "
                             "{planet} in the {system} system. They are {trait1}, {trait2}, and {trait3}.",
                             reside=["inhabit", "reside on"],
                             environment=["abundant", "arid", "barren", "chilly", "cold", "dry", "dusty", "frigid",
                                          "humid", "lush", "misty", "overgrown", "rainy", "rocky", "sparse", "steamy",
                                          "stormy", "temperate", "torrid", "verdant", "warm", "wet", "windy"])

    def available_events(self):
        return [g.name for g in events.values() if self.eventChances.get(g.name, 0) > 0 and
                set(g.prereqs) <= set(self.knowledge) and g.name not in self.knowledge]

    def available_techs(self):
        return [g.name for g in techs.values() if set(g.prereqs) <= set(self.knowledge)
                and g.name not in self.knowledge]


if __name__ == "__main__":
    for n in range(100):
        print(Civ().stardate)
