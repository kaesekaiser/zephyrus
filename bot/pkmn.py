from utils import *
from pokemon import teams as pk
import json


with open("pokemon/dex.json", "r") as file:
    dexEntries = json.load(file)


ballColors = {
    "beast": "8FD5F6", "cherish": "E84535", "dive": "81C7EF", "dream": "F4B4D0", "dusk": "30A241", "fast": "F2C63F",
    "friend": "80BA40", "great": "3B82C4", "heal": "E95098", "heavy": "9B9EA4", "level": "F5D617", "love": "E489B8",
    "lure": "49B0BE", "luxury": "D29936", "master": "7E308E", "moon": "00A6BA", "nest": "7EBF41", "net": "0998B4",
    "park": "F4D050", "poke": "F18E38", "premier": "FFFFFF", "quick": "73B5E4", "repeat": "FFF338", "safari": "307D54",
    "sport": "F18E38", "timer": "FFFFFF", "ultra": "FDD23C"
}


def ball_emol():
    ret = choice(list(ballColors))
    return Emol(zeph.emojis[f"{ret}_ball"], hexcol(ballColors[ret]))


def find_mon(s: str):
    for mon in pk.natDex:
        if set(pk.fix(mon, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            ret = mon, pk.fix("-".join(re.split(pk.fix(mon), pk.fix(s))))
            break
    else:
        if pk.fix(s) == "nidoran":
            ret = "Nidoran-F", ""
        else:
            guess = sorted(list(pk.fixedDex), key=lambda c: wr.levenshtein(c, pk.fix(s)))
            raise commands.CommandError(f"``{s}`` not found. Did you mean {pk.fixedDex[guess[0]]}?")
    for form in pk.natDex[ret[0]].forms:
        if set(pk.fix(form, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            return pk.Mon(ret[0], form=form)
    else:
        return pk.Mon(ret[0])


def dex_entry(mon: pk.Mon):
    return {
        "s": f"#{str(mon.dex_no).rjust(3, '0')} {mon.full_name}",
        "thumb": pk.image(mon), "same_line": True, "fs": {
            "Type": " ／ ".join([zeph.strings[g.title()] for g in mon.types]), "Species": pk.species[mon.species.name],
            "Height": f"{mon.form.height} m", "Weight": f"{mon.form.weight} kg",
            "Entry": NewLine(pk.dexEntries[mon.species.name][list(pk.dexEntries[mon.species.name].keys())[-1]]),
            "Base Stats": NewLine(" ／ ".join([str(g) for g in mon.base_stats]))
        }
    }


def scroll_list(l: iter, at: int, curved: bool = False):
    def format_item(index: int):
        return f"**- {l[index].upper()}**" if index == at else f"- {smallcaps(l[index].lower())}"

    if len(l) <= 7:
        return "\n".join([
            ("\u2007" * [6, 5, 3, 0][abs(g - 4)] if curved else "") + format_item(g) for g in range(len(l))
        ])
    return "\n".join([
        ("\u2007" * [6, 5, 3, 0][abs(g - at)] if curved else "") + format_item(g % len(l))
        for g in range(at - 3, at + 4)
    ])


class DexNavigator(Navigator):
    def __init__(self, start: pk.Mon):
        super().__init__(ball_emol(), [], 1, "",  # params really don't matter here
                         prev=zeph.emojis["dex_prev"], nxt=zeph.emojis["dex_next"])
        self.mon = start
        self.dex = pk.gameDexes["Ultra Sun"]
        self.mode = None
        self.jumpDest = None
        self.funcs[zeph.emojis["forms"]] = self.forms_mode
        self.funcs[zeph.emojis["search"]] = self.jump_mode
        self.funcs[zeph.emojis["help"]] = self.help_mode
        self.funcs[zeph.emojis["no"]] = self.close
        self.funcs["jump"] = self.jump
        self.funcs["wait"] = self.do_nothing
        self.last_guess = None

    def do_nothing(self):
        pass

    def forms_mode(self):
        self.mode = "forms" if self.mode != "forms" else None

    def jump_mode(self):
        self.mode = "jump" if self.mode != "jump" else None

    def help_mode(self):
        self.mode = "help" if self.mode != "help" else None

    def jump(self):
        if isinstance(self.jumpDest, pk.Mon):
            self.mon = self.jumpDest
        else:
            self.mon = pk.Mon(self.dex[self.jumpDest])
        self.jumpDest = None
        self.mode = None
        self.last_guess = None

    @property
    def con(self):
        if not self.mode:
            return self.emol.con(
                f"#{str(self.mon.dex_no).rjust(3, '0')} {self.mon.full_name}",
                thumb=pk.image(self.mon), same_line=True, fs={
                    "Type": " ／ ".join([zeph.strings[g.title()] for g in self.mon.types]),
                    "Species": pk.species[self.mon.species.name],
                    "Height": f"{self.mon.form.height} m", "Weight": f"{self.mon.form.weight} kg",
                    "Entry": NewLine(
                        pk.dexEntries[self.mon.species.name][list(pk.dexEntries[self.mon.species.name].keys())[-1]]
                    ),
                    "Base Stats": NewLine(
                        " ／ ".join([str(g) for g in self.mon.base_stats]) +
                        f" ({sum(self.mon.base_stats)})\n\n[Bulbapedia]({self.mon.bulbapedia}) | "
                        f"[Serebii]({self.mon.serebii}) | [Pok\u00e9monDB]({self.mon.pokemondb})"
                    )
                },
            )
        elif self.mode == "forms":
            return self.emol.con(
                f"{self.mon.species.name} Forms",
                d=scroll_list(self.mon.form_names, self.mon.form_names.index(self.mon.full_name)),
                thumb=pk.image(self.mon)
            )
        elif self.mode == "jump":
            return self.emol.con(
                "Find Pok\u00e9mon", footer="Say the name or dex number.",
                d=self.last_guess if self.last_guess else "What Pok\u00e9mon are you looking for?"
            )
        elif self.mode == "help":
            return self.emol.con(
                "Help", d=f"Use the reactions as buttons to navigate the Pok\u00e9dex!\n\n"
                f"{zeph.emojis['dex_prev']} and {zeph.emojis['dex_next']} scroll between different Pok\u00e9mon or "
                f"menu options.\n"
                f"{zeph.emojis['forms']} lets you change between different forms of a Pok\u00e9mon.\n"
                f"{zeph.emojis['search']} lets you find a specific Pok\u00e9mon.\n{zeph.emojis['help']} brings you "
                f"here.\n{zeph.emojis['no']} closes the Pok\u00e9dex."
                f"\n\nHitting the same button again will take you back to the Pok\u00e9mon data screen."
            )

    def advance_page(self, direction: int):
        if direction:
            if not self.mode:
                self.mon = pk.Mon(self.dex[self.mon.dex_no + direction])
            elif self.mode == "forms":
                self.mon = pk.Mon(
                    self.mon.species, form=list(self.mon.species.forms)[
                        (list(self.mon.species.forms).index(self.mon.form.name) + direction)
                        % len(self.mon.species.forms)
                    ]
                )

    async def get_emoji(self, ctx: commands.Context):
        if self.mode == "jump":
            def pred(mr: MR, u: User):
                if isinstance(mr, discord.Message):
                    if can_int(mr.content):
                        return u == ctx.author and int(mr.content) in range(1, len(self.dex) + 1) \
                            and mr.channel == ctx.channel
                    return u == ctx.author and mr.channel == ctx.channel
                else:
                    return u == ctx.author and mr.emoji in self.funcs and mr.message.id == self.message.id

            mess = (await zeph.wait_for(
                'reaction_or_message', timeout=300, check=pred
            ))[0]
            if isinstance(mess, discord.Message):
                await mess.delete()
                try:
                    self.jumpDest = int(mess.content)
                except ValueError:
                    try:
                        self.jumpDest = find_mon(mess.content)
                    except commands.CommandError as e:
                        self.last_guess = str(e)
                        return "wait"
                    return "jump"
                return "jump"
            elif isinstance(mess, discord.Reaction):
                return mess.emoji
        return (await zeph.wait_for(
            'reaction_add', timeout=300, check=lambda r, u: r.emoji in self.legal and
            r.message.id == self.message.id and u == ctx.author
        ))[0].emoji


@zeph.command(
    aliases=["dex"], usage="z!pokedex [pok\u00e9mon...]\nz!pokedex [dex number]\nz!pokedex help",
    description="Browses the Pok\u00e9dex.",
    help="Opens the Pok\u00e9dex! ``z!dex [pok\u00e9mon...]`` or ``z!dex [dex number]`` will start you at a "
         "specific Pok\u00e9mon; otherwise, it starts at everyone's favorite, Bulbasaur. "
         "``z!dex help`` gives help with navigating the dex.\n\nYou can even name a specific form of a "
         "Pok\u00e9mon - e.g. ``z!dex giratina origin`` starts at Giratina, in Origin Forme."
)
async def pokedex(ctx: commands.Context, *, mon: str = "1"):
    if can_int(mon):
        init_mon = pk.Mon(pk.gameDexes["Ultra Sun"][int(mon)])
    elif mon.lower() == "help":
        init_mon = pk.Mon(pk.natDex["Bulbasaur"])
    else:
        init_mon = find_mon(mon)
    nav = DexNavigator(init_mon)
    if mon.lower() == "help":
        nav.mode = "help"
    return await nav.run(ctx)


class EffNavigator(Navigator):
    types = (None, ) + pk.types

    def __init__(self, type1: str, type2: str = None):
        super().__init__(ball_emol(), [], 1, "", prev="", nxt="")
        self.type1 = type1
        self.type2 = type2
        self.funcs[zeph.emojis["left1"]] = self.type1bac
        self.funcs[zeph.emojis["right1"]] = self.type1for
        self.funcs[zeph.emojis["left2"]] = self.type2bac
        self.funcs[zeph.emojis["right2"]] = self.type2for

    @property
    def eff_dict(self):
        def eff(atk: str, dfn: str):
            return pk.effectiveness[atk].get(dfn, 1)

        ret = {
            "4x": ", ".join([g for g in pk.types if eff(g, self.type1) * eff(g, self.type2) == 4]),
            "2x": ", ".join([g for g in pk.types if eff(g, self.type1) * eff(g, self.type2) == 2]),
            "1x": ", ".join([g for g in pk.types if eff(g, self.type1) * eff(g, self.type2) == 1]),
            "1/2x": ", ".join([g for g in pk.types if eff(g, self.type1) * eff(g, self.type2) == 0.5]),
            "1/4x": ", ".join([g for g in pk.types if eff(g, self.type1) * eff(g, self.type2) == 0.25]),
            "0x": ", ".join([g for g in pk.types if eff(g, self.type1) * eff(g, self.type2) == 0])
        }
        return {g: j for g, j in ret.items() if j}

    def type1for(self):
        self.type1 = pk.types[(pk.types.index(self.type1) + 1) % len(pk.types)]

    def type1bac(self):
        self.type1 = pk.types[(pk.types.index(self.type1) - 1) % len(pk.types)]

    def type2for(self):
        self.type2 = self.types[(self.types.index(self.type2) + 1) % len(self.types)]

    def type2bac(self):
        self.type2 = self.types[(self.types.index(self.type2) - 1) % len(self.types)]

    @property
    def image(self):
        try:
            return pk.image(find_mon(choice(pk.exemplaryMons[frozenset([self.type1, self.type2])])))
        except KeyError:
            return None

    @property
    def con(self):
        second_type = f"``{self.type2}`` {zeph.emojis[self.type2.title()]}" if self.type2 else "``None``"
        return self.emol.con(
            "Type Effectiveness", thumb=self.image,
            d=f"{zeph.emojis['left1']} [``{self.type1}`` {zeph.emojis[self.type1.title()]}] {zeph.emojis['right1']} / "
              f"{zeph.emojis['left2']} [{second_type}] {zeph.emojis['right2']}\n\n" +
              "\n".join([f"**{g}:** {j}" for g, j in self.eff_dict.items()])
        )


@zeph.command(
    aliases=["pkmn", "pk"], usage="z!pokemon help",
    description="Performs various Pok\u00e9mon-related functions.",
    help="Performs a variety of Pok\u00e9mon-related functions. I'm continually adding to this, so just use "
         "``z!pokemon help`` for more details."
)
async def pokemon(ctx: commands.Context, func: str = None, *args):
    if not func:
        return await ball_emol().send(
            ctx, "It's Pok\u00e9mon.",
            d="This command is gonna do a good bit eventually. For now it's not much; see `z!pokemon help` for info."
        )

    return await PokemonInterpreter(ctx).run(str(func).lower(), *args)


class PokemonInterpreter(Interpreter):
    redirects = {"t": "type", "e": "eff"}

    @staticmethod
    def type_emol(typ: str):
        return Emol(zeph.emojis[typ.title()], hexcol(pk.typeColors[typ]))

    async def _help(self, *args):
        help_dict = {
            "type": "``z!pokemon type <type>`` shows type effectiveness (offense and defense) for a given type.",
            "eff": "``z!pokemon eff`` checks defensive type matchups against a type combination. Use the buttons "
                   f"({zeph.emojis['left1']}{zeph.emojis['right1']}{zeph.emojis['left2']}{zeph.emojis['right2']}) "
                   "to change types.\n``z!pokemon eff <mon...>`` shows matchups against a given species or form.\n"
                   "``z!pokemon eff <type1> [type2]`` shows matchups against a given type combination."
        }
        desc_dict = {
            "type": "Shows type effectiveness for a type.",
            "eff": "Checks type matchups against a combination of types."
        }
        shortcuts = {j: g for g, j in self.redirects.items() if len(g) == 1}

        def get_command(s: str):
            return f"**`{s}`** (or **`{shortcuts[s]}`**)" if shortcuts.get(s) else f"**`{s}`**"

        if not args or args[0].lower() not in help_dict:
            return await ball_emol().send(
                self.ctx, "z!pokemon help",
                d="Available functions:\n\n" + "\n".join(f"{get_command(g)} - {j}" for g, j in desc_dict.items()) +
                  "\n\nFor information on how to use these, use ``z!planes help <function>``."
            )

        return await ball_emol().send(self.ctx, f"z!pokemon {args[0].lower()}", d=help_dict[args[0].lower()])

    async def _type(self, *args):
        typ = str(args[0]).title()
        if typ.title() not in pk.types:
            raise commands.CommandError(f"{typ} isn't a type.")

        eff = {
            "Super effective against": [g for g in pk.types if pk.effectiveness[typ][g] > 1],
            "Not very effective against": [g for g in pk.types if 0 < pk.effectiveness[typ][g] < 1],
            "Ineffective against": [g for g in pk.types if not pk.effectiveness[typ][g]],
            "Immune to": [g for g in pk.types if not pk.effectiveness[g][typ]],
            "Resistant to": [g for g in pk.types if 0 < pk.effectiveness[g][typ] < 1],
            "Weak to": [g for g in pk.types if pk.effectiveness[g][typ] > 1]
        }
        return await self.type_emol(typ).send(
            self.ctx, f"{typ}-type", fs={g: ", ".join(j) for g, j in eff.items() if j}, same_line=True
        )

    async def _eff(self, *args):
        try:
            types = find_mon(" ".join(args)).types
        except commands.CommandError:
            if set(g.title() for g in args).issubset(set(EffNavigator.types)) and 0 < len(args) < 3:
                types = [g.title() for g in args]
            else:
                types = ["Normal"]

        return await EffNavigator(*types).run(self.ctx)

    async def _test(self, *args):
        stat = pk.StatChange(1, {g: randrange(-3, 4) for g in pk.StatChange.stat_name_dict})
        mon = find_mon("Pikachu")
        eff = mon.apply(stat)
        for i in eff:
            await ball_emol().send(
                self.ctx, pk.stat_change_text(mon, i, eff[i])
            )
        return await ball_emol().send(self.ctx, str(mon.stat_stages))
