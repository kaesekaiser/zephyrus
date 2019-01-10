from game import *
from utilities import dice as di, weed as wd, timein as ti, translate as tr
from re import split, search
from math import atan2, sqrt, pi
import requests
import pinyin
import jyutping
from io import BytesIO
from random import choices
from unicodedata import name as uni_name


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
        "R": lambda n: n + 9 * 273.15 / 5 - 32,
    },
    "K": {
        "C": lambda n: n - 273.15,
        "F": lambda n: 9 * (n - 273.15) / 5 + 32,
        "R": lambda n: 9 * n / 5,
    },
    "R": {
        "C": lambda n: 5 * n / 9 - 273.15,
        "F": lambda n: n - 9 * 273.15 / 5 + 32,
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


@zeph.command(aliases=["weed"])
async def sayno(ctx: commands.Context):
    return await ClientEmol(":leaves:", hexcol("98e27c"), ctx).say(wd.sayno())


@zeph.command(aliases=["pick"])
async def choose(ctx: commands.Context, *, text: str):
    picks = split("\s+or\s+", text)
    string = choice(["I pick {}!", "Obviously it's {}.", "{}, of course.", "{}, obviously.", "Definitely {}."])
    return await chooseEmol.send(ctx, string.format(f"**{choice(picks)}**"))


@zeph.command(name="8ball")
async def eightball(ctx: commands.Context, *, text: str):
    if not text:
        raise commands.MissingRequiredArgument

    options = ["It is certain.", "As I see it, yes.", "Reply hazy, try again.", "Don't count on it.",
               "It is decidedly so.", "Most likely.", "Ask again later.", "My reply is no.",
               "Without a doubt.", "Outlook good.", "Better not tell you now.", "My sources say no.",
               "Yes - definitely.", "Yes.", "Cannot predict now.", "Outlook not so good.",
               "You may rely on it.", "Signs point to yes.", "Concentrate and ask again.", "Very doubtful."]
    return await chooseEmol.send(ctx, choice(options))


blankColor = rk.Image.open("utilities/color.png")


def rgb_to_hsv(r: int, g: int, b: int):
    return round(atan2(sqrt(3) * (g - b), 2 * r - g - b) * 360 / (2 * pi)) % 360,\
           round(100 - 100 * min(r, g, b) / 255),\
           round(100 * max(r, g, b) / 255)


@zeph.command(aliases=["colour"])
async def color(ctx: commands.Context, *, col: str):
    if col.casefold() == "random".casefold():
        ret = discord.Colour.from_rgb(randrange(256), randrange(256), randrange(256))
    else:
        try:
            if len(col.split()) == 3:
                ret = discord.Colour.from_rgb(*[int(g) for g in col.split()])
            else:
                ret = hexcol(col.strip("#"))
        except ValueError:
            raise commands.CommandError(f"Invalid color {col}.")
    if not 0 <= ret.value <= 16777215:
        raise commands.CommandError(f"Invalid color {col}.")
    emol = ClientEmol(zeph.emojis["color_wheel"], ret, ctx)
    rk.global_fill(blankColor, (255, 255, 255), ret.to_rgb())\
        .save(f"utilities/colors/{str(ret.r)[-1]}{str(ret.b)[-1]}.png")
    image = await image_url(f"utilities/colors/{str(ret.r)[-1]}{str(ret.b)[-1]}.png")
    return await emol.say(f"#{hex(ret.value)[2:].rjust(6, '0')}", thumb=image,
                          d=f"**RGB:** {ret.to_rgb()}\n**HSV:** {rgb_to_hsv(*ret.to_rgb())}")


@zeph.command(aliases=["hue"])
async def hueshift(ctx: commands.Context, url: str, shift: int):
    message = await ctx.send("processing...")
    img = rk.Image.open(BytesIO(requests.get(url).content))
    rk.shift_hue(img, shift).save("utilities/colors/hue-shift.png")
    await message.delete()
    return await ctx.send(file=discord.File("utilities/colors/hue-shift.png"))


@zeph.command()
async def invert(ctx: commands.Context, url: str):
    img = rk.Image.open(BytesIO(requests.get(url).content))
    rk.invert_colors(img).save("utilities/colors/invert.png")
    return await ctx.send(file=discord.File("utilities/colors/invert.png"))


@zeph.command()
async def timein(ctx: commands.Context, *, place: str):
    try:
        ret = ti.format_dict(ti.timein(place), False)
    except IndexError:
        raise commands.CommandError("Location not found.")
    except KeyError:
        raise commands.CommandError("Location too vague.")
    address = ", ".join(ti.getcity(place))
    if address == "Unable to precisely locate.":
        raise commands.CommandError("Location too vague.")
    emoji = ret.split()[0]
    emoji = f":clock{(int(emoji.split(':')[0]) + (1 if int(emoji.split(':')[1]) >= 45 else 0) - 1) % 12 + 1}" \
            f"{'30' if 15 <= int(emoji.split(':')[1]) < 45 else ''}:"
    return await ClientEmol(emoji, hexcol("b527e5"), ctx).say(ret, footer=address)


chinese_punctuation = {
    "？": "?", "！": "!", "。": ".", "，": ",", "：": ":", "；": ";", "【": "[", "】": "]", "（": "(", "）": ")",
    "《": "⟨", "》": "⟩", "、": ","
}


def get_pinyin(c: str):
    return f" {pinyin.get(c)}" if pinyin.get(c) != c else chinese_punctuation.get(c, "")


def get_jyutping(c: str):
    ret = jyutping.get(c)[0]
    if type(ret) == str:
        return f" {jyutping.get(c)[0]}"
    if type(ret) == list:
        return f" {jyutping.get(c)[0][0]}"
    return chinese_punctuation.get(c, "")


@zeph.command(name="pinyin")
async def pinyin_command(ctx: commands.Context, *, chinese: str):
    ret = "".join([get_pinyin(c) for c in chinese]).strip()
    if not ret:
        raise commands.CommandError("No Chinese text input.")
    return await zhong.send(ctx, ret)


@zeph.command(name="jyutping")
async def jyutping_command(ctx: commands.Context, *, cantonese: str):
    ret = "".join([get_jyutping(c) for c in cantonese]).strip()
    if not ret:
        raise commands.CommandError("No Chinese text input.")
    return await zhong.send(ctx, ret)


@zeph.command(aliases=["trans"])
async def translate(ctx: commands.Context, fro: str, to: str, *, text: str):
    trans = ClientEmol(":twisted_rightwards_arrows:", blue, ctx)
    if fro.lower() not in tr.LANGCODES and fro.lower() not in tr.LANGCODES.values() and fro.lower() not in tr.redirs:
        raise commands.CommandError(f"{fro} is not a valid language.")
    fro = tr.specify(fro.lower())
    if to is None:
        raise commands.CommandError("Please input a destination language.")
    if to.lower() not in tr.LANGCODES and to.lower() not in tr.LANGCODES.values() and to.lower() not in tr.redirs:
        raise commands.CommandError(f"{to} is not a valid language.")
    to = tr.specify(to.lower())
    if len(text) > 250:
        raise commands.CommandError("Text length is limited to 250 characters.")

    if fro == "auto":
        lang = tr.translator.detect(text).lang
    else:
        lang = fro

    translation = tr.translator.translate(text, to, fro)
    pron = translation.pronunciation if translation.pronunciation != translation.text and \
        translation.pronunciation is not None else ""
    return await trans.say(
        translation.text, d=pron,
        footer="{}{} -> {}".format("detected: " if fro == "auto" else "",
                                   tr.LANGUAGES[lang].title(), tr.LANGUAGES[to].title())
    )


async def get_translation(fro: str, to: str, text: str):
    """Turning this into a coroutine for use with badtranslate(). In previous versions, using non-coroutines would
    actually kill the bot, as it took too long to run all of the translation requests. Since coroutines are awaited,
    this should prevent this from happening."""
    return tr.Translator().translate(text, to, fro).text


@zeph.command(aliases=["badtrans"])
async def badtranslate(ctx: commands.Context, *, text: str):
    if len(text) > 250:
        raise commands.CommandError("Text length is limited to 250 characters.")
    bad = ClientEmol(":boom:", hexcol("DC5B00"), ctx)
    message = await bad.say("translating...")
    langs = ["en"] + choices(list(tr.LANGCODES), k=25)
    for i in range(25):
        text = await get_translation(langs[i], langs[i + 1], text)
        await bad.edit(message, "translating...", d=f"{i + 1}/25")
    return await bad.edit(message, await get_translation(langs[-1], "en", text))


@zeph.command()
async def avatar(ctx: commands.Context, user: User):
    return await ctx.send(
        embed=construct_embed(author=author_from_user(user, name=f"{user.display_name}'s Avatar", url=user.avatar_url),
                              color=user.colour, image=user.avatar_url)
    )


@zeph.command(aliases=["rune"])
async def runes(ctx: commands.Context, *, s: str):
    dic = {"ᛆ": "a", "ᛒ": "b", "ᛍ": "c", "ᛑ": "d", "ᚧ": "ð", "ᛂ": "e", "ᚠ": "f", "ᚵ": "g", "ᚼ": "h", "ᛁ": "i", "ᚴ": "k",
           "ᛚ": "l", "ᛘ": "m", "ᚿ": "n", "ᚮ": "o", "ᛔ": "p", "ᛕ": "p", "ᛩ": "q", "ᚱ": "r", "ᛌ": "s", "ᛋ": "s", "ᛐ": "t",
           "ᚢ": "u", "ᚡ": "v", "ᚥ": "w", "ᛪ": "x", "ᛦ": "y", "ᛎ": "z", "ᚦ": "þ", "ᛅ": "æ", "ᚯ": "ø"}

    return await ClientEmol(":flag_is:", hexcol("38009e"), ctx).say("".join([dic.get(g, g) for g in s]))


emojiCountries = {  # :flag_():
    "ac": "Ascension Island", "ad": "Andorra", "ae": "United Arab Emirates", "af": "Afghanistan",
    "ag": "Antigua and Barbuda", "ai": "Anguilla", "al": "Albania", "am": "Armenia", "ao": "Angola", "aq": "Antarctica",
    "ar": "Argentina", "as": "American Samoa", "at": "Austria", "au": "Australia", "aw": "Aruba", "ax": "Åland Islands",
    "az": "Azerbaijan", "ba": "Bosnia and Herzegovina", "bb": "Barbados", "bd": "Bangladesh", "be": "Belgium",
    "bf": "Burkina Faso", "bg": "Bulgaria", "bh": "Bahrain", "bi": "Burundi", "bj": "Benin", "bl": "St. Barthélemy",
    "bm": "Bermuda", "bn": "Brunei", "bo": "Bolivia", "bq": "Caribbean Netherlands", "br": "Brazil", "bs": "Bahamas",
    "bt": "Bhutan", "bv": "Bouvet Island", "bw": "Botswana", "by": "Belarus", "bz": "Belize", "ca": "Canada",
    "cc": "Cocos Islands", "cd": "Congo-Kinshasa", "cf": "Central African Republic", "cg": "Congo-Brazzaville",
    "ch": "Switzerland", "ci": "Côte d'Ivoire", "ck": "Cook Islands", "cl": "Chile", "cm": "Cameroon", "cn": "China",
    "co": "Colombia", "cp": "Clipperton Island", "cr": "Costa Rica", "cu": "Cuba", "cv": "Cape Verde", "cw": "Curaçao",
    "cx": "Christmas Island", "cy": "Cyprus", "cz": "Czechia", "de": "Germany", "dg": "Diego Garcia", "dj": "Djibouti",
    "dk": "Denmark", "dm": "Dominica", "do": "Dominican Republic", "dz": "Algeria", "ea": "Ceuta and Melilla",
    "ec": "Ecuador", "ee": "Estonia", "eg": "Egypt", "eh": "Western Sahara", "er": "Eritrea", "es": "Spain",
    "et": "Ethiopia", "eu": "European Union", "fi": "Finland", "fj": "Fiji", "fk": "Falkland Islands",
    "fm": "Micronesia", "fo": "Faroe Islands", "fr": "France", "ga": "Gabon", "gb": "United Kingdom", "gd": "Grenada",
    "ge": "Georgia", "gf": "French Guiana", "gg": "Guernsey", "gh": "Ghana", "gi": "Gibraltar", "gl": "Greenland",
    "gm": "Gambia", "gn": "Guinea", "gp": "Guadeloupe", "gq": "Equatorial Guinea", "gr": "Greece",
    "gs": "South Georgia and South Sandwich Islands", "gt": "Guatemala", "gu": "Guam", "gw": "Guinea-Bissau",
    "gy": "Guyana", "hk": "Hong Kong", "hm": "Heard and McDonald Islands", "hn": "Honduras", "hr": "Croatia",
    "ht": "Haiti", "hu": "Hungary", "ic": "Canary Islands", "id": "Indonesia", "ie": "Ireland", "il": "Israel",
    "im": "Isle of Man", "in": "India", "io": "British Indian Ocean Territory", "iq": "Iraq", "ir": "Iran",
    "is": "Iceland", "it": "Italy", "je": "Jersey", "jm": "Jamaica", "jo": "Jordan", "jp": "Japan", "ke": "Kenya",
    "kg": "Kyrgyzstan", "kh": "Cambodia", "ki": "Kiribati", "km": "Comoros", "kn": "St. Kitts and Nevis",
    "kp": "North Korea", "kr": "South Korea", "kw": "Kuwait", "ky": "Cayman Islands", "kz": "Kazakhstan", "la": "Laos",
    "lb": "Lebanon", "lc": "St. Lucia", "li": "Liechtenstein", "lk": "Sri Lanka", "lr": "Liberia", "ls": "Lesotho",
    "lt": "Lithuania", "lu": "Luxembourg", "lv": "Latvia", "ly": "Libya", "ma": "Morocco", "mc": "Monaco",
    "md": "Moldova", "me": "Montenegro", "mf": "Saint Martin", "mg": "Madagascar", "mh": "Marshall Islands",
    "mk": "Macedonia", "ml": "Mali", "mm": "Myanmar", "mn": "Mongolia", "mo": "Macau", "mp": "Northern Mariana Islands",
    "mq": "Martinique", "mr": "Mauritania", "ms": "Montserrat", "mt": "Malta", "mu": "Mauritius", "mv": "Maldives",
    "mw": "Malawi", "mx": "Mexico", "my": "Malaysia", "mz": "Mozambique", "na": "Namibia", "nc": "New Caledonia",
    "ne": "Niger", "nf": "Norfolk Island", "ng": "Nigeria", "ni": "Nicaragua", "nl": "Netherlands", "no": "Norway",
    "np": "Nepal", "nr": "Nauru", "nu": "Niue", "nz": "New Zealand", "om": "Oman", "pa": "Panama", "pe": "Peru",
    "pf": "French Polynesia", "pg": "Papua New Guinea", "ph": "Philippines", "pk": "Pakistan", "pl": "Poland",
    "pm": "St. Pierre and Miquelon", "pn": "Pitcairn Islands", "pr": "Puerto Rico", "ps": "Palestine", "pt": "Portugal",
    "pw": "Palau", "py": "Paraguay", "qa": "Qatar", "re": "Réunion", "ro": "Romania", "rs": "Serbia", "ru": "Russia",
    "rw": "Rwanda", "sa": "Saudi Arabia", "sb": "Solomon Islands", "sc": "Seychelles", "sd": "Sudan", "se": "Sweden",
    "sg": "Singapore", "sh": "St. Helena", "si": "Slovenia", "sj": "Svalbard and Jan Mayen", "sk": "Slovakia",
    "sl": "Sierra Leone", "sm": "San Marino", "sn": "Senegal", "so": "Somalia", "sr": "Suriname", "ss": "South Sudan",
    "st": "São Tomé and Príncipe", "sv": "El Salvador", "sx": "Sint Maarten", "sy": "Syria", "sz": "Swaziland",
    "ta": "Tristan da Cunha", "td": "Chad", "tf": "French Southern Territories", "tg": "Togo", "th": "Thailand",
    "tj": "Tajikistan", "tk": "Tokelau", "tl": "Timor-Leste", "tm": "Turkmenistan", "tn": "Tunisia", "to": "Tonga",
    "tr": "Turkey", "tt": "Trinidad and Tobago", "tv": "Tuvalu", "tw": "Taiwan", "tz": "Tanzania", "ua": "Ukraine",
    "ug": "Uganda", "um": "U.S. Outlying Islands", "un": "United Nations", "us": "United States", "uy": "Uruguay",
    "uz": "Uzbekistan", "va": "Vatican City", "vc": "St. Vincent and Grenadines", "ve": "Venezuela",
    "vg": "British Virgin Islands", "vi": "U.S. Virgin Islands", "vn": "Vietnam", "vu": "Vanuatu",
    "wf": "Wallis and Futuna", "ws": "Samoa", "xk": "Kosovo", "ye": "Yemen", "yt": "Mayotte", "za": "South Africa",
    "zm": "Zambia", "zw": "Zimbabwe"
}


async def interpret_potential_emoji(emote: str):
    try:
        uni_name(emote)
    except TypeError:
        try:
            emote.split(":")[2]
        except IndexError:
            if emote == chr(int("1f3f3", 16)) + "\ufe0f\u200d" + chr(int("1f308", 16)):
                name = "gay"
            elif emote == chr(int("1f3f4", 16)) + "\u200d\u2620\ufe0f":
                name = "pirates"
            elif emote in ["".join([chr(ord(c) + 127365) for c in g]) for g in emojiCountries]:
                name = emojiCountries["".join([chr(ord(c) - 127365) for c in emote])].lower()
            elif search(r"[🏻🏼🏽🏾🏿‍♂♀]+", emote) is not None:
                name = await interpret_potential_emoji("".join(split(r"[🏻🏼🏽🏾🏿‍♂♀]+", emote)))
            else:
                raise commands.CommandError("Only input one character.")
        else:
            if emote.split(":")[1] not in zeph.emojis:
                raise commands.CommandError("I don't have access to that emote.")
            else:
                name = emote.split(":")[1]
    except ValueError:
        raise commands.CommandError("Invalid character.")
    else:
        name = uni_name(emote)
    return name


@zeph.command()
async def sheriff(ctx: commands.Context, emote: str):
    name = await interpret_potential_emoji(emote)
    return await ctx.send("⠀ ⠀ ⠀  :cowboy:\n　   {0}\u2060{0}\u2060{0}\n    {0}   {0}　{0}\n"
                          "   :point_down:  {0} {0} :point_down:\n"
                          "  　  {0}　{0}\n　   {0}　 {0}\n　   :boot:     :boot:\nhowdy. {1}"
                          .format(emote, "the name's mccree" if ord(emote[0]) == int("1f55b", 16) else
                                  f"i'm the sheriff of {name.lower()}"))
