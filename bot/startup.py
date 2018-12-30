import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot, Context
from random import randrange, random, choice
from datetime import date, timedelta, datetime
import platform
from minigames import connectfour as cf, poker as pk, yahtzee as yz, jotto as jo, hangman as hm, planes as pn,\
    uno as un, boggle as bg, casino as cs, risk as rk
from utilities import stocks as sk, weed as wd, wiki as wk, translate as tr, dict as dc, words as wr, timein as ti
from pokemon import walker as pm
from dnd import dungeongen as dg
from math import floor, ceil, log
from copy import deepcopy as copy
from time import time
from termcolor import colored
import atexit
import inspect
import os
with open("storage/vals.txt", "r") as ei:
    valdat = ei.readlines()
uservals = {l.split("|")[0]: float(l.split("|")[1]) for l in valdat}
client = Bot(description="A bot that does bot things", command_prefix="z!", pm_help=False, help_attrs={"name": "Шaf"})
startval = 10000
kaisid = "238390171022655489"
lets = "qwertyuiopasdfghjklzxcvbnm"
gamechannels = {}


class User:
    def __init__(self, no: str, bal: int=10000):
        self.id = int(no)
        self.bal = bal


def hexcol(hex_code: str):
    return discord.Colour(int(hex_code, 16))


def val(i: str):
    if i in uservals:
        return uservals[i]
    uservals[i] = startval
    rewritevals()
    return uservals[i]


def rewritevals():
    with open("storage/vals.txt", "w") as f:
        for i in list(uservals.keys()):
            f.write("{}|{}|\n".format(i, round(uservals[i], 2)))


def rewriteplanes():
    with open("storage/planes.txt", "w") as f:
        f.write("\n".join([str(g) for g in pn.users.values()]))


atexit.register(rewritevals)
atexit.register(print, "hi")


def addval(u, n):
    uservals[u.id] = round(uservals[u.id] + n, 2)
    rewritevals()


def commfloat(s):
    return float("".join([c for c in s if c != ","]))


def twodig(no):
    n = float(round(no, 2))
    return str(n) if len(str(n).split(".")[1]) > 1 else str(float(n)) + "0"


def getemoji(name: str, emoji_object: bool=False):
    try:
        ret = [g for g in client.get_all_emojis() if g.name == name and g.server in getattr(client, "fortServers")][0]
        return ret if emoji_object else str(ret)
    except IndexError:
        return getemoji("typeless")


def null_message():
    return discord.Message(reactions=[])


def null_context():
    return Context()


class IL:
    def __init__(self, o):
        self.self = o

    def __str__(self):
        return str(self.self)


class Author:
    def __init__(self, name, url=discord.Embed.Empty, icon=discord.Embed.Empty):
        self.name = name
        self.url = url
        self.icon = icon


# INLINE: IF TRUE, PUTS IN SAME LINE. IF FALSE, PUTS ON NEW LINE.
def conembed(**kwargs):
    title = kwargs.get("s", kwargs.get("title", discord.embeds.EmptyEmbed))
    desc = kwargs.get("d", kwargs.get("desc", discord.embeds.EmptyEmbed))
    color = kwargs.get("col", kwargs.get("color", discord.embeds.EmptyEmbed))
    fields = kwargs.get("fs", kwargs.get("fields"))
    ret = discord.Embed(title=title, description=desc, colour=color)
    if fields is not None:
        for i in list(fields.keys()):
            if len(str(fields[i])) != 0:
                ret.add_field(name=i, value=str(fields[i]),
                              inline=(False if type(fields[i]) == IL else
                                      kwargs.get("inline", kwargs.get("il", False))))
    if kwargs.get("footer") is not None:
        ret.set_footer(text=kwargs.get("footer"))
    if kwargs.get("thumb") is not None:
        ret.set_thumbnail(url=kwargs.get("thumb"))
    if kwargs.get("author") is not None:
        ret.set_author(name=kwargs.get("author").name, url=kwargs.get("author").url, icon_url=kwargs.get("author").icon)
    if kwargs.get("url") is not None:
        ret.url = kwargs.get("url")
    if kwargs.get("image") is not None:
        ret.set_image(url=kwargs.get("image"))
    return ret


def conemol(e: str, s: str, col: discord.Colour, **kwargs):
    return conembed(title=f"{e} \u2223 {s}", col=col, **kwargs)


async def emolsay(e: str, s: str, col: discord.Colour, **kwargs):
    return await client.say(embed=conemol(e, s, col, **kwargs))


def conerr(s, **kwargs):
    return conemol(":no_entry:", s, hexcol("880000"), **kwargs)


async def errsay(s, **kwargs):
    return await client.say(embed=conerr(s, **kwargs))


def consucc(s, **kwargs):
    return conemol(":white_check_mark:", s, hexcol("22bb00"), **kwargs)


async def succsay(s, **kwargs):
    return await client.say(embed=consucc(s, **kwargs))


async def yieldsay(s: str, **kwargs):
    return await emolsay(getemoji("yield"), s, hexcol("DD2E44"), **kwargs)


async def confirm(caller: discord.Member, prefix: str, say=yieldsay, yes: str='confirm', no: str='cancel',
                  timeout: int=60):
    message = await say(prefix, d=f"To {yes}, click {getemoji('yes')}. To {no}, click {getemoji('no')}.")
    await client.add_reaction(message, getemoji("yes", True))
    await client.add_reaction(message, getemoji("no", True))
    conf = await client.wait_for_reaction(timeout=timeout, message=message, user=caller,
                                          check=lambda c, u: c.emoji in [getemoji("yes", True), getemoji("no", True)])
    if conf is None:
        await say("Confirmation request timed out.")
        await client.delete_message(message)
        return False
    if conf.reaction.emoji == getemoji("yes", True):
        return True
    return False


async def delete_message(message: discord.Message):
    try:
        await asyncio.sleep(0.1)
        await client.delete_message(message)
    except discord.errors.HTTPException:
        pass


async def image_url(fp: str):
    return (await client.send_file(client.get_channel("528460450069872642"), fp)).attachments[0]["url"]


class Button:
    def __init__(self, emoji: str, func: callable, *args, **kwargs):
        self.emoji = emoji
        self.func = func
        self.args = args
        self.kwargs = kwargs

    async def run(self):
        return await self.func(*self.args, **self.kwargs)


class RefreshButton(Button):  # specifically refreshes some list. does nothing special except marks as a refresh
    def __init__(self, func: callable, *args, **kwargs):
        super().__init__("🔄", func, *args, **kwargs)


class Navigator:  # intended as a parent class
    def __init__(self, con: callable, l: list, per: int, s: str, **kwargs):
        self.conFunc = con
        self.table = l
        self.per = per
        self.page = 1
        self.pgs = ceil(len(self.table) / self.per)
        self.title = s
        self.message = null_message()
        self.kwargs = kwargs
        self.funcs = {}

    def legal(self):
        return ["◀", "▶"] + list(self.funcs.keys())

    def post_process(self):  # runs on page change!
        pass

    def con(self):
        return self.conFunc(self.title.format(page=self.page, pgs=self.pgs),
                            d=none_list(page_list(self.table, self.per, self.page), "\n"), **self.kwargs)

    async def run(self, caller: discord.Member):
        self.message = await client.say(embed=self.con())
        for button in self.legal():
            await client.add_reaction(self.message, button)
        while True:
            command = await client.wait_for_reaction(message=self.message, timeout=300, user=caller,
                                                     check=lambda c, u: c.emoji in self.legal())
            if command is None:
                return
            emoji = command.reaction.emoji
            if emoji in self.funcs:
                try:
                    await self.funcs[emoji]()
                except TypeError:
                    self.funcs[emoji]()
            try:
                self.page = (self.page + (-1 if emoji == "◀" else 1 if emoji == "▶" else 0) - 1) % self.pgs + 1
            except ZeroDivisionError:
                self.page = 1
            await client.edit_message(self.message, embed=self.con())  # no clue why pycharm doesn't like this. it works
            try:
                await client.remove_reaction(self.message, command.reaction.emoji, caller)
            except discord.errors.Forbidden:
                pass
            try:
                await self.post_process()
            except TypeError:
                self.post_process()


def get_dm(user: discord.Member):
    for i in client.private_channels:
        if user in i.recipients and len(i.recipients) == 2:
            return i


def best_guess(target: str, l: iter):
    di = {g: wr.levenshtein(target, g.lower()) for g in l}
    return choice([key for key in di if di[key] == min(list(di.values()))])


def lower(l: list):
    return [g.lower() for g in l]


def none_list(l: list, joiner: str=", "):
    return joiner.join(l) if len(l) > 0 else "none"


def plural(s: str, n: float, inter: str=""):
    return s if n == 1 else s + inter + "s"


def page_list(l: list, per: int, page: int):  # assumes page number is between 1 and total pages
    return l[int(page) * per - per:int(page) * per]


def beta():
    return client.user.id != "405190396684009472"


emojiCountries = {
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
planemojis = {**{"".join(emojiCountries[g].split()): g for g in emojiCountries}, "TimorLeste": "tl",
              "GuineaBissau": "gw", "IvoryCoast": "ci", "Bosnia": "ba", "DRCongo": "cd", "Congo": "cg", "SaoTome": "st",
              "USVirginIslands": "vi", "Curacao": "cw", "StLucia": "lc", "StKittsandNevis": "kn", "StVincent": "vc"}
yesDict = {True: "Yes", False: "No"}
