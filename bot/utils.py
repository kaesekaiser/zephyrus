from game import *
from random import choice
from unicodedata import name as uni_name
from re import split as reg_split, search as reg_search
import jyutping as jp
import pinyin as yn


@client.command()
async def mock(*args):
    def dumb(s):
        def multicount(s, chars):
            return sum([s.count(ch) for ch in chars])
        return "".join([s[g].lower() if (g - multicount(s[:g], (" ", "'", ".", "?", "!", "\""))) % 2 == 1
                        else s[g].upper() for g in range(len(s))])
    await client.say(dumb(" ".join(args)))


@client.command()
async def expand(*args):
    return await client.say(" ".join([c for c in " ".join(args)]))


def squarize(s, j=" "):
    noms = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    return j.join([chr(127462 - 97 + ord(g.lower())) if ord(g.lower()) in range(97, 123) else
                   ":{}:".format(noms[int(g)]) if ord(g) in range(48, 58) else
                   ":question:" if g == "?" else ":exclamation:" if g == "!" else g for g in s])


@client.command(aliases=["sq"])
async def square(*args):
    await client.say(squarize(" ".join(args)))


@client.command()
async def clap(*args):
    await client.say(":clap:" + ":clap:".join(args))


@client.command()
async def flagsquare(*args):
    await client.say(squarize(" ".join(args), ""))


@client.command(pass_context=True)
async def ping(ctx: Context):
    message = await client.say("fuck off")
    return await client.edit_message(
        message, f"fuck off ({round((message.timestamp - ctx.message.timestamp).microseconds / 1000)} ms)")


@client.command()
async def say(*args):
    await client.say(" ".join(args))


@client.command(aliases=["dice"])
async def roll(dice: str):
    n, s = 1 if dice[0] == "d" else int(dice.split("d")[0]), int(dice.split("d")[1])
    score = [randrange(s) + 1 for g in range(n)]
    tot, rat = round(sum(score)), round(sum(score) / (n * s), 5)
    col = 256 * round(200 if rat >= 0.5 else 400 * rat) + 256 * 256 * round(200 if rat <= 0.5 else 400 * (1 - rat))
    try:
        await emolsay(":game_die:", "Result: **{}**".format(tot), discord.Colour(col), d="Rolls: {}".format(score))
    except discord.HTTPException:
        await errsay("Too many dice.")


def tempconv(deg: float, unit: str):
    ret = [round(9 * deg / 5 + 32), "° F"] if unit.lower() == "c" else\
          [round(5 * (deg - 32) / 9), "° C"]
    return [":thermometer:"] + ret


def lenconv(meas: float, unit: str):
    ret = [round(2.54 * meas, 1), " cm"] if unit.lower() == "in" else\
          [round(meas / 2.54, 1), " in"] if unit.lower() == "cm" else\
          [round(0.3048 * meas, 2), " m"] if unit.lower() == "ft" else\
          [f"{floor(3.2808 * meas)} ft {round(12 * ((3.2808 * meas) % 1))} in", ""] if unit.lower() == "m" else\
          [round(1.6093 * meas, 2), " km"] if unit.lower() == "mi" else\
          [round(meas / 1.6093, 2), " mi"]
    return [":straight_ruler:"] + ret


def weightconv(meas: float, unit: str):
    ret = [round(28.3495 * meas), " g"] if unit.lower() == "oz" else\
          [round(meas / 28.3495, 1), " oz"] if unit.lower() == "g" else\
          [round(0.4536 * meas, 2), " kg"] if unit.lower() == "lb" else \
          ["{} lb {} oz".format(floor(2.2046 * meas), round(16 * ((3.2808 * meas) % 1))), ""]
    return [":scales:"] + ret


def areaconv(meas: float, unit: str):
    ret = [round(0.092903 * meas, 2), " m2"] if unit.lower() == "ft2" else\
          [round(meas / 0.092903), " ft2"] if unit.lower() == "m2" else\
          [round(2.58999 * meas, 1), " km2"] if unit.lower() == "mi2" else\
          [round(meas / 2.58999, 1), " mi2"]
    return [":triangular_ruler:"] + ret


@client.command(aliases=["c"])
async def conv(meas: float, unit: str):
    if unit.lower() not in ["c", "cm", "m", "km", "g", "kg", "f", "in", "ft", "mi", "oz", "lb",
                            "ft2", "m2", "mi2", "km2"]:
        return await errsay("Unrecognized unit.")
    v = tempconv(meas, unit) if unit.lower() in ["c", "f"] else\
        lenconv(meas, unit) if unit.lower() in ["cm", "m", "km", "in", "ft", "mi"] else\
        weightconv(meas, unit) if unit.lower() in ["g", "kg", "oz", "lb"] else\
        areaconv(meas, unit) if unit.lower() in ["ft2", "m2", "mi2", "km2"] else []
    return await emolsay(v[0], "{}{}".format(v[1], v[2]), hexcol("efc700"))


@client.command(aliases=["weed"])
async def sayno():
    await emolsay(":leaves:", wd.sayno(), hexcol("98e27c"))


async def wikisay(s, **kwargs):
    await emolsay(":globe_with_meridians:", s, hexcol("4100b5"), **kwargs)


@client.command()
async def randomwiki():
    wik = wk.WikiParser()
    wik.feed(wk.readurl(wk.wikilink.format("Special:Random")))
    return await wikisay(wik.title, d=wik.desc, url=wk.wikilink.format("_".join(wik.title.split(" "))))


@client.command(aliases=["fw"])
async def foreignwiki(language: str, *args):
    if len(args) == 0:
        return await errsay("Please input a title.")

    fp = wk.ForeignParser()
    try:
        fp.feed(wk.readurl(wk.wikilink.format("_".join(args))))
    except wk.HTTPError:
        return await errsay("Article not found in English.")

    if language.lower() == "all":
        try:
            return await wikisay(f"Foreign versions of {fp.title}",
                                 d=", ".join([f"{fp.redirects[g]} *({g})*" for g in fp.redirects]))
        except discord.errors.HTTPException:
            return await wikisay("there's literally too many to put in one message")

    if language.lower() == "multi":
        langs = "it", "scn", "nap", "vec", "sc", "lij", "pms", "lmo"
        return await wikisay(f"Foreign titles of {fp.title}",
                             d="\n".join([f"**{fp.redirects.get(g)}** - {fp.languages.get(fp.redirects.get(g))}"
                                          for g in langs if g in fp.redirects]))

    if language.lower() == "zhong":
        if "zh" not in fp.redirects:
            return await wikisay("Article not found in Mandarin.")
        man = f"**Mandarin** - {fp.languages['Chinese']} _({yn.get(fp.languages['Chinese'])})_"
        if "zh-yue" in fp.redirects:
            can = f"**Cantonese** - {fp.languages['Cantonese']} _({' '.join(jp.get(fp.languages['Cantonese']))})_"
        else:
            can = f"***Cantonese*** - _{' '.join(jp.get(fp.languages['Chinese']))}_"
        return await wikisay(f"Chinese titles of {fp.title}", d=man + "\n" + can)

    jyu = language.lower() in ["jyutping", "jyut"]
    language = "zh-yue" if jyu else language
    pin = language.lower() in ["pinyin", "pin"]
    language = "zh" if pin else language
    if language.title() not in fp.languages and language.lower() not in fp.redirects:
        return await wikisay("Article not found in that language.")
    language = fp.redirects.get(language.lower(), language.title())
    if jyu:
        return await wikisay(" ".join(jp.get(fp.languages[language])), url=fp.links[language])
    if pin:
        return await wikisay(yn.get(fp.languages[language]), url=fp.links[language])
    return await wikisay(fp.languages[language], url=fp.links[language])


@client.command()
async def wiki(*args):
    if len(args) == 0:
        return await errsay("Please input a title.")

    wik = wk.WikiParser()
    try:
        wik.feed(wk.readurl(wk.wikilink.format("_".join(args))))
    except wk.HTTPError:
        return await errsay("Article not found.")
    return await wikisay(wik.title, d=wik.desc, url=wk.wikilink.format("_".join(wik.title.split(" "))))


@client.command(aliases=["trans"])
async def translate(fro: str=None, to: str=None, *args):
    async def transay(s, **kwargs):
        await emolsay(":twisted_rightwards_arrows:", s, hexcol("5177ca"), **kwargs)

    return await transay("z!translate has been deprecated until further notice.",
                         d="the API I was using to cheat the system no longer works")

'''if fro.lower() not in tr.LANGCODES and fro.lower() not in tr.LANGCODES.values() and fro.lower() not in tr.redirs:
        return await errsay(f"{fro} is not a valid language.")
    fro = tr.specify(fro.lower())
    if to is None:
        return await errsay("Please input a destination language.")
    if to.lower() not in tr.LANGCODES and to.lower() not in tr.LANGCODES.values() and to.lower() not in tr.redirs:
        return await errsay(f"{to} is not a valid language.")
    to = tr.specify(to.lower())
    if len(args) == 0:
        return await errsay("No translation text given.")
    s = " ".join(args)
    if len(s) > 250:
        return await errsay("Text length is limited to 250 characters.")

    if fro == "auto":
        lang = tr.translator.detect(s).lang
    else:
        lang = fro

    trans = tr.translator.translate(s, to, fro)
    pron = (trans.pronunciation + "\n") if trans.pronunciation != trans.text and trans.pronunciation is not None else ""
    return await transay(trans.text, d=pron +
                         "*{}{} -> {}*".format("detected: " if fro == "auto" else "",
                                               tr.LANGUAGES[lang], tr.LANGUAGES[to]))'''


'''@client.command(pass_context=True, aliases=["badtrans"])
async def badtranslate(ctx, *args):
    async def badtransay(s, footer=None):
        await emolsay(":boom:", s, hexcol("DC5B00"), footer=footer)

    text, oldlang = " ".join(args), "en"
    origtext = text
    if len(args) == 0:
        return await errsay("Please input text to translate.")
    if len(text) > 250:
        return await errsay("Text can only be up to 250 characters long.")
    await badtransay("Translating...", "please wait until after this process is completed to issue further commands")

    for i in range(30):
        lang = choice(list(tr.LANGUAGES.keys()))
        text = tr.Translator().translate(text, lang, oldlang).text
        oldlang = lang

    text = tr.Translator().translate(text, "en", oldlang).text
    return await badtransay(text, "from: {}".format(origtext))'''


async def getdef(word):
    dic = dc.DictParser()
    try:
        dic.feed(dc.readurl(dc.deflink.format(word.lower())))
    except dc.HTTPError:
        return await errsay("Word not found.")
    else:
        if len(dic.definition) < 3:
            return await errsay("Word not found.")
        else:
            return await emolsay(":book:", dic.word, hexcol("3a589e"),
                                 d="_{}._ {}".format(dic.part, dic.definition))


@client.command(aliases=["def", "dict", "dictionary"])
async def define(*args):
    if len(args) == 0:
        return await errsay("Please input a word.")
    return await getdef("%20".join(args))


@client.command()
async def charcount(*args):
    return await emolsay(":straight_ruler:", "{} characters".format(len(" ".join(args))), hexcol("efc700"))


@client.command()
async def timein(*args):
    try:
        ret = ti.format_dict(ti.timein(" ".join(args)), False)
    except IndexError:
        return await errsay("Place not found.")
    except KeyError:
        return await errsay("Location too vague.")
    address = ", ".join(ti.getcity(" ".join(args)))
    if address == "Unable to precisely locate.":
        return await errsay("Location too vague.")
    emoji = ret.split()[0]
    emoji = f":clock{(int(emoji.split(':')[0]) + (1 if int(emoji.split(':')[1]) >= 45 else 0) - 1) % 12 + 1}" \
            f"{'30' if 15 <= int(emoji.split(':')[1]) < 45 else ''}:"
    return await emolsay(emoji, ret, hexcol("b527e5"), footer=address)


@client.command()
async def weather(*args):
    try:
        wet = ti.weather(" ".join(args))
    except ValueError:
        return await errsay("Weather data not available.")
    except IndexError:
        return await errsay("Place not found.")
    ll = ti.getlatlong(" ".join(args))
    long = round(ll["lng"], 2)
    emoji = ":earth_americas:" if -170 <= long < -30 else ":earth_africa:" if -30 <= long < 65 else ":earth_asia:"
    await emolsay(emoji, f"It is {wet.weather['temp']}°F and {wet.weather['phrase']} in {', '.join(wet.locale)}.",
                  hexcol("5c913b"), footer=f"Updated at {wet.weather['time']}.")


@client.command()
async def wordpath(*args):
    args = [arg.lower() for arg in args]
    ret = [args[0].upper()]
    for i in range(len(args) - 1):
        ret.extend(wr.fullpath(args[i], args[i + 1]))
    await emolsay(":recycle:", " -> ".join(args), hexcol("77b255"), d="```ml\n{}```".format("\n".join(ret)))


@client.command()
async def drivetime(*args):
    async def drivesay(s, **kwargs):
        await emolsay(":red_car:", s, hexcol("dd2e44"), **kwargs)

    if len(args) == 0:
        return await errsay("Specify a starting point and destination.")

    args = [arg.lower() for arg in args]
    if "to" not in args:
        if args[0] != "help":
            return await errsay("Specify a destination.")
        return await drivesay("HELP", d="``z!drivetime`` uses the Google Directions API to find the estimated driving "
                                        "time between two locations. To use it, call ``z!drivetime``, followed by your "
                                        "starting point, then the word \"to,\" then your destination.\n\n"
                                        "    *e.g.* ``z!drivetime Berlin to Paris``\n"
                                        "    *e.g.* ``z!drivetime 1600 Pennsylvania Avenue, Washington, DC to "
                                        "350 Fifth Avenue, New York, NY``")
    if args.count("to") > 1:
        return await errsay("Too many destinations.")
    origin = " ".join(args[:args.index("to")])
    destination = " ".join(args[args.index("to") + 1:])
    if origin == "":
        return await errsay("Specify a starting point.")
    if destination == "":
        return await errsay("Specify a destination.")
    try:
        d = ti.directions(origin, destination, units="imperial", departure_time=ti.datetime.now())
    except IndexError:
        return await drivesay("Could not determine driving time.")
    else:
        try:
            return await drivesay(f"{d['duration_in_traffic']['text']} ({d['distance']['text']})",
                                  d=f"{', '.join(ti.getcity(origin))} -> {', '.join(ti.getcity(destination))}",)
        except KeyError:
            try:
                return await drivesay(f"{d['duration']['text']} ({d['distance']['text']})",
                                      d=f"{', '.join(ti.getcity(origin))} -> {', '.join(ti.getcity(destination))}", )
            except KeyError as error:
                print(f"KeyError: {error}\n{d}")
                return await drivesay("Could not determine driving time.")


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
            elif reg_search(r"[🏻🏼🏽🏾🏿‍♂♀]+", emote) is not None:
                name = await interpret_potential_emoji("".join(reg_split(r"[🏻🏼🏽🏾🏿‍♂♀]+", emote)))
            else:
                return await errsay("Only input one character.")
        else:
            if getemoji(emote.split(":")[1]) == getemoji("typeless"):
                return await errsay("I don't have access to that emote.")
            else:
                name = emote.split(":")[1]
    except ValueError:
        return await errsay("Invalid character.")
    else:
        name = uni_name(emote)
    return name


@client.command()
async def sheriff(emote: str):
    name = await interpret_potential_emoji(emote)
    if type(name) != str:
        return

    return await client.say("⠀ ⠀ ⠀  :cowboy:\n　   {0}\u2060{0}\u2060{0}\n    {0}   {0}　{0}\n"
                            "   :point_down:  {0} {0} :point_down:\n"
                            "  　  {0}　{0}\n　   {0}　 {0}\n　   :boot:     :boot:\nhowdy. {1}"
                            .format(emote, "the name's mccree" if ord(emote[0]) == int("1f55b", 16) else\
                                    f"i'm the sheriff of {name.lower()}"))


@client.command()
async def langcodes(page=1):
    codes = [f"{g.title()}: [{tr.LANGCODES[g].upper()}]" for g in tr.LANGCODES]
    if not (0 < page < 12):
        page = 1
    return await emolsay(":twisted_rightwards_arrows:", "Google Translate / ISO 639-1 Language Codes", hexcol("5177ca"),
                         d="```ini\n" + "\n".join(codes[10*(page-1):10*page]) + f"```Page {page} of 11")


async def zhongsay(s: str, **kwargs):
    return await emolsay(":u7a7a:", s, hexcol("8000b0"), **kwargs)


@client.command(aliases=["jp"])
async def jyutping(*s: str):
    return await zhongsay(" ".join([" ".join(jp.get(g)) for g in s]))


@client.command(aliases=["py"])
async def pinyin(*s: str):
    return await zhongsay(" ".join([yn.get(g) for g in s]))


@client.command()
async def revpin(s: str):
    return await zhongsay(f"Chinese characters transliterable to {s}",
                          d=" / ".join([g for g in yn.get_reverse(s)]))


@client.command(aliases=["rune"])
async def runes(*s: str):
    dic = {"ᛆ": "a", "ᛒ": "b", "ᛍ": "c", "ᛑ": "d", "ᚧ": "ð", "ᛂ": "e", "ᚠ": "f", "ᚵ": "g", "ᚼ": "h", "ᛁ": "i", "ᚴ": "k",
           "ᛚ": "l", "ᛘ": "m", "ᚿ": "n", "ᚮ": "o", "ᛔ": "p", "ᛕ": "p", "ᛩ": "q", "ᚱ": "r", "ᛌ": "s", "ᛋ": "s", "ᛐ": "t",
           "ᚢ": "u", "ᚡ": "v", "ᚥ": "w", "ᛪ": "x", "ᛦ": "y", "ᛎ": "z", "ᚦ": "þ", "ᛅ": "æ", "ᚯ": "ø"}

    def trans(word):
        return "".join([dic.get(g, g) for g in word])

    return await emolsay(":flag_is:", " ".join([trans(g) for g in s]), hexcol("38009e"))


async def unisay(s: str, **kwargs):
    return await emolsay(":regional_indicator_u:", s, hexcol("5177CA"), **kwargs)


@client.command(aliases=["u"])
async def unicode(*args: str):
    if len(args) == 0:
        return await errsay("No hex code input.")
    elif len(args) == 1:
        try:
            i = int(args[0], 16)
        except ValueError:
            return await errsay("Invalid hex code.")
        try:
            char = chr(i)
        except ValueError:
            return await errsay("Hex code not in Unicode range.")
        try:
            return await unisay(char, footer=uni_name(char))
        except ValueError:
            return await unisay(char, footer="name not found")
    else:
        for s in args:
            try:
                int(s, 16)
            except ValueError:
                return await errsay(f"Invalid hex code {s}.")
            try:
                chr(int(s, 16))
            except ValueError:
                return await errsay(f"Code {s} is out of Unicode range.")
        return await unisay("".join([chr(int(g, 16)) for g in args]))


@client.command(aliases=["ord"])
async def ord_command(s: str):
    if len(s) == 1:
        return await unisay(f"{ord(s)} \u2223 ``u{hex(ord(s))[2:].lower().rjust(4, '0')}``")
    return await unisay(s, d="\n".join([f"``{g}``: {ord(g)} \u2223 ``u{hex(ord(g))[2:].lower().rjust(4, '0')}``"
                                        for g in s]))


@client.command()
async def collatz(n: int):
    def coll(x: int):
        while x != 1:
            if x % 2 == 0:
                x = x // 2
            else:
                x = x * 3 + 1
            yield x

    if n < 1:
        return await errsay("too small a number")
    return await client.say(f"__{len(list(coll(n)))} iterations__\n{n} → " + " → ".join([str(g) for g in coll(n)]))


@client.command()
async def base(b: int, n: str, f: int=None):
    if b < 2 or b > 36:
        return await errsay("Base must be between 2 and 36.")
    if f is None:
        try:
            int(n)
        except ValueError:
            return await errsay(f"{n} is not an integer.",
                                d="To convert from a base other than base 10, do ``z!base <to> <n> <from>``.")
        else:
            f = 10
    try:
        return await emolsay(":1234:", f"``{rk.rebase(n.lower(), f, b).upper()}``", hexcol("5177ca"))
    except IndexError:
        return await errsay(f"Invalid base {f} number.")

'''
@client.command()
async def canipa(*args: str):
    def valid_char(s: str):
        if s[0].lower() in ["u", "h", "r"]:
            try:
                int(s[1])
                int(s[2])
            except ValueError:
                return False
            except IndexError:
                return False
            return 0 <= int(s[1]) <= 4 and 0 <= int(s[2]) <= 5
        return False

    def char(s: str):
        vowels = {"u": 0, "h": 100, "r": 30}
        if s[0].lower() in vowels:
            return int("e000", 16) + vowels[s[0].lower()] + int(s[1]) + 5 * (5 - int(s[2]))

    for arg in args:
        if not valid_char(arg):
            return await errsay(f"Invalid code {arg}.")

    return await unisay("".join([chr(char(g)) for g in args]))
'''

@client.command()
async def diacritize(*args: str):
    return await client.say("".join(reg_split(r"[◌\s]+", "".join(args))))


@client.command()
async def rot13(*args: str):
    async def rotsay(s, **kwargs):
        return await emolsay(":regional_indicator_r:", s, hexcol("5177ca"), **kwargs)

    up = [chr(a) for a in range(65, 65+26)]
    low = [chr(a) for a in range(97, 97+26)]
    up = {up[g]: up[g - 13] for g in range(26)}
    low = {low[g]: low[g - 13] for g in range(26)}
    try:
        return await rotsay("".join([up.get(g, low.get(g, g)) for g in " ".join(args)]))
    except discord.errors.HTTPException:
        try:
            return await rotsay("that's very long", d="".join([up.get(g, low.get(g, g)) for g in " ".join(args)]))
        except discord.errors.HTTPException:
            return await errsay("inputs must be less than 2000 characters",
                                d="isn't Discord supposed to limit you to 2000 characters anyway :thinking:")


async def choosesay(s: str, **kwargs):
    return await emolsay(":8ball:", s, hexcol("E1E8ED"), **kwargs)


@client.command(aliases=["pick"])
async def choose(*args: str):
    args = reg_split(r"\s+or\s+", " ".join(args))
    if len(args) == 1:
        raise commands.errors.MissingRequiredArgument
    string = choice(["I pick {}!", "Obviously it's {}.", "{}, of course.", "{}, obviously.", "Definitely {}."])
    return await choosesay(string.format(f"**{choice(args)}**"))


@client.command(aliases=["8ball"])
async def eightball(*args: str):
    if len(args) == 0:
        raise commands.errors.MissingRequiredArgument

    options = ["It is certain.", "As I see it, yes.", "Reply hazy, try again.", "Don't count on it.",
               "It is decidedly so.", "Most likely.", "Ask again later.", "My reply is no.",
               "Without a doubt.", "Outlook good.", "Better not tell you now.", "My sources say no.",
               "Yes - definitely.", "Yes.", "Cannot predict now.", "Outlook not so good.",
               "You may rely on it.", "Signs point to yes.", "Concentrate and ask again.", "Very doubtful."]
    return await choosesay(choice(options))
