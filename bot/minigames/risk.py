from minigames.imaging import *
from math import log, ceil
from random import choice, randrange, sample


if __name__ == "__main__":
    directory = "C:/Users/Kaesekaiser/PycharmProjects/discobot/risk_dir/"
else:
    directory = "risk_dir/"


baseOrder = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
playerOrder = ["Red", "Blue", "Green", "Black"]
borders = {
    "Alaska": ["Kamchatka", "Yukon", "Alberta"],
    "Alberta": ["Alaska", "Yukon", "Ontario", "Montana"],
    "Appalachia": ["Quebec", "Ontario", "Montana", "Mexico"],
    "Argentina": ["Queensland", "Brazil", "Peru"],
    "Basque": ["Britain", "Germany", "Mediterranean", "Mali"],
    "Brazil": ["Colombia", "Peru", "Argentina", "Sahel"],
    "Britain": ["Iceland", "Scandinavia", "Germany", "Basque"],
    "China": ["Mongolia", "Tibet", "Siam", "Japan"],
    "Colombia": ["Mexico", "Peru", "Brazil"],
    "Congo": ["Sahel", "Sudan", "Kalahari"],
    "Egypt": ["Mali", "Sahel", "Sudan", "Mashriq", "Mediterranean"],
    "Germany": ["Scandinavia", "Britain", "Basque", "Mediterranean", "Russia"],
    "Greenland": ["Nunavut", "Quebec", "Iceland"],
    "Iceland": ["Greenland", "Scandinavia", "Britain"],
    "India": ["Mashriq", "Turkestan", "Tibet", "Siam"],
    "Indonesia": ["Siam", "Papua", "Outback"],
    "Irkutsk": ["Yakutsk", "Siberia", "Mongolia", "Kamchatka"],
    "Japan": ["Mongolia", "Kamchatka", "China"],
    "Kalahari": ["Madagascar", "Sudan", "Congo"],
    "Kamchatka": ["Yakutsk", "Irkutsk", "Mongolia", "Japan", "Alaska"],
    "Madagascar": ["Kalahari", "Sudan"],
    "Mali": ["Basque", "Mediterranean", "Egypt", "Sahel"],
    "Mashriq": ["Mediterranean", "Russia", "Turkestan", "India", "Sudan", "Egypt"],
    "Mediterranean": ["Basque", "Germany", "Russia", "Mashriq", "Egypt", "Mali"],
    "Mexico": ["Appalachia", "Montana", "Colombia"],
    "Mongolia": ["Kamchatka", "Irkutsk", "Siberia", "Tibet", "China", "Japan"],
    "Montana": ["Alberta", "Ontario", "Appalachia", "Mexico"],
    "Nunavut": ["Greenland", "Quebec", "Ontario", "Yukon"],
    "Ontario": ["Nunavut", "Yukon", "Alberta", "Montana", "Appalachia", "Quebec"],
    "Outback": ["Indonesia", "Papua", "Queensland"],
    "Papua": ["Indonesia", "Outback", "Queensland"],
    "Peru": ["Colombia", "Brazil", "Argentina"],
    "Quebec": ["Greenland", "Nunavut", "Ontario", "Appalachia"],
    "Queensland": ["Outback", "Papua", "Argentina"],
    "Russia": ["Scandinavia", "Germany", "Mediterranean", "Mashriq", "Turkestan", "Ural"],
    "Sahel": ["Mali", "Egypt", "Sudan", "Congo", "Brazil"],
    "Scandinavia": ["Iceland", "Britain", "Germany", "Russia"],
    "Siam": ["China", "Tibet", "India", "Indonesia"],
    "Siberia": ["Ural", "Turkestan", "Tibet", "Mongolia", "Irkutsk", "Yakutsk"],
    "Sudan": ["Mashriq", "Egypt", "Sahel", "Congo", "Kalahari", "Madagascar"],
    "Tibet": ["Siberia", "Mongolia", "China", "Siam", "India", "Turkestan"],
    "Turkestan": ["Russia", "Ural", "Siberia", "Tibet", "India", "Mashriq"],
    "Ural": ["Russia", "Turkestan", "Siberia"],
    "Yakutsk": ["Siberia", "Irkutsk", "Kamchatka"],
    "Yukon": ["Alaska", "Alberta", "Ontario", "Nunavut"],
}
colors = {
    "Red": (219, 106, 106),
    "Blue": (95, 169, 223),
    "Yellow": (223, 223, 95),
    "Black": (128, 128, 128),
    "Green": (121, 214, 134),
    "Purple": (186, 109, 218),
    None: (192, 192, 192)
}
imageCorners = {
    "Alaska": (66, 178),
    "Alberta": (218, 275),
    "Appalachia": (386, 354),
    "Argentina": (548, 730),
    "Basque": (900, 344),
    "Brazil": (560, 607),
    "Britain": (892, 289),
    "China": (1463, 403),
    "Colombia": (520, 570),
    "Congo": (994, 581),
    "Egypt": (994, 457),
    "Germany": (960, 299),
    "Greenland": (564, 37),
    "Iceland": (819, 225),
    "India": (1269, 423),
    "Indonesia": (1448, 601),
    "Irkutsk": (1452, 238),
    "Japan": (1628, 380),
    "Kalahari": (1007, 669),
    "Kamchatka": (1632, 166),
    "Madagascar": (1173, 703),
    "Mali": (855, 431),
    "Mashriq": (1084, 402),
    "Mediterranean": (979, 359),
    "Mexico": (331, 460),
    "Mongolia": (1421, 324),
    "Montana": (290, 356),
    "Nunavut": (282, 42),
    "Ontario": (377, 275),
    "Outback": (1541, 698),
    "Papua": (1640, 640),
    "Peru": (517, 639),
    "Quebec": (527, 257),
    "Queensland": (1660, 697),
    "Russia": (1054, 193),
    "Sahel": (855, 511),
    "Scandinavia": (972, 181),
    "Siam": (1422, 485),
    "Siberia": (1365, 113),
    "Sudan": (1062, 517),
    "Tibet": (1336, 358),
    "Turkestan": (1193, 311),
    "Ural": (1214, 158),
    "Yakutsk": (1503, 155),
    "Yukon": (204, 186)
}
province_centers = {
    "Alaska": (145, 231),
    "Alberta": (320, 312),
    "Appalachia": (469, 428),
    "Argentina": (603, 813),
    "Basque": (944, 394),
    "Brazil": (676, 694),
    "Britain": (935, 319),
    "China": (1532, 468),
    "Colombia": (572, 600),
    "Congo": (1062, 640),
    "Egypt": (1064, 491),
    "Germany": (1018, 339),
    "Greenland": (735, 129),
    "Iceland": (841, 268),
    "India": (1356, 504),
    "Indonesia": (1542, 637),
    "Irkutsk": (1544, 312),
    "Japan": (1674, 433),
    "Kalahari": (1071, 751),
    "Kamchatka": (1764, 228),
    "Madagascar": (1191, 740),
    "Mali": (930, 493),
    "Mashriq": (1173, 457),
    "Mediterranean": (1062, 383),
    "Mexico": (414, 525),
    "Mongolia": (1540, 378),
    "Montana": (352, 407),
    "Nunavut": (441, 234),
    "Ontario": (452, 324),
    "Outback": (1608, 769),
    "Papua": (1692, 667),
    "Peru": (580, 711),
    "Quebec": (578, 320),
    "Queensland": (1715, 782),
    "Russia": (1149, 304),
    "Sahel": (971, 576),
    "Scandinavia": (1025, 238),
    "Siam": (1481, 547),
    "Siberia": (1441, 242),
    "Sudan": (1141, 599),
    "Tibet": (1415, 430),
    "Turkestan": (1289, 377),
    "Ural": (1311, 266),
    "Yakutsk": (1596, 222),
    "Yukon": (278, 234)
}
images = {
    g: {
        j: global_fill(Image.open(directory + f"{g}.png"), colors["Red"], colors[j]) for j in colors
    } for g in borders
}
main_map = Image.open(directory + "nqr.png").convert("RGBA")
numbers = {
    g: Image.open(directory + f"{g}.png").convert("RGBA") for g in range(1, 33)
}
capitals = {
    g: Image.open(directory + f"capital{g}.png").convert("RGBA") for g in list(colors)[:6]
}


def dec(n: str, fro: int):
    for c in n:
        if c not in baseOrder[:fro]:
            raise IndexError(f"invalid base {fro} number {n}")
    n = "".join(list(reversed(n)))
    return sum([baseOrder.index(n[g]) * fro ** g for g in range(len(n))])


def d2b(n: int, length: int=0):
    return rebase(str(n), 10, 2).rjust(length, "0")


def rebase(n: str, fro: int, to: int):
    n = dec(n, fro)
    if not n:
        return "0"
    return "".join(reversed([baseOrder[(n % (to ** (g + 1))) // (to ** g)] for g in range(int(log(n + 0.5, to)) + 1)]))


def snip(s: str, n: int, from_back: bool=False):  # breaks string into n-long pieces
    if not from_back:
        return [s[n * m:n * (m + 1)] for m in range(ceil(len(s) / n))]
    else:
        return list(reversed([s[-n:]] + [s[-n * (m + 1):-n * m] for m in range(1, ceil(len(s) / n))]))


def back_cut(s: str, *dist: int):  # breaks string into pieces of varying length, starting from the back
    ret = [s]
    for n in dist:
        temp = ret[-1]
        ret[-1] = temp[-abs(n):]
        ret.append(temp[:-abs(n)])
    return ret  # the list is backwards; that is, the piece at the back of the string is at the front of the list


def random_bin(length: int):
    return "".join([choice(["0", "1"]) for g in range(length)])


def orders(n: int):
    possible = sorted([
        "-".join([p1, p2, p3, p4])
        for p1 in playerOrder[:4]
        for p2 in playerOrder[:4] if p2 not in [p1]
        for p3 in playerOrder[:4] if p3 not in [p1, p2]
        for p4 in playerOrder[:4] if p4 not in [p1, p2, p3]
    ])
    return [g.split("-") for g in sorted(list(set("-".join(j.split("-")[:n]) for j in possible)))]


class Province:
    def __init__(self, name: str, binary: str=None):
        self.name = name
        if binary is None:
            self.owner = None
            self.troops = 1
        else:
            self.owner = playerOrder[dec(binary[:2], 2)]
            self.troops = dec(binary[2:], 2) + 1

    def __str__(self):
        owner = d2b(playerOrder.index(self.owner), 2)
        troops = d2b(self.troops - 1, 5)
        return owner + troops

    def full_str(self):
        return f"Province of {self.name} | Owner: {self.owner} | Troops: {self.troops}"


class Board:
    def __init__(self, binary: str=None):
        if binary is None:
            self.provinces = {key: Province(key) for key in borders}
        else:
            binary = snip(binary, 7)
            self.provinces = {list(borders)[n]: Province(list(borders)[n], binary=binary[n])
                              for n in range(len(binary))}

    def __str__(self):
        return "".join([str(g) for g in self.provinces.values()])

    def full_str(self):
        return "\n".join([g.full_str() for g in self.provinces.values()])


class Player:
    def __init__(self, binary: str=None):
        if not binary:
            self.capital = None
        else:
            self.capital = list(borders)[dec(binary, 2)]

    def __str__(self):
        return d2b(list(borders).index(self.capital), 6)


class Game:
    def __init__(self, password: str=None):
        if not password:
            self.players = {g: Player(d2b(randrange(45))) for g in playerOrder[:6]}
            self.board = Board(random_bin(7 * 45))
            self.atBat = randrange(len(self.players))
            self.playerOrder = sample(list(self.players), len(self.players))
        else:
            password = back_cut(rebase(password, 62, 2), 3, 7 * 45, 3, 10)
            self.players = {playerOrder[g]: Player(snip(password[4], 6, True)[g])
                            for g in range(dec(password[0], 2))}
            self.board = Board(password[1])
            self.playerOrder = orders(len(self.players))[dec(password[3], 2)]
            self.atBat = dec(password[2], 2)
        self.capitals = {j.capital: g for g, j in self.players.items()}
        self.inverseCapitals = {j: g for g, j in self.capitals.items()}

    def __str__(self):
        return rebase(
            "".join([str(g) for g in self.players.values()]) +
            d2b(orders(len(self.players)).index(self.playerOrder), 10) +
            d2b(self.atBat, 3) +
            str(self.board) +
            d2b(len(self.players), 3), 2, 62
        )

    def full_str(self):
        return (
            f"Players: {len(self.players)}\n"
            f"Player Order: {self.playerOrder}\n"
            f"Player Capitals: {' | '.join([g + ': ' + j.capital for g, j in self.players.items()])}\n"
            f"At Bat: {self.playerOrder[self.atBat]}\n"
            f"BOARD:\n{self.board.full_str()}"
        )

    def print(self):
        base = Image.open(directory + "nqr.png")
        for province in self.board.provinces.values():
            if province.owner is not None:
                merge_down(
                    images[province.name][province.owner],
                    base,
                    *imageCorners[province.name]
                )
            if province.name in self.capitals:
                merge_down(
                    capitals[self.capitals[province.name]],
                    base,
                    *province_centers[province.name], True
                )
            merge_down(
                numbers[province.troops],
                base,
                *province_centers[province.name], True
            )
        return base


if __name__ == '__main__':
    game = Game()
    print(game.full_str())
    p = str(game)
    print(p)
    print(Game(p).full_str())
    print(str(Game(p)))
    print("\n" + str(game.full_str() == Game(p).full_str()))
