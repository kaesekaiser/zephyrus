from typing import Union
rightlet = [":regional_indicator_f:", "   |", ":regional_indicator_o:", "   |", ":regional_indicator_u:", "   |",
            ":regional_indicator_r:"]


class Column:
    def __init__(self):
        self.stack = [0, 0, 0, 0, 0, 0]

    def __getitem__(self, item: int):
        return self.stack[item]

    def __setitem__(self, key: int, value):
        self.stack[key] = value

    def drop(self, n: int):
        self.stack[self.stack.index(0)] = n

    @property
    def full(self):
        return 0 not in self.stack


class Board:
    groups = [[(c, r) for c in range(4)] for r in range(6)] +\
             [[(c + 1, r) for c in range(4)] for r in range(6)] +\
             [[(c + 2, r) for c in range(4)] for r in range(6)] +\
             [[(c + 3, r) for c in range(4)] for r in range(6)] +\
             [[(c, r) for r in range(4)] for c in range(7)] +\
             [[(c, r + 1) for r in range(4)] for c in range(7)] +\
             [[(c, r + 2) for r in range(4)] for c in range(7)] +\
             [[(c + n, n) for n in range(4)] for c in range(4)] +\
             [[(c + n, 1 + n) for n in range(4)] for c in range(4)] +\
             [[(c + n, 2 + n) for n in range(4)] for c in range(4)] +\
             [[(c + n, 5 - n) for n in range(4)] for c in range(4)] +\
             [[(c + n, 4 - n) for n in range(4)] for c in range(4)] +\
             [[(c + n, 3 - n) for n in range(4)] for c in range(4)]

    def __init__(self, blank: str, red: str, yellow: str, white: str, top: str):
        self.board = [Column() for g in range(7)]
        self.emoDict = {-1: yellow, 0: blank, 1: red, 2: white}
        self.top = top + "\n"

    def __getitem__(self, item: Union[tuple, list, int]):
        if type(item) == int:
            return self.board[item]
        return self.board[item[0]][item[1]]

    def __setitem__(self, key: Union[tuple, list], value):
        self.board[key[0]][key[1]] = value

    def __str__(self):
        return self.top + "\n".join(
            ["".join(
                [self.emoDict[2] if (c, 5-r) in self.win_pattern else self.emoDict[self[c, 5-r]] for c in range(7)]
            ) for r in range(6)]
        )

    def drop(self, column, team):
        self.board[column].drop(team)

    @property
    def full(self):
        return False not in [g.full for g in self.board]

    @property
    def win_pattern(self):
        for group in self.groups:
            gen = [self[g] for g in group]
            if gen.count(gen[0]) == 4 and 0 not in gen:
                return group
        return []

    @property
    def victor(self):
        try:
            return self[self.win_pattern[0]]
        except IndexError:
            return None
