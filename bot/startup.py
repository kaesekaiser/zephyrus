import discord
import asyncio
import inspect
import json
# import pinyin_jyutping_sentence as pjs
import re

import requests.exceptions
from discord.ext import commands
from typing import Union
from minigames import imaging as im
from utilities import words as wr
from math import ceil, atan2, sqrt, pi
from random import choice
from pyquery import PyQuery
from functools import partial


User = Union[discord.Member, discord.User]
MR = Union[discord.Message, discord.Reaction]
Flint = Union[float, int]


class Zeph(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(get_command_prefix, case_insensitive=True, help_command=None, intents=intents)
        # with open("storage/call_channels.txt", "r") as f:
        #     self.phoneNumbers = {int(g.split("|")[0]): int(g.split("|")[1]) for g in f.readlines()}
        #     self.callChannels = {int(g.split("|")[1]): int(g.split("|")[2]) for g in f.readlines()}
        self.plane_users = {}
        self.epitaph_channels = []
        # self.roman = pjs.RomanizationConversion()
        self.airport_maps = {
            1: im.Image.open("minigames/minimaps/worldzoom1.png").convert("RGBA"),
            2: im.Image.open("minigames/minimaps/worldzoom2.png").convert("RGBA"),
            4: im.Image.open("minigames/minimaps/worldzoom4.png").convert("RGBA")
        }
        self.airport_icon = im.Image.open("minigames/minimaps/airport_large.png").convert("RGBA")
        for i in self.airport_maps.values():
            assert isinstance(i, im.Image.Image)
        assert isinstance(self.airport_icon, im.Image.Image)
        self.version = self.get_version()
        self.channel_link = None
        self.reminders = []
        self.server_settings = {}
        self.nativities = []
        self.tags = {}
        self.walker_users = {}
        self.usage_stats = {}

    @staticmethod
    def get_version():
        # this is a really gross way of getting the version I know. but shut up
        try:
            step1 = str(PyQuery(url="https://github.com/kaesekaiser/zephyrus/releases/latest"))
        except requests.exceptions.ConnectionError:
            return "version check failed"
        step2 = re.search(r"octicon octicon-tag.*?</span>", step1, re.S)[0]
        zeph_version = re.search(r"(?<=ml-1\">)\s*.*?\s*(?=</span>)", step2.replace("\n", ""))[0].strip()
        try:
            step3 = re.search(r"released this.*?to master", step1, re.S)[0]
            zeph_version += "." + re.search(r"[0-9]*(?= commit)", step3)[0]
        except TypeError:
            zeph_version += ".0"
        return zeph_version

    @property
    def emojis(self) -> dict:
        """Emotes that come from my own personal servers, that I use in commands."""
        return {g.name: g for g in self._connection.emojis if g.guild.id in testing_emote_servers}

    @property
    def all_emojis(self) -> dict:
        """Emotes from any server Zeph is in."""
        return {
            g.name: g for g in self._connection.emojis
            if g.available and zeph.server_settings[g.guild.id].public_emotes
        }

    @property
    def strings(self) -> dict:
        return {g: str(j) for g, j in self.emojis.items()}

    def save(self):
        # with open("storage/call_channels.txt", "w") as f:
        #     f.write("\n".join([f"{g}|{j}|{self.callChannels.get(j, '')}" for g, j in self.phoneNumbers.items()]))
        if self.plane_users:  # if planes fails to initialize for some reason, DO NOT overwrite saved data
            with open("storage/planes.txt", "w") as f:
                f.write("\n".join([str(g) for g in self.plane_users.values()]))
        if self.walker_users:
            with open("storage/walker.txt", "w") as f:
                f.write("\n".join(str(g) for g in self.walker_users.values()))
        with open("storage/reminders.txt", "w") as f:
            f.write("\n".join(str(g) for g in self.reminders))
        if self.server_settings:  # zephyrus has accidentally erased this before, so only write if it exists
            with open("storage/server_settings.json", "w") as f:
                json.dump({g: j.minimal_json for g, j in self.server_settings.items()}, f, indent=4)
        with open("storage/usage.json", "w") as f:
            json.dump(self.usage_stats, f, indent=4)

    def load_usage_stats(self):
        with open("storage/usage.json", "r") as f:
            self.usage_stats = json.load(f)

    # async def load_romanization(self):
    #     print("Loading romanizer...")
    #     with open("utilities/rom.json", "r") as f:
    #         file = json.load(f)
    #     self.roman.jyutping_char_map.update(file["jp_char"])
    #     self.roman.jyutping_word_map.update(file["jp_word"])
    #     self.roman.pinyin_char_map.update(file["py_char"])
    #     self.roman.pinyin_word_map.update(file["py_word"])
    #     self.roman.process_sentence_jyutping("你好")
    #     print("Romanizer loaded.")


def get_command_prefix(bot: Zeph, message: discord.Message):
    if not message.guild:
        return "z!"
    if not bot.server_settings.get(message.guild.id):
        return "z!"
    return bot.server_settings.get(message.guild.id).command_prefixes


zeph = Zeph()


def hexcol(hex_code: str):
    if int(hex_code, 16) < 0:
        raise ValueError("negative hexcol code")
    if int(hex_code, 16) > 16777215:
        raise ValueError("hexcol int should be less than 16777215")
    return discord.Colour(int(hex_code, 16))


class NewLine:
    def __init__(self, obj):
        self.object = obj

    def __str__(self):
        return str(self.object)

    def __bool__(self):
        return bool(self.object)


class EmbedAuthor:
    def __init__(self, name, url=None, icon=None):
        self.name = name
        self.url = url
        self.icon = icon


def author_from_user(user: User, name: str = None, url: str = None):
    return EmbedAuthor(name if name else f"{user.name}#{user.discriminator}", icon=user.avatar.url, url=url)


# SAME_LINE: IF TRUE, PUTS IN SAME LINE. IF FALSE, PUTS ON NEW LINE.
def construct_embed(**kwargs):
    title = kwargs.get("s", kwargs.get("title"))
    desc = kwargs.get("d", kwargs.get("desc"))
    color = kwargs.get("col", kwargs.get("color"))
    fields = kwargs.get("fs", kwargs.get("fields", {}))
    ret = discord.Embed(title=title, description=desc, colour=color)
    for i in fields:
        if len(str(fields[i])) != 0:
            ret.add_field(name=i, value=str(fields[i]),
                          inline=(False if type(fields[i]) == NewLine else kwargs.get("same_line", False)))
    if kwargs.get("footer"):
        ret.set_footer(text=kwargs.get("footer"))
    if kwargs.get("thumb", kwargs.get("thumbnail")):
        ret.set_thumbnail(url=kwargs.get("thumb", kwargs.get("thumbnail")))
    if kwargs.get("author"):
        ret.set_author(name=kwargs.get("author").name, url=kwargs.get("author").url, icon_url=kwargs.get("author").icon)
    if kwargs.get("url"):
        ret.url = kwargs.get("url")
    if kwargs.get("image"):
        ret.set_image(url=kwargs.get("image"))
    if kwargs.get("time", kwargs.get("timestamp")):
        ret.timestamp = kwargs.get("time", kwargs.get("timestamp"))
    return ret


class Emol:  # fancy emote-color embeds
    def __init__(self, e: Union[discord.Emoji, str], col: discord.Colour):
        self.emoji = str(e)
        self.color = col

    def con(self, s: str = "", **kwargs):  # constructs
        return construct_embed(title=f"{self.emoji} \u2223 {s}" if s else "", col=self.color, **kwargs)

    async def send(self, destination: discord.abc.Messageable, s: str = None, **kwargs):  # sends
        return await destination.send(embed=self.con(s, **kwargs))

    async def edit(self, message: discord.Message, s: str = None, **kwargs):  # edits message
        return await message.edit(embed=self.con(s, **kwargs))


class ClientEmol(Emol):
    def __init__(self, e: Union[discord.Emoji, str], col: discord.Colour, ctx: commands.Context):
        super().__init__(e, col)
        self.ctx = ctx

    async def say(self, s: str = None, **kwargs):
        return await self.send(self.ctx, s, **kwargs)

    async def resend_if_dm(self, mess: discord.Message, s: str = None, **kwargs):
        if isinstance(self.ctx.channel, discord.DMChannel):
            return await self.say(s, **kwargs)
        else:
            return await self.edit(mess, s, **kwargs)


# IMPORTANT EMOLS
err = Emol(":no_entry:", hexcol("880000"))  # error
succ = Emol(":white_check_mark:", hexcol("22bb00"))  # success
chooseEmol = Emol(":8ball:", hexcol("e1e8ed"))
wiki = Emol(":globe_with_meridians:", hexcol("4100b5"))
phone = Emol(":telephone:", hexcol("DD2E44"))
plane = Emol(":airplane:", hexcol("3a99f7"))
lost = Emol(":map:", hexcol("55ACEE"))  # redirects - looking for these commands?


async def confirm(s: str, dest: discord.abc.Messageable, caller: User = None, **kwargs):
    def pred(r: discord.Reaction, u: User):
        return r.emoji in [zeph.emojis["yes"], zeph.emojis["no"]] and r.message.id == message.id and \
               ((caller is None and u != zeph.user) or u == caller)

    emol = kwargs.get("emol", Emol(zeph.emojis["yield"], hexcol("DD2E44")))

    message = await emol.send(
        dest, s,
        d=kwargs.get("desc_override") if "desc_override" in kwargs else
        (f"{kwargs.get('add_info', '')} To {kwargs.get('yes', 'confirm')}, react with {zeph.emojis['yes']}. "
         f"To {kwargs.get('no', 'cancel')}, react with {zeph.emojis['no']}.")
    )
    await message.add_reaction(zeph.emojis["yes"])
    await message.add_reaction(zeph.emojis["no"])
    try:
        if kwargs.get("allow_text_response"):
            def mr_pred(mr: MR, u: User):
                if isinstance(mr, discord.Reaction):
                    return pred(mr, u)
                else:
                    if isinstance(dest, commands.Context):
                        return mr.content.lower() in ["yes", "no"] and general_pred(dest)(mr)
                    else:
                        return mr.content.lower() in ["yes", "no"] and mr.channel == dest and \
                               ((caller is None and u != zeph.user) or u == caller)
            con = (await zeph.wait_for("reaction_or_message", timeout=kwargs.get("timeout", 120), check=mr_pred))[0]
            if isinstance(con, discord.Reaction):
                con = con.emoji.name
            else:
                con = con.content.lower()
        else:
            con = (await zeph.wait_for("reaction_add", timeout=kwargs.get("timeout", 120), check=pred))[0].emoji.name
    except asyncio.TimeoutError:
        await emol.edit(message, "Confirmation request timed out.")
        return False
    else:
        if kwargs.get("delete"):  # this should only be used in EXTREME edge cases
            await message.delete()
        return con == "yes"


async def image_url(fp: str):
    return (await zeph.get_channel(528460450069872642).send(file=discord.File(fp))).attachments[0].url


def plural(s: str, n: Union[float, int], **kwargs):
    """Pluralizes a noun if n != 1. 'plural' kwarg allows alternative plural form."""
    return kwargs.get("plural", s + "s") if n != 1 else s


def a_or_an(s: str) -> str:
    return f"a{'n' if s.strip('*_ ')[0].lower() in 'aeiou' else ''} {s}"


def none_list(ls: Union[list, tuple], joiner: str = ", ", if_empty: str = "none"):
    return joiner.join(ls) if ls else if_empty


def flint(n: Flint):
    return int(n) if int(n) == n else n


def snip(s: str, n: int, from_back: bool = False):  # breaks string into n-long pieces
    if not from_back:
        return [s[n * m:n * (m + 1)] for m in range(ceil(len(s) / n))]
    else:
        return list(reversed([s[-n:]] + [s[-n * (m + 1):-n * m] for m in range(1, ceil(len(s) / n))]))


def add_commas(n: Union[Flint, str]):
    if "e" in str(n):
        return str(n)
    n = str(n).split(".")
    if len(n[0]) < 5:
        return ".".join(n)
    n[0] = ",".join(snip(n[0], 3, True))
    return ".".join(n)


def grad(fro: Flint, to: Flint, value: Flint):
    """Returns a float that is <value> / 1 of the way from <fro> to <to>."""
    return fro + (to - fro) * value


def gradient(from_hex: str, to_hex: str, value: Flint):
    from_value = 1 - value
    return hexcol(
        "".join([hex(int(int(from_hex[g:g+2], 16) * from_value + int(to_hex[g:g+2], 16) * value))[2:]
                 for g in range(0, 5, 2)])
    )


def rgb_to_hsv(r: int, g: int, b: int):
    return round(atan2(sqrt(3) * (g - b), 2 * r - g - b) * 360 / (2 * pi)) % 360,\
           round(100 - 100 * min(r, g, b) / 255),\
           round(100 * max(r, g, b) / 255)


def hue_gradient(from_hex: str, to_hex: str, value: Flint, backwards: bool = False):
    from_hsv = rgb_to_hsv(*hexcol(from_hex).to_rgb())
    to_hsv = rgb_to_hsv(*hexcol(to_hex).to_rgb())
    return discord.Colour.from_hsv(
        grad(from_hsv[0] + (360 if backwards else 0), to_hsv[0], value) % 360,
        grad(from_hsv[1], to_hsv[1], value), grad(from_hsv[2], to_hsv[2], value)
    )


def page_list(ls: list, per_page: int, page: int):  # assumes page number is between 1 and total pages
    return ls[int(page) * per_page - per_page:int(page) * per_page]


def page_dict(d: dict, per_page: int, page: int):  # assumes page number is between 1 and total pages
    return {g: j for g, j in d.items() if g in page_list(list(d.keys()), per_page, page)}


class Navigator:
    """Intended mostly as a parent class. Large number of seemingly unnecessary functions is intentional; it allows
    for child classes to overwrite large amounts of the run() function without having to overwrite the function
    itself. """

    def __init__(self, emol: Emol, ls: list = (), per: int = 8, title: str = "",
                 prev: discord.Emoji | str | None = "◀", nxt: discord.Emoji | str | None = "▶", **kwargs):
        # kwargs are also passed to Emol.con()
        self.emol = emol
        self.table = ls
        self.per = per
        self.page = 1
        self.title = kwargs.get("s", title)
        self.message = None
        self.timeout = kwargs.pop("timeout", 60)
        self.prefix = kwargs.pop("prefix", "")
        self.kwargs = kwargs
        self.funcs = {}
        self.prev = prev
        self.next = nxt
        self.closed_elsewhere = False  # to prevent weird loop things if a different method closes the menu
        self.remove_reaction = kwargs.pop("remove_reaction", True)  # whether to remove the user's input reaction
        self.remove_immediately = kwargs.pop("remove_immediately", False)  # rarely needed

    @property
    def pgs(self):
        return ceil(len(self.table) / self.per)

    @property
    def page_list(self):
        return page_list(self.table, self.per, self.page)

    @property
    def legal(self):
        return [g for g in [self.prev, self.next] + list(self.funcs.keys()) if g]

    async def add_buttons(self, to_message: discord.Message = None):
        if not to_message:
            to_message = self.message

        for button in self.legal:
            if "!" not in str(button):
                try:
                    await to_message.add_reaction(button)
                except discord.errors.HTTPException:
                    pass

    def pre_process(self):  # runs immediately before calling the main function
        pass

    def post_process(self):  # runs on page change!
        pass

    def con(self):
        return self.emol.con(
            self.title.format(page=self.page, pgs=self.pgs),
            d=self.prefix + none_list(self.page_list, "\n"), **self.kwargs
        )

    def advance_page(self, direction: int):
        self.page = (self.page + direction - 1) % self.pgs + 1

    def dynamic_timeout(self) -> int | float:
        return self.timeout

    async def get_emoji(self, ctx: commands.Context):
        """Detects a button press, and returns the emoji that was pressed."""
        def pred(mr: MR, u: User):
            if isinstance(mr, discord.Message):
                return u == ctx.author and mr.channel == ctx.channel and self.is_valid_non_emoji(mr.content)
            else:
                return u == ctx.author and mr.message == self.message and mr.emoji in self.legal

        mess = (await zeph.wait_for('reaction_or_message', timeout=self.dynamic_timeout(), check=pred))[0]

        if isinstance(mess, discord.Message):
            try:
                await mess.delete()
            except discord.HTTPException:
                pass
            return mess.content
        else:
            return mess.emoji

    def is_valid_non_emoji(self, emoji: str):
        pass

    async def run_nonstandard_emoji(self, emoji: discord.Emoji | str, ctx: commands.Context):
        # For doing weird things with the input.
        pass

    async def close(self):
        self.closed_elsewhere = True  # may be called outside of a button press
        return await self.remove_buttons()

    async def remove_buttons(self, from_message: discord.Message = None):
        if not from_message:
            from_message = self.message

        for button in self.legal.__reversed__():
            if "!" not in str(button):
                try:
                    await from_message.remove_reaction(button, from_message.author)
                except discord.errors.HTTPException:
                    pass

    async def after_timeout(self):
        return await self.close()

    async def update_message(self):
        await self.message.edit(embed=self.con())

    async def run(self, ctx: commands.Context, on_new_message: bool = True, skip_setup: bool = False):
        """This function should never be overwritten."""
        if not skip_setup:
            if on_new_message:
                self.message = await ctx.channel.send(embed=self.con())
            else:
                assert isinstance(self.message, discord.Message)
                await self.message.edit(embed=self.con())

            await self.add_buttons()

        while True:
            try:
                emoji = await self.get_emoji(ctx)
            except asyncio.TimeoutError:
                return await self.after_timeout()

            if self.remove_immediately:
                try:
                    await self.message.remove_reaction(emoji, ctx.author)
                except discord.HTTPException:
                    pass

            if asyncio.iscoroutinefunction(self.pre_process):
                await self.pre_process()
            else:
                self.pre_process()

            if emoji in self.funcs:
                if should_await(self.funcs[emoji]):
                    await self.funcs[emoji]()
                else:
                    self.funcs[emoji]()

            if emoji not in self.legal:
                await self.run_nonstandard_emoji(emoji, ctx)

            if (self.funcs.get(emoji) == self.close) or self.closed_elsewhere:
                return

            try:
                self.advance_page(-1 if emoji == self.prev else 1 if emoji == self.next else 0)
            except ZeroDivisionError:
                self.page = 1

            await self.update_message()

            if self.remove_reaction and not self.remove_immediately:
                try:
                    await self.message.remove_reaction(emoji, ctx.author)
                except discord.HTTPException:
                    pass

            if asyncio.iscoroutinefunction(self.post_process):
                await self.post_process()
            else:
                self.post_process()

            if self.closed_elsewhere:
                return


class FieldNavigator(Navigator):
    def __init__(self, emol: Emol, d: dict, per: int, s: str, **kwargs):
        super().__init__(emol, [], per, s, **kwargs)
        self.table = d

    def con(self):
        return self.emol.con(
            self.title.format(page=self.page, pgs=self.pgs),
            d=self.prefix,
            fs=page_dict(self.table, self.per, self.page), **self.kwargs
        )


class NumSelector(Navigator):
    """A Navigator with the option to select one of a numerical list via chat message built-in."""
    def __init__(self, emol: Emol, ls: list = (), per: int = 8, s: str = "", **kwargs):
        super().__init__(emol, ls, per, s, **kwargs)
        self.can_multi_select = bool(kwargs.get("multi", False))

        for n in kwargs.get("allowable_selections", range(self.per)):
            self.funcs[f"!select {n+1}"] = partial(self.select, n)

    def select(self, n: int):
        # What to do with the selection. Exists to be overwritten by child classes.
        pass

    @property
    def can_select_now(self):
        # Whether numerical selection is currently permitted.
        return True

    def is_valid_user_selection(self, n: int):
        # Whether a given n is a valid number for selection.
        return 1 <= n <= len(self.page_list)

    def is_valid_nonnumerical_input(self, s: str):
        # Whether an input message s is a valid non-numerical input. Exists to be overwritten by child classes.
        return False

    async def run_nonstandard_emoji(self, emoji: discord.Emoji | str, ctx: commands.Context):
        if self.can_multi_select:
            if str(emoji).startswith("!select ") and len(str(emoji)) > 9:
                for c in emoji[8:]:
                    if can_int(c):
                        if should_await(self.select):
                            await self.select(int(c) - 1)
                        else:
                            self.select(int(c) - 1)
        if isinstance(emoji, str):
            await self.run_nonnumerical_input(emoji, ctx)

    async def run_nonnumerical_input(self, user_input: str, ctx: commands.Context):
        pass

    async def get_emoji(self, ctx: commands.Context):
        def pred(mr: MR, u: User):
            if isinstance(mr, discord.Message) and mr.content:
                if self.is_valid_nonnumerical_input(mr.content):
                    return u == ctx.author and mr.channel == ctx.channel
                elif self.can_select_now:
                    if self.can_multi_select:
                        return u == ctx.author and mr.channel == ctx.channel and \
                            all(can_int(c) or c == " " for c in mr.content) and \
                            [self.is_valid_user_selection(int(c)) for c in mr.content if can_int(c)]
                    else:
                        return u == ctx.author and mr.channel == ctx.channel and can_int(mr.content) and \
                            self.is_valid_user_selection(int(mr.content))
            else:
                return u == ctx.author and mr.message == self.message and mr.emoji in self.legal

        mess = (await zeph.wait_for('reaction_or_message', timeout=self.timeout, check=pred))[0]

        if isinstance(mess, discord.Message):
            try:
                await mess.delete()
            except discord.HTTPException:
                pass

            if self.is_valid_nonnumerical_input(mess.content):
                return mess.content
            else:
                return f"!select {mess.content}"

        else:
            return mess.emoji


class Nativity:
    """Short for "Navigator activity". Blocks the use of specified commands while a text-based menu is active,
    to prevent multiple such menus from being opened simultaneously."""
    def __init__(self, ctx: commands.Context, *commands_to_block: str, **kwargs):
        self.ctx = ctx
        self.special_case = kwargs.pop("special_case", None)  # manually matches a passcode-based special case
        if self.special_case:
            self.commands = []
        else:
            self.commands = commands_to_block
        self.block_all = kwargs.pop("block_all", False)
        self.warning = kwargs.pop(
            "warning_text", f"{'C' if self.block_all else 'Some c'}ommands are blocked while this menu is active."
        )

    def __eq__(self, other):
        return isinstance(other, Nativity) and self.ctx == other.ctx

    def match(self, ctx: commands.Context):
        return ctx.author == self.ctx.author and ctx.channel == self.ctx.channel and self.block(ctx.command)

    def match_special_case(self, ctx: commands.Context, passcode: str):
        if self.special_case:
            return ctx.author == self.ctx.author and ctx.channel == self.ctx.channel and passcode == self.special_case
        else:
            return False

    def block(self, cmd: commands.Command):
        return self.block_all or (cmd.name in self.commands)


def nativity_special_case_match(ctx: commands.Context, passcode: str):
    """Returns True iff a matching Nativity exists."""
    for nativity in zeph.nativities:
        if nativity.match_special_case(ctx, passcode):
            return True
    return False


class Interpreter:
    redirects = {}

    def __init__(self, ctx: commands.Context):
        self.ctx = ctx

    @property
    def au(self):
        return self.ctx.author

    async def run(self, func: str, *args):
        functions = dict([g for g in inspect.getmembers(type(self), predicate=inspect.isroutine)
                          if g[0][0] == "_" and g[0][1] != "_"])
        try:
            functions["_" + self.redirects.get(func, func)]
        except KeyError:
            if should_await(self.fallback):
                return await self.fallback(func, *args)
            else:
                return self.fallback(func, *args)
        else:
            func = self.redirects.get(func, func)
            if asyncio.iscoroutinefunction(self.before_run):
                # noinspection PyUnresolvedReferences
                await self.before_run(func)
            else:
                self.before_run(func)
            return await functions["_" + func](self, *args)

    def before_run(self, func: str):
        pass

    def fallback(self, *args):
        """Called if argument given is not a valid function."""
        raise commands.CommandError(
            f"Unrecognized command `{args[0]}`.\nSee **`z!{self.ctx.command.name} help`** for a list of valid commands."
        )


def lower(ls: Union[list, tuple]):
    if type(ls) == tuple:
        return tuple(g.lower() for g in ls)
    return [g.lower() for g in ls]


def can_use_without_error(func: callable, arg, error_type=ValueError):
    try:
        func(arg)
    except error_type:
        return False
    return True


def can_int(s: str):
    if not isinstance(s, (str, int, float)):
        return False
    return can_use_without_error(int, s)


def can_float(s: str):
    if not isinstance(s, (str, int, float)):
        return False
    return can_use_without_error(float, s)


def best_guess(target: str, ls: iter):
    di = {g: wr.levenshtein(target, g.lower()) for g in ls}
    return choice([key for key in di if di[key] == min(list(di.values()))])


def two_digit(n: Flint):
    return str(round(n, 2)) + "0" * (2 - len(str(round(n, 2)).split(".")[1]))


def grammatical_join(ls: list, conj: str = "and"):
    if len(ls) <= 2:
        return f" {conj} ".join(ls)
    else:
        return f"{', '.join(ls[:-1])}, {conj} {ls[-1]}"


def admin_check(ctx: commands.Context):
    if ctx.author.id not in [238390171022655489, 474398677599780886]:
        raise commands.CommandError("You don't have permission to run that command.")


def yesno(b: bool):
    return "yes" if b else "no"


def name_focus(user: User):
    return f"**{user.name}**#{user.discriminator}"


def should_await(func: callable):
    if isinstance(func, partial):
        return asyncio.iscoroutinefunction(func.func)
    else:
        return asyncio.iscoroutinefunction(func)


def tsum(*lists: iter):
    try:
        assert [len(g) for g in lists].count(len(lists[0])) == len(lists)  # all lists are the same length
    except AssertionError:
        raise ValueError("All lists must be the same length.")
    else:
        return [sum(g[j] for g in lists) for j in range(len(lists[0]))]


def checked(b: bool):
    return zeph.emojis["checked"] if b else zeph.emojis["unchecked"]


def caseless_match(s: str, database: iter) -> Union[str, None]:
    try:
        return [g for g in database if str(g).lower() == s.lower()][0]
    except IndexError:
        return None


def general_pred(ctx: commands.Context) -> callable:
    return lambda m: m.author == ctx.author and m.channel == ctx.channel


blue = hexcol("3B88C3")  # color that many commands use
testing_emote_servers = [  # servers that either are my testing server or that I use only for emote storage
    405184040161771522, 516004299785109516, 516336805151506449, 516017413729419265, 516044646942638090,
    516015721998843904, 516079973447237648, 528460450069872640, 800832873854271528, 826341777837260811
]
activity_channel = 791776037893308417  # channel ID for the channel in which zeph sends ready + error messages to me
