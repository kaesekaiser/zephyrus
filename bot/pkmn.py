from utils import *
from pokemon import mons as pk
import json


with open("pokemon/dex.json", "r") as file:
    dexEntries = json.load(file)


def find_mon(s: str):
    for mon in pk.natDex:
        if set(pk.fix(mon, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            ret = mon, pk.fix("-".join(re.split(pk.fix(mon), pk.fix(s))))
            break
    else:
        if pk.fix(s) == "nidoran":
            ret = "Nidoran-F", ""
        else:
            best_guess = sorted(list(pk.fixedDex), key=lambda c: wr.levenshtein(c, pk.fix(s)))
            raise commands.CommandError(f"Mon {s} not found. Did you mean {pk.fixedDex[best_guess[0]]}?")
    for form in pk.natDex[ret[0]].forms:
        if set(pk.fix(form, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            return pk.Mon(ret[0], form=form)
    else:
        return pk.Mon(ret[0])


def dex_entry(mon: pk.Mon, dex: str="Ultra Moon"):
    return {
        "s": f"#{str(mon.dex_no).rjust(3, '0')} {mon.full_name}",
        "thumb": pk.image(mon), "same_line": True, "footer": f"version: {dex}", "fs": {
            "Type": " ／ ".join([zeph.strings[g.lower()] for g in mon.types]), "Species": pk.species[mon.species.name],
            "Height": f"{mon.form.height} m", "Weight": f"{mon.form.weight} kg",
            "Entry": NewLine(pk.dexEntries[mon.species.name].get(dex, "_unavailable_"))}
    }


def scroll_list(l: iter, at: int, curved: bool=False):
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
        super().__init__(Emol(zeph.emojis["poke"], hexcol("f18e38")), [], 1, "",  # params really don't matter here
                         prev=zeph.emojis["dex_prev"], nxt=zeph.emojis["dex_next"])
        self.mon = start
        self.dex = pk.gameDexes["Ultra Sun"]
        self.mode = None
        self.jumpDest = None
        self.funcs["🇸"] = self.scroll_mode
        self.funcs["🇻"] = self.version_mode
        self.funcs["🇫"] = self.forms_mode
        self.funcs["🇯"] = self.jump_mode
        self.funcs[zeph.emojis["help"]] = self.help_mode
        self.funcs[zeph.emojis["no"]] = self.close
        self.funcs["jump"] = self.jump

    def scroll_mode(self):
        self.mode = "scroll" if self.mode != "scroll" else None

    def version_mode(self):
        if self.mode == "version" and self.mon.species.name not in self.dex:
            self.mon = self.dex[1]
        self.mode = "version" if self.mode != "version" else None

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

    @property
    def con(self):
        if not self.mode:
            return self.emol.con(**dex_entry(self.mon, self.dex.name))
        elif self.mode == "scroll":
            return self.emol.con(
                "National Pok\u00e9dex", footer=f"version: {self.dex.name}",
                d=scroll_list([f"``{str(g + 1).rjust(3, '0')}`` {j}" for g, j in enumerate(self.dex.dex)],
                              self.mon.dex_no - 1)
            )
        elif self.mode == "version":
            return self.emol.con(
                "Pok\u00e9dex Version", d=scroll_list(list(pk.gameDexes), list(pk.gameDexes).index(self.dex.name))
            )
        elif self.mode == "forms":
            return self.emol.con(
                f"{self.mon.species.name} Forms",
                d=scroll_list(self.mon.form_names, self.mon.form_names.index(self.mon.full_name))
            )
        elif self.mode == "jump":
            return self.emol.con(
                "Jump to Pok\u00e9mon", d="What Pok\u00e9mon do you want to jump to?",
                footer="Say the name or dex number."
            )
        elif self.mode == "help":
            return self.emol.con(
                "Help", d=f"Use the reactions as buttons to navigate the Pok\u00e9dex!\n\n"
                f"{zeph.emojis['dex_prev']} and {zeph.emojis['dex_next']} scroll between different Pok\u00e9mon or "
                f"menu options.\n:regional_indicator_s: takes you to the list of Pok\u00e9mon.\n"
                f":regional_indicator_v: lets you set which version of the Pok\u00e9dex to use.\n"
                f":regional_indicator_f: lets you change between different forms of a Pok\u00e9mon.\n"
                f":regional_indicator_j: lets you jump to a specific Pok\u00e9mon.\n{zeph.emojis['help']} brings you "
                f"here.\n{zeph.emojis['no']} closes the Pok\u00e9dex."
                f"\n\nHitting the same button again will take you back to the Pok\u00e9mon data screen."
            )

    def advance_page(self, direction: int):
        if direction:
            if not self.mode or self.mode == "scroll":
                self.mon = pk.Mon(self.dex[self.mon.dex_no + direction])
            elif self.mode == "version":
                self.dex = pk.gameDexes[
                    list(pk.gameDexes)[(list(pk.gameDexes).index(self.dex.name) + direction) % len(pk.gameDexes)]
                ]
                if self.mon.species.name not in self.dex:
                    self.mon = pk.Mon(self.dex[1])
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
                    try:
                        find_mon(mr.content)
                    except commands.CommandError:
                        return False
                    else:
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
                    self.jumpDest = find_mon(mess.content)
                return "jump"
            elif isinstance(mess, discord.Reaction):
                return mess.emoji
        return (await zeph.wait_for(
            'reaction_add', timeout=300, check=lambda r, u: r.emoji in self.legal and
            r.message.id == self.message.id and u == ctx.author
        ))[0].emoji


@zeph.command(aliases=["dex"])
async def pokedex(ctx: commands.Context, *, mon: str="1"):
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
