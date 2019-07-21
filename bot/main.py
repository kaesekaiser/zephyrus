from planes import *
from sys import version_info
import datetime
import subprocess


aliases = {
    "conn4": "connect4", "dice": "roll", "caesar": "rot", "vig": "vigenere", "devig": "devigenere", "?": "help",
    "h": "help", "sq": "square", "fsq": "flagsquare", "small": "smallcaps", "c": "convert", "conv": "convert",
    "weed": "sayno", "pick": "choose", "colour": "color", "hue": "hueshift", "trans": "translate", "p": "planes",
    "badtrans": "badtranslate", "rune": "runes", "wiki": "wikipedia", "fw": "foreignwiki", "dex": "pokedex",
    "bed": "bedtime", "jp": "jyutping", "sherriff": "sheriff", "pkmn": "pokemon", "pk": "pokemon", "nl": "narahlena",
    "simp": "simplified", "trad": "traditional", "fac": "factors"
}


commandCategories = {
    "Games": ["connect4", "jotto", "anagrams", "boggle", "duel", "epitaph", "pokedex", "planes", "pokemon"],
    "Text": ["mock", "expand", "square", "flagsquare", "clap", "scramble", "smallcaps", "sheriff"],
    "Ciphers": ["rot", "rot13", "vigenere", "devigenere"],
    "Utilities": ["roll", "convert", "sayno", "choose", "8ball", "color", "timein", "avatar", "wikipedia", "bedtime",
                  "factors"],
    "Images": ["hueshift", "invert"],
    "Languages": ["pinyin", "jyutping", "translate", "badtranslate", "runes", "foreignwiki", "yale", "narahlena",
                  "simplified", "traditional"],
    "Bot": ["ping", "help", "invite", "about"]
}


commandFormats = {
    "connect4": "z!connect4 <@opponent>",
    "jotto": "z!jotto",
    "anagrams": "z!anagrams",
    "boggle": "z!boggle",
    "duel": "z!duel <@opponent>",
    "risk": "see z!risk help",
    "mock": "z!mock <text...>\nz!mock",
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
    "pinyin": "z!pinyin <Mandarin text...>",
    "jyutping": "z!jyutping <Cantonese text...>",
    "translate": "z!translate <from> <to> <text...>",
    "badtranslate": "z!badtranslate <text...>",
    "avatar": "z!avatar <@user>",
    "runes": "z!runes <runic text...>",
    "sheriff": "z!sheriff <emoji>",
    "wikipedia": "z!wikipedia <search...>",
    "foreignwiki": "z!foreignwiki <language> <title...>\nz!foreignwiki all <title...>",
    "epitaph": "z!epitaph\nz!epitaph handsoff",
    "pokedex": "z!pokedex [pok\u00e9mon...]\nz!pokedex [dex number]\nz!pokedex help",
    "planes": "z!planes help",
    "bedtime": "z!bedtime\nz!bedtime stop",
    "yale": "z!yale <Cantonese text...>",
    "pokemon": "z!pokemon help",
    "narahlena": "z!narahlena <Narahlena text...>",
    "simplified": "z!simplified <Traditional Chinese text...>",
    "traditional": "z!traditional <Simplified Chinese text...>",
    "factors": "z!factors <integer>",

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
    "mock": "DoEs ThIs To YoUr TeXt. If no text is given, mocks the message immediately above the command.\n\n"
            "``guy: I think Zephyrus is bad\nperson: z!mock\nZephyrus: I tHiNk ZePhYrUs Is BaD``",
    "expand": "D o e s \u00a0 t h i s \u00a0 t o \u00a0 y o u r \u00a0 t e x t .",
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
                  "``z!vig zephyrus bot`` → ``asiimkvg``\n``z!devig asiimkvg bot`` → ``zephyrus``\n"
                  "``z!devig asiimkvg fun`` → ``vyvdsxqm``",
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
              "``z!pinyin 你好`` → ``nǐhǎo``",
    "jyutping": "Romanizes Cantonese text according to the Jyutping romanization scheme.\n\n"
                "``z!jyutping 你好`` → ``nei5hou2``",
    "translate": "Via Google Translate, translates ``<text>`` between languages. ``<from>`` and ``<to>`` must be "
                 "either the name of the language or the [code](https://cloud.google.com/translate/docs/languages) "
                 "for the language. ``chinese`` defaults to Simplified Chinese; for Traditional, use "
                 "``traditional-chinese`` or ``zh-tw``. You can also use ``auto`` or ``detect`` for the detect "
                 "language option.\n\n"
                 "``z!translate English French Hello, my love`` → ``Bonjour mon amour``\n"
                 "``z!translate auto en Hola, señor`` → ``Hello sir``",
    "badtranslate": "Via Google Translate, translates English language text back and forth between twenty-five random "
                    "languages. The result is a garbled mess which only vaguely resembles the original, if at all.\n\n"
                    "``z!badtranslate This is an example sentence.`` → ``That's my law.``",
    "avatar": "Returns a link to a user's avatar.",
    "runes": "Transcribes [medieval Nordic runes](https://en.wikipedia.org/wiki/Medieval_runes) into Latin letters.",
    "sheriff": "Calls the sheriff of ``<emoji>``.",
    "wikipedia": "Searches Wikipedia for ``<search>``.",
    "foreignwiki": "``z!foreignwiki <language> <title...>`` finds the ``<language>`` version of the English Wikipedia "
                   "article ``<title>``.\n``z!foreignwiki all <title...>`` lists all languages which have a version "
                   "of ``<title>``.",
    "epitaph": "Runs a game of [Max Kreminski's Epitaph](https://mkremins.github.io/epitaph/). As an "
               "ascended civilization, lead a burgeoning planet to join you in the stars. Play the original.\n\n"
               "``z!epitaph handsoff`` runs a game without player input.",
    "pokedex": "Opens the Pok\u00e9dex! ``z!dex [pok\u00e9mon...]`` or ``z!dex [dex number]`` will start you at a "
               "specific Pok\u00e9mon; otherwise, it starts at everyone's favorite, Bulbasaur. "
               "``z!dex help`` gives help with navigating the dex.\n\nYou can even name a specific form of a "
               "Pok\u00e9mon - e.g. ``z!dex giratina origin`` starts at Giratina, in Origin Forme.",
    "planes": "Lets you play a game I'm just calling Planes. It's a sort of idle shipping simulator - really similar "
              "to a mobile game called Pocket Planes - where you buy airports and airplanes, and use them to take jobs "
              "back and forth for profit. There's many sub-commands, so do ``z!planes help`` for more info on what "
              "exactly you can do, and how to do it.",
    "bedtime": "Lets you set up a bedtime reminder at a certain time, so you can sleep like a normal human. Just do "
               "``z!bedtime`` and I'll walk you through the process. Do ``z!bedtime stop`` if you want to turn off "
               "the reminder after you've set it up.",
    "yale": "Romanizes Cantonese text according to the Yale romanization scheme. There's also a Yale romanization "
            "scheme for Mandarin text, but this isn't that, and that's not on this bot.\n\n"
            "``z!yale 你好`` → ``néihhóu``",
    "pokemon": "Performs a variety of Pok\u00e9mon-related functions. I'm continually adding to this, so just use "
               "``z!pokemon help`` for more details.",
    "narahlena": "Converts ASCII Narahlena input into actual Narahlena orthography.\n\n"
                 "[Narahlena](https://fort.miraheze.org/wiki/Narahlena) is a constructed language Fort's making. This "
                 "command probably doesn't mean much to most people. Feel free to check it out, though.",
    "simplified": "Converts Traditional Chinese characters to Simplified Chinese.",
    "traditional": "Converts Simplified Chinese characters to Traditional Chinese.",
    "factors": "Returns the prime factors of <integer>.",

    "help": "Shows the usage + format of a command. If no command is provided, lists all available commands."
}


@zeph.command(name="help", aliases=["?", "h"])
async def help_(ctx: commands.Context, comm: str = None):
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


@zeph.command()
async def about(ctx: commands.Context):
    def runtime_format(dt: datetime.timedelta):
        if dt.days:
            return f"{dt.days} d {dt.seconds // (60 * 60) % 24} h {dt.seconds // 60 % 60} m"
        return f"{dt.seconds // (60 * 60)} h {dt.seconds // 60 % 60} m {int(dt.seconds) % 60} s"

    py_version = "{}.{}.{}".format(*version_info)
    step1 = str(wk.PyQuery(
        "https://github.com/kaesekaiser/zephyrus/releases/latest", {"title": "CSS"}
    ))  # this is a really gross way of getting the version I know. but shut up
    step2 = re.search(r"octicon octicon-tag.*?</span>", step1, re.S)[0]
    zeph_version = re.search(r"(?<=>).*?(?=</span>)", step2)[0]

    return await ClientEmol(":robot:", hexcol("6fc96f"), ctx).say(
        author=author_from_user(zeph.user, f"\u2223 {zeph.user.name}"),
        d=f"**Connected to:** {len(zeph.guilds) - len(getattr(zeph, 'fortServers'))} servers / "
        f"{len(set(zeph.users))} users\n"
        f"**Commands:** {len([g for g in zeph.commands if g not in aliases])}\n"
        f"**Runtime:** {runtime_format(datetime.datetime.now() - getattr(zeph, 'readyTime'))}\n"
        f"**Build:** {zeph_version} / Python {py_version}\n"
        f"[GitHub](https://github.com/kaesekaiser/zephyrus) / "
        f"[Invite](https://discordapp.com/oauth2/authorize?client_id={zeph.user.id}&scope=bot&permissions=8192)",
        thumbnail=zeph.user.avatar_url
    )


@zeph.command(hidden=True)
async def update(ctx: commands.Context):
    if ctx.author.id != 238390171022655489:
        raise commands.CommandError("You don't have permission to run that command.")

    await ctx.send(content="be right back :wave:")
    await zeph.logout()
    subprocess.Popen(["sudo", "bash", "/home/pi/Documents/update.sh"])


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


async def sampa(ctx: commands.Context):
    notes = ["".join(g) for g in re.findall(sampa_regex, ctx.message.content)]
    ret = []
    for note in notes:
        if note[0] == "x":
            for rep in x_sampa_dict:
                note = re.sub(r"(?<!\*)" + rep, x_sampa_dict[rep], note)
        ret.append(note[1:])
    return await ctx.send(content="\n".join(ret))


@zeph.event
async def on_ready():
    setattr(zeph, "readyTime", datetime.datetime.now())
    print(f"ready at {getattr(zeph, 'readyTime')}")
    print([g for g in zeph.all_commands if g not in aliases])
    print([g for g in zeph.all_commands if g not in aliases and not zeph.all_commands[g].hidden and
          (g not in commandFormats or g not in descs or g not in [j for k in commandCategories.values() for j in k])])
    setattr(zeph, "fortServers", [g for g in zeph.guilds if g.owner.id in [238390171022655489, 474398677599780886]])
    zeph.loop.create_task(initialize_planes())
    zeph.loop.create_task(zeph.load_romanization())


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
        try:
            await err.send(ctx, str(exception))
        except discord.errors.HTTPException:
            await err.send(ctx, "Error!", desc=str(exception))
    else:
        await err.send(ctx, f"``{str(exception)}``")
        raise exception


sampa_regex = re.compile(r"((?<=\s|`)[xz][\[/].+?[\]/](?=\s|`))|(^[xz][\[/].+?[\]/](?=\s|$))", re.S + re.M)


@zeph.event
async def on_message(message: discord.Message):
    zeph.dispatch("reaction_or_message", message, message.author)
    if re.search(sampa_regex, message.content):
        await sampa(await zeph.get_context(message))
    await zeph.process_commands(message)


@zeph.event
async def on_reaction_add(reaction: discord.Reaction, user: User):
    zeph.dispatch("reaction_or_message", reaction, user)
    zeph.dispatch("button", reaction, user, True)


@zeph.event
async def on_reaction_remove(reaction: discord.Reaction, user: User):
    zeph.dispatch("button", reaction, user, False)


async def regularly_save():
    while True:
        await asyncio.sleep(60)
        zeph.save()


zeph.loop.create_task(regularly_save())
