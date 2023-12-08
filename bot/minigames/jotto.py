class Jotto:
    def __init__(self, word: str):
        self.word = word
        self.list = [c for c in self.word.lower()]
        self.history = {}

    def guess(self, guess: str):
        lguess = [c for c in guess.lower()]
        ret = sum([self.list.count(lguess[i]) >= lguess[:i+1].count(lguess[i]) for i in range(len(lguess))])
        self.history[guess.lower()] = ret
        return ret
