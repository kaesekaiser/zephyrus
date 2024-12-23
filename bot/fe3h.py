from classes.bot import Zeph
from classes.embeds import Emol
from classes.interpreter import Interpreter
from classes.menus import Navigator
from discord.ext import commands
from functions import hex_to_color
from utilities import fe3hdata as fe

femol = Emol(":crossed_swords:", hex_to_color("FFAC33"))


class FE3HInterpreter(Interpreter):
    redirects = {"meal": "meals"}

    async def _help(self, *args: str):
        help_dict = {
            "meals": "`z!fe3h meals <character>` lists a characters' favorite meals.\n"
                     "`z!fe3h meals <char1> <char2>` lists all the favorite meals shared by two characters."
        }
        desc_dict = {
            "meals": "Check characters' favorite meals.",
        }

        if len(args) == 0 or (args[0].lower() not in help_dict and args[0].lower() not in self.redirects):
            return await femol.send(
                self.ctx, "z!fe3h help",
                d="Available functions:\n\n" + "\n".join(f"`{g}` - {j}" for g, j in desc_dict.items()) +
                  "\n\nFor information on how to use these, use `z!fe3h help <function>`.\n"
                  "(more functions will be added in the future!)"
            )

        ret = self.redirects.get(args[0].lower(), args[0].lower())

        return await femol.send(self.ctx, f"z!fe3h {ret}", d=help_dict[ret])

    async def _meals(self, *args: str):
        if not args or len(args) > 2:
            raise commands.CommandError("Format: `z!fe3h meals <1 or 2 character(s)...>`")

        for arg in args:
            if arg.title() not in fe.characters:
                raise commands.CommandError(f"Invalid character `{arg}`.")

        shared_meals = [f"- {g}" for g, j in fe.meals.items() if all(c.title() in j for c in args)]
        emol = Emol(self.bot.emojis["motivated"], hex_to_color("86FE9F"))

        if not shared_meals:
            return await emol.send(self.ctx, f"{args[0].title()} and {args[1].title()} have no meals in common.")

        if len(args) == 2:
            title = f"Meals Shared by {args[0].title()} and {args[1].title()}"
        else:
            title = f"{args[0].title()}'s Favorite Meals"

        return await Navigator(self.bot, emol, shared_meals, 8, title + " [{page}/{pgs}]").run(self.ctx)


class FE3HCog(commands.Cog):
    def __init__(self, bot: Zeph):
        self.bot = bot

    @commands.command(
        name="fe3h", aliases=["fe"],
        description="Various Fire Emblem: Three Houses data.",
        help="Returns various data from the game Fire Emblem: Three Houses. WIP. See `z!fe3h help` for more."
    )
    async def fe3h_command(self, ctx: commands.Context, func: str = None, *args: str):
        if not func:
            return await femol.send(
                ctx, "Fire Emblem: Three Houses",
                d="This command spits out various data from the game Fire Emblem: Three Houses. It's still a work in "
                  "progress, so it doesn't do much yet. Use `z!fe3h help` for more info."
            )

        return await FE3HInterpreter(self.bot, ctx).run(func, *args)
