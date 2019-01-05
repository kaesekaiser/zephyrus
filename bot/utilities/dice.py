from random import randrange
from re import findall, search


class BadString(Exception):
    pass


def roll_die(sides: int):
    if sides == -1:
        return randrange(3) - 1
    return randrange(sides) + 1


class Die:
    def __init__(self, s: str):
        if search("[^0-9d!+\-><=f%lh]", s.lower()):
            wrong = findall("[^0-9d!+\-><=f%lh]", s.lower())
            raise BadString(f"Invalid characters: ``{'``, ``'.join(wrong)}``")

        self.str = s.lower()

        if self.str.count("d") == 0:
            raise BadString("No die included.")
        if self.str.count("d") > 1:
            raise BadString("Only roll one set of dice at a time.")
        if self.str.index("d") == 0:
            self.count = 1
        else:
            self.count = int(self.str[:self.str.index("d")])

        if search("d%[^0-9]?", self.str):  # percent dice
            self.sides = 100
        elif search("df[^0-9]?", self.str):  # Fudge dice
            self.sides = -1
        elif search("d[0-9]+", self.str):  # regular dice
            self.sides = int(findall("(?<=d)[0-9]+", self.str)[0])
        else:
            raise BadString("Bad sides argument.")
        if self.sides == 0:
            raise BadString("Can't roll a zero-sided die.")
        if self.sides == 1:
            raise BadString("Can't roll a one-sided die.")

        if search("!", self.str):  # exploding!
            if self.sides == 0:
                raise BadString("Can't explode Fudge dice.")
            if search("!>[0-9]+", self.str):
                self.explode = lambda roll: roll > int(findall("(?<=!>)[0-9]+", self.str)[0])
                self.explodeString = f'!>{int(findall("(?<=!>)[0-9]+", self.str)[0])}'
                if self.explode(1):
                    raise BadString("Die would infinitely explode.")
            elif search("!<[0-9]+", self.str):
                self.explode = lambda roll: roll < int(findall("(?<=!<)[0-9]+", self.str)[0])
                self.explodeString = f'!<{int(findall("(?<=!<)[0-9]+", self.str)[0])}'
                if self.explode(self.sides):
                    raise BadString("Die would infinitely explode.")
            elif search("!=[0-9]+", self.str):
                self.explode = lambda roll: roll == int(findall("(?<=!=)[0-9]+", self.str)[0])
                self.explodeString = f'!={int(findall("(?<=!=)[0-9]+", self.str)[0])}'
            elif search("![0-9]+", self.str):
                self.explode = lambda roll: roll == int(findall("(?<=!)[0-9]+", self.str)[0])
                self.explodeString = f'!={int(findall("(?<=!)[0-9]+", self.str)[0])}'
            else:
                if self.sides == -1:
                    self.explode = lambda roll: roll == 1
                else:
                    self.explode = lambda roll: roll == self.sides
                self.explodeString = "!"
        else:
            self.explode = lambda roll: False
            self.explodeString = ""

        if search("-", self.str):  # dropping highest or lowest roll
            if search("-h", self.str):
                self.drop = "-H"
            elif search("-l", self.str):
                self.drop = "-L"
            else:
                raise BadString("Invalid ``-`` argument.")
        else:
            self.drop = ""
        if self.drop and self.count == 1:
            raise BadString("Can't drop the only die you roll.")

        if search("\+", self.str):  # adding n to total
            if search("\+[0-9]+\Z", self.str):
                self.add = int(findall("(?<=\+)[0-9]+\Z", self.str)[0])
            else:
                raise BadString("Invalid ``+`` argument. ``+`` must be at the end of a string.")
        else:
            self.add = 0

        self.addString = f"+{self.add}" if self.add else ""

    def __str__(self):
        return f"{self.count}d{self.sides if self.sides != -1 else 'F'}{self.explodeString}{self.drop}{self.addString}"

    def run(self):
        ret, str_ret = [], []
        for i in range(self.count):
            roll = roll_die(self.sides)
            while self.explode(roll):
                ret.append(roll)
                str_ret.append(f"{roll}!")
                roll = roll_die(self.sides)
            ret.append(roll)
            str_ret.append(str(roll))
        if self.drop == "-H":
            total = sum(sorted(ret)[:-1])
        elif self.drop == "-L":
            total = sum(sorted(ret)[1:])
        else:
            total = sum(ret)
        return f"[{', '.join(str_ret)}]{self.drop}{self.addString} = **{total + self.add}**"


if __name__ == "__main__":
    d = Die("d%-H!<100.")
    print(d)
    print(d.run())
