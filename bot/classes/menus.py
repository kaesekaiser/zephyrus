import asyncio
import discord
from classes.bot import Zeph
from classes.embeds import Emol
from discord.ext import commands
from functions import can_int, general_pred, hex_to_color, none_list, should_await
from math import ceil


def page_list(ls: list, per_page: int, page: int):  # assumes page number is between 1 and total pages
    return ls[int(page) * per_page - per_page:int(page) * per_page]


def page_dict(d: dict, per_page: int, page: int):  # assumes page number is between 1 and total pages
    return {g: j for g, j in d.items() if g in page_list(list(d.keys()), per_page, page)}


class Navigator:
    """Intended mostly as a parent class. Large number of seemingly unnecessary functions is intentional; it allows
    for child classes to overwrite large amounts of the run() function without having to overwrite the function
    itself. """

    def __init__(self, bot: Zeph, emol: Emol, ls: list = (), per: int = 8, title: str = "",
                 prev: discord.Emoji | str | None = "◀", nxt: discord.Emoji | str | None = "▶", **kwargs):
        # kwargs are also passed to Emol.con()
        self.bot = bot
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
        def pred(mr: discord.Message | discord.Reaction, u: discord.User | discord.Member):
            if isinstance(mr, discord.Message):
                return u == ctx.author and mr.channel == ctx.channel and self.is_valid_non_emoji(mr.content)
            else:
                return u == ctx.author and mr.message == self.message and mr.emoji in self.legal

        mess = (await self.bot.wait_for('reaction_or_message', timeout=self.dynamic_timeout(), check=pred))[0]

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
    def __init__(self, bot: Zeph, emol: Emol, d: dict, per: int, s: str, **kwargs):
        super().__init__(bot, emol, [], per, s, **kwargs)
        self.table = d

    def con(self):
        return self.emol.con(
            self.title.format(page=self.page, pgs=self.pgs),
            d=self.prefix,
            fs=page_dict(self.table, self.per, self.page), **self.kwargs
        )


class NumSelector(Navigator):
    """A Navigator with the option to select one of a numerical list via chat message built-in."""
    def __init__(self, bot: Zeph, emol: Emol, ls: list = (), per: int = 8, s: str = "", **kwargs):
        super().__init__(bot, emol, ls, per, s, **kwargs)
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
        def pred(mr: discord.Message | discord.Reaction, u: discord.User | discord.Member):
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

        mess = (await self.bot.wait_for('reaction_or_message', timeout=self.timeout, check=pred))[0]

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
