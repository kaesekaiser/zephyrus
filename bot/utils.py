from game import *
from utilities import dice as di, weed as wd, timein as ti, wiki as wk, convert as cv, keys
from unicodedata import name as uni_name
from urllib.error import HTTPError
import hanziconv
import pycantonese
import datetime
import requests
from math import log10, isclose
from sympy import factorint


@zeph.command(
    usage="z!mock [text...]",
    description="DoEs ThIs To YoUr TeXt.",
    help="DoEs ThIs To YoUr TeXt. If no text is given, mocks the message above you.\n\n"
         "`guy: I think Zephyrus is bad\nperson: z!mock\nZephyrus: I tHiNk ZePhYrUs Is BaD`\n\n"
         "You can also reply to a message (using Discord's new reply feature) with `z!mock`, and it will mock "
         "that message."
)
async def mock(ctx: commands.Context, *input_text):
    def multi_count(s, chars):
        return sum([s.count(ch) for ch in chars])

    def dumb(s: str):
        return "".join(
            s[g].lower() if (g - multi_count(s[:g], (" ", "'", ".", "?", "!", "\""))) % 2 == s[0].isupper()
            else s[g].upper() for g in range(len(s))
        )

    text = " ".join(input_text)
    if not text:
        text = "^"  # use new message pointing system

    if ctx.message.reference:  # if the message is a reply to another message
        if input_text:
            raise commands.CommandError("Either reply to a message, OR manually input text. Don't do both.")

        ref = ctx.message.reference
        if ref.cached_message:  # check for the cached message first, it'll be faster
            text = ref.cached_message.content
        else:  # if not, try to manually fetch the referenced message
            try:
                text = (await zeph.get_channel(ref.channel_id).fetch_message(ref.message_id)).content
            except discord.HTTPException:
                raise commands.CommandError("I couldn't find the referenced message, sorry.")
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    elif await get_message_pointer(ctx, text, allow_fail=True):
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
    help="Rolls some dice. Uses standard dice notation:\n`AdB` rolls `A` `B`-sided dice. `A` defaults to 1 "
         "if empty.\n`d%` becomes `d100`, and `dF` rolls Fudge dice, which are `[-1, -1, 0, 0, "
         "1, 1]`.\n`!` explodes a die if it rolls the highest number (that is, it rolls an additional extra "
         "die).\n`!>N`, `!<N`, `!=N` explodes a die if it's greater than, less than, or equal to `N`, "
         "respectively.\n`-H` drops the highest roll. `-L` drops the lowest.\n`+N` at the end of a die "
         "adds `N` to the total roll."
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
         "e.g. `rot 5` shifts all letters down 5 positions, so `hello` becomes `mjqqt`. If you want to "
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
         "`z!vig zephyrus bot` → `asiimkvg`\n`z!devig asiimkvg bot` → `zephyrus`\n"
         "`z!devig asiimkvg fun` → `vyvdsxqm`"
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
    help="Returns the color that corresponds to your input. `random` will randomly generate a color."
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
    help="Shifts the hue of an image by `<value>` (out of 360)."
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
    usage="z!timein <place...>", aliases=["time", "ti"],
    description="Tells you what time it is somewhere.",
    help="Returns the current local time in `<place>`."
)
async def timein(ctx: commands.Context, *, place: str):
    try:
        ret = ti.format_time_dict(ti.time_in(place), False)
    except IndexError:
        raise commands.CommandError("Location not found.")
    except KeyError:
        raise commands.CommandError("Location too vague.")

    address = ti.placename(place)
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
         "`z!pinyin 你好` → `nǐhǎo`"
)
async def pinyin_command(ctx: commands.Context, *, chinese: str):
    return await ctx.send(get_pinyin(chinese))


@zeph.command(
    name="jyutping", aliases=["jp"], usage="z!jyutping <Cantonese text...>",
    description="Romanizes Cantonese text using Jyutping.",
    help="Romanizes Cantonese text according to the Jyutping romanization scheme.\n\n"
         "`z!jyutping 你好` → `nei5hou2`"
)
async def jyutping_command(ctx: commands.Context, *, cantonese: str):
    return await ctx.send(get_jyutping(cantonese))


@zeph.command(
    name="yale", usage="z!yale <Cantonese text...>",
    description="Romanizes Cantonese text using the Yale scheme.",
    help="Romanizes Cantonese text according to the Yale romanization scheme. There's also a Yale romanization "
         "scheme for Mandarin text, but this isn't that, and that's not on this bot.\n\n"
         "`z!yale 你好` → `néihhóu`"
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


def find_user(guild: discord.Guild, s: str):
    def score(txt: str):
        if s.lower() == txt.lower():  # search identical to name
            return 0  # result = 0
        if s.lower() in txt.lower():  # name contains string, prioritizing shorter names + names that start with string
            return 0 + (len(txt) - len(s)) / 32 + (txt.lower().index(s.lower()) != 0)  # 0 < result < 2
        # sort remainder by longest common subsequence, shorter names first
        return 32 - wr.lcs(s.lower(), txt.lower()) + len(txt) / 32 + 2  # result > 2

    # including a very slight bias towards actual username
    return sorted(guild.members, key=lambda c: min(score(c.name), score(c.display_name) + 0.01))[0]


@zeph.command(
    usage="z!avatar [user]",
    description="Returns a link to a user's avatar.",
    help="Returns a link to a user's avatar. If `[user]` is left blank, links your avatar.\n\n"
         "This command works slightly differently in DMs. When used in a server, `[user]` will be converted to a "
         "member of that server. However, in DMs, `[user]` will be converted to any user Zephyrus shares a server "
         "with, if possible."
)
async def avatar(ctx: commands.Context, *, user: str = None):
    if not user:
        user = ctx.author
    else:
        try:
            user = await commands.MemberConverter().convert(ctx, user)
        except commands.BadArgument:
            if not ctx.guild:
                raise commands.CommandError(
                    f"User `@{user}` not found." + (
                        "\nThis looks like a valid username + discriminator, which means this user probably doesn't "
                        "share a server with Zephyrus. Due to a Discord limitation, I can't see users I don't share "
                        "servers with." if re.search(r"#[0-9]{4}$", user) else ""
                    )
                )
            if len(ctx.guild.members) > 1000:
                try:  # more blunt method for large servers, in which lcs() takes too long
                    user = [g for g in ctx.guild.members if g.name.lower() == user.lower()][0]
                except IndexError:
                    raise commands.CommandError(
                        f"User `@{user}` not found.\n"
                        f"This server is large, so please specify their username exactly, or just ping them."
                    )
            else:
                user = find_user(ctx.guild, user)

    av_url = str(user.avatar_url_as(static_format="png"))
    display_name = user.display_name if ctx.guild else str(user)
    return await ctx.send(
        embed=construct_embed(author=author_from_user(user, name=f"{display_name}'s Avatar", url=av_url),
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
            if emote.split(":")[1] not in zeph.all_emojis:
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
    help="Calls the sheriff of `<emoji>`."
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
    help="Searches Wikipedia for `<search>`."
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
    help="`z!foreignwiki <language> <title...>` finds the `<language>` version of the English Wikipedia "
         "article `<title>`.\n`z!foreignwiki all <title...>` lists all languages which have a version "
         "of `<title>`."
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


x_sampa_dict = {
    "d`z`": "ɖ͡ʐ", "t`s`": "ʈ͡ʂ", r"dK\\": "d͡ɮ", "tK": "t͡ɬ", r"dz\\": "d͡ʑ", r"ts\\": "t͡ɕ", "dz`": "d͡ʐ",
    "ts`": "t͡ʂ", "dz": "d͡z", "ts": "t͡s", "dZ": "d͡ʒ", "tS": "t͡ʃ",
    r'\|\\\|\\': 'ǁ', r'G\\_<': 'ʛ', r'J\\_<': 'ʄ', '_B_L': '᷅', '_H_T': '᷄', '_R_F': '᷈', 'b_<': 'ɓ', 'd_<': 'ɗ',
    'g_<': 'ɠ', r'r\\`': 'ɻ', '<F>': '↘', '<R>': '↗', r'_\?\\': 'ˤ', 'd`': 'ɖ', r'h\\': 'ɦ', r'j\\': 'ʝ', 'l`': 'ɭ',
    r'l\\': 'ɺ', 'n`': 'ɳ', r'p\\': 'ɸ', 'r`': 'ɽ', r'r\\': 'ɹ', 's`': 'ʂ', r's\\': 'ɕ', r't`': 'ʈ', r'v\\': 'ʋ',
    r'x\\': 'ɧ', 'z`': 'ʐ', r'z\\': 'ʑ', r'B\\': 'ʙ', r'G\\': 'ɢ', r'H\\': 'ʜ', r'I\\': 'ᵻ', r'J\\': 'ɟ',
    r'K\\': 'ɮ', r'L\\': 'ʟ', r'M\\': 'ɰ', r'N\\': 'ɴ', r'O\\': 'ʘ', r'R\\': 'ʀ', r'U\\': 'ᵿ', r'X\\': 'ħ',
    r'\?\\': 'ʕ', r':\\': 'ˑ', r'@\\': 'ɘ', r'3\\': 'ɞ', r'<\\': 'ʢ', r'>\\': 'ʡ', r'!\\': 'ǃ', r'\|\|': '‖',
    r'\|\\': 'ǀ', r'=\\': 'ǂ',
    r'-\\': '‿', '_"': '̈', r'_\+': '̟', '_-': '̠', '_/': '̌', r'_\\': '̂', '_0': '̥', '_>': 'ʼ', r'_\^': '̯',
    '_}': '̚', '_A': '̘', '_a': '̺', '_B': '̏', '_c': '̜', '_d': '̪', '_e': '̴', '_F': '̂', '_G': 'ˠ', '_H': '́',
    '_h': 'ʰ', '_j': 'ʲ', '_k': '̰', '_L': '̀', '_l': 'ˡ', '_M': '̄', '_m': '̻', '_N': '̼', '_n': 'ⁿ', '_O': '̹',
    '_o': '̞', '_q': '̙', '_R': '̌', '_r': '̝', '_T': '̋', '_t': '̤', '_v': '̬', '_w': 'ʷ', '_X': '̆', '_x': '̽',
    '_=': '̩', '_~': '̃',
    r'\{': 'æ', 'A': 'ɑ', 'B': 'β', 'C': 'ç', 'D': 'ð', 'E': 'ɛ', 'F': 'ɱ', 'G': 'ɣ', 'H': 'ɥ', 'I': 'ɪ', 'J': 'ɲ',
    'K': 'ɬ', 'L': 'ʎ', 'M': 'ɯ', 'N': 'ŋ', 'O': 'ɔ', 'P': 'ʋ', 'Q': 'ɒ', r'R': 'ʁ', 'S': 'ʃ', 'T': 'θ', 'U': 'ʊ',
    'V': 'ʌ', 'W': 'ʍ', 'X': 'χ', 'Y': 'ʏ', 'Z': 'ʒ', '"': 'ˈ', '%': 'ˌ', "'": 'ʲ', '’': 'ʲ', ':': 'ː', '@': 'ə',
    '}': 'ʉ', '1': 'ɨ', '2': 'ø', '3': 'ɜ', '4': 'ɾ', '5': 'ɫ', '6': 'ɐ', '7': 'ɤ', '8': 'ɵ', '9': 'œ', '&': 'ɶ',
    r'\|': '|', r'\^': 'ꜛ', '!': 'ꜜ', '=': '̩', '`': '˞', '~': '̃', r'\.': '.', r'\?': 'ʔ', r'\)': '͡', '0': '∅',
    '-': '', r'\*': ''
}


@zeph.command(
    usage="z!sampa <X-SAMPA text...>",
    description="Converts X-SAMPA to IPA.",
    help="Converts a given string of [X-SAMPA](https://en.wikipedia.org/wiki/X-SAMPA) to the International Phonetic "
         "Alphabet. `*` can be used as an escape character."
)
async def sampa(ctx: commands.Context, *, text: str):
    for rep in x_sampa_dict:
        text = re.sub(r"(?<!\*)" + rep, x_sampa_dict[rep], text)
    return await ctx.send(content=text)


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
                                   "To end the call, use `z!phone hangup`.")

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
        return await phone.send(ctx, f"This server's zPhone number is: `{get_phone_no(ctx.guild)}`")

    if func == "call":
        try:
            return await Call.call(ctx.channel, channel).run()
        except AssertionError:
            raise commands.CommandError(f"No server with the number `{channel}`.")"""


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
    if log10(number) >= 25:
        raise commands.CommandError("Please keep numbers to 25 digits or less.")

    def get_factors(n: int):
        fac_dic = factorint(n)
        return [g for l in [[k] * v for k, v in fac_dic.items()] for g in l]

    return await ClientEmol(":1234:", blue, ctx).say(f"Prime factors of {number}:", d=f"`= {get_factors(number)}`")


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
        raise commands.CommandError(
            "I deprecated the full emote list because it got slightly too obnoxious.\n"
            "Use `z!e <emote>` to look for a specific emote."
        )

    else:
        for arg in args:
            if arg not in zeph.all_emojis:
                if len(args) == 1:
                    raise commands.CommandError("I don't have that emote.")
                else:
                    raise commands.CommandError(f"I don't have the `{arg}` emote.")
        try:
            await ctx.send("".join(str(zeph.all_emojis[g]) for g in args))
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
    name="react", aliases=["r"], usage="z!react <emote>\nz!react <message link> <emote>", hidden=True,
    description="Reacts to a message.",
    help="`z!r <emote>` reacts to the message immediately above yours with the input emote. You can also reply "
         "to a message (using Discord's new reply feature) with `z!r <emote>`, and it will react to that message. "
         "Finally, you can also give a message URL (right-click and hit Copy Message Link), and it will react to "
         "the linked message. Then, you yourself can react with that emote, and Zeph's will disappear - it'll "
         "look like you just used Nitro to react.\n\n"
         "Note that emote names are *case-sensitive*."
)
async def react_command(ctx: commands.Context, *args: str):
    if len(args) > 2 or len(args) < 1:
        raise commands.BadArgument

    if args[-1].strip(":") not in zeph.all_emojis:
        raise commands.CommandError("I don't have that emote.")
    emote = zeph.all_emojis[args[-1].strip(":")]

    if len(args) == 1:
        pointer = "^"
    else:
        pointer = args[0]

    if ctx.message.reference:  # if the message is a reply to another message
        if len(args) == 2:
            raise commands.CommandError("Either reply to a message, OR give a URL. Don't do both.")
        ref = ctx.message.reference
        if ref.cached_message:  # check for the cached message first, it'll be faster
            mess = ref.cached_message
        else:  # if not, try to manually fetch the referenced message
            try:
                mess = await zeph.get_channel(ref.channel_id).fetch_message(ref.message_id)
            except discord.HTTPException:
                raise commands.CommandError("I couldn't find the referenced message, sorry.")

    else:
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

    def remaining_time(self, now: datetime.datetime = datetime.datetime.now()):
        return reminder_td(datetime.datetime.fromtimestamp(self.time) - now)

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


def reminder_td(td: datetime.timedelta):
    """pretty timedelta formatting for reminders"""
    td_minutes = round(td.total_seconds() / 60)  # rounding to account for small variations
    ds, hs, ms = td_minutes // 1440, td_minutes // 60 % 24, td_minutes % 60
    return "".join([
        f"{ds} {plural('day', ds)} " if ds else "",
        f"{hs} {plural('hour', hs)} " if hs else "",
        f"{ms} {plural('minute', ms)}" if ms else "",
    ]).strip()


class RemindNavigator(Navigator):
    def __init__(self, user: User):
        self.user = user
        rems = sorted([g for g in zeph.reminders if g.author == self.user.id], key=lambda c: c.time)
        super().__init__(
            Emol(":alarm_clock:", hexcol("DD2E44")), rems, 4, "Reminders [{page}/{pgs}]", close_on_timeout=True
        )
        self.funcs[zeph.emojis["no"]] = self.close
        for g in range(self.per):
            self.funcs[f"remove {g+1}"] = partial(self.remove_reminder, g)
        self.funcs["remove all"] = self.remove_all

    @property
    def rems(self):
        return sorted([g for g in zeph.reminders if g.author == self.user.id], key=lambda c: c.time)

    @property
    def pgs(self):
        return ceil(len(self.rems) / self.per)

    async def remove_reminder(self, n: int):
        try:
            rem = page_list(self.rems, self.per, self.page)[n]
        except IndexError:  # if there aren't that many listed on the page, do nothing
            return

        zeph.reminders.remove(rem)
        await succ.edit(self.message, "Reminder removed.")
        if len(self.rems) == 0:  # if you just removed your only reminder, close the menu
            self.closed_elsewhere = True
            await asyncio.sleep(2)
            return await self.close()
        else:
            if self.page > self.pgs:
                self.page -= 1
            return await asyncio.sleep(2)

    async def remove_all(self):
        for rem in list(self.rems):
            zeph.reminders.remove(rem)
        await succ.edit(self.message, "All reminders removed.")
        await asyncio.sleep(2)
        self.closed_elsewhere = True
        return await self.close()

    @property
    def con(self):
        now = datetime.datetime.now()

        return self.emol.con(
            self.title.format(page=self.page, pgs=self.pgs),
            d="\n".join(
                f"**`[{g+1}]`** {j.text} (in **{j.remaining_time(now)}**)"
                for g, j in enumerate(page_list(self.rems, self.per, self.page))
            ) + "\n\nTo remove a reminder, say `remove <#>` in chat, e.g. `remove 1`. "
                "You can also say `remove all` to get rid of all your reminders at once."
        )

    async def get_emoji(self, ctx: commands.Context):
        def pred(mr: MR, u: User):
            if isinstance(mr, discord.Message):
                return u == ctx.author and mr.channel == ctx.channel and mr.content in self.funcs.keys()
            else:
                return u == ctx.author and mr.message == self.message and mr.emoji in self.legal

        mess = (await zeph.wait_for('reaction_or_message', timeout=300, check=pred))[0]

        if isinstance(mess, discord.Message):
            try:
                await mess.delete()
            except discord.HTTPException:
                pass
            return mess.content
        else:
            return mess.emoji

    async def close(self):
        if len(self.rems) == 0:
            await self.emol.edit(self.message, "Menu closed; you have no more reminders set.")
        else:
            await self.emol.edit(self.message, "This menu has closed.")
        await self.remove_buttons()


@zeph.command(
    name="remindme", aliases=["remind", "rme", "rem"], usage="z!remindme <reminder...> in <time...>\nz!remindme list",
    description="Reminds you of something later.",
    help="`z!remindme <reminder> in <time>` sets the bot to DM you with a reminder in a certain amount of time. "
         "`<reminder>` can be anything. `<time>` can use any combination of integer days, hours, or minutes, "
         "separated by spaces and in that order. `z!remindme list` lists your set reminders, and lets you remove any "
         "if need be. **Make sure your DMs are open, or else the reminder won't send.**\n\n"
         "e.g. `z!remindme eat food in 2 hours`, `z!rme work on essay in 5 hours 30 minutes`, or "
         "`z!remind talk to Sam in 3 days`."
)
async def remind_command(ctx: commands.Context, *text: str):
    # leaving input text as a list, rather than a single string like usual, to make splitting easier

    if "in" not in text:
        if " ".join(text).lower() in ["list", "edit", "remove", "delete"]:
            if not [g for g in zeph.reminders if g.author == ctx.author.id]:
                return await Emol(":alarm_clock:", hexcol("DD2E44")).send(ctx, "You have no reminders set currently.")

            return await RemindNavigator(ctx.author).run(ctx)

        raise commands.BadArgument

    if not ctx.author.dm_channel:
        try:
            await ctx.author.create_dm()
        except discord.HTTPException:
            raise commands.CommandError("I can't DM you! Are your DMs open?\n`z!remindme` uses DMs to send reminders.")

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
        await succ.send(ctx, "Alright, wiseguy, I'll send it right now.")
        try:
            return await reminder.send()
        except discord.HTTPException:
            raise commands.CommandError("Never mind, I can't DM you. Are your DMs open?")

    zeph.reminders.append(reminder)
    timedelta = datetime.datetime.fromtimestamp(timestamp) - datetime.datetime.now()

    return await succ.send(
        ctx, "Reminder added!", d=f"I'll remind you in {reminder_td(timedelta)}."
    )


@zeph.command(
    name="weather", usage="z!weather <location...>",
    description="Shows the weather somewhere.",
    help="Shows the weather in `<location>` - condition, temperature, highs and lows, rain chance, etc. Weather data "
         "might be delayed by a couple minutes.\n\n"
         "`<location>` is converted to an actual place by [Google's geocoding API]"
         "(https://developers-dot-devsite-v2-prod.appspot.com/maps/documentation/utils/geocoder) (same as `z!timein`)."
)
async def weather_command(ctx: commands.Context, *, location: str):
    def heading_direction(heading: float):
        dirs = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW", "N"
        ]
        return dirs[round(heading * 16 / 360)]

    def format_kelvin(k: float):
        return f"**{ti.fahr(k)}° F** (**{round(k - 273.15)}° C**)"

    def conditions(r: dict):
        return "; ".join(
            f"{[e for e, v in weather_emotes.items() if g['id'] in v][0]} {g['description']}"
            for g in r['current']['weather']
        )

    try:
        lat_long = ti.lat_long(location)
    except IndexError:
        raise commands.CommandError("Location not found.")

    req = requests.get(ti.weather_url.format(**lat_long, key=keys.open_weather)).json()
    title = f"Weather in {ti.short_placename(location)}"

    weather_emotes = {  # weather condition codes to emotes
        ":sunny:": (800, ),
        ":white_sun_small_cloud:": (801, ),
        ":partly_sunny:": (802, ),
        ":white_sun_cloud:": (803, ),
        ":cloud:": (701, 711, 721, 731, 741, 751, 761, 804),
        ":thunder_cloud_rain:": (200, 201, 202, 210, 211, 212, 221, 230, 231, 232),
        ":cloud_rain:": (300, 301, 302, 310, 311, 312, 313, 314, 321, 500, 501, 502, 503, 504, 520, 521, 522, 531),
        ":cloud_snow:": (511, ),
        ":snowflake:": (600, 601, 602, 611, 612, 613, 615, 616, 620, 621, 622),
        ":volcano:": (762, ),  # volcanic ash
        ":dash:": (771, ),  # squalls
        ":tornado:": (781, )  # self-explanatory
    }

    return await ClientEmol(":umbrella2:", hexcol("9266CC"), ctx).say(
        title,
        d=f"**{conditions(req)}** / :thermometer: {format_kelvin(req['current']['temp'])}\n---\n"
        f":sweat_drops: humidity: **{req['current']['humidity']}%** / "
        f":thought_balloon: feels like: {format_kelvin(req['current']['feels_like'])}\n"
        f":wind_blowing_face: wind: ** {heading_direction(req['current']['wind_deg'])} "
        f"{round(req['current']['wind_speed'] * 2.23693629)} mph** "
        f"(**{round(req['current']['wind_speed'] * 3.6)} kph**)\n---\n"
        f":fire: daily high: {format_kelvin(req['daily'][0]['temp']['max'])} / "
        f":ice_cube: low: {format_kelvin(req['daily'][0]['temp']['min'])}\n"
        f":umbrella: rain chance: **{round(req['daily'][0]['pop'] * 100)}%**",
        timestamp=datetime.datetime.utcfromtimestamp(req['current']['dt']),
        footer=ti.placename(location)
    )


@zeph.command(
    name="role", usage="REDIRECT", hidden=True
)
async def role_redirect_command(ctx: commands.Context):
    return await lost.send(
        ctx, "You might be looking for...",
        d="**`role`** might refer to multiple commands:\n"
          "- `z!selfroles`, which lets you self-assign roles.\n"
          "- `z!rolemembers`, which lists all the members of a role."
    )


class CounterNavigator(Navigator):
    def __init__(self, start_at: int = 0):
        super().__init__(
            Emol(":1234:", blue), [], 1, "Counter", prev=zeph.emojis["minus"], nxt=zeph.emojis["plus"]
        )
        self.page = start_at
        self.mode = "count"
        self.funcs[zeph.emojis["settings"]] = self.change_mode

    async def change_mode(self):
        if self.mode == "count":
            self.mode = "settings"
        else:
            self.mode = "count"

    @property
    def con(self):
        if self.mode == "count":
            return self.emol.con(
                self.title, d=f"**{add_commas(self.page)}**",
                footer="Use the buttons to count up or down."
            )
        else:
            return self.emol.con(
                "Settings",
                d="To change a setting, say `<option>:<value>` - for example, `increment:5`. You can "
                  "reset the counter via `value:0`.\n\n"
                  "`increment` must be an integer between 1 and 999,999,999.\n"
                  "`value` must be an integer between -999,999,999 and 999,999,999.\n"
                  "`title` must be less than 200 characters.",
                fs={"Increment by (`increment`)": add_commas(self.per),
                    "Current value (`value`)": add_commas(self.page),
                    "Title (`title`)": self.title},
                same_line=True
            )

    def advance_page(self, direction: int):
        if direction:
            self.page = round(self.page + self.per) if direction > 0 else round(self.page - self.per)

    @staticmethod
    def is_valid_setting(s: str):
        if s.count(":") != 1:
            return False

        option, value = s.lower().split(":")

        if option == "increment":
            return can_int(value) and len(value) < 10 and int(value) > 0
        elif option == "value":
            return can_int(value) and len(value.strip("-")) < 10
        elif option == "title":
            return len(value) <= 200
        else:
            return False

    def apply_settings_change(self, option: str, value: str):
        """Assumes that the string <option>:<value> passes is_valid_setting()."""

        if option.lower() == "increment":
            self.per = int(value)
        if option.lower() == "value":
            self.page = int(value)
        if option.lower() == "title":
            self.title = value

    async def get_emoji(self, ctx: commands.Context):
        if self.mode == "settings":
            def pred(mr: MR, u: User):
                if isinstance(mr, discord.Message):
                    return u == ctx.author and mr.channel == ctx.channel and self.is_valid_setting(mr.content)
                else:
                    return u == ctx.author and mr.emoji in self.funcs and mr.message.id == self.message.id

            mess = (await zeph.wait_for(
                'reaction_or_message', timeout=300, check=pred
            ))[0]
            if isinstance(mess, discord.Message):
                await mess.delete()
                self.apply_settings_change(*mess.content.split(":"))
                return "wait"
            elif isinstance(mess, discord.Reaction):
                return mess.emoji

        return (await zeph.wait_for(
            'reaction_add', timeout=300, check=lambda r, u: r.emoji in self.legal and
            r.message.id == self.message.id and u == ctx.author
        ))[0].emoji


@zeph.command(
    name="counter", aliases=["count"], usage="z!counter [starting value]",
    description="Runs a counter, so you can count.",
    help="Runs a simple counter. Count up or down by an adjustable value using the reaction buttons. I wouldn't "
         "recommend using this command if you have to repeatedly and *quickly* change the value, however; due to "
         "Discord's rate limits, some of your clicks might get lost. Optional argument is the value the counter starts "
         "at; this defaults to 0."
)
async def counter_command(ctx: commands.Context, start_value: int = 0):
    return await CounterNavigator(start_value).run(ctx)


@zeph.command(
    name="yesno", aliases=["poll", "yn"], usage="z!yesno <poll question...>",
    description="Sets up a simple yes/no poll.",
    help="Sets up a very simple yes-or-no poll for other server members to answer. You provide a question, and "
         "Zeph creates a fancy-looking box, with fancy-looking reactions. Just a slightly faster and slightly "
         "prettier way to collect opinions."
)
async def yesno_command(ctx: commands.Context, *, question: str):
    if len(question) > 1800:
        raise commands.CommandError("Keep questions to under 1800 characters.")

    if isinstance(ctx.channel, discord.DMChannel):
        raise commands.CommandError("This command can't be run in DMs.")

    emol = Emol(zeph.emojis["yesno"], hexcol("7289DA"))

    message = await emol.send(ctx, "Yea or Nay?", d=question)
    await message.add_reaction(zeph.emojis["yea"])
    await message.add_reaction(zeph.emojis["nay"])

    return
