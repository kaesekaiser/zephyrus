from minigames.hangterms import *


class Hangman:
    def __init__(self, term: str):
        self.upterm = term
        self.term = self.upterm.lower()
        self.guessed = []
        self.miss = 0

    def guess(self, letter):
        self.guessed.append(letter.upper())
        if letter not in self.term:
            self.miss += 1
            return 0
        return self.term.count(letter)

    def blanks(self):
        return " ".join([c.upper() if c.upper() in self.guessed or c not in letters else "_" for c in str(self.term)])

    def revealed(self):
        return " ".join([c.upper() for c in self.term])
