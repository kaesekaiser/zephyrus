from game import *
from utilities import dice as di, weed as wd, timein as ti, translate as tr, wiki as wk, convert as cv
from unicodedata import name as uni_name
from urllib.error import HTTPError
import hanziconv
import pycantonese
import datetime
from math import log10, isclose


@zeph.command(
    usage="z!mock <text...>\nz!mock",
    description="DoEs ThIs To YoUr TeXt.",
    help="DoEs ThIs To YoUr TeXt. If no text is given, mocks the message above you.\n\n"
         "`guy: I think Zephyrus is bad\nperson: z!mock\nZephyrus: I tHiNk ZePhYrUs Is BaD`\n\n"
         "You can also point to a specific message by using a string of carets, or a message link, as the input text. "
         "`z!mock ^^^` will mock the message three above yours."
)
async def mock(ctx: commands.Context, *text):
    def multi_count(s, chars):
        return sum([s.count(ch) for ch in chars])

    def dumb(s: str):
        return "".join(
            s[g].lower() if (g - multi_count(s[:g], (" ", "'", ".", "?", "!", "\""))) % 2 == s[0].isupper()
            else s[g].upper() for g in range(len(s))
        )

    text = " ".join(text)
    if not text:
        text = "^"  # use new message pointing system

    if await get_message_pointer(ctx, text, allow_fail=True):
        text = (await get_message_pointer(ctx, text)).content
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    return await ctx.send(dumb(text))


@zeph.command(
    usage="z!expand <text...>", hidden=True,
    help="D o e s \u00a0 t h i s \u00a0 t o \u00a0 y o u r \u00a0 t e x t ."
)
async def expand(ctx: commands.Context, *, text):
    return await ctx.send(" ".join([c for c in text]))


def squarize(s: str, joiner="\u200b"):
    noms = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    return joiner.join([chr(127462 - 97 + ord(g.lower())) if ord(g.lower()) in range(97, 123) else
                        ":{}:".format(noms[int(g)]) if ord(g) in range(48, 58) else
                        ":question:" if g == "?" else ":exclamation:" if g == "!" else g for g in s])


@zeph.command(
    aliases=["sq"], usage="z!square <text...>",
    help=squarize("Does this to your text.")
)
async def square(ctx: commands.Context, *, text):
    return await ctx.send(squarize(text))


@zeph.command(
    usage="z!clap <text...>\nz!clap",
    description="Does :clap: this :clap: to :clap: your :clap: text. :clap:",
    help="Does :clap: this :clap: to :clap: your :clap: text. :clap: If no text is given, claps the message above you."
)
async def clap(ctx: commands.Context, *, text: str = None):
    if not text:
        async for message in ctx.channel.history(limit=10):
            if message.id < ctx.message.id and message.content:
                text = message.content
                try:
                    await ctx.message.delete()
                except discord.Forbidden:
                    pass
                break

    return await ctx.send(" 👏 ".join(text.split()) + " 👏")


@zeph.command(
    usage="z!ping",
    help="Pong!"
)
async def ping(ctx: commands.Context):
    message = await ctx.send(":ping_pong:!")
    return await message.edit(
        content=f":ping_pong:! ({round((message.created_at - ctx.message.created_at).microseconds / 1000)} ms)")


@zeph.command(
    aliases=["dice"], usage="z!roll [dice]",
    description="Rolls some dice using standard dice notation.",
    help="Rolls some dice. Uses standard dice notation:\n``AdB`` rolls ``A`` ``B``-sided dice. ``A`` defaults to 1 "
         "if empty.\n``d%`` becomes ``d100``, and ``dF`` rolls Fudge dice, which are ``[-1, -1, 0, 0, "
         "1, 1]``.\n``!`` explodes a die if it rolls the highest number (that is, it rolls an additional extra "
         "die).\n``!>N``, ``!<N``, ``!=N`` explodes a die if it's greater than, less than, or equal to ``N``, "
         "respectively.\n``-H`` drops the highest roll. ``-L`` drops the lowest.\n``+N`` at the end of a die "
         "adds ``N`` to the total roll."
)
async def roll(ctx: commands.Context, die: str = "1d6"):
    dice = ClientEmol(":game_die:", hexcol("EA596E"), ctx)
    try:
        die = di.Die(die)
    except di.BadString as e:
        return await dice.say(str(e))
    else:
        return await dice.say(f"Rolling {die}...", d=die.run())


lowerAlphabet = "abcdefghijklmnopqrstuvwxyz"
smallAlphabet = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"


def smallcaps(s: str):
    if s.isupper():
        return smallcaps(s.lower())

    alpha_dict = {"\u00e9": "ᴇ́", **{lowerAlphabet[g]: smallAlphabet[g] for g in range(26)}}
    return "".join([alpha_dict.get(g, g) for g in s])


def caesar_cipher(letter: str, n: int):
    if letter.lower() not in lowerAlphabet:
        return letter
    if letter.isupper():
        return caesar_cipher(letter.lower(), n).upper()
    return lowerAlphabet[(lowerAlphabet.index(letter) + n) % 26]


@zeph.command(
    aliases=["rot"], usage="z!rot <shift #> <text...>",
    description="Puts text through a Caesar cipher.",
    help="Puts text through a Caesar cipher, which shifts all letters some number of positions down the alphabet.\n\n"
         "e.g. ``rot 5`` shifts all letters down 5 positions, so ``hello`` becomes ``mjqqt``. If you want to "
         "decipher a Caesar'd text, put in a negative shift number."
)
async def caesar(ctx: commands.Context, n: int, *, text: str):
    return await ctx.send("".join([caesar_cipher(c, n) for c in text]))


def vig(letter: str, *ks: str, reverse: bool = False):
    if letter.lower() not in lowerAlphabet:
        return letter
    if letter.isupper():
        return vig(letter.lower(), *ks, reverse=reverse).upper()
    mul = -1 if reverse else 1
    return lowerAlphabet[(lowerAlphabet.index(letter) + mul * sum([lowerAlphabet.index(g.lower()) for g in ks])) % 26]


@zeph.command(
    aliases=["vig"], usage="z!vigenere <word> <keys...>",
    description="Puts text through a [Vigenere cipher](https://en.wikipedia.org/wiki/Vigen%C3%A8re_cipher).",
    help="Puts text through a [Vigenere cipher](https://en.wikipedia.org/wiki/Vigen%C3%A8re_cipher) using the "
         "provided keys. Note that the text can't contain any spaces, so use underscores or dashes if you want "
         "to space it."
)
async def vigenere(ctx: commands.Context, text: str, *keys: str):
    return await ctx.send("".join([vig(text[n], *(k[n % len(k)] for k in keys)) for n in range(len(text))]))


@zeph.command(
    aliases=["devig"], usage="z!devigenere <word> <keys...>",
    description="Deciphers Vigenere'd text.",
    help="Deciphers Vigenere'd text using the provided keys. Using a different set of keys than the text "
         "was encoded with, will more than likely return a garbled mess.\n\n"
         "``z!vig zephyrus bot`` → ``asiimkvg``\n``z!devig asiimkvg bot`` → ``zephyrus``\n"
         "``z!devig asiimkvg fun`` → ``vyvdsxqm``"
)
async def devigenere(ctx: commands.Context, text: str, *keys: str):
    return await ctx.send("".join(
        [vig(text[n], *(k[n % len(k)] for k in keys), reverse=True) for n in range(len(text))]
    ))


@zeph.command(
    usage="z!scramble <text...>",
    help="eDso thsi ot uryo xtt.e"
)
async def scramble(ctx: commands.Context, *text: str):
    return await ctx.send(content=" ".join(["".join(sample(g, len(g))) for g in text]))


@zeph.command(
    aliases=["tc", "tconv"], usage="z!tconvert <temperature> <unit> to <unit>\nz!tconvert <temperature> <unit>",
    description="Converts between units of temperature.",
    help="Converts between units of temperature: C, F, K, and R. More info at "
         "https://github.com/kaesekaiser/zephyrus/blob/master/docs/convert.md."
)
async def tconvert(ctx: commands.Context, n: str, *text):
    if "." in n:
        digits_in = len(n.split(".")[1])
    else:
        digits_in = 0
    n = float(n)

    if "to" in text:
        text = [cv.find_abbr(g, True) for g in " ".join(text).split(" to ")]
    else:
        text = (cv.find_abbr(" ".join(text), True), )

    try:
        ret = cv.temp_convert(n, *text)
    except ValueError:
        raise commands.CommandError(f"Can't convert between {text[0]} and {text[1]}.")
    else:
        if cv.temp_convert(n, text[0], "K")[1] < 0:
            raise commands.CommandError(f"{n} °{text[0]} is below absolute zero.")
        value = max(min(cv.temp_convert(n, text[0], "F")[1], 120), 0) / 120
        temp = ClientEmol(":thermometer:", gradient("88C9F9", "DD2E44", value), ctx)
        return await temp.say(f"{round(ret[1], digits_in) if digits_in else round(ret[1])} {cv.add_degree(ret[0])}",
                              d=f"= {n} {cv.add_degree(text[0])}")


@zeph.command(
    aliases=["c", "conv"], usage="z!convert <number> <unit...> to <unit...>\nz!convert <number> <unit...>",
    description="Converts between units of measurement.",
    help="Converts between units of measurement. More info at "
         "https://github.com/kaesekaiser/zephyrus/blob/master/docs/convert.md."
)
async def convert(ctx: commands.Context, n: str, *text):
    conv = ClientEmol(":straight_ruler:", hexcol("efc700"), ctx)

    # determining number of sig figs
    if "e" in n:
        digits_in = len("".join(n.split("e")[0].split(".")))  # number of digits provided to scientific notation
    elif "." in n:
        first_significant = [g for g in range(len(n)) if n[g] not in "-+0."][0]
        digits_in = len("".join(n[first_significant:].split(".")))  # number of significant figures
    else:
        digits_in = len(n)  # if it's just an integer
    digits_in = max(digits_in, 3)  # at least 3 sig figs no matter what

    try:
        n = float(n)
    except ValueError:
        raise commands.BadArgument

    if "to" in text:
        text = tuple(cv.MultiUnit.from_str(cv.unrulyAbbreviations.get(g, g)) for g in " ".join(text).split(" to "))
        if len(text) != 2:
            raise commands.BadArgument
    else:
        text = (cv.MultiUnit.from_str(cv.unrulyAbbreviations.get(" ".join(text), " ".join(text))), )

    if n < 0:
        raise commands.CommandError(f"Can't have negative measurements.")

    ret = cv.convert_multi(n, *text)

    if ret[0] == "ft":
        digits_out = digits_in - floor(log10(ret[1])) - 2
        inc = round(12 * (ret[1] % 1), digits_out)
        if isclose(inc, int(inc), abs_tol=1e-10) and digits_out == 1:
            inc = round(inc)
        return await conv.say(f"{add_commas(floor(ret[1]))} ft {inc} in",
                              d=f"= {n} {text[0]}")

    if ret[1] == int(ret[1]):
        digits_out = -1
    else:
        digits_out = digits_in - floor(log10(ret[1])) - 1

    return await conv.say(f"{add_commas(round(ret[1], digits_out) if digits_out > 0 else round(ret[1]))} {ret[0]}",
                          d=f"= {n} {text[0]}")


@zeph.command(
    aliases=["weed"], usage="z!sayno",
    help="Say no to drugs."
)
async def sayno(ctx: commands.Context):
    return await ClientEmol(":leaves:", hexcol("98e27c"), ctx).say(wd.sayno())


@zeph.command(
    aliases=["pick"], usage="z!choose <option...> or <option...> ...",
    help="Chooses one from a list of options."
)
async def choose(ctx: commands.Context, *, text: str):
    picks = re.split(r"\s+or\s+", text)
    string = choice(["I pick {}!", "Obviously it's {}.", "{}, of course.", "{}, obviously.", "Definitely {}."])
    return await chooseEmol.send(ctx, string.format(f"**{choice(picks)}**"))


@zeph.command(  # an easter egg command. z!choose but in a pidgin conlang.
    hidden=True, usage="z!tekat <option...> sing <option...> ...",
    help="Chooses one from a list of options, but in Lam Kiraga."
)
async def tekat(ctx: commands.Context, *, text: str):
    picks = re.split(r"\s+sing\s+", text)
    string = choice(["De tekat {}!"])  # will add more later
    return await chooseEmol.send(ctx, string.format(f"**{choice(picks)}**"))


@zeph.command(
    name="8ball", usage="z!8ball <question...>",
    help="The divine magic 8-ball answers your yes-or-no questions."
)
async def eightball(ctx: commands.Context, *, text: str):
    if not text:
        raise commands.MissingRequiredArgument

    options = ["It is certain.", "As I see it, yes.", "Reply hazy, try again.", "Don't count on it.",
               "It is decidedly so.", "Most likely.", "Ask again later.", "My reply is no.",
               "Without a doubt.", "Outlook good.", "Better not tell you now.", "My sources say no.",
               "Yes - definitely.", "Yes.", "Cannot predict now.", "Outlook not so good.",
               "You may rely on it.", "Signs point to yes.", "Concentrate and ask again.", "Very doubtful."]
    return await chooseEmol.send(ctx, choice(options))


blankColor = rk.Image.open("images/color.png")


@zeph.command(
    aliases=["colour"], usage="z!color <hex code>\nz!color <red> <green> <blue>\nz!color random",
    description="Shows you a color.",
    help="Returns the color that corresponds to your input. ``random`` will randomly generate a color."
)
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
        .save(f"images/{str(ret.r)[-1]}{str(ret.b)[-1]}.png")
    image = await image_url(f"images/{str(ret.r)[-1]}{str(ret.b)[-1]}.png")
    return await emol.say(f"#{hex(ret.value)[2:].rjust(6, '0')}", thumb=image,
                          d=f"**RGB:** {ret.to_rgb()}\n**HSV:** {rgb_to_hsv(*ret.to_rgb())}")


"""@zeph.command(
    aliases=["hue"], usage="z!hueshift <image url> <value>",
    description="Hue-shifts an image.",
    help="Shifts the hue of an image by ``<value>`` (out of 360)."
)
async def hueshift(ctx: commands.Context, url: str, shift: int):
    message = await ctx.send("processing...")
    img = rk.Image.open(BytesIO(requests.get(url).content))
    rk.shift_hue(img, shift).save("images/hue-shift.png")
    await message.delete()
    return await ctx.send(file=discord.File("images/hue-shift.png"))


@zeph.command(
    usage="z!invert <image url>",
    help="Inverts the colors of an image."
)
async def invert(ctx: commands.Context, url: str):
    img = rk.Image.open(BytesIO(requests.get(url).content))
    rk.invert_colors(img).save("images/invert.png")
    return await ctx.send(file=discord.File("images/invert.png"))"""


@zeph.command(
    usage="z!timein <place...>",
    description="Tells you what time it is somewhere.",
    help="Returns the current local time in ``<place>``."
)
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


def chinese_punctuate(s: str):
    chinese_punctuation = {
        "？": "? ", "！": "! ", "。": ". ", "，": ", ", "：": ": ", "；": "; ", "【": " [", "】": "] ", "（": " (", "）": ") ",
        "《": " ⟨", "》": "⟩ ", "、": ", ", "／": " / ", "『": ' "', "』": '" '
    }
    ret = f" {s} "
    for i in chinese_punctuation:
        ret = i.join(ret.split(f" {i} ")).replace(i, chinese_punctuation[i])
    return " ".join(re.split(r"\s+", ret)).strip(" ")


def get_pinyin(c: str):
    return chinese_punctuate(zeph.roman.process_sentence_pinyin(hanziconv.HanziConv.toSimplified(c)))


def get_jyutping(s: str):
    return chinese_punctuate(zeph.roman.process_sentence(
        hanziconv.HanziConv.toTraditional(s), zeph.roman.jyutping_word_map, zeph.roman.jyutping_char_map, lambda x: x
    ))


def get_yale(s: str):
    yale = get_jyutping(s)
    for i in re.findall(r"[a-z]+[0-9]", get_jyutping(s)):
        yale = yale.replace(i, pycantonese.jyutping2yale(i))
    return yale


@zeph.command(
    name="pinyin", usage="z!pinyin <Mandarin text...>", aliases=["py"],
    description="Romanizes Chinese text using Hanyu Pinyin.",
    help="Romanizes Chinese text according to the Hanyu Pinyin romanization scheme - that is, it turns the "
         "Chinese characters into Latin syllables that sound like their Mandarin pronunciations.\n\n"
         "``z!pinyin 你好`` → ``nǐhǎo``"
)
async def pinyin_command(ctx: commands.Context, *, chinese: str):
    return await ctx.send(get_pinyin(chinese))


@zeph.command(
    name="jyutping", aliases=["jp"], usage="z!jyutping <Cantonese text...>",
    description="Romanizes Cantonese text using Jyutping.",
    help="Romanizes Cantonese text according to the Jyutping romanization scheme.\n\n"
         "``z!jyutping 你好`` → ``nei5hou2``"
)
async def jyutping_command(ctx: commands.Context, *, cantonese: str):
    return await ctx.send(get_jyutping(cantonese))


@zeph.command(
    name="yale", usage="z!yale <Cantonese text...>",
    description="Romanizes Cantonese text using the Yale scheme.",
    help="Romanizes Cantonese text according to the Yale romanization scheme. There's also a Yale romanization "
         "scheme for Mandarin text, but this isn't that, and that's not on this bot.\n\n"
         "``z!yale 你好`` → ``néihhóu``"
)
async def yale_command(ctx: commands.Context, *, cantonese: str):
    return await ctx.send(get_yale(cantonese))


@zeph.command(
    aliases=["simp"], usage="z!simplified <Traditional Chinese text...>",
    help="Converts Traditional Chinese characters to Simplified Chinese."
)
async def simplified(ctx: commands.Context, *, trad: str):
    return await ctx.send(hanziconv.HanziConv.toSimplified(trad))


@zeph.command(
    aliases=["trad"], usage="z!traditional <Simplified Chinese text...>",
    help="Converts Simplified Chinese characters to Traditional Chinese."
)
async def traditional(ctx: commands.Context, *, simp: str):
    return await ctx.send(hanziconv.HanziConv.toTraditional(simp))


@zeph.command(
    aliases=["trans"], usage="z!translate <from> <to> <text...>",
    description="Google Translates text between languages.",
    help="Via Google Translate, translates ``<text>`` between languages. ``<from>`` and ``<to>`` must be "
         "either the name of the language or the [code](https://cloud.google.com/translate/docs/languages) "
         "for the language. ``chinese`` defaults to Simplified Chinese; for Traditional, use "
         "``traditional-chinese`` or ``zh-tw``. You can also use ``auto`` or ``detect`` for the detect "
         "language option.\n\n"
         "``z!translate English French Hello, my love`` → ``Bonjour mon amour``\n"
         "``z!translate auto en Hola, señor`` → ``Hello sir``"
)
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
    return await trans.say(
        translation.text, footer="{}{} -> {}".format("detected: " if fro == "auto" else "",
                                                     tr.LANGUAGES[lang].title(), tr.LANGUAGES[to].title())
    )


async def get_translation(fro: str, to: str, text: str):
    """Turning this into a coroutine for use with badtranslate(). In previous versions, using non-coroutines would
    actually kill the bot, as it took too long to run all of the translation requests. Since coroutines are awaited,
    this should prevent this from happening."""
    return tr.Translator().translate(text, to, fro).text


"""
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
"""


@zeph.command(
    usage="z!avatar [@user]",
    description="Returns a link to a user's avatar.",
    help="Returns a link to a user's avatar. If `[@user]` is left blank, links your avatar."
)
async def avatar(ctx: commands.Context, user: str = None):
    if not user:
        user = ctx.author
    av_url = str(user.avatar_url_as(format="png"))
    return await ctx.send(
        embed=construct_embed(author=author_from_user(user, name=f"{user.display_name}'s Avatar", url=av_url),
                              color=user.colour, image=av_url)
    )


"""@zeph.command(
    aliases=["rune"], usage="z!runes <runic text...>",
    help="Transcribes [medieval Nordic runes](https://en.wikipedia.org/wiki/Medieval_runes) into Latin letters."
)
async def runes(ctx: commands.Context, *, s: str):
    dic = {"ᛆ": "a", "ᛒ": "b", "ᛍ": "c", "ᛑ": "d", "ᚧ": "ð", "ᛂ": "e", "ᚠ": "f", "ᚵ": "g", "ᚼ": "h", "ᛁ": "i", "ᚴ": "k",
           "ᛚ": "l", "ᛘ": "m", "ᚿ": "n", "ᚮ": "o", "ᛔ": "p", "ᛕ": "p", "ᛩ": "q", "ᚱ": "r", "ᛌ": "s", "ᛋ": "s", "ᛐ": "t",
           "ᚢ": "u", "ᚡ": "v", "ᚥ": "w", "ᛪ": "x", "ᛦ": "y", "ᛎ": "z", "ᚦ": "þ", "ᛅ": "æ", "ᚯ": "ø"}

    return await ClientEmol(":flag_is:", hexcol("38009e"), ctx).say("".join([dic.get(g, g) for g in s]))"""


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


def interpret_potential_emoji(emote: str):
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
            elif re.search(r"[🏻🏼🏽🏾🏿‍♂♀]+", emote):
                name = interpret_potential_emoji("".join(re.split(r"[🏻🏼🏽🏾🏿‍♂♀]+", emote)))
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


@zeph.command(
    aliases=["sherriff"], usage="z!sheriff <emoji>",
    description="Calls the sheriff of an emoji.",
    help="Calls the sheriff of ``<emoji>``."
)
async def sheriff(ctx: commands.Context, emote: str):
    name = interpret_potential_emoji(emote)
    return await ctx.send("⠀ ⠀ ⠀  :cowboy:\n　   {0}\u2060{0}\u2060{0}\n    {0}   {0}　{0}\n"
                          "   :point_down:  {0} {0} :point_down:\n"
                          "  　  {0}　{0}\n　   {0}　 {0}\n　   :boot:     :boot:\nhowdy. {1}"
                          .format(emote, "the name's mccree" if ord(emote[0]) == int("1f55b", 16) else
                                  f"i'm the sheriff of {name.lower()}"))


class WikiNavigator(Navigator):
    def __init__(self, *results: wk.Result):
        self.results = results
        super().__init__(wiki, [g.desc for g in results], 1, "")

    @property
    def con(self):
        return self.emol.con(
            self.results[self.page - 1].title.replace("****", ""), footer=f"{self.page}/{self.pgs}",
            d=self.results[self.page - 1].desc.replace("****", ""),
            url=f"https://en.wikipedia.org{self.results[self.page - 1].link}"
        )


@zeph.command(
    aliases=["wiki"], usage="z!wikipedia <search...>",
    description="Searches Wikipedia.",
    help="Searches Wikipedia for ``<search>``."
)
async def wikipedia(ctx: commands.Context, *, title: str):
    parser = wk.WikiParser()
    parser.feed(wk.readurl(wk.wikiSearch.format("+".join(title.split()))))
    try:
        return await WikiNavigator(*parser.results).run(ctx)
    except IndexError:
        return await wiki.send(ctx, "No results found.")


@zeph.command(
    aliases=["fw"], usage="z!foreignwiki <language> <title...>\nz!foreignwiki all <title...>",
    description="Finds non-English mirrors of a Wikipedia article.",
    help="``z!foreignwiki <language> <title...>`` finds the ``<language>`` version of the English Wikipedia "
         "article ``<title>``.\n``z!foreignwiki all <title...>`` lists all languages which have a version "
         "of ``<title>``."
)
async def foreignwiki(ctx: commands.Context, lang: str, *, title: str):
    parser = wk.ForeignParser()
    try:
        parser.feed(wk.readurl(wk.wikilink.format("_".join(title.split()))))
    except HTTPError:
        raise commands.CommandError("Article not found in English.")
    if lang.casefold() == "all":
        return await Navigator(wiki, [parser.form(g) for g in parser.lang_link], 8,
                               "Foreign titles of " + parser.title + " [{page}/{pgs}]").run(ctx)
    lang = parser.code_lang.get(lang.lower(), lang.title())
    try:
        return await wiki.send(ctx, parser.lang_title[lang], url=parser.lang_link[lang])
    except KeyError:
        raise commands.CommandError(f"Article unavailable in {lang}.")


"""def get_phone_no(guild: discord.Guild):
    if guild.id not in zeph.phoneNumbers.values():
        zeph.phoneNumbers[choice([g for g in range(1000000) if g not in zeph.phoneNumbers])] = guild.id
    return {j: g for g, j in zeph.phoneNumbers.items()}[guild.id]


def from_phone_no(s: str):
    try:
        return zeph.get_guild(zeph.phoneNumbers[int(s)])
    except IndexError:
        raise commands.CommandError("That number doesn't exist.")


class Call:
    def __init__(self, caller: discord.TextChannel, receiver: discord.TextChannel, not_set: bool=False):
        self.caller = caller
        self.receiver = receiver
        self.not_set = not_set
        self.hungUpOn = phone.con("They hung up.")
        self.timedOut = phone.con("Call timed out.")
        self.connected = phone.con("You're connected!", d="Prefix messages with \"> \" to send them over.\n"
                                   "To end the call, use ``z!phone hangup``.")

    async def one_way(self, fro: discord.TextChannel, to: discord.TextChannel):
        def pred(m: discord.Message):
            if m.author == zeph.user:
                embeds = [g.to_dict() for g in m.embeds]
                return (self.timedOut.to_dict() in embeds or self.hungUpOn.to_dict() in embeds) and m.channel == fro
            return (m.content.startswith(">") or m.content.lower() == "z!phone hangup") and m.channel == fro

        while True:
            try:
                mess = await zeph.wait_for("message", timeout=300, check=pred)
            except asyncio.TimeoutError:
                await to.send(embed=self.timedOut)
                return await fro.send(embed=self.timedOut)
            assert isinstance(mess, discord.Message)
            if mess.author.id == zeph.user.id:
                return
            if mess.content.lower() == "z!phone hangup":
                await to.send(embed=self.hungUpOn)
                return await phone.send(fro, "Call ended.")
            else:
                await to.send(content=f":telephone: **{mess.author.display_name}:** {mess.content.lstrip('> ')}")

    async def run(self):
        await phone.send(self.caller, "Calling...")
        if await confirm(f"Incoming call from {self.caller.guild.name}!",
                         self.receiver, yes="pick up", no="decline", emol=phone):
            zeph.loop.create_task(self.one_way(self.caller, self.receiver))
            zeph.loop.create_task(self.one_way(self.receiver, self.caller))
            await self.caller.send(embed=self.connected)
            await self.receiver.send(embed=self.connected)
        else:
            await phone.send(self.caller, "Call declined.")

    @staticmethod
    def call(fro: discord.TextChannel, to: str):
        to = from_phone_no(to)
        assert isinstance(to, discord.Guild)
        if to.system_channel:
            return Call(fro, to.system_channel)
        elif zeph.callChannels.get(to.id):
            return Call(fro, zeph.get_channel(zeph.call_channels[to.id]))
        else:
            return Call(fro, to.text_channels[0], not_set=True)


@zeph.command(name="phone")
async def phone_command(ctx: commands.Context, func: str = "help", channel: str=None):
    func = func.lower()
    if func == "number":
        func = "no"

    if func == "help":
        return await phone.send(ctx, "Help")

    if func == "register":
        if channel:
            try:
                int(channel)
            except ValueError:
                raise commands.CommandError(f"{channel} isn't a valid zPhone number.")
            else:
                if len(str(int(channel))) != 6:
                    raise commands.CommandError(f"{channel} isn't a valid zPhone number.")
                if int(channel) in zeph.phoneNumbers:
                    raise commands.CommandError("That number is already taken.")
        else:
            channel = choice([g for g in range(100000, 1000000) if g not in zeph.phoneNumbers])

    if func == "no":
        return await phone.send(ctx, f"This server's zPhone number is: ``{get_phone_no(ctx.guild)}``")

    if func == "call":
        try:
            return await Call.call(ctx.channel, channel).run()
        except AssertionError:
            raise commands.CommandError(f"No server with the number ``{channel}``.")"""


def nln(n: int):
    reds = {rk.rebase(g, 10, 24): rk.rebase(g, 10, 8).rjust(2, "0") for g in range(24)}
    return re.sub("|".join(reds.keys()), lambda m: reds[m[0]] + " ", rk.rebase(n, 10, 24)).lstrip("0").rstrip(" ")


@zeph.command(
    aliases=["fac"], usage="z!factors <integer>",
    description="Finds the prime factors of a number.",
    help="Returns the prime factors of `<integer>`."
)
async def factors(ctx: commands.Context, number: int):
    if number < 1:
        raise commands.CommandError("Number must be greater than 0.")
    if log10(number) >= 15:
        raise commands.CommandError("Please keep numbers to 15 digits or less.")

    def get_factors(n: int):
        min_search = 3
        ret = []
        while n % 2 == 0:
            n = round(n / 2)
            ret.append(2)
        original = n
        max_search = ceil(original ** 0.5) + 1
        max_search += not max_search % 2
        while True:
            for i in range(min_search, max_search + 2, 2):
                if n % i == 0:
                    ret.append(i)
                    n = round(n / i)
                    break
                else:
                    min_search = i
            if ret.count(2) == len(ret):
                return ret + [original]
            if min_search == max_search:
                if n == 1:
                    return sorted(ret)
                return sorted(ret + [n])

    return await ClientEmol(":1234:", blue, ctx).say(f"Prime factors of {number}:", d=f"``= {get_factors(number)}``")


@zeph.command(
    name="base", usage="z!base <base> <base-10 integer>\nz!base <to> <integer> <from>",
    description="Converts integers between bases.",
    help="`z!base <base> <base-10 integer>` converts a base-10 (a regular number with digits 0-9) integer to a given "
         "base.\n`z!base <to> <integer> <from>` converts an integer of any base to any other base. Note that "
         "Zephyrus can only use bases between 2 and 36, inclusive.\n\n"
         "`z!base 2 19` → `10011`\n`z!base 10 11001 2` → `25`\n`z!base 16 792997` → `C19A5`"
)
async def base_command(ctx: commands.Context, to_base: int, num: str, from_base: int = 10):
    if to_base not in range(2, 37) or from_base not in range(2, 37):
        return await err.send(ctx, "Base must be between 2 and 36, inclusive.")

    try:
        ret = rk.rebase(num.lower(), from_base, to_base).upper()
    except IndexError:
        return await err.send(ctx, f"{num.upper()} is not a base-{from_base} number.")

    subscript = "".join(chr(ord(g) - 48 + 8320) for g in str(from_base))

    return await ClientEmol(":1234:", blue, ctx).say(ret, d=f"is ({num.upper()}){subscript} in base {to_base}.")


@zeph.command(
    name="age", usage="z!age",
    description="Shows you how old your account is.",
    help="`z!age` tells you how old your account is, and when you joined the server. That's it, really."
)
async def age_command(ctx: commands.Context):
    age_emol = ClientEmol(":hourglass:", hexcol("ffac33"), ctx)
    return await age_emol.say(
        f"{ctx.author.display_name}'s Age",
        d=f"You created your account on **{ctx.author.created_at.date().strftime('%B %d, %Y').replace(' 0', ' ')}**.\n"
        f"You joined this server on **{ctx.author.joined_at.date().strftime('%B %d, %Y').replace(' 0', ' ')}**."
    )


@zeph.command(
    name="emoji", aliases=["emote", "e"], usage="z!emoji [emote(s)...]",
    description="Sends a custom emoji.",
    help="`z!e <emote>` returns the input custom emote, if Zeph has one by that name. `z!e` lists all custom emotes "
         "Zeph has access to.\n\nNote that emote names are *case-sensitive*."
)
async def emote_command(ctx: commands.Context, *args: str):
    if not args:
        messages, ret = [], ""
        for emote in zeph.emojis.values():
            if emote.guild_id not in testing_emote_servers:
                if len(ret + str(emote)) < 2000:
                    ret += str(emote)
                else:
                    messages.append(ret)
                    ret = str(emote)
        messages.append(ret)

        for message in messages:
            await ctx.send(message)

    else:
        for arg in args:
            if arg not in zeph.emojis:
                if len(args) == 1:
                    raise commands.CommandError("I don't have that emote.")
                else:
                    raise commands.CommandError(f"I don't have the `{arg}` emote.")
        try:
            await ctx.send("".join(str(zeph.emojis[g]) for g in args))
        except discord.errors.HTTPException:
            raise commands.CommandError("I can't fit that many emotes in one message.")


async def get_message_pointer(ctx: commands.Context, pointer: str, fallback=None, allow_fail: bool = False):
    """Tries to get a Message object from a pointer.
    If pointer is a string of carets, returns the Nth message back.
    If pointer is a valid link to or ID for a message, returns that message.
    If pointer is neither, returns the fallback input (default None).
    If allow_fail is True, a message not found error will not prevent execution."""

    mess = fallback
    if pointer == "^" * len(pointer):
        async for message in ctx.channel.history(before=ctx.message, limit=len(pointer)):
            mess = message  # really shoddy way to get the Nth message back. is there a better way? probably.
    else:
        try:
            mess = await commands.MessageConverter().convert(ctx, pointer)
        except commands.BadArgument as e:
            if not allow_fail:
                raise commands.CommandError(str(e))
    return mess


@zeph.command(
    name="react", aliases=["r"], usage="z!react [^...] <emote>\nz!react <message link> <emote>", hidden=True,
    description="Reacts to a message.",
    help="`z!r <emote>` reacts to the message immediately above yours with the input emote. `z!r ^ <emote>` does the "
         "same thing. `z!r ^^ <emote>` reacts to the message *two* above yours; `z!r ^^^ <emote>` reacts to the third, "
         "and so on. You can also link a specific message to react to via the URL or ID. It's a way to semi-give "
         "yourself nitro privileges, assuming Zeph has the emote you want.\n\n"
         "Note that emote names are *case-sensitive*."
)
async def react_command(ctx: commands.Context, *args: str):
    if len(args) > 2 or len(args) < 1:
        raise commands.BadArgument

    if args[-1].strip(":") not in zeph.emojis:
        raise commands.CommandError("I don't have that emote.")
    emote = zeph.emojis[args[-1].strip(":")]

    if len(args) == 1:
        pointer = "^"
    else:
        pointer = args[0]

    mess = await get_message_pointer(ctx, pointer, fallback=ctx.message)

    await mess.add_reaction(emote)

    def pred(r: discord.RawReactionActionEvent):
        return r.emoji == emote and r.message_id == mess.id and r.user_id == ctx.author.id

    try:
        await zeph.wait_for('raw_reaction_add', timeout=30, check=pred)
    except asyncio.TimeoutError:
        pass

    await mess.remove_reaction(emote, zeph.user)  # remove zeph's reaction once the user has also reacted
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass


@zeph.command(
    aliases=["rw"], usage="z!randomword [pattern]",
    description="Generates a random word.",
    help="Generates a random word made of IPA symbols. If `[pattern]` is not specified, it defaults to CVCVCVCV.\n\n"
         "Valid pattern letters are: **`C`** for consonants, **`F`** for fricatives, **`J`** for palatals, **`K`** "
         "for clicks, **`L`** for laterals, **`N`** for nasals, **`P`** for plosives, **`R`** for rhotics, **`S`** "
         "for sibilants, **`T`** for taps, **`U`** for all vowels, **`V`** for the five basic vowels [a e i o u], "
         "**`W`** for approximants, and **`X`** for trills."
)
async def randomword(ctx: commands.Context, pattern: str = "CVCVCVCV"):
    """Stolen pretty much directly from Leo (https://github.com/Slorany/LeonardBot)."""

    subs = {
        "A": "",
        "B": "",
        "C": "pbtdʈɖcɟkgqɢʔmɱnɳɲŋɴʙrʀɾɽɸβfvθðszʃʒʂʐçʝxɣχʁħʕhɦɬɮʋɹɻjɰlɭʎʟ",  # consonants
        "D": "",
        "E": "",
        "F": "ɸβfvθðszʃʒʂʐçʝxɣχʁħʕhɦɬɮ",  # fricatives
        "G": "",
        "H": "",
        "I": "",
        "J": "cɟɲçʝjʎɕʑ",  # palatals
        "K": "ǁǂǃǀʘ",  # clicks
        "L": "ʟʎlɬɮɭɺ",  # laterals
        "M": "",
        "N": "mɱnɳɲŋɴ",  # nasals
        "O": "",
        "P": "pbtdʈɖcɟkgqɢʔ",  # plosives
        "Q": "",
        "R": "rɾɹɻʀʁɽɺ",  # rhotics
        "S": "szʃʒʂʐ",  # sibilants
        "T": "ɾɽɺ",  # taps / flaps
        "U": "iyɨʉɯuɪʏʊeøɘɵɤoəɛœɜɞʌɔæɐaɶɑɒ",  # all vowels
        "V": "aeiou",  # the basic five vowels
        "W": "ʋɹɻjɰlɭʎʟwʍɥ",  # approximants
        "X": "ʙrʀ",  # trills
        "Y": "",
        "Z": ""
    }

    def choose_sub(s: str): return "" if not len(subs.get(s, s)) else choice(subs[s]) if subs.get(s) else s

    ret = "".join(choose_sub(c) for c in pattern)
    if not ret:
        raise commands.CommandError("Pattern would be empty. Do `z!help rw` for a list of valid sets.")
    return await ctx.send(ret)


with open("utilities/stest.txt", "r") as fp:
    stest_sentences = fp.read().splitlines()


@zeph.command(
    aliases=["stest"], usage="z!syntaxtest [number 1-218]\nz!syntaxtest list",
    description="Gives you a sentence to test conlang syntax.",
    help="`z!stest` returns a random sentence from the [list of 218 conlang syntax test sentences]"
         "(https://web.archive.org/web/20120427054736/http://fiziwig.com/conlang/syntax_tests.html).\n"
         "`z!stest <number 1-218>` returns sentence #`number`.\n"
         "`z!stest list` links a full list of the sentences."
)
async def syntaxtest(ctx: commands.Context, arg: str = None):
    """This is also taken from Leo (see randomword, above)."""

    if not arg:
        return await ctx.send(choice(stest_sentences))

    if str(arg).lower() == "list":
        return await ctx.send("Here's the list of the 218 syntax test sentences: <http://pastebin.com/raw/BpfjThwA>")

    try:
        int(arg)
    except ValueError:
        raise commands.BadArgument
    else:
        if int(arg) < 1 or int(arg) > 218:
            raise commands.BadArgument
        else:
            return await ctx.send(stest_sentences[int(arg) - 1])


class RMNavigator(Navigator):
    def __init__(self, roles: list):
        super().__init__(
            Emol(":clipboard:", hexcol("C1694F")), [name_focus(g) for g in roles[0].members],
            8, "Role Members [{page}/{pgs}]",
            prefix=f"Total: **{len(roles[0].members)}** ({roles[0].mention})\n\n"
        )
        self.roles = roles
        self.roleIndex = 0
        if len(roles) > 1:
            self.funcs["🔃"] = self.cycle_role

    @property
    def role(self):
        return self.roles[self.roleIndex]

    def cycle_role(self):
        self.roleIndex = (self.roleIndex + 1) % len(self.roles)
        self.table = [name_focus(g) for g in self.role.members]
        self.prefix = f"Total: **{len(self.role.members)}** ({self.role.mention})\n\n"
        self.page = 1


@zeph.command(
    aliases=["rm"], usage="z!rolemembers <role>",
    description="Lists all the members of a certain role.",
    help="`z!rm <role>` returns a scrollable list of all server members who have the given role, along with a count."
)
async def rolemembers(ctx: commands.Context, *, role_name: str):
    """Another command idea taken from Leo, but this one is heavily adapted from the original."""

    possible_roles = [g for g in ctx.guild.roles if g.name.lower() == role_name.lower()]
    emol = Emol(":clipboard:", hexcol("C1694F"))

    if len(possible_roles) == 0:
        raise commands.CommandError(f"`{role_name}` role not found.")

    if len(possible_roles) > 1:  # fuck you manti
        await emol.send(ctx, f"There are multiple roles called `{role_name}`.",
                        d="Use the :arrows_clockwise: button to cycle between them.")

    return await RMNavigator(sorted(possible_roles, key=lambda c: -len(c.members))).run(ctx)


class Reminder:
    def __init__(self, author_id: int, text: str, timestamp: float):
        self.author = author_id
        self.text = text
        self.time = timestamp

    async def send(self):
        try:
            await zeph.get_user(self.author).send(f"**Reminder:** {self.text}")
        except AttributeError:
            print(f"A reminder failed to send: {str(self)}")

    def __str__(self):
        return f"{self.author}|{self.time}|{self.text}"

    def __eq__(self, other):
        return str(self) == str(other) and isinstance(other, Reminder)

    @staticmethod
    def from_str(s: str):
        return Reminder(int(s.split("|")[0]), "|".join(s.split("|")[2:]), float(s.split("|")[1]))


def load_reminders():
    zeph.reminders.clear()
    with open("storage/reminders.txt", "r") as f:
        for rem in f.readlines():
            zeph.reminders.append(Reminder.from_str(rem.strip("\n")))


@zeph.command(
    name="remindme", aliases=["remind", "rme", "rem"], usage="z!remindme <reminder...> in <time...>",
    description="Reminds you of something later.",
    help="`z!remindme <reminder> in <time>` sets the bot to DM you with a reminder in a certain amount of time. "
         "`<reminder>` can be anything. `<time>` can use any combination of integer days, hours, or minutes, "
         "separated by spaces and in that order.\n\n"
         "e.g. `z!remindme eat food in 2 hours`, `z!rme work on essay in 5 hours 30 minutes`, or "
         "`z!remind talk to Sam in 3 days`."
)
async def remind_command(ctx: commands.Context, *text: str):
    # leaving input text as a list, rather than a single string like usual, to make splitting easier
    def concise_td(td: datetime.timedelta):
        td_minutes = round(td.total_seconds() / 60)  # rounding to account for small variations
        ds, hs, ms = td_minutes // 1440, td_minutes // 60 % 24, td_minutes % 60
        return "".join([
            f"{ds} {plural('day', ds)} " if ds else "",
            f"{hs} {plural('hour', hs)} " if hs else "",
            f"{ms} {plural('minute', ms)}" if ms else "",
        ]).strip()

    if "in" not in text:
        raise commands.BadArgument

    last_in = [g for g in range(len(text)) if text[g] == "in"][-1]
    reminder, elapse = " ".join(text[:last_in]), " ".join(text[last_in + 1:])
    time_regex = r"([0-9]+ days?)?(^|,? |$)(([0-9]+ hours?)?(^|,? |$))?([0-9]+ minutes?)?"

    if not re.fullmatch(time_regex, elapse):
        raise commands.CommandError("Invalid time. Time argument accepts days, hours, and minutes, in that order.")

    def zero(x): return int(x[0]) if x else 0
    days = zero(re.search(r"[0-9]+(?= day)", elapse))
    hours = zero(re.search(r"[0-9]+(?= hour)", elapse))
    minutes = zero(re.search(r"[0-9]+(?= minute)", elapse))

    timestamp = time.time() + days * 86400 + hours * 3600 + minutes * 60

    if timestamp > 2147483648:
        raise commands.CommandError("That's too far out.")

    reminder = Reminder(ctx.author.id, reminder, timestamp)

    if days + hours + minutes == 0:
        await reminder.send()
        return await succ.send(ctx, "Alright, wiseguy, I'll send it right now.")

    zeph.reminders.append(reminder)
    timedelta = datetime.datetime.fromtimestamp(timestamp) - datetime.datetime.now()

    return await succ.send(ctx, "Reminder added!", d=f"I'll remind you in {concise_td(timedelta)}.")
