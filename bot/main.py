from utils import *
from sys import version_info
import datetime


aliases = {
    "conn4": "connect4", "dice": "roll", "caesar": "rot", "vig": "vigenere", "devig": "devigenere", "?": "help",
    "h": "help", "sq": "square", "fsq": "flagsquare", "small": "smallcaps", "c": "convert", "conv": "convert",
    "weed": "sayno", "pick": "choose", "colour": "color", "hue": "hueshift", "trans": "translate",
    "badtrans": "badtranslate", "rune": "runes"
}


commandCategories = {
    "Games": ["connect4", "jotto", "anagrams", "boggle", "duel", "risk"],
    "Text": ["mock", "expand", "square", "flagsquare", "clap", "scramble", "smallcaps"],
    "Ciphers": ["rot", "rot13", "vigenere", "devigenere"],
    "Utilities": ["roll", "convert", "sayno", "choose", "8ball", "color", "timein", "avatar"],
    "Images": ["hueshift", "invert"],
    "Languages": ["pinyin", "jyutping", "translate", "badtranslate", "runes"],
    "Bot": ["ping", "help", "invite", "about"]
}


commandFormats = {
    "connect4": "z!connect4 <@opponent>",
    "jotto": "z!jotto",
    "anagrams": "z!anagrams",
    "boggle": "z!boggle",
    "duel": "z!duel <@opponent>",
    "risk": "see z!risk help",
    "mock": "z!mock <text...>",
    "expand": "z!expand <text...>",
    "square": "z!square <text...>",
    "flagsquare": "z!flagsquare <text...>",
    "clap": "z!clap <text...>",
    "ping": "z!ping",
    "roll": "z!roll <dice>",
    "rot": "z!rot <shift #> <text...>",
    "rot13": "z!rot13 <text...>",
    "vigenere": "z!vigenere <word> <keys...>",
    "devigenere": "z!devigenere <word> <keys...>",
    "invite": "z!invite",
    "scramble": "z!scramble <text...>",
    "smallcaps": "z!smallcaps <text...>",
    "convert": "z!convert <number> <unit...> to <unit...>\nz!convert <number> <unit...>",
    "sayno": "z!sayno",
    "choose": "z!choose <option...> or <option...> [etc.]",
    "8ball": "z!8ball <question...>",
    "color": "z!color <hex code>\nz!color <red> <green> <blue>\nz!color random",
    "hueshift": "z!hueshift <image url> <value>",
    "invert": "z!invert <image url>",
    "about": "z!about",
    "timein": "z!timein <place...>",
    "pinyin": "z!pinyin <Chinese text...>",
    "jyutping": "z!jyutping <Chinese text...>",
    "translate": "z!translate <from> <to> <text...>",
    "badtranslate": "z!badtranslate <text...>",
    "avatar": "z!avatar <@user>",
    "runes": "z!runes <runic text...>",

    "help": "z!help [command]"
}


descs = {
    "connect4": "Challenges an opponent to a nice game of Connect Four. Nothing is at stake - except your pride.",
    "jotto": "Plays a game of Jotto. Similar to Mastermind, but with words. I'll choose a random four-letter word, "
             "and you start guessing other four-letter words. I'll tell you how many of the letters in your guess "
             "are also in my word. The goal is to figure out my word.\n\ne.g. if my word is ``area``, then the guess "
             "``cats`` returns ``1``, ``near`` returns ``3``, and ``away`` returns ``2``. It doesn't matter what "
             "position the letters are in - ``acts`` and ``cats`` are functionally the same guess.",
    "anagrams": "Plays a game of Anagrams. I'll randomly pick eight letters, and you name as many words as possible "
                "that you can spell with those eight letters.",
    "boggle": "Plays a game of Boggle. I'll generate a board by rolling some letter dice, and you name as many "
              "words as possible that you can spell by stringing those letters together. The letters have to be next "
              "to each other on the board, and you can't use the same die more than once in a word.",
    "duel": "Challenges an opponent to a duel. Hope you're quick to the draw.",
    "risk": "currently in a development state",
    "mock": "DoEs ThIs To YoUr TeXt.",
    "expand": "D o e s   t h i s   t o   y o u r   t e x t .\nThere should be more spaces here, but Discord for some "
              "reason doesn't like extraneous spaces in embeds. Oh well, you get the idea.",
    "square": ":regional_indicator_d: :regional_indicator_o: :regional_indicator_e: :regional_indicator_s:   "
              ":regional_indicator_t: :regional_indicator_h: :regional_indicator_i: :regional_indicator_s:   "
              ":regional_indicator_t: :regional_indicator_o:   :regional_indicator_y: :regional_indicator_o: "
              ":regional_indicator_u: :regional_indicator_r:   :regional_indicator_t: :regional_indicator_e: "
              ":regional_indicator_x: :regional_indicator_t: .",
    "flagsquare": "Same as ``z!square``, but leaves out the spaces - so sometimes country flags appear. That is, it "
                  ":flag_do::flag_es: :flag_th::flag_is: :flag_to: :regional_indicator_y::regional_indicator_o:"
                  ":regional_indicator_u::regional_indicator_r: :regional_indicator_t::regional_indicator_e:"
                  ":regional_indicator_x::regional_indicator_t:.",
    "clap": ":clap:Does:clap:this:clap:to:clap:your:clap:text.",
    "ping": "Pong!",
    "roll": "Rolls some dice. Uses standard dice notation:\n``AdB`` rolls ``A`` ``B``-sided dice. ``A`` defaults to 1 "
            "if empty.\n``d%`` becomes ``d100``, and ``dF`` rolls Fudge dice, which are ``[-1, -1, 0, 0, "
            "1, 1]``.\n``!`` explodes a die if it rolls the highest number (that is, it rolls an additional extra "
            "die).\n``!>N``, ``!<N``, ``!=N`` explodes a die if it's greater than, less than, or equal to ``N``, "
            "respectively.\n``-H`` drops the highest roll. ``-L`` drops the lowest.\n``+N`` at the end of a die "
            "adds ``N`` to the total roll.",
    "rot": "Puts text through a Caesar cipher, which shifts all letters some number of positions down the alphabet.\n\n"
           "e.g. ``rot 5`` shifts all letters down 5 positions, so ``hello`` becomes ``mjqqt``. If you want to "
           "decipher a Caesar'd text, put in a negative shift number.",
    "rot13": "Puts text through the ROT13 cipher, which is also a Caesar cipher with a shift of 13. Astute observers "
             "will note that putting ROT13 text back through ROT13 returns the original text.",
    "vigenere": "Puts text through a [Vigenere cipher](https://en.wikipedia.org/wiki/Vigen%C3%A8re_cipher) using the "
                "provided keys. Note that the text can't contain any spaces, so use underscores or dashes if you want "
                "to space it.",
    "devigenere": "Deciphers Vigenere'd text using the provided keys. Using a different set of keys than the text "
                  "was encoded with, will more than likely return a garbled mess.\n\n"
                  "``z!vig zephyrus bot`` > ``asiimkvg``\n``z!devig asiimkvg bot`` > ``zephyrus``\n"
                  "``z!devig asiimkvg fun`` > ``vyvdsxqm``",
    "invite": "Spits out the invite link for Zephyrus, so you can bring it to other servers.",
    "scramble": "eDso thsi ot uryo xtt.e",
    "smallcaps": "Dᴏᴇs ᴛʜɪs ᴛᴏ ʏᴏᴜʀ ᴛᴇxᴛ.",
    "convert": "Converts between units of measurement. More info at "
               "https://github.com/kaesekaiser/zephyrus/blob/master/docs/convert.md.",
    "sayno": "Say no to drugs.",
    "choose": "Chooses one from a list of options.",
    "8ball": "The divine magic 8-ball answers your yes-or-no questions.",
    "color": "Returns the color that corresponds to your input. ``random`` will randomly generate a color.",
    "hueshift": "Shifts the hue of an image by ``<value>`` (out of 360).",
    "invert": "Inverts the colors of an image.",
    "about": "Shows some information about the bot.",
    "timein": "Returns the current local time in ``<place>``.",
    "pinyin": "Romanizes Chinese text according to the Hanyu Pinyin romanization scheme - that is, it turns the "
              "Chinese characters into Latin syllables that sound like their Mandarin pronunciations.\n\n"
              "``z!pinyin 你好`` > ``nǐ hǎo``",
    "jyutping": "Romanizes Chinese text according to the Jyutping romanization scheme, which is used for the "
                "Cantonese language.\n\n``z!jyutping 你好`` > ``nei5 hou3``",
    "translate": "Via Google Translate, translates <text> between languages. <from> and <to> must be either the "
                 "full names of the language, or the [code](https://cloud.google.com/translate/docs/languages) "
                 "for the language. ``chinese`` defaults to Simplified Chinese; for Traditional, use "
                 "``traditional-chinese`` or ``zh-tw``.\n\n"
                 "``z!translate English French Hello, my love`` > ``Bonjour mon amour``",
    "badtranslate": "Via Google Translate, translates English language text back and forth between twenty-five random "
                    "languages. The result is a garbled mess which only vaguely resembles the original, if at all.\n\n"
                    "``z!badtranslate This is an example sentence.`` > ``This is his word.``",
    "avatar": "Returns a link to a user's avatar.",
    "runes": "Transcribes [medieval Nordic runes](https://en.wikipedia.org/wiki/Medieval_runes) into Latin letters.",

    "help": "Shows the usage + format of a command. If no command is provided, lists all available commands."
}


@zeph.command(name="help", aliases=["?", "h"])
async def help_(ctx: commands.Context, comm: str=None):
    hep = ClientEmol(":grey_question:", hexcol("59c4ff"), ctx)
    spacing = "\u00a0" * 5

    comm = aliases.get(comm).lower() if aliases.get(comm) else comm
    if comm not in commandFormats:
        return await hep.say(
            "Full Command List",
            d="\n".join([f"**__{g}__**\n{spacing}``{'``, ``'.join(sorted(j))}``" for g, j in commandCategories.items()])
              + "\n\nFor help with any of these, use ``z!help [command]``."
        )
    else:
        help_dict = {"Format": f"``{commandFormats[aliases.get(comm, comm)]}``"}
        if [g for g, j in aliases.items() if j == comm]:
            help_dict["Aliases"] = f'``{", ".join([f"z!{g}" for g, j in aliases.items() if j == comm])}``'
        return await hep.say(f"``z!{comm}``", d=descs[comm], fs=help_dict, il=True)


@zeph.command()
async def invite(ctx: commands.Context):
    return await ctx.send(content='https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8192'
                          .format(zeph.user.id))


zephBuild = "2.0 v7"


@zeph.command()
async def about(ctx: commands.Context):
    def runtime_format(dt: datetime.timedelta):
        if dt.days:
            return f"{dt.days} d {dt.seconds // (24 * 60)} h {dt.seconds // 60} m"
        return f"{dt.seconds // (24 * 60)} h {dt.seconds // 60} m {int(dt.seconds) % 60} s"
    py_version = "{}.{}.{}".format(*version_info)

    return await ClientEmol(":robot:", hexcol("6fc96f"), ctx).say(
        author=author_from_user(zeph.user, f"\u2223 {zeph.user.name}"),
        d=f"**Connected to:** {len(zeph.guilds) - len(getattr(zeph, 'fortServers'))} servers / "
        f"{len(set(zeph.users))} users\n"
        f"**Runtime:** {runtime_format(datetime.datetime.now() - getattr(zeph, 'readyTime'))}\n"
        f"**Build:** {zephBuild} / Python {py_version}\n"
        f"[GitHub](https://github.com/kaesekaiser/zephyrus) / "
        f"[Invite](https://discordapp.com/oauth2/authorize?client_id={zeph.user.id}&scope=bot&permissions=8192) / "
        f"[Testing](https://discord.gg/t8CBnHP)",
        thumbnail=zeph.user.avatar_url
    )


@zeph.event
async def on_ready():
    setattr(zeph, "readyTime", datetime.datetime.now())
    print(f"ready at {getattr(zeph, 'readyTime')}")
    print([g for g in zeph.all_commands if g not in aliases])
    print([g for g in zeph.all_commands if (g not in commandFormats or g not in descs or g not in
           [j for k in commandCategories.values() for j in k]) and g not in aliases])
    setattr(zeph, "fortServers", [g for g in zeph.guilds if g.owner.id in [238390171022655489, 474398677599780886]])


@zeph.event
async def on_command_error(ctx: commands.Context, exception):
    command = ctx.message.content.split()[0].split("!")[1]
    if type(exception) in [commands.errors.MissingRequiredArgument, commands.errors.BadArgument,
                           commands.errors.TooManyArguments]:
        await err.send(
            ctx, f"Format: ``{'`` or ``'.join(commandFormats[aliases.get(command, command)].splitlines())}``"
        )
    elif type(exception) == commands.errors.CommandNotFound:
        pass
    elif type(exception) == commands.CommandError:
        await err.send(ctx, str(exception))
    else:
        await err.send(ctx, f"``{str(exception)}``")
        raise exception
