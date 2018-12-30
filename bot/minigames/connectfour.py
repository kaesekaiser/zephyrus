rightlet = [":regional_indicator_f:", "   |", ":regional_indicator_o:", "   |", ":regional_indicator_u:", "   |",
            ":regional_indicator_r:"]


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
        self.board = [[0 for j in range(6)] for g in range(7)]
        self.emoDict = {-1: yellow, 0: blank, 1: red, 2: white}
        self.top = top

    def str(self):
        return "\n".join([self.top if r == 0 else "".join([self.emoDict[self.board[c][6-r]] for c in range(7)])
                          for r in range(7)])

    def isfull(self, column):
        return False if self.board[column][5] == 0 else True

    def drop(self, column, team):
        self.board[column][self.board[column].index(0)] = team

    def victor(self):
        for g in self.groups:
            gen = [self.board[g[n][0]][g[n][1]] for n in range(4)]
            if gen.count(gen[0]) == 4 and 0 not in gen:
                vic = self.board[g[0][0]][g[0][1]]
                for j in g:
                    self.board[j[0]][j[1]] = 2
                return vic
        return False
