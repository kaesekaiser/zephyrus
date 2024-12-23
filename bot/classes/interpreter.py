import asyncio
import inspect
from classes.bot import Zeph
from discord.ext import commands
from functions import should_await


class Interpreter:
    redirects = {}

    def __init__(self, bot: Zeph, ctx: commands.Context):
        self.bot = bot
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
