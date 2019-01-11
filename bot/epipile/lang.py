from random import choice, random, sample
from math import floor


def biased_rand(l: iter, n: float=2):  # biased towards low end of list
    r = random()
    return l[floor(r ** n * len(l))]


consonants = ["b", "b", "c", "c", "d", "d", "g", "g", "h", "h", "k", "k", "m", "m", "n", "n", "l", "p", "p", "q", "s",
              "t", "t", "v", "v", "x", "y", "z"]
vowels = ["a", "e", "i", "o", "u", "a", "e", "i", "o", "u", "a", "e", "i", "o", "u", "a", "e", "i", "o", "u",
          "A", "E", "I", "O", "U"]
sibilants = ["f", "s", ""]
liquids = ["j", "l", "r", "w", "", ""]
separators = ["", "", "'", "-"]
vowelOrthos = [
    {"A": "a", "E": "e", "I": "i", "O": "o", "U": "u"},
    {"A": "a", "E": "e", "I": "i", "O": "o", "U": "u"},
    {"A": "a", "E": "e", "I": "i", "O": "o", "U": "u"},
    {"A": "a", "E": "e", "I": "i", "O": "o", "U": "u"},
    {"A": "a", "E": "e", "I": "i", "O": "o", "U": "u"},
    {"A": "á", "E": "é", "I": "í", "O": "ó", "U": "ú"},
    {"A": "ä", "E": "ë", "I": "ï", "O": "ö", "U": "ü"},
    {"A": "â", "E": "ê", "I": "î", "O": "ô", "U": "û"},
    {"A": "aa", "E": "ee", "I": "ii", "O": "oo", "U": "uu"},
    {"A": "å", "E": "e", "I": "i", "O": "ø", "U": "u"}
]
syllables = [
    ["cs", "v", "ce"], ["cs", "v", "ce"], ["cs", "v", "ce"], ["cs", "v", "ce"], ["cs", "v", "ce"],
    ["cs", "v", "v", "ce"], ["cs", "v", "v", "ce"], ["cs", "v", "v", "ce"],
    ["cs", "v", "v"], ["cs", "v", "v"],
    ["cs", "v"], ["cs", "v"], ["cs", "v"], ["cs", "v"], ["cs", "v"],
    ["v", "ce"], ["v", "ce"], ["v", "ce"], ["v", "ce"],
    ["cs", "l", "v", "ce"], ["cs", "l", "v", "ce"],
    ["cs", "l", "v"], ["cs", "l", "v"],
    ["cs", "v", "l", "ce"], ["cs", "v", "l", "ce"],
    ["v"], ["v"], ["v"], ["v"],
    ["s", "cs", "v", "ce"], ["s", "cs", "v", "ce"],
    ["s", "cs", "v"], ["s", "cs", "v"],
    ["s", "l", "v"], ["s", "l", "v"],
    ["s", "l", "v", "ce"], ["s", "l", "v", "ce"]
]


def gen_word_structure():
    syls = [g + (["b"] if random() < 0.2 else []) for g in sample(syllables, choice([2, 2, 2, 2, 2, 2, 3, 4]))]
    return [g for item in syls for g in item]


class Language:
    def __init__(self):
        self.startConsonants = sample(consonants, choice([3, 3, 3, 3, 4]))
        self.endConsonants = sample(consonants, choice([3, 3, 3, 3, 4]))
        self.vowels = sample(vowels, choice([3, 3, 3, 3, 4]))
        self.separator = choice(separators)
        self.liquids = sample(liquids, choice([1, 1, 1, 1, 1, 1, 1, 2, 2, 3]))
        self.wordStructures = [gen_word_structure() for g in range(3)]
        self.sibilants = sample(sibilants, choice([1, 1, 1, 1, 2]))
        self.ortho = choice(vowelOrthos)

    def word(self):
        struct = biased_rand(self.wordStructures)
        dic = {"cs": self.startConsonants, "ce": self.endConsonants, "v": self.vowels, "l": self.liquids,
               "s": self.sibilants, "b": [self.separator]}
        inter = [biased_rand(dic[g]) for g in struct]
        if inter[-1] in separators:
            inter = inter[:-1]
        ret = [inter[0]]
        for i in range(1, len(inter)):
            if inter[i - 1].lower() != inter[i].lower():
                ret.append(inter[i])
        return "".join([self.ortho.get(g, g) for g in ret])

    def name(self):
        return f"{self.word().capitalize()} {self.word().capitalize()}" if random() < 0.2 else self.word().capitalize()


if __name__ == "__main__":
    lng = Language()
    print(" ".join([lng.word().title() for g in range(10)]))
