from pkmn_battle import *
from copy import deepcopy as copy


def find_mon(s: str, **kwargs) -> pk.Mon:
    """Use **kwargs to pass additional arguments to the Mon.__init__() statement."""
    if can_int(s) or isinstance(s, int):
        return pk.Mon(list(pk.nat_dex.keys())[(int(s) - 1) % len(pk.nat_dex)], **kwargs)
    if ret := pk.species_and_forms.get(pk.fix(s)):
        return pk.Mon(ret[0], form=ret[1], **kwargs)
    for mon in pk.nat_dex:
        if set(pk.fix(mon, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            ret = mon, pk.fix("-".join(re.split(pk.fix(mon), pk.fix(s))))
            break
    else:
        if pk.fix(s) == "nidoran":
            ret = "Nidoran-F", ""
        else:
            if kwargs.get("fail_silently") or kwargs.get("return_on_fail"):
                return kwargs.get("return_on_fail", pk.Mon.null())
            else:
                guess = sorted(list(pk.fixed_dex), key=lambda c: wr.levenshtein(c, pk.fix(s)))
                raise commands.CommandError(f"`{s}` not found. Did you mean {pk.fixed_dex[guess[0]]}?")
    for form in pk.nat_dex[ret[0]].forms:
        if set(pk.fix(form, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            return pk.Mon(ret[0], form=form, **kwargs)
    else:
        return pk.Mon(ret[0], **kwargs)


def find_move(s: str) -> pk.Move:
    try:
        return [j.copy() for g, j in pk.moveDex.items() if pk.fix(g) == pk.fix(s)][0]
    except IndexError:
        lis = {pk.fix(g): g for g in pk.moveDex}
        guess = sorted(list(lis), key=lambda c: wr.levenshtein(c, pk.fix(s)))
        raise commands.CommandError(f"`{s}` not found. Did you mean {lis[guess[0]]}?")


def scroll_list(ls: iter, at: int, curved: bool = False, wrap: bool = True) -> str:
    def format_item(index: int):
        return f"**\\> {ls[index].upper()}**" if index == at else f"- {smallcaps(ls[index].lower())}"

    if len(ls) <= 7:
        if curved:
            raise ValueError("Scroll list is too short to curve.")
        return "\n".join([
            ("\u2007" * [6, 5, 3, 0][abs(g - 4)] if curved else "") + format_item(g) for g in range(len(ls))
        ])
    if not wrap:
        if curved:
            raise ValueError("Non-wrapping scroll lists cannot be curved.")
        return "\n".join([
            format_item(g) for g in range(min(max(at - 3, 0), len(ls) - 7), max(min(at + 4, len(ls)), 7))
        ])
    return "\n".join([
        ("\u2007" * [6, 5, 3, 0][abs(g - at)] if curved else "") + format_item(g % len(ls))
        for g in range(at - 3, at + 4)
    ])


class DexNavigator(Navigator):
    def __init__(self, start: pk.Mon, **kwargs):
        super().__init__(
            kwargs.get("emol", ball_emol()), [], 1, "",
            prev=zeph.emojis["dex_prev"], nxt=zeph.emojis["dex_next"], close_on_timeout=True
        )
        self.mon = start
        self.mode = kwargs.get("starting_mode")
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

    async def close(self):
        return await self.remove_buttons()

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
            self.mon = find_mon(self.jumpDest)
        self.jumpDest = None
        self.mode = None
        self.last_guess = None

    @property
    def con(self):
        if not self.mode:
            return self.emol.con(
                f"#{str(self.mon.dex_no).rjust(4, '0')} {self.mon.full_name}",
                thumb=pk.image(self.mon), d=display_mon(self.mon, "dex")
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
                          f"{zeph.emojis['dex_prev']} and {zeph.emojis['dex_next']} scroll between different "
                          f"Pok\u00e9mon or menu options.\n"
                          f"{zeph.emojis['forms']} lets you change between different forms of a Pok\u00e9mon.\n"
                          f"{zeph.emojis['search']} lets you find a specific Pok\u00e9mon.\n{zeph.emojis['help']} "
                          f"brings you here.\n{zeph.emojis['no']} closes the Pok\u00e9dex."
                          f"\n\nHitting the same button again will take you back to the Pok\u00e9mon data screen."
            )

    def advance_page(self, direction: int):
        if direction:
            if not self.mode:
                self.mon = find_mon(self.mon.dex_no + direction)
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
                        return u == ctx.author and int(mr.content) in range(1, len(pk.nat_dex) + 1) \
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
        self.dex = copy(pk.nat_dex)
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

    async def close(self):
        self.closed_elsewhere = True
        return await self.remove_buttons()

    def filter(self, mon: pk.Mon):
        """Returns true if the species should be included in the list, false otherwise."""

        funcs = []
        if self.gen:
            funcs.append(lambda m: m.generation == self.gen)
        if self.types:
            funcs.append(lambda m: set(self.types) <= set(m.types_with_none))
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
        mon_name = mon.species_and_form if (self.forms and mon.species.notable_forms) else mon.species.name
        dex_no = str(mon.dex_no).rjust(4, '0')

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
            dex = [pk.Mon(j, form=f) for j in pk.nat_dex.values() for f in [None, *j.notable_forms]]
        else:
            dex = [pk.Mon(j) for j in pk.nat_dex.values()]
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
            return all(g.title() in pk.types or g.title() == "None" for g in re.split(r"[/,]", value))
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
            self.types = () if value == "any" else tuple(g.title() for g in re.split(r"[/,]", value))
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
        def ain(x):
            return "any" if x is None or len(str(x)) == 0 else x

        if self.mode == "settings":
            return self.emol.con(
                "Search Settings",
                d=f"To change a setting, say `<option>:<value>` - for example, `gen:7`. "
                  f"Hit {zeph.emojis['help']} for more info on each filter. "
                  f"Hit {zeph.emojis['settings']} again to go to the search results.",
                same_line=True,
                fs={"Generation (`gen`)": ain(self.gen), "Types (`types`)": ain(", ".join(self.types)),
                    "Starts with (`name`)": ain(self.name), "Sort (`sort`)": self.sort_name,
                    "Has Mega/Alolan? (`has`)": ain(self.has), "Include alt forms? (`forms`)": yesno(self.forms)},
                footer=f"Total Pokémon meeting criteria: {len(self.table)}"
            )

        if self.mode == "help":
            return self.emol.con(
                "Search Criteria",
                d="`gen:<n>` - filters by generation. `<n>` must be between 1 and 9, e.g. `gen:4`. `gen:any` resets "
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
    name="pokedex",
    aliases=["dex"], usage="z!pokedex [pok\u00e9mon | dex number]\nz!pokedex help\nz!pokedex search [terms...]",
    description="Browses the Pok\u00e9dex.",
    help="**NOTE: `z!dex` is being deprecated in favor of `z!pokemon dex`.\n\n"
         "Opens the Pok\u00e9dex! `z!dex [pok\u00e9mon...]` or `z!dex [dex number]` will start you at a "
         "specific Pok\u00e9mon; otherwise, it starts at everyone's favorite, Bulbasaur. "
         "`z!dex help` gives help with navigating the dex.\n\nYou can even name a specific form of a "
         "Pok\u00e9mon - e.g. `z!dex giratina origin` starts at Giratina, in Origin Forme.\n\n"
         "`z!dex search` will lead you to a separate menu which lets you sort and filter through the Pok\u00e9dex. "
         "You can change search terms from there; you can also include the search terms in your command, e.g. "
         "`z!dex search type:fire gen:5`."
)
async def dex_command(ctx: commands.Context, *mon: str):
    await err.send(ctx, "`z!dex` is being deprecated. Use `z!pokemon dex` instead.")
    return await PokemonInterpreter(ctx).run("dex", *mon)


class EffNavigator(Navigator):
    types = (None,) + pk.types

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
            return pk.image(find_mon(choice(pk.exemplary_mons[frozenset([self.type1, self.type2])])))
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
    name="pokemon", aliases=["pkmn", "pk"], usage="z!pokemon help",
    description="Performs various Pok\u00e9mon-related functions.",
    help="Performs a variety of Pok\u00e9mon-related functions. I'm continually adding to this, so just use "
         "`z!pokemon help` for more details."
)
async def pokemon_command(ctx: commands.Context, func: str = None, *args):
    if not func:
        return await ball_emol().send(
            ctx, "It's Pok\u00e9mon.",
            d="This command is gonna do a good bit eventually. For now it's not much; see `z!pokemon help` for info."
        )

    return await PokemonInterpreter(ctx).run(str(func).lower(), *args)


def type_emol(typ: str):
    return Emol(zeph.emojis[typ.title()], hexcol(pk.typeColors[typ]))


class BuildAMonNavigator(Navigator):
    editable_properties = [
        "species", "form", "level", "tera", "item", "ability", "moves", "nature", "evs", "ivs", "gender", "nickname",
        "key"
    ]

    def __init__(self, ctx: commands.Context, title: str = "Build-A-Mon", **kwargs):
        super().__init__(kwargs.get("emol", ball_emol()), [], 0, "", prev="", nxt="")
        self.ctx = ctx
        self.title = title
        self.mon = kwargs.get("starting_mon", find_mon("Bulbasaur"))
        self.saved = False
        self.cancelled = False
        self.funcs["💾"] = self.save_and_exit
        self.funcs[zeph.emojis["no"]] = self.cancel
        self.delete_on_close = kwargs.get("delete_on_close", False)

    def general_pred(self, m: discord.Message):
        return m.channel == self.ctx.channel and m.author == self.ctx.author

    async def save_and_exit(self):
        self.saved = True
        await self.close()

    async def cancel(self):
        self.cancelled = True
        await self.close()

    async def close(self):
        self.closed_elsewhere = True
        if self.delete_on_close:
            await self.message.delete()
        else:
            await self.remove_buttons()

    @staticmethod
    def species_exists(s: str):
        try:
            find_mon(s)
        except commands.CommandError:
            return False
        else:
            return True

    @staticmethod
    def move_exists(s: str):
        try:
            find_move(s)
        except commands.CommandError:
            return s.lower() in ["reorder", "done"]
        else:
            return True

    @staticmethod
    def stats_from_str(s: str) -> list[int]:
        if len(s.split()) == 2 and s.startswith("all "):
            return [int(s.split()[1])] * 6
        return [int(g) for g in s.split()]

    @staticmethod
    def parse_nature(s: str) -> str:
        if s.title() in pk.natures:
            return s.title()
        if re.fullmatch(r"\+(atk|def|spa|spd|spe) -(atk|def|spa|spd|spe)", s.lower()):
            six_stats = list(pk.six_stats.keys())
            ni = (six_stats.index(s.lower().split()[0][1:]) - 1) * 5 + six_stats.index(s.lower().split()[1][1:]) - 1
            return pk.natures[ni]
        return ""

    @staticmethod
    def valid_evs(s: str):
        split = s.split()
        if len(split) == 2 and split[0].lower() == "all" and can_int(split[1]) and 0 <= int(split[1]) * 6 <= 512:
            return True
        if not (len(split) == 6 and all([can_int(g) for g in split])):
            return False
        evs = [int(g) for g in split]
        if sum(evs) > 510:
            return False
        if any([g > 252 or g < 0 for g in evs]):
            return False
        return True

    @staticmethod
    def valid_ivs(s: str):
        split = s.split()
        if len(split) == 2 and split[0].lower() == "all" and can_int(split[1]) and 0 <= int(split[1]) <= 31:
            return True
        if not (len(split) == 6 and all([can_int(g) for g in split])):
            return False
        ivs = [int(g) for g in split]
        if any([g > 31 or g < 0 for g in ivs]):
            return False
        return True

    async def after_timeout(self):
        raise asyncio.TimeoutError

    async def get_emoji(self, ctx: commands.Context):
        def pred(mr: MR, u: User = self.ctx.author):
            if isinstance(mr, discord.Message):
                return self.general_pred(mr) and mr.content.lower() in self.editable_properties
            elif isinstance(mr, discord.Reaction):
                return mr.emoji in self.legal and mr.message.id == self.message.id and u == self.ctx.author

        user_input = (await zeph.wait_for("reaction_or_message", check=pred, timeout=300))[0]
        if isinstance(user_input, discord.Message):
            await user_input.delete()
            return user_input.content.lower()
        elif isinstance(user_input, discord.Reaction):
            return user_input.emoji

    async def wait_for(self, message_type: str, force_lower: bool = True) -> str:
        def valid_move_swap(s: str):
            if not (len(s.split()) == 2 and all([can_int(g) for g in s.split()])):
                return s.lower() == "done"
            swap = [int(g) for g in s.split()]
            if swap[0] == swap[1] or any([g > len(self.mon.moves) or g < 1 for g in swap]):
                return False
            return True

        def form_exists(s: str):
            try:
                self.mon.species.get_form_name(s)
            except ValueError:
                return False
            else:
                return True

        additional_checks = {
            "species": self.species_exists,
            "form": form_exists,
            "nickname": lambda c: len(c) <= 18,
            "level": can_int,
            "gender": lambda c: (c.lower() in ["male", "female", "random"]) and self.mon.default_gender == "random",
            "tera": lambda c: caseless_match(c, pk.types),
            "item": lambda c: caseless_match(c, pk.held_items) or c.lower() == "none",
            "ability": lambda c: caseless_match(c, pk.abilities) or c.lower() == "none",
            "move": self.move_exists,
            "nature": self.parse_nature,
            "evs": self.valid_evs,
            "ivs": self.valid_ivs,
            "move_placement": (
                lambda c: (can_int(c) and 1 <= int(c) <= 4) or self.mon.has_move(c) or c.lower() == "cancel"
            ),
            "move_swap": valid_move_swap
        }
        necessary_check = additional_checks.get(message_type, lambda m: True)
        mess = await zeph.wait_for(
            "message", check=lambda m: self.general_pred(m) and bool(necessary_check(m.content)), timeout=300
        )
        await mess.delete()
        if force_lower:
            return mess.content.lower()
        else:
            return mess.content

    async def run_nonstandard_emoji(self, emoji: Union[discord.Emoji, str], ctx: commands.Context):
        if emoji == "moves":
            return await self.edit_moves()
        if emoji == "form" and len(self.mon.species.forms) == 1:
            mess = await self.emol.send(self.ctx, f"{self.mon.species.name} has no form changes.")
            await asyncio.sleep(2)
            return await mess.delete()
        if emoji == "gender" and self.mon.default_gender != "random":
            mess = await self.emol.send(self.ctx, f"{self.mon.species.name} is {self.mon.default_gender} only.")
            await asyncio.sleep(2)
            return await mess.delete()

        if emoji not in self.editable_properties:
            return

        messages = {
            "species": "What species should the mon be?",
            "form": f"What form should the mon be?\nAvailable forms: "
                    f"{', '.join([g if g else 'Base' for g in self.mon.species.forms.keys()])}.",
            "nickname": "What should the mon's nickname be?\nNicknames can be no more than 18 characters long. "
                        "To remove its nickname, say `none`.",
            "level": "What level should the mon be?",
            "gender": "What should the mon's gender be?",
            "tera": "What should the mon's Tera type be?",
            "item": "What item should the mon hold?",
            "ability": "What ability should the mon have?",
            "nature": "What nature should the mon have?\nName the nature itself, or define it via its stat changes: "
                      "an Adamant nature may be input as `+Atk -SpA`, for example.",
            "evs": "What should the mon's EVs be?\nGive six numbers separated by spaces, e.g. `0 252 0 4 0 252`. "
                   "These must be a [valid set of EVs](https://www.smogon.com/ingame/guides/understanding-evs).",
            "ivs": "What should the mon's IVs be?\nGive six numbers separated by spaces, e.g. `31 0 31 31 31 0`. "
                   "These must be between 0 and 31.",
            "key": "Paste the key of the mon you'd like to import."
        }
        mess = await self.emol.send(
            self.ctx, messages[emoji].split("\n")[0], d="\n".join(messages[emoji].split("\n")[1:]),
        )
        user_input = await self.wait_for(emoji, force_lower=emoji not in ["key", "nickname"])
        if emoji == "species":
            mon = find_mon(user_input)
            pack = self.mon.pack
            pack["spc"] = mon.species
            pack["form"] = mon.form.name
            del pack["tera"]
            self.mon = pk.Mon.unpack(pack)
        if emoji == "form":
            self.mon.change_form(user_input)
        if emoji == "nickname":
            self.mon.set_nickname(user_input)
        if emoji == "level":
            self.mon.level = int(user_input)
        if emoji == "gender":
            self.mon.gender = user_input
        if emoji == "tera":
            self.mon.tera_type = caseless_match(user_input, pk.types)
        if emoji == "item":
            if user_input == "none":
                self.mon.held_item = "No Item"
            else:
                self.mon.held_item = caseless_match(user_input, pk.held_items)
        if emoji == "ability":
            if user_input == "none":
                self.mon.ability = "No Ability"
            else:
                self.mon.ability = caseless_match(user_input, pk.abilities)
        if emoji == "nature":
            self.mon.nature = self.parse_nature(user_input)
        if emoji == "evs":
            self.mon.ev = self.stats_from_str(user_input)
            self.mon.hpc = self.mon.hp
        if emoji == "ivs":
            self.mon.iv = self.stats_from_str(user_input)
            self.mon.hpc = self.mon.hp
        if emoji == "key":
            try:
                self.mon = pk.Mon.from_key(user_input)
            except IndexError:
                await self.emol.edit(mess, "Invalid key.")
                await asyncio.sleep(2)
        return await mess.delete()

    @property
    def fancy_move_list(self):
        return "\n".join(display_move(g, "inline") for g in self.mon.moves)

    async def edit_moves(self):
        mess = await self.emol.send(
            self.ctx, "What move would you like to add?",
            d="Name a move. To reorder existing moves, say `reorder`; to exit this menu, say `done`."
        )
        move_name = ""
        while True:
            if move_name:
                await self.emol.edit(
                    mess, "What move would you like to add?",
                    d="Name a move. To reorder existing moves, say `reorder`; to exit this menu, say `done`."
                )
            move_name = await self.wait_for("move")
            if move_name == "done":
                return await mess.delete()
            if move_name == "reorder":
                while True:
                    await self.emol.edit(
                        mess, "Which moves would you like to swap?",
                        d=f"{self.fancy_move_list}\n\nGive a pair of numbers separated by spaces, e.g. `1 4`. "
                          f"To exit this menu, say `done`."
                    )
                    swap = await self.wait_for("move_swap")
                    if swap == "done":
                        break
                    else:
                        swap = [int(g) for g in swap.split()]
                        temp = self.mon.moves[swap[0] - 1]
                        self.mon.moves[swap[0] - 1] = self.mon.moves[swap[1] - 1]
                        self.mon.moves[swap[1] - 1] = temp
            else:
                move = find_move(move_name).pack
                if len(self.mon.moves) < 4:
                    self.mon.add_move(move)
                    await self.emol.edit(mess, f"{self.mon.name} learned {move.name}!")
                    await asyncio.sleep(1)
                else:
                    await self.emol.edit(
                        mess, f"Which move should be replaced with {move.name}?",
                        d=f"{self.fancy_move_list}\n\nGive a number (1-4) or a name. To cancel, say `cancel`."
                    )
                    rep = await self.wait_for("move_placement")
                    if rep == "cancel":
                        continue
                    if can_int(rep):
                        rep = int(rep)
                    rep = self.mon.has_move(rep) - 1
                    await self.emol.edit(
                        mess, f"{self.mon.name} forgot {self.mon.moves[rep].name}, and learned {move.name} instead!")
                    self.mon.moves[rep] = move
                    await asyncio.sleep(1)

    @property
    def con(self):
        return self.emol.con(
            self.title, d=display_mon(self.mon, "builder"),
            footer=f"To change something, say the name of the value you'd like to edit.",
            thumbnail=pk.image(self.mon)
        )


class BuildATeamNavigator(Navigator):
    def __init__(self, ctx: commands.Context, team: pk.Team = pk.Team("Build-A-Team"), **kwargs):
        super().__init__(
            kwargs.get("emol", ball_emol()), [], 1, kwargs.get("title", "Build-A-Team"), prev="🔼", nxt="🔽",
            close_on_timeout=True
        )
        self.ctx = ctx
        self.team = team
        self.saved = False
        self.cancelled = False
        self.funcs["📝"] = self.edit
        self.funcs["⤴"] = self.set_lead
        self.funcs[zeph.emojis["plus"]] = self.add
        self.funcs[zeph.emojis["minus"]] = self.remove
        self.funcs["💾"] = self.save_and_exit
        self.funcs[zeph.emojis["no"]] = self.cancel

    @property
    def mon(self):
        if self.team.mons:
            return pk.Mon.unpack(self.team.mons[self.page - 1])
        return pk.Mon.null()

    async def get_mon(self, new: bool = False):
        bam = BuildAMonNavigator(
            self.ctx, starting_mon=find_mon("Bulbasaur") if new else self.mon, delete_on_close=True, emol=self.emol
        )
        try:
            await bam.run(self.ctx)
        except asyncio.TimeoutError:
            await self.emol.edit(self.message, "Build-A-Mon timed out.", d="Changes have been saved.")
            await asyncio.sleep(3)
        if bam.cancelled:
            return self.mon
        return bam.mon

    async def save_and_exit(self):
        self.saved = True
        await self.close()

    async def cancel(self):
        self.cancelled = True
        await self.close()

    async def edit(self):
        if self.team.mons:
            self.team.update_mon(await self.get_mon())

    async def add(self):
        if self.pgs < 6:
            self.team.add(await self.get_mon(new=True))

    def remove(self):
        if self.team.mons:
            self.team.remove(self.page - 1)
            if self.page > len(self.team.mons):
                self.page -= 1

    def set_lead(self):
        if self.page != 1:
            self.team.switch(0, self.page - 1, update_pos_values=True)
            self.page = 1

    async def close(self):
        self.closed_elsewhere = True
        return await self.remove_buttons()

    @property
    def pgs(self):
        return len(self.team.mons)

    @property
    def con(self):
        bs = "\\"
        return self.emol.con(
            self.title,
            d=none_list([
                f"{'**' + bs + '>' if n == self.page - 1 else '-'} "
                f"{display_mon(g, 'team_builder')}"
                f"{'**' if n == self.page - 1 else ''}"
                for n, g in enumerate(self.team.mons)
            ], "\n", "*you have no pokemon lol*") +
            f"\n\n📝 edit selection\n⤴ set lead\n"
            f"{zeph.emojis['plus']} add new mon\n{zeph.emojis['minus']} remove selection\n"
            f"💾 save and exit\n{zeph.emojis['no']} exit without saving"
        )


class PokemonInterpreter(Interpreter):
    redirects = {"t": "type", "e": "eff", "m": "move", "s": "test", "b": "build"}

    @staticmethod
    def move_embed(move: pk.Move):
        return type_emol(move.type).con(move.name, d=display_move(move, "full"))

    async def _help(self, *args):
        help_dict = {
            "type": "`z!pokemon type <type>` shows type effectiveness (offense and defense) for a given type.",
            "eff": "`z!pokemon eff` checks defensive type matchups against a type combination. Use the buttons "
                   f"({zeph.emojis['left1']}{zeph.emojis['right1']}{zeph.emojis['left2']}{zeph.emojis['right2']}) "
                   "to change types.\n`z!pokemon eff <mon...>` shows matchups against a given species or form.\n"
                   "`z!pokemon eff <type1> [type2]` shows matchups against a given type combination.",
            "move": "`z!pokemon move <move>` shows various information about a move - including type, power, "
                    "accuracy, etc.",
            "dex": "`z!pokemon dex [mon...]` opens the dex.\n"
                   "- If `mon` is a number, the dex opens on that number.\n"
                   "- If `mon` is a name, the dex opens on that mon. Form names may also be included, e.g. "
                   "`z!pk dex giratina-origin` or `z!pk dex alolan raichu`.\n"
                   "- If `mon` is not given, the dex opens on #0001 Bulbasaur.\n\n"
                   "`z!pokemon dex search [args...]` allows searching and filtering of the dex based on certain "
                   "search terms. For more info on these terms, see `z!pk dex search`."
        }
        desc_dict = {
            "type": "Shows type effectiveness for a type.",
            "eff": "Checks type matchups against a combination of types.",
            "move": "Shows info about a move.",
            "dex": "Browses the dex."
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
        a = pk.Team("Red Team")
        d = pk.Team("Blue Team")
        emol = ball_emol()
        a.add(find_mon("Leafeon", moves=["X-Scissor", "Leaf Blade", "Sunny Day", "Quick Attack"]))
        d.add(find_mon("Aron", moves=["Flash Cannon", "Earthquake", "Stone Edge", "Ice Punch"]))
        d.add(find_mon("Lairon", moves=["Flamethrower", "Thunderbolt", "Ice Beam", "Energy Ball"]))

        if len(args) > 0 and args[0].lower() == "custom":
            if len(args) > 1 and args[1].lower() == "blank":
                a.clear()
                d.clear()

            bat1 = BuildATeamNavigator(self.ctx, a.copy(), title="Red Team", emol=emol)
            try:
                await bat1.run(self.ctx)
            except asyncio.TimeoutError:
                return await emol.send(self.ctx, "Build-A-Team timed out.")
            if bat1.cancelled:
                return await emol.send(self.ctx, "Battle cancelled.")
            if bat1.saved:
                a = bat1.team

            bat2 = BuildATeamNavigator(self.ctx, d.copy(), title="Blue Team", emol=emol)
            try:
                await bat2.run(self.ctx)
            except asyncio.TimeoutError:
                return await emol.send(self.ctx, "Build-A-Team timed out.")
            if bat2.cancelled:
                return await emol.send(self.ctx, "Battle cancelled.")
            if bat2.saved:
                d = bat2.team

        b = Battle(field, self.ctx, a, d, emol=emol)
        return await b.run()

    async def _build(self, *args):
        admin_check(self.ctx)

        if len(args) > 0:
            if len(args) > 1 and args[0].lower() == "key":
                try:
                    mon = pk.Mon.from_key(args[1])
                except IndexError:
                    raise commands.CommandError("Invalid key.")
            else:
                mon = find_mon(" ".join(args))
        else:
            mon = find_mon("Bulbasaur")

        try:
            return await BuildAMonNavigator(self.ctx, starting_mon=mon).run(self.ctx)
        except asyncio.TimeoutError:
            return

    async def _move(self, *args):
        admin_check(self.ctx)

        move = find_move(" ".join(args))
        return await self.ctx.send(embed=self.move_embed(move))

    async def _team(self, *args):
        admin_check(self.ctx)

        team = pk.Team("Test Team")
        original_team = team.copy()
        bat = BuildATeamNavigator(self.ctx, team)
        await bat.run(self.ctx)
        return await bat.emol.send(
            self.ctx, "Team Keys",
            d=f"```asciidoc\n{bat.team.keys() if bat.saved else original_team.keys()}```"
        )

    async def _dex(self, *args):
        mon = " ".join(args) if args else "1"
        if mon.lower().split()[0] == "search":
            search_args = mon.lower().split()[1:]

            nav = DexSearchNavigator(mode=None if search_args else "settings")
            for arg in search_args:
                if not nav.is_valid_setting(arg):
                    raise commands.CommandError(f"Invalid search term `{arg}`.")
                else:
                    nav.apply_settings_change(*arg.split(":"))

            nav.reapply_search()
            return await nav.run(self.ctx)

        nav = DexNavigator(find_mon(mon), starting_mode=("help" if mon.lower() == "help" else None))
        return await nav.run(self.ctx)


@zeph.command(hidden=True, aliases=["lm"], usage="z!lm name type category PP power accuracy contact target **kwargs")
async def loadmove(
        ctx: commands.Context, name: str, typ: str, category: str, pp: int, pwr: Union[int, str], accuracy: int,
        contact: bool, target: str, *args
):
    admin_check(ctx)

    shortcuts = {
        "pt": "can_protect", "mc": "can_magic_coat", "sn": "can_snatch", "mm": "can_mirror_move",
        "rcr": "raised_crit_ratio"
    }

    def interpret_kwarg(s: str):
        if len(s.split("=")) == 1:
            return shortcuts.get(s, s), True
        elif s.startswith("z_effect=") or s.startswith("z="):
            return "z_effect", dict((interpret_kwarg("=".join(s.split("=")[1:])),))
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

    await ctx.send(f"```py\n{move.json}```", embed=PokemonInterpreter.move_embed(move))
    try:
        assert await confirm(f"{'Overwrite' if move.name in pk.moveDex else 'Save'} this move?", ctx, yes="save")
    except AssertionError:
        pass
    else:
        pk.moveDex[move.name] = move.copy()
        with open("pokemon/moves.json", "w") as f:
            json.dump({g: j.json for g, j in pk.moveDex.items()}, f, indent=4)
        return await succ.send(ctx, "Move saved.")


@zeph.command(
    hidden=True, name="loadmon", aliases=["lp", "pn"],
    usage="z!lp name"
)
async def loadmon_command(ctx: commands.Context, name: str, *args):
    admin_check(ctx)

    emol = ball_emol()

    if existing_mon := find_mon(name, fail_silently=True):
        if await confirm(
                "A mon with that name already exists.", ctx,
                desc_override=f"Add a new form to {existing_mon.species.name}?", allow_text_response=True
        ):
            species = pk.nat_dex[existing_mon.species.name]
        else:
            return
    else:
        species = pk.Species(name)
    force_exit = False
    while True:
        if args:
            user_input = " ".join(args)
            args = []
        else:
            try:
                await emol.send(
                    ctx, f"Input this form's stats:",
                    d="Format: `HP Atk Def SpA SpD Spe type1 type2 height weight [form name]`"
                )
                user_input = (await zeph.wait_for("message", check=general_pred(ctx), timeout=300)).content
            except asyncio.TimeoutError:
                return await emol.send(ctx, "Request timed out.")
        if user_input.lower() == "cancel":
            return await emol.send(ctx, "Dex addition cancelled.")
        form = pk.Form.from_str(user_input)
        if form.name == "done":
            force_exit = True
            form.name = ""
        species.add_form(form)
        mon = pk.Mon(species, form=form.name)
        await emol.send(ctx, f"#{existing_mon.dex_no} {name}", d=display_mon(mon, "dex"), thumbnail=pk.image(mon))
        if await confirm("Does this look right?", ctx, desc_override="", allow_text_response=True):
            if force_exit or not (await confirm("Add another form?", ctx, desc_override="", allow_text_response=True)):
                if existing_mon:
                    pk.rewrite_mons()
                    return await succ.send(ctx, f"{species.name} updated.")
                else:
                    pk.add_new_mon(species)
                    return await succ.send(ctx, f"{species.name} added to dex.")
            else:
                continue
        else:
            species.remove_form(form)
