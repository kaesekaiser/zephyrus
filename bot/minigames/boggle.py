from random import choice, sample
adj = -5, -4, -3, -1, 1, 3, 4, 5


def score(word: str):
    return 1 if len(word) < 5 else 2 if len(word) == 5 else 3 if len(word) == 6 else 5 if len(word) == 7\
        else 11


class Board:
    dice = ["LRNNZH", "EGHWEN", "SESITO", "TOWATO", "JOBABO", "RLYDEV", "DITTYS", "QUINHW",
            "SUINEE", "COITUM", "FASPFK", "NEAGEA", "VWTHER", "DIXELR", "PASHCO", "TLRYET"]

    def __init__(self):
        self.board = [choice([c for c in sample(self.dice, 16)[g]]) for g in range(16)]
        self.guessed = []
        self.points = 0

    def __str__(self):
        return "| " + ("|\n| ".join(
            [" ".join(
                ["Qu" if j == "Q" else (j + " ") for j in self.board[4 * g:4 * g + 4]]
            ) for g in range(4)]
        )) + "|"

    def guess(self, word):  # assumes word can be formed
        self.guessed.append(word)
        self.points += score(word)

    def adjs(self, index):
        ret = {}
        for a in adj:
            if index + a in range(16) and \
                    ((index + a) // 4 == index // 4 or a not in (-1, 1)) and \
                    ((index + a) // 4 == index // 4 - 1 or a not in (-5, -4, -3)) and \
                    ((index + a) // 4 == index // 4 + 1 or a not in (5, 4, 3)):
                ret[a] = self.board[index + a]
        return ret

    def find(self, word):
        word = "Q".join(word.lower().split("qu")).upper()
        if word.upper()[0] not in self.board:
            return False
        starts = [g for g in range(16) if self.board[g] == word.upper()[0]]
        for s in starts:
            if self.path(word, s, [s]):
                return True
        return False

    def path(self, word, index, used):
        if len(word) == 1:
            return True
        if word[1] not in self.adjs(index).values():
            return False
        tests = [(g + index) for g in self.adjs(index) if (g + index) not in used and self.board[g + index] == word[1]]
        if len(tests) == 0:
            return False
        for g in tests:
            if self.path(word[1:], g, [*used, g]):
                return True
        return False


if __name__ == "__main__":
    b = Board()
    while True:
        print(b)
        print(b.find(input()))
