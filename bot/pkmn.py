from utils import *
from pokemon import mons as pk
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
            "Type": " ／ ".join([zeph.strings[g.lower()] for g in mon.types]), "Species": pk.species[mon.species.name],
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
                    "Type": " ／ ".join([zeph.strings[g.lower()] for g in self.mon.types]),
                    "Species": pk.species[self.mon.species.name],
                    "Height": f"{self.mon.form.height} m", "Weight": f"{self.mon.form.weight} kg",
                    "Entry": NewLine(
                        pk.dexEntries[self.mon.species.name][list(pk.dexEntries[self.mon.species.name].keys())[-1]]
                    ),
                    "Base Stats": NewLine(" ／ ".join([str(g) for g in self.mon.base_stats]))
                }
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


@zeph.command(aliases=["dex"])
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


@zeph.command(aliases=["pkmn", "pk"])
async def pokemon(ctx: commands.Context, func: str = None, *args):
    if not func:
        return await ball_emol().send(
            ctx, "Fucking Pok\u00e9mon.", d="This command is gonna do a good bit eventually. For now it's not much."
        )

    return await PokemonInterpreter(ctx).run(str(func).lower(), *args)


class PokemonInterpreter(Interpreter):
    @staticmethod
    def type_emol(typ: str):
        return Emol(zeph.emojis[typ.lower()], hexcol(pk.typeColors[typ]))

    async def _help(self, *args):
        help_dict = {
            "type": "``z!pokemon type <type>`` shows type effectiveness for a given type.",
            "eff": "``z!pokemon eff <mon>`` shows all types' effectiveness against a specific species or form of "
                   "Pok\u00e9mon."
        }

        if not args or args[0].lower() not in help_dict:
            return await ball_emol().send(
                self.ctx, "z!pokemon help",
                d=f"Available functions:\n```{', '.join(list(help_dict.keys()))}```\n"
                f"For information on how to use these, use ``z!pokemon help <function>``."
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
        mon = find_mon(" ".join(args))
        eff = {
            "Doubly weak to": ", ".join([g for g in pk.types if mon.eff(g) == 4]),
            "Weak to": ", ".join([g for g in pk.types if mon.eff(g) == 2]),
            "Damaged normally by": NewLine(", ".join([g for g in pk.types if mon.eff(g) == 1])),
            "Resistant to": ", ".join([g for g in pk.types if mon.eff(g) == 0.5]),
            "Doubly resistant to": ", ".join([g for g in pk.types if mon.eff(g) == 0.25]),
            "Immune to": ", ".join([g for g in pk.types if mon.eff(g) == 0]),
        }
        return await ball_emol().send(
            self.ctx, f"{mon.full_name} ({' ／ '.join([zeph.strings[g.lower()] for g in mon.types])})",
            fs={g: j for g, j in eff.items() if j}, thumb=pk.image(mon), same_line=True
        )
