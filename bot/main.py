from planes import *
from sys import version_info


class HelpNavigator(Navigator):
    @property
    def con(self):
        return self.emol.con(
            self.title.format(page=self.page, pgs=self.pgs),
            d=none_list(page_list(self.table, self.per, self.page), "\n") +
            "\n\nFor help with any of these, use ``z!help [command]``.",
            **self.kwargs
        )


@zeph.command(
    name="help", aliases=["?", "h"], usage="z!help [command]",
    description="Lists all commands, or helps you with one.",
    help="Shows the usage + format of a command. If no command is provided, lists all available commands."
)
async def help_command(ctx: commands.Context, comm: str = None):
    hep = ClientEmol(":grey_question:", hexcol("59c4ff"), ctx)

    try:
        comm = zeph.all_commands[comm if comm else ""]
    except KeyError:
        comms = sorted(
            f"**`{g.name}`** - {g.description if g.description else g.help}" for g in zeph.commands if not g.hidden
        )
        return await HelpNavigator(hep, comms, 10, "Full Command List [{page}/{pgs}]").run(ctx)
    else:
        aliases = [f"z!{g}" for g, j in zeph.all_commands.items() if j.name == comm.name and g != j.name]
        help_dict = {"Format": f"``{comm.usage}``"}
        if aliases:
            help_dict["Aliases"] = f'``{", ".join(aliases)}``'
        return await hep.say(f"``z!{comm.name}``", d=comm.help, fs=help_dict, il=True)


@zeph.command(
    usage="z!invite",
    help="Spits out the invite link for Zephyrus, so you can bring it to other servers."
)
async def invite(ctx: commands.Context):
    return await ctx.send(content='https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8192'
                          .format(zeph.user.id))


@zeph.command(
    usage="z!about",
    help="Shows some information about the bot."
)
async def about(ctx: commands.Context):
    def runtime_format(dt: datetime.timedelta):
        if dt.days:
            return f"{dt.days} d {dt.seconds // (60 * 60) % 24} h {dt.seconds // 60 % 60} m"
        return f"{dt.seconds // (60 * 60)} h {dt.seconds // 60 % 60} m {int(dt.seconds) % 60} s"

    py_version = "{}.{}.{}".format(*version_info)

    return await ClientEmol(":robot:", hexcol("6fc96f"), ctx).say(
        author=author_from_user(zeph.user, f"\u2223 {zeph.user.name}"),
        d=f"**Connected to:** {len([g for g in zeph.guilds if g.id not in testing_emote_servers])} servers / "
        f"{len(set(zeph.users))} users\n"
        f"**Commands:** {len([g for g, j in zeph.all_commands.items() if g == j.name and not j.hidden])}\n"
        f"**Runtime:** {runtime_format(datetime.datetime.now() - getattr(zeph, 'readyTime'))}\n"
        f"**Build:** {zeph.version} / Python {py_version}\n"
        f"[GitHub](https://github.com/kaesekaiser/zephyrus) / "
        f"[Invite](https://discordapp.com/oauth2/authorize?client_id={zeph.user.id}&scope=bot&permissions=8192)",
        thumbnail=zeph.user.avatar_url,
        footer=f"Feel free to DM {zeph.get_user(238390171022655489)} with any questions!"
    )


@zeph.command(
    name="wordlist", aliases=["wl"], usage="z!wordlist <add | remove | check> <words...>",
    description="Checks and suggests changes to the word list used for the word games.",
    help="If you're Fort, this modifies the word list. If you're not, this suggests to Fort a modification that "
         "you think should be made to the word list that `z!jotto`, `z!anagrams`, and `z!boggle` use. `z!wl add` "
         "suggests words to add, and `z!wl remove` suggests words to remove. You can make multiple suggestions in "
         "the same command - e.g. `z!wl add word1 word2 word3`.\n\n"
         "`z!wl check` just checks whether the words you pass it are in the word list already."
)
async def wordlist_command(ctx: commands.Context, aor: str, *words: str):
    if aor.lower() not in ["add", "remove", "check"]:
        raise commands.errors.BadArgument
    aor = aor.lower()

    if not words:
        raise commands.CommandError("no words input")
    if aor == "check":
        words = sorted(list(set(g.lower() for g in words)))
        in_words = [g for g in words if g in wr.wordList]
        out_words = [g for g in words if g not in in_words]
        in_words = f"{zeph.emojis['yes']} In word list: `{' '.join(in_words)}`\n" if in_words else ""
        out_words = f"{zeph.emojis['no']} Not in word list: `{' '.join(out_words)}`" if out_words else ""
        return await ClientEmol(":blue_book:", hexcol("55acee"), ctx).say("Word Check", d=in_words + out_words)

    if aor == "add":
        words = sorted(list(set(g.lower() for g in words if g.lower() not in wr.wordList)))
        if not words:
            raise commands.CommandError("Word(s) already in word list.")
    if aor == "remove":
        words = sorted(list(set(g.lower() for g in words if g.lower() in wr.wordList)))
        if not words:
            raise commands.CommandError("Word(s) not in word list.")

    try:
        admin_check(ctx)
    except commands.CommandError:
        await zeph.get_channel(607102546892554240).send(
            content=f"{ctx.author} has suggested that you {aor} the following word(s):\n`{' '.join(words)}`"
        )
        return await succ.send(ctx, "Suggestion sent.")
    else:
        if aor == "add":
            wr.wordList.extend(words)
        else:
            for g in words:
                try:
                    wr.wordList.remove(g)
                except ValueError:
                    pass
        wr.wordDict.update({l: tuple(g for g in wr.wordList if len(g) == l) for l in range(1, 23)})
        with open("utilities/words.txt", "w") as f:
            f.writelines("\n".join(sorted(wr.wordList)))
        return await succ.send(ctx, "Word list updated.")


@zeph.command(
    hidden=True, usage="z!save",
    help="Saves any data stored during downtime."
)
async def save(ctx: commands.Context):
    admin_check(ctx)

    zeph.save()
    return await succ.send(ctx, "Saved!")


@zeph.command(
    hidden=True, name="eval", usage="z!eval <code...>",
    help="Evaluates Python code."
)
async def eval_command(ctx: commands.Context, *, text: str):
    admin_check(ctx)

    ret = str(eval(text, globals(), {"ctx": ctx}))
    if len(ret) > 1980:
        ret = [f"```{ret[1980*g:1980*(g+1)]}```" for g in range(len(ret) // 1980 + 1)]
    else:
        ret = [f"```py\n{ret}\n```"]

    for res in ret:
        await ctx.send(content=res)


@zeph.command(
    hidden=True, name="send", usage="z!send <channel> <message...>",
    description="Sends a message to a given channel.",
    help="Sends ``<message>`` to ``<channel>``."
)
async def send_command(ctx: commands.Context, channel_id: int, *, message: str):
    admin_check(ctx)

    channel = zeph.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        raise commands.CommandError("ID does not point to a text channel.")

    try:
        return await channel.send(content=message)
    except discord.errors.Forbidden:
        raise commands.CommandError("I can't send a message to that channel.")


class ChannelLink:  # just a class to keep track of things. it doesn't really do much but look nice
    def __init__(self, fro: discord.TextChannel, to: discord.TextChannel):
        self.fro = fro
        self.to = to

    def should_activate(self, message: discord.Message):
        if not self.fro:
            return False
        if message.channel != self.fro and message.channel != self.to:
            return False
        if message.author == zeph.user:
            return False
        if message.content.lower() == "z!unlink":
            return False
        return True


@zeph.command(
    hidden=True, name="link", usage="z!link user <user ID>\nz!link channel <channel ID>",
    description="Lets you communicate through Zephyrus.",
    help="Connects you, the viewer, to a given text channel or DM channel and lets you both talk through Zephyrus and "
         "read the messages back."
)
async def link_command(ctx: commands.Context, channel_type: str, idn: int):
    admin_check(ctx)

    if zeph.channelLink is not None:
        raise commands.CommandError("Zephyrus is already connected somewhere. Try using `z!disconnect` first.")

    if channel_type == "channel":
        channel = zeph.get_channel(idn)
        if not isinstance(channel, discord.TextChannel):
            raise commands.CommandError("ID does not point to a text channel I can access.")
        if not channel.permissions_for(channel.guild.me).send_messages:
            raise commands.CommandError("I can't speak in this channel.")

        await succ.send(ctx, f"Connected to #{channel.name}!")

    elif channel_type == "user":
        user = zeph.get_user(idn)
        if not user:
            raise commands.CommandError("ID does not point to a user I can see.")
        if not user.dm_channel:
            await user.create_dm()
        channel = user.dm_channel

        await succ.send(ctx, f"Connected to {user}!")

    else:
        raise commands.CommandError("Unknown channel type. Valid inputs are `user` and `channel`.")

    zeph.channelLink = ChannelLink(ctx.channel, channel)


@zeph.command(
    hidden=True, name="unlink", usage="z!unlink",
    help="Disconnects any existing channel link."
)
async def unlink_command(ctx: commands.Context):
    admin_check(ctx)

    zeph.channelLink = None
    await succ.send(ctx, "Unlinked.")


@zeph.command(
    hidden=True, name="presence", aliases=["pres"], usage="z!presence <type> <activity...> [url]",
    description="Updates the bot's presence.",
    help="Update's the bot's presence to ``<activity>``. ``<type>`` must be ``playing``, ``listening``, ``streaming``,"
         "or ``watching``. If a URL is included (for a Twitch stream), prefix it with ``url=``."
)
async def presence_command(ctx: commands.Context, activity_type: str, *, activity: str):
    admin_check(ctx)

    types = {
        "playing": discord.ActivityType.playing,
        "streaming": discord.ActivityType.streaming,
        "listening": discord.ActivityType.listening,
        "watching": discord.ActivityType.watching
    }
    if activity_type.lower() not in types:
        raise commands.CommandError("Type must be ``playing``, ``listening``, or ``watching``.")

    if activity.split()[-1][:4] == "url=":
        url = activity.split()[-1][4:]
        activity = " ".join(activity.split()[:-1])
    else:
        url = None

    await zeph.change_presence(activity=discord.Activity(type=types[activity_type.lower()], name=activity, url=url))
    return await succ.send(ctx, "Presence updated.")


@zeph.command(
    name="close", hidden=True, usage="z!close",
    help="Saves and stops the bot."
)
async def close_command(ctx: commands.Context):
    admin_check(ctx)

    zeph.save()
    await ClientEmol(":wave:", blue, ctx).say("Bye!")
    await zeph.close()


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
         "Alphabet. ``*`` can be used as an escape character."
)
async def sampa(ctx: commands.Context, *, text: str):
    for rep in x_sampa_dict:
        text = re.sub(r"(?<!\*)" + rep, x_sampa_dict[rep], text)
    return await ctx.send(content=text)


@zeph.event
async def on_ready():
    setattr(zeph, "readyTime", datetime.datetime.now())
    print(f"ready at {getattr(zeph, 'readyTime')}")
    zeph.loop.create_task(initialize_planes())
    zeph.loop.create_task(zeph.load_romanization())
    await zeph.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="you ❤"))


@zeph.event
async def on_command_error(ctx: commands.Context, exception):
    if type(exception) in [commands.errors.MissingRequiredArgument, commands.errors.BadArgument,
                           commands.errors.TooManyArguments]:
        await err.send(
            ctx, f"Format: ``{'`` or ``'.join(ctx.command.usage.splitlines())}``"
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


@zeph.event
async def on_message(message: discord.Message):
    zeph.dispatch("reaction_or_message", message, message.author)

    if zeph.user in message.mentions and "🤗" in message.content:
        await message.channel.send(":hugging:")
    if zeph.user in message.mentions and "<:o7:686317637495423031>" in message.content:
        await message.channel.send(zeph.emojis.get("o7", "o7"))
    if zeph.user in message.mentions and re.search(r"^(.*\s)?o7(\s.*)?$", message.content):
        await message.channel.send("o7")

    if zeph.channelLink is not None and zeph.channelLink.should_activate(message):
        if message.channel == zeph.channelLink.to:
            await zeph.channelLink.fro.send(f"**{message.author}**: {message.content}")
        if message.channel == zeph.channelLink.fro:
            await zeph.channelLink.to.send(message.content)

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
