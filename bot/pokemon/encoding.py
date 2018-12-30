from pokemon.battle import *
from math import log


baseChars = {**{g: chr(g + 65) for g in range(26)}, **{g + 26: str(g) for g in range(10)},
             **{g + 36: chr(g + 97) for g in range(26)}, 62: "-", 63: "?"}
speciesNumbers = [*list(natDex.keys()), "Rattata Alolan", "Raticate Alolan", "Raichu Alolan", "Sandshrew Alolan",
                  "Sandslash Alolan", "Vulpix Alolan", "Ninetales Alolan", "Diglett Alolan", "Dugtrio Alolan",
                  "Meowth Alolan", "Persian Alolan", "Geodude Alolan", "Graveler Alolan", "Golem Alolan",
                  "Grimer Alolan", "Muk Alolan", "Exeggutor Alolan", "Marowak Alolan", "Kyogre Primal",
                  "Groudon Primal", "Deoxys Attack", "Deoxys Defense", "Deoxys Speed", "Wormadam Sandy",
                  "Wormadam Trash", "Rotom Heat", "Rotom Wash", "Rotom Frost", "Rotom Fan", "Rotom Mow",
                  "Giratina Origin", "Shaymin Sky", "Tornadus Therian", "Thundurus Therian", "Landorus Therian",
                  "Kyurem Black", "Kyurem White", "Meloetta Pirouette", "Greninja Ash", "Floette Eternal",
                  "Aegislash Shield", "Pumpkaboo Small", "Pumpkaboo Large", "Pumpkaboo Super", "Gourgeist Small",
                  "Gourgeist Large", "Gourgeist Super", "Zygarde 10%", "Zygarde Complete", "Hoopa Unbound",
                  "Oricorio Pom Pom", "Oricorio Pa'u", "Oricorio Sensu", "Lycanroc Dusk", "Lycanroc Midnight",
                  "Necrozma Dusk Mane", "Necrozma Dawn Wings", "Necrozma Ultra"]


def base(n: int, b: int):  # priority: capital letters, numbers, lowercase letters
    if n == 0:
        return "A"
    if b == 1:
        return "A" * n
    if b > len(baseChars) or b < 2:
        raise ValueError("invalid base")
    return "".join(reversed([baseChars[(n % (b ** (g + 1))) // (b ** g)] for g in range(int(log(n, b)) + 1)]))


def debase(n: str, b: int):  # required because of letter priority; int() will not work
    if n == "A":
        return 0
    if b == 1:
        return len(n)
    if b > len(baseChars) or b < 2:
        raise ValueError("invalid base")
    return sum([b ** g * {v: k for k, v in baseChars.items()}[n[-g - 1]] for g in range(len(n))])


def rebase(n: str, f: int, t: int):
    return base(debase(n, f), t)


def add_zeroes(s: str, n: int):
    return "A" * (n - len(s)) + s


def random_evs():
    ret = [0, 0, 0, 0, 0, 0]
    for i in range(510):
        while True:
            rand = randrange(6)
            if ret[rand] < 252:
                break
        ret[rand] += 1
    return ret


def code_len(n: int, b: int):  # digits required to encode n different values in base b
    return int(ceil(log(n, b)))


class Coder:
    def __init__(self, b: int):
        self.base = b
        self.speciesLen = code_len(len(speciesNumbers), self.base)
        # max value for EVs isn't actually 253 ** 6 - 1 because EVs are limited to 510 total
        self.evLen = code_len(252 * 253 ** 5 + 252 * 253 ** 4 + 6 * 253 ** 3 + 1, self.base)
        self.ivLen = code_len(32 ** 6, self.base)
        self.levLen = code_len(100, self.base)
        self.totalLen = self.speciesLen + self.evLen + self.ivLen + self.levLen

    def encode_iv(self, l: list):
        return add_zeroes(base(sum([32 ** g * l[g] for g in range(len(l))]), self.base), self.ivLen)

    def decode_iv(self, s: str):
        return [(debase(s, self.base) % (32 ** (g + 1))) // (32 ** g) for g in range(6)]

    def encode_ev(self, l: list):
        return add_zeroes(base(sum([253 ** g * l[g] for g in range(len(l))]), self.base), self.evLen)

    def decode_ev(self, s: str):
        return [(debase(s, self.base) % (253 ** (g + 1))) // (253 ** g) for g in range(6)]

    def encode_moves(self, d: dict):
        moveLen = code_len(len(movedict), 2)

        def encode_move(m: Move):
            return add_zeroes(base(list(movedict.keys()).index(m.name), 2), moveLen) + \
                add_zeroes(base(m.pp - m.ppc, 2), 7)

        fullLen = len(rebase(encode_move(getMove(list(movedict.keys())[-2], 64)) * 4, 2, self.base))
        return add_zeroes(rebase("".join([encode_move(g) for g in d.values()]), 2, self.base), fullLen)

    def encode_mon(self, m: Mon):
        species = base(speciesNumbers.index(m.de_get()), self.base)
        evs = self.encode_ev(m.evs)
        ivs = self.encode_iv(m.ivs)
        level = add_zeroes(base(m.level - 1, self.base), self.levLen)
        return rebase(species + evs + ivs + level, self.base, 64)

    def decode_mon(self, s: str):
        ret = add_zeroes(rebase(s, 64, self.base), self.totalLen)
        species, ret = ret[:self.speciesLen], ret[self.speciesLen:]
        evs, ret = ret[:self.evLen], ret[self.evLen:]
        ivs, ret = ret[:self.ivLen], ret[self.ivLen:]
        level, ret = ret[:self.levLen], ret[self.levLen:]
        return getMon(speciesNumbers[debase(species, self.base)], evs=self.decode_ev(evs),
                      ivs=self.decode_iv(ivs), level=debase(level, self.base) + 1)


def random_mon():
    return getMon(choice(speciesNumbers), evs=random_evs(), ivs=[randrange(31) for g in range(6)],
                  moves=sample(list(movedict.values()), 4), level=randrange(1, 101))


if __name__ == "__main__":
    c = Coder(14)
    m = random_mon()
    print(m)
    print(c.encode_mon(m))
    dm = c.decode_mon(c.encode_mon(m))
    print(dm)
    print(dm.evs == m.evs and dm.ivs == m.ivs)
    try:
        print(c.decode_mon("ThisCodeIsAHitmontop"))
    except IndexError:
        print("invalid mon code")
    # print(c.encode_mon(getMon(speciesNumbers[-1], evs=[252, 252, 6, 0, 0, 0], ivs=[31, 31, 31, 31, 31, 31])))
