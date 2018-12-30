from planes import *
validServers = []


aliases = {
    "conn4": "connectfour", "?": "help", "h": "help", "$": "bal", "sq": "square", "holdem": "poker",
    "net": "networth", "c": "conv", "weed": "sayno", "p": "planes", "def": "define", "dictionary": "define",
    "dict": "define", "pkmn": "pokemon", "trans": "translate", "connect4": "connectfour", "dice": "roll",
    "poke": "pokemon", "pk": "pokemon", "walker": "pokewalker", "pw": "pokewalker", "stocks": "stock",
    "fw": "foreignwiki", "u": "unicode", "rune": "runes", "jp": "jyutping", "ord_command": "ord",
    "py": "pinyin"
}


commandFormats = {
    "help": "z!help [command]",
    "connectfour": "z!connectfour <user>",
    "mock": "z!mock <text>",
    "expand": "z!expand <text>",
    "say": "z!say <text>",
    "ping": "z!ping",
    "roll": "z!roll [# dice]d<# sides>",
    "square": "z!square <text>",
    "flagsquare": "z!flagsquare <text>",
    "conv": "z!conv <value> <unit>",
    "sayno": "z!sayno",
    "jotto": "z!jotto",
    "hangman": "z!hangman [category]",
    "wiki": "z!wiki <article>",
    "randomwiki": "z!randomwiki",
    "foreignwiki": "z!foreignwiki <language> <article>\nz!foreignwiki all <article>",
    "translate": "z!translate <from> <to> <text>",
    "define": "z!define <word>",
    "charcount": "z!charcount <text>",
    "timein": "z!timein <place>",
    "weather": "z!weather <place>",
    "sheriff": "z!sheriff <emoji>",
    "clap": "z!clap <text>",
    "epitaph": "z!epitaph\nz!epitaph handsoff\nz!epitaph tech [technology]",
    "duel": "z!duel <opponent>",
    "collatz": "z!collatz <number>",
    "boggle": "z!boggle",
    "anagrams": "z!anagrams",
    "wordpath": "z!wordpath <word1> <word2>",
    "drivetime": "z!drivetime <start> to <destination>",
    "langcodes": "z!langcodes [page]",
    "jyutping": "z!jyutping <Chinese text>",
    "pinyin": "z!pinyin <Chinese text>",
    "revpin": "z!revpin <syllable>",
    "runes": "z!runes <runic text>",
    "unicode": "z!unicode <hex code(s)>",
    "ord": "z!ord <character>",
    "base": "z!base <to> <integer> [from]",
    "diacritize": "z!diacritize <character> [diacritics]",
    "rot13": "z!rot13 <text>",
    "pokemon": "see z!pokemon help",
    "rpg": "see z!rpg help",
    "planes": "see z!planes help",
    "invite": "z!invite"
}


descs = {
    "help": "Shows description of [command]. If [command] is left blank, shows list of commands.",
    "connectfour": "Challenges <user> to a nice game of Connect Four. To play, just say the column number (1-7), "
                   "displayed above the columns) you'd like to drop your piece into. No stakes but your dignity.",
    "mock": "Turns ``this kind of text`` into ``tHiS kInD oF tExT``.",
    "expand": "E x p a n d s   y o u r   t e x t.",
    "say": "Literally just repeats <text> back to you. There's no need for this to exist.",
    "ping": "Pong.",
    "roll": "Rolls [dice] dice with <sides> sides. [dice] defaults to 1.",
    "square": "Turns <text> into :regional_indicator_t: :regional_indicator_h: :regional_indicator_e: "
              ":regional_indicator_s: :regional_indicator_e:   :regional_indicator_t: :regional_indicator_h: "
              ":regional_indicator_i: :regional_indicator_n: :regional_indicator_g: :regional_indicator_s:.",
    "flagsquare": "Same as ``z!square``, but without the spaces, so a lot of country flag emojis show up.",
    "conv": "Converts between metric and imperial measurements.\n\n"
            "Accepted temperature units: ``C, F``\n"
            "Accepted length units: ``cm, m, km, in, ft, mi``\n"
            "Accepted weight units: ``g, kg, oz, lb``",
    "sayno": "Say no to drugs, kids.",
    "jotto": "Starts a game of Jotto. Similar to Mastermind, but with words. The bot chooses "
             "a random four-letter word, and the player attempts to deduce that word. To do that, "
             "the player guesses a valid, four-letter English word, and the bot returns the amount "
             "of letters in the player's guess that are also in the bot's word. The game ends when "
             "the player guesses the correct word.\n\n"
             "ex: If the word is ``cats``, the guess ``play`` returns ``1``, the guess ``helm`` returns"
             " ``0``, the guess ``area`` returns ``1``, since there's only one A in ``cats``, and the guess"
             " ``fact`` returns ``3``.",
    "hangman": f"Starts a game of hangman. If [category] is left blank, a random category is chosen. A random term is "
               f"then picked from that category.\n\nAvailable categories: ```{', '.join(list(hm.hangdict.keys()))}```",
    "wiki": "Returns the link to the Wikipedia article with the given title, if there is one.",
    "randomwiki": "Returns a random Wikipedia article.",
    "foreignwiki": "Returns the <language> version of the English Wikipedia <article>, if it exists."
                   "<language> must be either a language name or an ISO code.\n"
                   "``z!foreignwiki all <article>`` lists all foreign wikis with a version of <article>.",
    "translate": "-- CURRENTLY DEPRECATED UNTIL FURTHER NOTICE --\n\n"
                 "Uses Google Translate to translate between languages. <from> and <to> can be in the form of either "
                 "language names or ISO language codes (e.g. ``en`` for English). <from> can also be ``auto`` to "
                 "detect the input language.\n\n"
                 "**Note: ``chinese`` defaults to Simplified Chinese. To translate into Traditional Chinese, use "
                 "``traditional-chinese`` or ``zh-tw``.*",
    "define": "Gives the most common definition of <word>.",
    "charcount": "Returns the number of characters in <text>.",
    "timein": "Returns the current time in <place>.",
    "weather": "Returns the current weather in <place>.",
    "sheriff": "Calls the sheriff of <emoji>.",
    "clap": ":clap:Adds:clap:claps:clap:between:clap:your:clap:words.",
    "epitaph": "Raise a planetary civilization to great heights in Epitaph (original: "
               "https://mkremins.github.io/epitaph). As an ascended spacefaring civilization, interfere in a newborn "
               "society by sharing your technological secrets to guide it towards ascension, or watch it die to "
               "one of the universe's many filters blocking its path.\n\n"
               "``z!epitaph`` to play a game.\n``z!epitaph handsoff`` to watch a civ run without interference.\n"
               "``z!epitaph tech`` to see the technology tree.\n"
               "``z!epitaph tech <technology>`` to see details for a specific technology.",
    "duel": "Challenge your friends to a duel. First one to draw by sending the gun emoji in chat wins.",
    "collatz": "Iterates the Collatz conjecture over a number. If n is even, divide by 2; if "
               "odd, multiply by 3 and add 1. All numbers eventually reach 1.",
    "boggle": "Runs a nice game of Boggle. Find all the words you can by stringing neighboring letters together.",
    "anagrams": "Runs an Anagrams game. Rearrange the letters to make as many words as possible.",
    "wordpath": "Finds the shortest edit path between two words, using Levenshtein distance.",
    "drivetime": "Using Google Maps, calculates the driving time between two locations, taking into account "
                 "current traffic.",
    "langcodes": "Shows abbreviated language codes for ``z!translate``.",
    "jyutping": "Gives the Jyutping (Cantonese) romanization of a string of Chinese characters.",
    "pinyin": "Gives the Pinyin romanization of a string of Chinese characters.",
    "revpin": "-- CURRENTLY BROKEN --\n\nGives the __rev__erse __Pin__yin of <syllable> - that is, a list of Chinese "
              "characters which can be transliterated as <syllable>.",
    "runes": "Transliterates medieval Nordic runes into Latin letters.",
    "unicode": "Returns the Unicode characters corresponding to input hex codes.\ne.g. ``z!unicode 0041`` > ``A``",
    "ord": "The inverse of ``z!unicode``. Returns the Unicode code, in both hex and decimal, for an input character.",
    "base": "Converts a base [from] integer into a base <to> integer. [from] defaults to base 10.",
    "diacritize": "Adds input combining diacritics to <character>.",
    "rot13": "Puts <text> through the ROT13 cipher. Astute observers will realize that putting ROT13 text back through "
             "the cipher returns it to its original state.",
    "pokemon": "A bunch of Pokémon shit. Do ``z!pokemon help`` for more info.",
    "rpg": "A framework for some kind of RPG I wanted to make. It doesn't really do anything at the moment, but"
           " see ``z!rpg help`` if you're interested.",
    "planes": "A neat little Pocket Planes kinda game, a shipping simulator. Do ``z!p help`` for more info.",
    "invite": "Gives the link to invite Zephyrus to another server."
}


@client.command(aliases=["?", "h"])
async def help(comm: str=None):
    async def helpsay(s, **kwargs):
        await emolsay(":grey_question:", s, hexcol("59c4ff"), **kwargs)

    comm = aliases.get(comm).lower() if aliases.get(comm) else comm
    if comm not in commandFormats:
        return await helpsay(
            "Full Command List", d=f"```css\n{', '.join(sorted(list(commandFormats)))}```"
            f"For help with any of these, type ``z!help [command]``."
        )
    else:
        help_dict = {"Format": f"``{commandFormats[aliases.get(comm, comm)]}``"}
        if [g for g, j in aliases.items() if j == comm]:
            help_dict["Aliases"] = f'``{", ".join([f"z!{g}" for g, j in aliases.items() if j == comm])}``'
        return await helpsay(f"``z!{comm}``", d=descs[comm], fs=help_dict, il=True)


@client.command()
async def invite():
    return await client.say('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8192'
                            .format(client.user.id))


@client.event
async def on_ready():
    del client.commands['Шaf']
    if client.user.name == "Zephyrus":
        print(colored("ZEPHYRUS IS ONLINE", color="green", attrs=["bold"]))
    else:
        print(colored("BEPHYRUS IS ONLINE", color="green", attrs=["bold"]))
    print(f"connected to {colored(str(len(client.servers)), color='cyan', attrs=['bold'])} servers and "
          f"{colored(str(len(set(client.get_all_members()))), color='red', attrs=['bold'])} users")
    print('--------')
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8192'.format(client.user.id))
    print(f"Started up at {str(datetime.now())} ({time()})")
    print("Missing Format:", [g for g in client.commands if not commandFormats.get(aliases.get(g, g))])
    print("Missing Help:", [g for g in client.commands if not descs.get(aliases.get(g, g))])
    setattr(client, "fortServers", [g for g in client.servers if g.owner.id in [kaisid, "474398677599780886"]])
    return await client.change_presence(game=discord.Game(name="z!rpg"))


@client.event
async def on_command_error(exception, context):
    command = context.message.content.split()[0].split("!")[1]
    if type(exception) in [commands.errors.MissingRequiredArgument, commands.errors.BadArgument,
                           commands.errors.TooManyArguments]:
        await client.send_message(context.message.channel, embed=conerr(
            f"Format: ``{'`` or ``'.join(commandFormats[aliases.get(command, command)].splitlines())}``"
        ))
    elif type(exception) == commands.errors.CommandNotFound:
        pass
    else:
        await client.send_message(context.message.channel, embed=conerr(str(exception)))
        raise exception


if wr.levenshtein(input(f"{colored('beta', 'red')} or {colored('stable', 'green')}? ").lower(), "beta") < 3:
    key = "NTI3MzQxNTk0MTUyNzk2MTYw.DwSW6A.chbnvyHdqw7JRvIAjIoe7V6SAI8"
else:
    key = "NDA1MTkwMzk2Njg0MDA5NDcy.DUgyyg.srsiV9DX2sVKmvj12HJkTWiXWdk"
client.run(key)
