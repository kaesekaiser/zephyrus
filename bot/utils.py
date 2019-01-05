from game import *
from utilities import dice as di


@zeph.command()
async def mock(ctx: commands.Context, *, text):
    def multi_count(s, chars):
        return sum([s.count(ch) for ch in chars])

    def dumb(s: str):
        return "".join([s[g].lower() if (g - multi_count(s[:g], (" ", "'", ".", "?", "!", "\""))) % 2 == 1
                        else s[g].upper() for g in range(len(s))])

    return await ctx.send(dumb(text))


@zeph.command()
async def expand(ctx: commands.Context, *, text):
    return await ctx.send(" ".join([c for c in text]))


def squarize(s: str, joiner=" "):
    noms = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    return joiner.join([chr(127462 - 97 + ord(g.lower())) if ord(g.lower()) in range(97, 123) else
                        ":{}:".format(noms[int(g)]) if ord(g) in range(48, 58) else
                        ":question:" if g == "?" else ":exclamation:" if g == "!" else g for g in s])


@zeph.command(aliases=["sq"])
async def square(ctx: commands.Context, *, text):
    return await ctx.send(squarize(text))


@zeph.command(aliases=["fsq"])
async def flagsquare(ctx: commands.Context, *, text):
    return await ctx.send(squarize(text, ""))


@zeph.command()
async def clap(ctx: commands.Context, *, text):
    return await ctx.send("👏" + "👏".join(text.split()))


@zeph.command()
async def ping(ctx: commands.Context):
    message = await ctx.send("fuck off")
    return await message.edit(
        content=f"fuck off ({round((message.created_at - ctx.message.created_at).microseconds / 1000)} ms)")


@zeph.command(aliases=["dice"])
async def roll(ctx: commands.Context, die: str="1d6"):
    dice = ClientEmol(":game_die:", hexcol("EA596E"), ctx)
    try:
        die = di.Die(die)
    except di.BadString as e:
        return await dice.say(str(e))
    else:
        return await dice.say(f"Rolling {die}...", d=die.run())


lowerAlphabet = "abcdefghijklmnopqrstuvwxyz"
smallAlphabet = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"


@zeph.command(aliases=["small"])
async def smallcaps(ctx: commands.Context, *, text: str):
    return await ctx.send(
        content="".join([smallAlphabet[lowerAlphabet.index(g)] if g in lowerAlphabet else g for g in text])
    )


class RIEmol(ClientEmol):  # regional indicator emol
    def __init__(self, letter: str, ctx: commands.Context):
        super().__init__(f":regional_indicator_{letter}:", blue, ctx)


def caesar_cipher(letter: str, n: int):
    if letter.lower() not in lowerAlphabet:
        return letter
    if letter.isupper():
        return caesar_cipher(letter.lower(), n).upper()
    return lowerAlphabet[(lowerAlphabet.index(letter) + n) % 26]


@zeph.command(aliases=["rot"])
async def caesar(ctx: commands.Context, n: int, *, text: str):
    return await RIEmol("r", ctx).say("".join([caesar_cipher(c, n) for c in text]))


@zeph.command()
async def rot13(ctx: commands.Context, *, text: str):
    return await RIEmol("r", ctx).say("".join([caesar_cipher(c, 13) for c in text]))


def vig(letter: str, *ks: str, reverse: bool=False):
    if letter.lower() not in lowerAlphabet:
        return letter
    if letter.isupper():
        return vig(letter.lower(), *ks, reverse=reverse).upper()
    mul = -1 if reverse else 1
    return lowerAlphabet[(lowerAlphabet.index(letter) + mul * sum([lowerAlphabet.index(g.lower()) for g in ks])) % 26]


@zeph.command(aliases=["vig"])
async def vigenere(ctx: commands.Context, text: str, *keys: str):
    return await RIEmol("v", ctx).say("".join(
        [vig(text[n], *(k[n % len(k)] for k in keys)) for n in range(len(text))]
    ))


@zeph.command(aliases=["devig"])
async def devigenere(ctx: commands.Context, text: str, *keys: str):
    return await RIEmol("v", ctx).say("".join(
        [vig(text[n], *(k[n % len(k)] for k in keys), reverse=True) for n in range(len(text))]
    ))


@zeph.command()
async def scramble(ctx: commands.Context, *text: str):
    return await ctx.send(content=" ".join(["".join(sample(g, len(g))) for g in text]))


def metric_dict(unit: str):
    met = {"Y": 1000000000000000000000000, "Z": 1000000000000000000000, "E": 1000000000000000000, "P": 1000000000000000,
           "T": 1000000000000, "G": 1000000000, "M": 1000000, "k": 1000, "h": 100, "da": 10, "": 1, "d": 0.1, "c": 0.01,
           "m": 0.001, "μ": 0.000001, "n": 0.000000001, "p": 0.000000000001, "f": 0.000000000000001,
           "a": 0.000000000000000001, "z": 0.000000000000000000001, "y": 0.000000000000000000000001}
    return {g + unit: j for g, j in met.items()}


def metric_name_dict(unit: str, abbreviation: str):
    met = {"yotta": "Y", "zetta": "Z", "exa": "E", "peta": "P", "tera": "T", "giga": "G", "mega": "M", "kilo": "k",
           "hecto": "h", "deca": "da", "deka": "da", "": "", "deci": "d", "centi": "c", "milli": "m", "micro": "μ",
           "nano": "n", "pico": "p", "femto": "f", "atto": "a", "zepto": "z", "yocto": "y"}
    return {g + unit: j + abbreviation for g, j in met.items()}


unitAbbreviations = {
    **metric_name_dict("meter", "m"),
    **metric_name_dict("metre", "m"),
    "inch": "in", "inches": "in", "foot": "ft", "feet": "ft", "yard": "yd", "mile": "mi", "fathom": "ftm",
    "astronomical unit": "AU",
    **metric_name_dict("gram", "g"),
    **metric_name_dict("gramme", "g"),
    "ounce": "oz", "pound": "lb", "stone": "st", "hundredweight": "cwt", "tonne": "Mg", "short ton": "ton",
    "metric ton": "Mg",
    "atomic mass unit": "amu",
    **metric_name_dict("dalton", "Da"),
    **metric_name_dict("liter", "L"),
    **metric_name_dict("litre", "l"),
    "teaspoon": "tsp", "tablespoon": "tbsp", "fluid ounce": "fl oz", "cup": "c", "pint": "pt", "quart": "qt",
    "gallon": "gal", "barrel": "bbl",
    "°C": "C", "celsius": "C", "centigrade": "C",
    "°F": "F", "fahrenheit": "F",
    "kelvin": "K",
    "°R": "R", "rankine": "R",
}


def add_degree(s: str):
    return s if s == "K" else "°" + s


class ConversionGroup:
    def __init__(self, *systems: dict, **inters: tuple):
        self.systems = systems
        self.allUnits = {j for g in systems for j in g}
        self.inters = inters
        for key, value in self.inters.items():
            [g for g in self.systems if key in g][0]["converter"] = key
            self.systems[0]["converter"] = value[1]

    def convert(self, n: Flint, fro: str, to: str=None):  # assumes both fro and to are in group
        if to == fro:
            return n
        fro_dict = [g for g in self.systems if fro in g][0]
        if to in fro_dict:
            return self.cws(n, fro, to, [g for g in self.systems if fro in g][0])
        if not to:
            to_dict = self.systems[not self.systems.index(fro_dict)]
            possible = {g: self.convert(n, fro, g)[1] for g in to_dict if g in defaultUnits}
            possible = dict(sorted(possible.items(), key=lambda g: max(g[1] / 3, 3 / g[1])))
            return list(possible)[0], possible[list(possible)[0]]
        to_dict = [g for g in self.systems if to in g][0]
        return to, self.cws(  # step 3: convert from system converter to desired unit
            self.cbs(  # step 2: convert between systems
                self.cws(  # step 1: convert to system converter
                    n, fro, fro_dict["converter"], fro_dict
                ), fro_dict["converter"], to_dict["converter"]
            ), to_dict["converter"], to, to_dict
        )

    def cbs(self, n: Flint, fro: str, to: str):  # convert between systems. uses metric as midpoint
        if to in self.systems[0]:
            return n * self.inters[fro][0]
        if fro in self.systems[0]:
            return n / self.inters[to][0]
        return self.cbs(self.cbs(n, fro, self.systems[0]["converter"]), self.systems[0]["converter"], to)

    @staticmethod
    def cws(n: Flint, fro: str, to: str, dic: dict):  # convert within system
        if dic[to] == dic[fro]:
            return n
        return n * dic[fro] / dic[to]


conversionTable = (  # groups of units of the same system
    ConversionGroup(  # length
        metric_dict("m"),
        {"in": 1, "ft": 12, "yd": 36, "mi": 12 * 5280, "ftm": 6 * 12},
        {"au": 1, "AU": 1, "ua": 1},
        **{"in": (0.0254, "m"), "au": (149597870700, "m")}  # only doing it this way because in= doesn't work
    ),
    ConversionGroup(  # mass
        metric_dict("g"),
        {"oz": 1, "lb": 16, "st": 16 * 14, "cwt": 1600, "ton": 32000, "long ton": 16 * 2240},
        {"amu": 1, "u": 1, **metric_dict("Da")},
        lb=(453.59237, "g"),
        amu=(1.660539040 * 10 ** -24, "g")
    ),
    ConversionGroup(  # volume
        {**metric_dict("L"), **metric_dict("l")},
        {"tsp": 1, "tbsp": 3, "fl oz": 6, "c": 48, "pt": 96, "qt": 192, "gal": 768,
         "bbl": 768 * 31.5, "hogshead": 768 * 63},
        tsp=(4.92892159375, "mL")
    ),
)
tempTable = {
    "C": {
        "F": lambda n: 9 * n / 5 + 32,
        "K": lambda n: n + 273.15,
        "R": lambda n: 9 * (n + 273.15) / 5,
    },
    "F": {
        "C": lambda n: 5 * (n - 32) / 9,
        "K": lambda n: 5 * (n - 32) / 9 + 273.15,
        "R": lambda n: n - 9 * 273.15 / 5,
    },
    "K": {
        "C": lambda n: n - 273.15,
        "F": lambda n: 9 * (n - 273.15) / 5 + 32,
        "R": lambda n: 9 * n / 5,
    },
    "R": {
        "C": lambda n: 5 * n / 9 - 273.15,
        "F": lambda n: n + 9 * 273.15 / 5,
        "K": lambda n: 5 * n / 9,
    }
}
flattenedConvTable = [j for g in conversionTable for j in g.allUnits] + list(tempTable)


defaultUnits = [  # units it's okay to default to if user doesn't give unit to which to convert
    "mm", "cm", "m", "km", "in", "ft", "mi", "mg", "g", "kg", "oz", "lb", "mL", "L", "ML", "tsp", "tbsp", "fl oz",
    "c", "pt", "qt", "gal"
]


def temp_convert(n: SigFig, fro: str, to: str=None):
    if not to:
        return temp_convert(n, fro, list(tempTable)[not list(tempTable).index(fro)])  # C to F; all else to C
    return to, tempTable[fro].get(to, lambda x: x)(n.n)


@zeph.command(aliases=["c", "conv"])
async def convert(ctx: commands.Context, n: str, *text):
    conv = ClientEmol(":straight_ruler:", hexcol("efc700"), ctx)
    n = SigFig(n)

    def find_abbr(s: str):
        s = "".join(s.split("."))
        if s[-1] == "s" and s[:-1].lower() in unitAbbreviations:
            return unitAbbreviations[s[:-1].lower()]
        if s in flattenedConvTable:
            return s
        if s.lower() in unitAbbreviations:
            return unitAbbreviations[s.lower()]
        raise commands.CommandError(f"Invalid unit ``{s}``.")

    if "to" in text:
        text = [find_abbr(g) for g in " ".join(text).split(" to ")]
    else:
        text = (find_abbr(" ".join(text)), )

    if text[0] in tempTable:
        try:
            ret = temp_convert(n, *text)
        except ValueError:
            raise commands.CommandError(f"Can't convert between {text[0]} and {text[1]}.")
        else:
            if temp_convert(n, text[0], "K")[1] < 0:
                raise commands.CommandError(f"{n} °{text[0]} is below absolute zero.")
            value = max(min(temp_convert(n, text[0], "F")[1], 120), 0) / 120
            temp = ClientEmol(":thermometer:", gradient("88C9F9", "DD2E44", value), ctx)
            return await temp.say(f"{round(SigFig(str(ret[1]), True), max(n.figs, 2))} {add_degree(ret[0])}",
                                  d=f"= {n} {add_degree(text[0])}")

    if n.n < 0:
        raise commands.CommandError(f"Can't have negative measurements.")

    try:
        group = [g for g in conversionTable if set(text) < g.allUnits][0]
    except IndexError:
        raise commands.CommandError(f"Can't convert between {text[0]} and {text[1]}.")

    ret = group.convert(n.n, *text)
    return await conv.say(f"{add_commas(round(SigFig(str(ret[1]), True), max(n.figs, 3)))} {ret[0]}",
                          d=f"= {n} {text[0]}")
