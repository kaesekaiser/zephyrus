import asyncio
import datetime
import discord
import re
import time
from classes.bot import Zeph
from classes.embeds import author_from_user, blue, ClientEmol, error, phone, success
from classes.menus import Navigator, page_list
from discord.ext import commands
from functions import admin_check, hex_to_color, none_list
from sys import version_info
from utilities.words import word_dict, word_list

from epitaph import EpitaphCog
from fe3h import FE3HCog
from game import GamesCog
from pkmn import PokemonCog
from planes import PlanesCog
from server import load_server_settings, ServerSettings, ServerSettingsCog
from tcgpocket import TCGPocketCog
from utils import convert_x_sampa, convert_z_sampa, load_reminders, UtilitiesCog


class HelpNavigator(Navigator):
    def con(self):
        return self.emol.con(
            self.title.format(page=self.page, pgs=self.pgs),
            d=none_list(page_list(self.table, self.per, self.page), "\n") +
            "\n\nFor help with any of these, use `z!help [command]`.",
            **self.kwargs
        )


class ChannelLink:  # just a class to keep track of things. it doesn't really do much but look nice
    def __init__(self, bot: Zeph, fro: discord.TextChannel, to: discord.TextChannel):
        self.bot = bot
        self.fro = fro
        self.to = to

    def should_activate(self, message: discord.Message):
        if not self.fro:
            return False
        if message.channel != self.fro and message.channel != self.to:
            return False
        if message.author == self.bot.user:
            return False
        if message.content.lower() == "z!unlink":
            return False
        return True


class MiscellaneousCog(commands.Cog):
    def __init__(self, bot: Zeph):
        self.bot = bot

    @commands.command(
        name="help", aliases=["?", "h"], usage="z!help [command]",
        description="Lists all commands, or helps you with one.",
        help="Shows the usage + format of a command. If no command is provided, lists all available commands."
    )
    async def help_command(self, ctx: commands.Context, comm: str = ""):
        hep = ClientEmol(":grey_question:", hex_to_color("59c4ff"), ctx)

        try:
            comm = self.bot.all_commands[comm]
        except KeyError:
            comms = sorted(
                f"**`{g.name}`** - {g.description if g.description else g.help}"
                for g in self.bot.commands if not g.hidden
            )
            return await HelpNavigator(self.bot, hep, comms, 10, "Full Command List [{page}/{pgs}]").run(ctx)
        else:
            if comm.usage == "REDIRECT":
                return await comm.__call__(ctx)  # show the redirect instead of running help

            aliases = [f"z!{g}" for g, j in self.bot.all_commands.items() if j.name == comm.name and g != j.name]
            help_dict = {"Format": "\n".join(f"`{g}`" for g in comm.usage.split("\n"))}
            if aliases:
                help_dict["Aliases"] = ", ".join(f"`{g}`" for g in aliases)
            return await hep.say(f"`z!{comm.name}`", d=comm.help, fs=help_dict, il=True)

    @commands.command(
        usage="z!invite",
        help="Spits out the invite link for Zephyrus, so you can bring it to other servers."
    )
    async def invite(self, ctx: commands.Context):
        return await ctx.send(
            content=f'https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}'
                    f'&scope=bot&permissions=275146730560'
        )

    @commands.command(
        usage="z!about",
        help="Shows some information about the bot."
    )
    async def about(self, ctx: commands.Context):
        def runtime_format(dt: datetime.timedelta):
            if dt.days:
                return f"{dt.days} d {dt.seconds // (60 * 60) % 24} h {dt.seconds // 60 % 60} m"
            return f"{dt.seconds // (60 * 60)} h {dt.seconds // 60 % 60} m {int(dt.seconds) % 60} s"

        py_version = "{}.{}.{}".format(*version_info)

        return await ClientEmol(":robot:", hex_to_color("6fc96f"), ctx).say(
            author=author_from_user(self.bot.user, f"\u2223 {self.bot.user.name}"),
            d=f"**Connected to:** {len(self.bot.guilds)} servers / {len(set(self.bot.users))} users\n"
            f"**Commands:** {len([g for g, j in self.bot.all_commands.items() if g == j.name and not j.hidden])}\n"
            f"**Runtime:** {runtime_format(datetime.datetime.now() - getattr(self.bot, 'readyTime'))}\n"
            f"**Build:** {self.bot.version} / Python {py_version}\n"
            f"[GitHub](https://github.com/kaesekaiser/zephyrus) / "
            f"[Invite](https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}"
            f"&scope=bot&permissions=268705856)",
            thumbnail=self.bot.user.avatar.url,
            footer=f"Feel free to DM {self.bot.get_user(238390171022655489)} with any questions!"
        )

    @commands.command(
        name="wordlist", aliases=["wl"], usage="z!wordlist <add | remove | check> <words...>",
        description="Checks and suggests changes to the word list used for the word games.",
        help="If you're Fort, this modifies the word list. If you're not, this suggests to Fort a modification that "
             "you think should be made to the word list that `z!jotto`, `z!anagrams`, and `z!boggle` use. `z!wl add` "
             "suggests words to add, and `z!wl remove` suggests words to remove. You can make multiple suggestions in "
             "the same command - e.g. `z!wl add word1 word2 word3`.\n\n"
             "`z!wl check` just checks whether the words you pass it are in the word list already."
    )
    async def wordlist_command(self, ctx: commands.Context, aor: str, *words: str):
        if aor.lower() not in ["add", "remove", "check"]:
            raise commands.errors.BadArgument
        aor = aor.lower()

        if not words:
            raise commands.CommandError("no words input")
        if aor == "check":
            words = sorted(list(set(g.lower() for g in words)))
            in_words = [g for g in words if g in word_list]
            out_words = [g for g in words if g not in in_words]
            in_words = f"{self.bot.emojis['yes']} In word list: `{' '.join(in_words)}`\n" if in_words else ""
            out_words = f"{self.bot.emojis['no']} Not in word list: `{' '.join(out_words)}`" if out_words else ""
            return await (ClientEmol(":blue_book:", hex_to_color("55acee"), ctx)
                          .say("Word Check", d=in_words + out_words))

        if aor == "add":
            words = sorted(list(set(g.lower() for g in words if g.lower() not in word_list)))
            if not words:
                raise commands.CommandError("Word(s) already in word list.")
        if aor == "remove":
            words = sorted(list(set(g.lower() for g in words if g.lower() in word_list)))
            if not words:
                raise commands.CommandError("Word(s) not in word list.")

        try:
            admin_check(ctx)
        except commands.CommandError:
            await self.bot.get_channel(607102546892554240).send(
                content=f"{ctx.author} has suggested that you {aor} the following word(s):\n`{' '.join(words)}`"
            )
            return await success.send(ctx, "Suggestion sent.")
        else:
            if aor == "add":
                word_list.extend(words)
            else:
                for g in words:
                    try:
                        word_list.remove(g)
                    except ValueError:
                        pass
            word_dict.update({n: tuple(g for g in word_list if len(g) == n) for n in range(1, 23)})
            with open("utilities/words.txt", "w") as f:
                f.writelines("\n".join(sorted(word_list)))
            return await success.send(ctx, "Word list updated.")

    @commands.command(
        name="feedback", aliases=["suggest", "contact"], usage="z!feedback <feedback...>",
        description="Sends feedback to the creator.",
        help="Sends feedback to the creator. You can also use this to make suggestions or just generally contact me, "
             "if you need."
    )
    async def feedback_command(self, ctx: commands.Context, *, text: str):
        if len(text) > 1600:
            raise commands.CommandError(
                "Please try to keep feedback relatively short.\nLike, 1600 characters should be plenty. "
                "If you really need to send more, just ask me to DM you. I'm only human."
            )

        # send the feedback to my feedback channel
        if isinstance(ctx.channel, discord.DMChannel) or isinstance(ctx.channel, discord.GroupChannel):
            await self.bot.get_channel(607102546892554240).send(
                f"**{str(ctx.author)}** (ID `{ctx.author.id}`), in DMs, says:\n{text}"
            )
        else:
            await self.bot.get_channel(607102546892554240).send(
                f"**{str(ctx.author)}** (ID `{ctx.author.id}`), in the guild **{ctx.guild.name}**, says:\n{text}\n\n"
                f"Link to message: {ctx.message.jump_url}"
            )

        return await success.send(ctx, "Feedback sent!")

    @commands.command(
        hidden=True, usage="z!save",
        help="Saves any data stored during downtime."
    )
    async def save(self, ctx: commands.Context):
        admin_check(ctx)

        self.bot.save()
        return await success.send(ctx, "Saved!")

    @commands.command(
        hidden=True, name="eval", usage="z!eval <code...>",
        help="Evaluates Python code."
    )
    async def eval_command(self, ctx: commands.Context, *, text: str):
        admin_check(ctx)

        ret = str(eval(text, globals(), {"ctx": ctx}))
        if len(ret) > 1980:
            ret = [f"```{ret[1980*g:1980*(g+1)]}```" for g in range(len(ret) // 1980 + 1)]
        else:
            ret = [f"```py\n{ret}\n```"]

        for res in ret:
            await ctx.send(content=res)

    @commands.command(
        hidden=True, name="send", usage="z!send <channel> <message...>",
        description="Sends a message to a given channel.",
        help="Sends `<message>` to `<channel>`."
    )
    async def send_command(self, ctx: commands.Context, channel_id: int, *, message: str):
        admin_check(ctx)

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            raise commands.CommandError("ID does not point to a text channel.")

        try:
            return await channel.send(content=message)
        except discord.errors.Forbidden:
            raise commands.CommandError("I can't send a message to that channel.")

    @commands.command(
        hidden=True, name="nickname", aliases=["nick"], usage="z!nickname <name...>\nz!nickname reset",
        description="Changes the bot's nickname.",
        help="Changes the bot's nickname to `<nickname>`. `z!nick reset` resets the nickname."
    )
    async def nickname_command(self, ctx: commands.Context, *, nick: str):
        admin_check(ctx)

        try:
            if nick == "reset":
                await ctx.guild.me.edit(nick="")
                return await success.send(ctx, "Nickname reset.")
            else:
                await ctx.guild.me.edit(nick=nick)
                return await success.send(ctx, "Nickname changed.")
        except discord.Forbidden:
            raise commands.CommandError("Insufficient permissions.")

    @commands.command(
        hidden=True, name="embed", usage="z!embed <code...>",
        help="Returns a message consisting of the encoded embed."
    )
    async def embed_command(self, ctx: commands.Context, *, code: str):
        admin_check(ctx)

        ret = eval(code, globals(), {"ctx": ctx})
        if not isinstance(ret, discord.Embed):
            raise commands.CommandError("Code does not construct an embed.")
        else:
            return await ctx.send(embed=ret)

    @commands.command(
        hidden=True, name="link", usage="z!link user <user ID>\nz!link channel <channel ID>",
        description="Lets you communicate through Zephyrus.",
        help="Connects you, the viewer, to a given text channel or DM channel and lets you both talk through Zephyrus "
             "and read the messages back."
    )
    async def link_command(self, ctx: commands.Context, channel_type: str, idn: int):
        admin_check(ctx)

        if self.bot.channel_link is not None:
            raise commands.CommandError("Zephyrus is already connected somewhere. Try using `z!disconnect` first.")

        if channel_type == "channel":
            channel = self.bot.get_channel(idn)
            if not isinstance(channel, discord.TextChannel):
                raise commands.CommandError("ID does not point to a text channel I can access.")
            if not channel.permissions_for(channel.guild.me).send_messages:
                raise commands.CommandError("I can't speak in this channel.")

            await success.send(ctx, f"Connected to #{channel.name}!")

        elif channel_type == "user":
            user = self.bot.get_user(idn)
            if not user:
                raise commands.CommandError("ID does not point to a user I can see.")
            if not user.dm_channel:
                await user.create_dm()
            channel = user.dm_channel

            await phone.send(  # for the sake of transparency
                channel, "DMs linked.",
                d="Hi! This is Fort, DMing you through Zeph. You can talk back, and I can read it."
            )
            await success.send(ctx, f"Connected to {user}!")

        else:
            raise commands.CommandError("Unknown channel type. Valid inputs are `user` and `channel`.")

        self.bot.channel_link = ChannelLink(self.bot, ctx.channel, channel)

    @commands.command(
        hidden=True, name="unlink", usage="z!unlink",
        help="Disconnects any existing channel link."
    )
    async def unlink_command(self, ctx: commands.Context):
        admin_check(ctx)

        if isinstance(self.bot.channel_link.to, discord.DMChannel):  # transparency again
            await phone.send(
                self.bot.channel_link.to, "DMs unlinked.",
                d="I can no longer read what you say here. Use `z!feedback` if you need anything else."
            )

        self.bot.channel_link = None
        await success.send(ctx, "Unlinked.")

    @commands.command(
        hidden=True, name="presence", aliases=["pres"], usage="z!presence <type> <activity...> [url]",
        description="Updates the bot's presence.",
        help="Update's the bot's presence to `<activity>`. `<type>` must be `playing`, `listening`, `streaming`,"
             "or `watching`. If a URL is included (for a Twitch stream), prefix it with `url=`."
    )
    async def presence_command(self, ctx: commands.Context, activity_type: str, *, activity: str):
        admin_check(ctx)

        types = {
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching
        }
        if activity_type.lower() not in types:
            raise commands.CommandError("Type must be `playing`, `listening`, or `watching`.")

        if activity.split()[-1][:4] == "url=":
            url = activity.split()[-1][4:]
            activity = " ".join(activity.split()[:-1])
        else:
            url = None

        await self.bot.change_presence(activity=discord.Activity(type=types[activity_type.lower()],
                                                                 name=activity, url=url))
        return await success.send(ctx, "Presence updated.")

    @commands.command(
        hidden=True, name="reloademoji", usage="z!reloademoji",
        help="Reloads application emoji."
    )
    async def reload_emoji_command(self, ctx: commands.Context):
        admin_check(ctx)

        await self.bot.load_emojis()
        await success.send(ctx, "Emoji reloaded.")

    @commands.command(
        name="close", hidden=True, usage="z!close",
        help="Saves and stops the bot."
    )
    async def close_command(self, ctx: commands.Context):
        admin_check(ctx)

        if self.bot.nativities:
            if not await self.bot.confirm("Someone has an active menu somewhere. Shut down anyway?", ctx):
                return await error.send(ctx, "Operation cancelled.")

        self.bot.save()
        await ClientEmol(":wave:", blue, ctx).say("Bye!")
        await self.bot.close()


zeph = Zeph()
activity_channel = 791776037893308417  # channel ID for the channel in which zeph sends ready + error messages to me


@zeph.event
async def on_ready():
    await zeph.add_cog(EpitaphCog(zeph))
    await zeph.add_cog(FE3HCog(zeph))
    await zeph.add_cog(GamesCog(zeph))
    await zeph.add_cog(PokemonCog(zeph))
    await zeph.add_cog(PlanesCog(zeph))
    await zeph.add_cog(ServerSettingsCog(zeph))
    await zeph.add_cog(TCGPocketCog(zeph))
    await zeph.add_cog(UtilitiesCog(zeph))
    await zeph.add_cog(MiscellaneousCog(zeph))

    try:
        load_reminders(zeph)
    except NameError:  # a weird error that seems to happen when the bot is still online when I click run?
        print("Bot has not fully shut down. Please z!close, and restart.")
    load_server_settings(zeph)
    zeph.load_walker_users()
    zeph.load_usage_stats()

    setattr(zeph, "readyTime", datetime.datetime.now())
    print(f"ready at {getattr(zeph, 'readyTime')}")
    await zeph.loop.create_task(zeph.load_emojis())
    await zeph.loop.create_task(zeph.initialize_planes())
    # zeph.loop.create_task(zeph.load_romanization())
    await zeph.loop.create_task(zeph.get_channel(activity_channel).send(f":up: **Ready** at `{datetime.datetime.now()}`"))
    await zeph.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="you ❤"))
    await zeph.loop.create_task(one_minute_cycle())


@zeph.event
async def on_command(ctx: commands.Context):
    zeph.usage_stats[ctx.command.name] = zeph.usage_stats.get(ctx.command.name, 0) + 1


@zeph.event
async def on_command_error(ctx: commands.Context, exception):
    if ctx.command == EpitaphCog.epitaph and ctx.channel in zeph.epitaph_channels:
        zeph.epitaph_channels.remove(ctx.channel)

    relevant_nativities = [g for g in zeph.nativities if g.ctx == ctx]
    for nativity in relevant_nativities:
        zeph.nativities.remove(nativity)

    if isinstance(exception, commands.UserInputError):
        await error.send(
            ctx, f"Format: `{'` or `'.join(ctx.command.usage.splitlines())}`"
        )
    elif type(exception) == commands.CommandNotFound:
        pass
    elif type(exception) == commands.CommandError:
        try:
            await error.send(ctx, str(exception).split("\n")[0], d="\n".join(str(exception).split("\n")[1:]))
        except discord.HTTPException:
            await error.send(ctx, "Error!", desc=str(exception))
    else:
        try:
            await error.send(ctx, f"`{str(exception)}`")
        except discord.HTTPException:
            await error.send(ctx, "Error!", desc=str(exception))
        try:
            if ctx.command.name != "eval":
                await zeph.get_channel(activity_channel).send(
                    f":no_entry: **Error**: `{str(exception)}`\n"
                    f":pencil: **Context**: `{ctx.message.content}`\n"
                    f":map: **Guild**: {ctx.guild if ctx.guild else 'DM'}\n"
                    f":fast_forward: **URL**: {ctx.message.jump_url}"
                )
        except discord.HTTPException:
            pass
        raise exception


@zeph.event
async def on_message(message: discord.Message):
    zeph.dispatch("reaction_or_message", message, message.author)

    if zeph.user in message.mentions and "🤗" in message.content:
        await message.channel.send(":hugging:")
    if zeph.user in message.mentions and "<:o7:686317637495423031>" in message.content:
        await message.channel.send(zeph.all_emojis.get("o7", "o7"))
    if zeph.user in message.mentions and re.search(r"^(.*\s)?o7(\s.*)?$", message.content):
        await message.channel.send("o7")
    if re.fullmatch("h+", message.content) and message.author != zeph.user:
        if (not message.guild) or zeph.server_settings.get(message.guild.id).can_h_in(message.channel):
            await message.channel.send(zeph.emojis.get("aitch", "h"))

    if (not message.guild or zeph.server_settings.get(message.guild.id, ServerSettings.null()).sampa) \
            and not message.author.bot:
        sampas = []
        for match in list(re.finditer(r"((?<=[^a-zA-Z0-9/\\_]x)|(?<=^x))(\[[^\s].*?]|/[^\s].*?/)", message.content)):
            sampas.append(convert_x_sampa(match[0]))
        for match in list(re.finditer(r"((?<=[^a-zA-Z0-9/\\_]z)|(?<=^z))(\[[^\s].*?]|/[^\s].*?/)", message.content)):
            sampas.append(convert_z_sampa(match[0]))
        if sampas:
            await message.channel.send("\n".join(sampas))

    if zeph.channel_link is not None and zeph.channel_link.should_activate(message):
        if message.channel == zeph.channel_link.to:
            await zeph.channel_link.fro.send(f"**{message.author}**: {message.content}")
        if message.channel == zeph.channel_link.fro:
            await zeph.channel_link.to.send(message.content)

    await zeph.process_commands(message)


@zeph.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    zeph.dispatch("reaction_or_message", reaction, user)
    zeph.dispatch("button", reaction, user, True)


@zeph.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.User):
    zeph.dispatch("button", reaction, user, False)


@zeph.event
async def on_member_join(member: discord.Member):
    if zeph.server_settings.get(member.guild.id).notify_join:
        await zeph.server_settings.get(member.guild.id).send_join(member)

    if zeph.server_settings.get(member.guild.id).autoroles:
        if member.bot and not zeph.server_settings.get(member.guild.id).autorole_bots:
            pass  # if the server doesn't give autoroles to bots
        else:
            await member.add_roles(*zeph.sorted_assignable_roles(member.guild, only_autoroles=True), reason="autorole")


@zeph.event
async def on_member_remove(member: discord.Member):
    if zeph.server_settings.get(member.guild.id).notify_leave:
        await zeph.server_settings.get(member.guild.id).send_leave(member)


@zeph.event
async def on_member_ban(guild: discord.Guild, user: discord.User):
    if zeph.server_settings.get(guild.id).notify_ban:
        await zeph.server_settings.get(guild.id).send_ban(user)


@zeph.event
async def on_member_unban(guild: discord.Guild, user: discord.User):
    if zeph.server_settings.get(guild.id).notify_unban:
        await zeph.server_settings.get(guild.id).send_unban(user)


@zeph.event
async def on_guild_join(guild: discord.Guild):
    if not zeph.server_settings.get(guild.id):
        zeph.server_settings[guild.id] = ServerSettings()


@zeph.event
async def on_guild_remove(guild: discord.Guild):
    if zeph.server_settings.get(guild.id):
        del zeph.server_settings[guild.id]


@zeph.check
def is_nativity_blocked(ctx: commands.Context):
    for nativity in zeph.nativities:
        if nativity.match(ctx):
            raise commands.CommandError(nativity.warning)
    else:
        return True


async def one_minute_cycle():  # unified process for things done once per minute
    while True:
        # check reminders
        now = time.time()
        for rem in zeph.reminders:
            if rem.time < now:
                try:
                    await zeph.get_user(rem.author).send(f"**Reminder:** {rem.text}")
                except AttributeError | discord.HTTPException:
                    print(f"A reminder failed to send: {str(rem)}")

                zeph.reminders.remove(rem)

        # save planes, etc data
        zeph.save()

        await asyncio.sleep(60)
