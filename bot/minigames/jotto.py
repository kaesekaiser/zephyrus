class Jotto:
    def __init__(self, word):
        self.word = word
        self.lword = [c for c in self.word]
        self.history = {}

    def guess(self, guess):
        lguess = [c for c in guess.lower()]
        ret = round(sum([1 if self.lword.count(lguess[i]) >= lguess[:i+1].count(lguess[i])
                         else 0 for i in range(len(lguess))]))
        self.history[guess.lower()] = ret
        return ret
