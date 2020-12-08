from pkmn_battle import *


def find_mon(s: str, **kwargs):
    """Use **kwargs to pass additional arguments to the Mon.__init__() statement."""
    for mon in pk.natDex:
        if set(pk.fix(mon, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            ret = mon, pk.fix("-".join(re.split(pk.fix(mon), pk.fix(s))))
            break
    else:
        if pk.fix(s) == "nidoran":
            ret = "Nidoran-F", ""
        else:
            guess = sorted(list(pk.fixedDex), key=lambda c: wr.levenshtein(c, pk.fix(s)))
            raise commands.CommandError(f"`{s}` not found. Did you mean {pk.fixedDex[guess[0]]}?")
    for form in pk.natDex[ret[0]].forms:
        if set(pk.fix(form, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            return pk.Mon(ret[0], form=form, **kwargs)
    else:
        return pk.Mon(ret[0], **kwargs)


def find_move(s: str):
    try:
        return [j.copy() for g, j in pk.moveDex.items() if pk.fix(g) == pk.fix(s)][0]
    except IndexError:
        lis = {pk.fix(g): g for g in pk.moveDex}
        guess = sorted(list(lis), key=lambda c: wr.levenshtein(c, pk.fix(s)))
        raise commands.CommandError(f"`{s}` not found. Did you mean {lis[guess[0]]}?")


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


def scroll_list(l: iter, at: int, curved: bool = False, wrap: bool = True):
    def format_item(index: int):
        return f"**- {l[index].upper()}**" if index == at else f"- {smallcaps(l[index].lower())}"

    if len(l) <= 7:
        if curved:
            raise ValueError("Scroll list is too short to curve.")
        return "\n".join([
            ("\u2007" * [6, 5, 3, 0][abs(g - 4)] if curved else "") + format_item(g) for g in range(len(l))
        ])
    if not wrap:
        if curved:
            raise ValueError("Non-wrapping scroll lists cannot be curved.")
        return "\n".join([
            format_item(g) for g in range(min(max(at - 3, 0), len(l) - 7), max(min(at + 4, len(l)), 7))
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


class DexSearchNavigator(Navigator):
    sorts = {
        "number": lambda m: m.dex_no + list(m.species.forms).index(m.form.name) * 0.01,  # list forms after, in order
        "name": lambda m: m.species.name + m.form.name,  # prioritize species name; list forms alphabetically
        "height": lambda m: m.height,
        "weight": lambda m: m.weight,
        "stats": lambda m: sum(m.base_stats),
        "hp": lambda m: m.form.hp,
        "attack": lambda m: m.form.atk,
        "defense": lambda m: m.form.dfn,
        "spattack": lambda m: m.form.spa,
        "spdefense": lambda m: m.form.spd,
        "speed": lambda m: m.form.spe
    }

    def __init__(self, **kwargs):
        super().__init__(ball_emol(), [], 8, "",  # only the `per` param matters; the table gets rewritten
                         prev=zeph.emojis["dex_prev"], nxt=zeph.emojis["dex_next"])
        self.mode = kwargs.get("mode", None)
        self.dex = copy(pk.natDex)
        self.funcs[zeph.emojis["settings"]] = self.settings_mode
        self.funcs[zeph.emojis["help"]] = self.help_mode
        self.funcs[zeph.emojis["no"]] = self.close
        self.funcs["wait"] = self.do_nothing

        self.gen = None
        self.types = ()
        self.name = None
        self.sort = "number"
        self.forms = False
        self.has = None

        self.reapply_search()

    @property
    def sort_name(self):
        return {
            "number": "National Dex no.",
            "name": "Alphabetical",
            "height": "Height",
            "weight": "Weight",
            "stats": "Total base stats",
            "hp": "HP stat",
            "attack": "Attack stat",
            "defense": "Defense stat",
            "spattack": "SpAttack stat",
            "spdefense": "SpDefense stat",
            "speed": "Speed stat"
        }[self.sort]

    def do_nothing(self):  # control
        pass

    def settings_mode(self):
        self.mode = "settings" if self.mode != "settings" else None

    def help_mode(self):
        self.mode = "help" if self.mode != "help" else None

    def filter(self, mon: pk.Mon):
        """Returns true if the species should be included in the list, false otherwise."""

        funcs = []
        if self.gen:
            funcs.append(lambda m: m.generation == self.gen)
        if self.types:
            funcs.append(lambda m: set(self.types) <= set(m.types))
        if self.name:
            funcs.append(lambda m: m.species.name.startswith(self.name))
        if self.has == "mega":
            funcs.append(lambda m: "Mega " in "".join(m.form_names))
        if self.has == "alolan":
            funcs.append(lambda m: "Alolan " in "".join(m.form_names))

        if not funcs:
            return True
        return all(f(mon) for f in funcs)

    def mon_display(self, mon: pk.Mon):
        mon_name = mon.name if (self.forms and mon.species.notable_forms) else mon.species.name
        dex_no = str(mon.dex_no).rjust(3, '0')

        if self.sort == "number":
            return f"**#{dex_no}** {mon_name}"
        elif self.sort == "name":
            return f"**{mon_name}** (#{dex_no})"
        elif self.sort == "height":
            return f"{mon_name} (**{mon.height}** m)"
        elif self.sort == "weight":
            return f"{mon_name} (**{mon.weight}** kg)"
        elif self.sort == "stats":
            return f"{mon_name} (**{sum(mon.base_stats)}** total)"
        elif self.sort == "hp":
            return f"{mon_name} (**{mon.form.hp}** HP)"
        elif self.sort == "attack":
            return f"{mon_name} (**{mon.form.atk}** Attack)"
        elif self.sort == "defense":
            return f"{mon_name} (**{mon.form.dfn}** Defense)"
        elif self.sort == "spattack":
            return f"{mon_name} (**{mon.form.spa}** SpAttack)"
        elif self.sort == "spdefense":
            return f"{mon_name} (**{mon.form.spd}** SpDefense)"
        elif self.sort == "speed":
            return f"{mon_name} (**{mon.form.spe}** Speed)"

    def reapply_search(self):
        if self.forms:
            dex = [pk.Mon(j, form=f) for j in pk.natDex.values() for f in [None, *j.notable_forms]]
        else:
            dex = [pk.Mon(j) for j in pk.natDex.values()]
        self.dex = filter(self.filter, dex)
        order = sorted(list(self.dex), key=self.sorts[self.sort])
        self.table = [self.mon_display(g) for g in order]
        self.page = 1

    @staticmethod
    def is_valid_setting(s: str):
        """Assumes s is lowercase."""
        if s.count(":") != 1:
            return False

        option, value = s.split(":")
        if value == "any" and option not in ["forms", "sort"]:
            return True

        if option == "gen":
            return can_int(value) and int(value) in range(1, 8)  # ALLOW RANGE VALUES ?
        elif option == "types" or option == "type":
            return all(g.title() in pk.types for g in value.split(","))
        elif option == "name":
            return len(value) == 1 and value.isalpha()
        elif option == "sort":
            return value in DexSearchNavigator.sorts
        elif option == "forms":
            return value in ["yes", "no"]
        elif option == "has":
            return value in ["mega", "alolan"]
        else:
            return False

    def apply_settings_change(self, option: str, value: str):
        """Assumes that the string <option>:<value> passes is_valid_setting()."""

        if option == "gen":
            self.gen = None if value == "any" else int(value)
        if option == "types" or option == "type":
            self.types = () if value == "any" else tuple(g.title() for g in value.split(","))
        if option == "name":
            self.name = None if value == "any" else value.upper()
        if option == "sort":
            self.sort = value
        if option == "forms":
            self.forms = value == "yes"
        if option == "has":
            self.has = None if value == "any" else value

    @property
    def con(self):
        def ain(x): return "any" if x is None or len(str(x)) == 0 else x

        if self.mode == "settings":
            return self.emol.con(
                "Search Settings", d=f"To change a setting, say `<option>:<value>` - for example, `gen:7`. "
                f"Hit {zeph.emojis['help']} for more info on each filter. Hit {zeph.emojis['settings']} again to go "
                f"to the search results.", same_line=True,
                fs={"Generation (`gen`)": ain(self.gen), "Types (`types`)": ain(", ".join(self.types)),
                    "Starts with (`name`)": ain(self.name), "Sort (`sort`)": self.sort_name,
                    "Has Mega/Alolan? (`has`)": ain(self.has), "Include alt forms? (`forms`)": yesno(self.forms)},
                footer=f"Total Pokémon meeting criteria: {len(self.table)}"
            )

        if self.mode == "help":
            return self.emol.con(
                "Search Criteria",
                d="`gen:<n>` - filters by generation. `<n>` must be between 1 and 7, e.g. `gen:4`. `gen:any` resets "
                  "the filter.\n\n"
                  "`type:<types>` (or `types:<types>`) - filters by type. `<types>` can be either one type, or two "
                  "types separated by a comma, e.g. `type:fire,flying`. `type:any` resets the filter.\n\n"
                  "`name:<letter>` - filters by first letter the mon's name. `<letter>` must be one letter, "
                  "e.g. `name:A`. `name:any` resets the filter.\n\n"
                  "`sort:<method>` - sorts the results in a certain order. `<method>` can be `name`, to sort A→Z; "
                  "`number`, to sort by National Dex number; `height`, to sort by height; `weight`, to sort by "
                  "weight; `stats`, to sort by total base stats; or any of `hp`, `attack`, `defense`, `spattack`, "
                  "`spdefense`, or `speed`, to sort by the respective stat. Default is `sort:number`.\n\n"
                  "`has:<form>` - filters by species which have a certain form. `<form>` can be `mega` or `alolan`. "
                  "`has:any` resets the filter.\n\n"
                  "`forms:yes` / `forms:no` - includes or excludes alternate forms in the filter. This includes Mega "
                  "Evolutions, Alolan forms, Primal forms, Rotom forms, etc., but does *not* include forms which are "
                  "solely aesthetic (like those of Vivillon or Gastrodon) or only change the Pokémon's type (like "
                  "Arceus and Silvally). Default is `forms:no`."
            )

        elif not self.mode:
            return self.emol.con(
                f"Search Results [{self.page}/{self.pgs}]",
                d=none_list(page_list(self.table, 8, self.page), "\n"),
                footer=f"Total Pokémon meeting criteria: {len(self.table)}"
            )

    def advance_page(self, direction: int):
        if direction and not self.mode:
            self.page = (self.page + direction - 1) % self.pgs + 1

    async def get_emoji(self, ctx: commands.Context):
        if self.mode == "settings":
            def pred(mr: MR, u: User):
                if isinstance(mr, discord.Message):
                    return u == ctx.author and mr.channel == ctx.channel and self.is_valid_setting(mr.content.lower())
                else:
                    return u == ctx.author and mr.emoji in self.funcs and mr.message.id == self.message.id

            mess = (await zeph.wait_for(
                'reaction_or_message', timeout=300, check=pred
            ))[0]
            if isinstance(mess, discord.Message):
                await mess.delete()
                self.apply_settings_change(*mess.content.lower().split(":"))
                self.reapply_search()
                return "wait"
            elif isinstance(mess, discord.Reaction):
                return mess.emoji

        return (await zeph.wait_for(
            'reaction_add', timeout=300, check=lambda r, u: r.emoji in self.legal and
            r.message.id == self.message.id and u == ctx.author
        ))[0].emoji


@zeph.command(
    aliases=["dex"], usage="z!pokedex [pok\u00e9mon | dex number]\nz!pokedex help\nz!pokedex search [terms...]",
    description="Browses the Pok\u00e9dex.",
    help="Opens the Pok\u00e9dex! `z!dex [pok\u00e9mon...]` or `z!dex [dex number]` will start you at a "
         "specific Pok\u00e9mon; otherwise, it starts at everyone's favorite, Bulbasaur. "
         "`z!dex help` gives help with navigating the dex.\n\nYou can even name a specific form of a "
         "Pok\u00e9mon - e.g. `z!dex giratina origin` starts at Giratina, in Origin Forme.\n\n"
         "`z!dex search` will lead you to a separate menu which lets you sort and filter through the Pok\u00e9dex. "
         "You can change search terms from there; you can also include the search terms in your command, e.g. "
         "`z!dex search type:fire gen:5`."
)
async def pokedex(ctx: commands.Context, *, mon: str = "1"):
    if mon.lower().split()[0] == "search":
        search_args = mon.lower().split()[1:]

        nav = DexSearchNavigator(mode=None if search_args else "settings")
        for arg in search_args:
            if not nav.is_valid_setting(arg):
                raise commands.CommandError(f"Invalid search term `{arg}`.")
            else:
                nav.apply_settings_change(*arg.split(":"))

        nav.reapply_search()
        return await nav.run(ctx)

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
        second_type = f"`{self.type2}` {zeph.emojis[self.type2.title()]}" if self.type2 else "`None`"
        return self.emol.con(
            "Type Effectiveness", thumb=self.image,
            d=f"{zeph.emojis['left1']} [`{self.type1}` {zeph.emojis[self.type1.title()]}] {zeph.emojis['right1']} / "
              f"{zeph.emojis['left2']} [{second_type}] {zeph.emojis['right2']}\n\n" +
              "\n".join([f"**{g}:** {j}" for g, j in self.eff_dict.items()])
        )


@zeph.command(
    aliases=["pkmn", "pk"], usage="z!pokemon help",
    description="Performs various Pok\u00e9mon-related functions.",
    help="Performs a variety of Pok\u00e9mon-related functions. I'm continually adding to this, so just use "
         "`z!pokemon help` for more details."
)
async def pokemon(ctx: commands.Context, func: str = None, *args):
    if not func:
        return await ball_emol().send(
            ctx, "It's Pok\u00e9mon.",
            d="This command is gonna do a good bit eventually. For now it's not much; see `z!pokemon help` for info."
        )

    return await PokemonInterpreter(ctx).run(str(func).lower(), *args)


def type_emol(typ: str):
    return Emol(zeph.emojis[typ.title()], hexcol(pk.typeColors[typ]))


class PokemonInterpreter(Interpreter):
    redirects = {"t": "type", "e": "eff", "m": "move", "s": "test"}

    @staticmethod
    def move_embed(move: pk.Move):
        priority = f" / **Priority:** {move.priority}" if move.priority else ""
        return type_emol(move.type).con(
            move.name,
            d=f"**Type:** {move.type} / **Category:** {move.category}\n"
            f"**Power:** {move.power_str} / **Accuracy:** {move.accuracy_str} / **PP:** {move.pp}{priority}\n"
            f"**Target:** {move.target}\n\n{move.description}"
        )

    async def _help(self, *args):
        help_dict = {
            "type": "`z!pokemon type <type>` shows type effectiveness (offense and defense) for a given type.",
            "eff": "`z!pokemon eff` checks defensive type matchups against a type combination. Use the buttons "
                   f"({zeph.emojis['left1']}{zeph.emojis['right1']}{zeph.emojis['left2']}{zeph.emojis['right2']}) "
                   "to change types.\n`z!pokemon eff <mon...>` shows matchups against a given species or form.\n"
                   "`z!pokemon eff <type1> [type2]` shows matchups against a given type combination.",
            "move": "`z!pokemon move <move>` shows various information about a move - including type, power, "
                    "accuracy, etc."
        }
        desc_dict = {
            "type": "Shows type effectiveness for a type.",
            "eff": "Checks type matchups against a combination of types.",
            "move": "Shows info about a move."
        }
        shortcuts = {j: g for g, j in self.redirects.items() if len(g) == 1}

        def get_command(s: str):
            return f"**`{s}`** (or **`{shortcuts[s]}`**)" if shortcuts.get(s) else f"**`{s}`**"

        if not args or args[0].lower() not in help_dict:
            return await ball_emol().send(
                self.ctx, "z!pokemon help",
                d="Available functions:\n\n" + "\n".join(f"{get_command(g)} - {j}" for g, j in desc_dict.items()) +
                  "\n\nFor information on how to use these, use `z!pokemon help <function>`."
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
        return await type_emol(typ).send(
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
        admin_check(self.ctx)

        field = pk.Field()
        b = Battle(field, self.ctx)
        a = find_mon("Leafeon", field=field, moves=["X-Scissor", "Solar Beam", "Quick Attack", "Yawn"])
        d = find_mon("Aggron", field=field, moves=["Tackle", "Quick Attack", "Growl", "Agility"], item="Light Ball")

        while not b.closed:
            await b.turn(a, d)

    async def _move(self, *args):
        move = find_move(" ".join(args))
        return await self.ctx.send(embed=self.move_embed(move))


@zeph.command(hidden=True, aliases=["lm"], usage="z!lm name type category PP power accuracy contact target **kwargs")
async def loadmove(
    ctx: commands.Context, name: str, typ: str, category: str, pp: int, pwr: Union[int, str], accuracy: int,
    contact: bool, target: str, *args
):
    admin_check(ctx)

    shortcuts = {
        "pt": "can_protect", "mc": "can_magic_coat", "sn": "can_snatch", "mm": "can_mirror_move",
        "kr": "can_kings_rock"
    }

    def interpret_kwarg(s: str):
        if len(s.split("=")) == 1:
            return shortcuts.get(s, s), True
        elif s.startswith("z_effect="):
            return "z_effect", dict((interpret_kwarg(s[9:]), ))
        else:
            return shortcuts.get(s.split("=")[0], s.split("=")[0]), eval(s.split("=")[1])

    kwargs = dict(interpret_kwarg(g) for g in args)

    assert typ.title() in pk.types
    assert category.title() in pk.categories

    move = pk.Move(name, typ.title(), category.title(), pp, pwr, accuracy, contact, eval(f"pk.{target}"), **kwargs)
    assert move.json == move.copy().json

    if move.category == pk.status and not move.z_effect:
        await ctx.send(embed=Emol(zeph.emojis["yield"], hexcol("DD2E44")).con("This status move has no Z-Effect."))
    if move.name in pk.moveDex:
        await ctx.send(embed=Emol(zeph.emojis["yield"], hexcol("DD2E44")).con("This move already exists."))

    await ctx.send(f"```py\n{move.json}```", embed=PokemonInterpreter.move_embed(move.copy()))
    try:
        assert await confirm(f"{'Overwrite' if move.name in pk.moveDex else 'Save'} this move?", ctx, yes="save")
    except AssertionError:
        pass
    else:
        pk.moveDex[move.name] = move.copy()
        with open("pokemon/moves.json", "w") as fp:
            json.dump({g: j.json for g, j in pk.moveDex.items()}, fp, indent=4)
        return await succ.send(ctx, "Move saved.")
