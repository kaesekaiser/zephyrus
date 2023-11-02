from pkmn_battle import *
from copy import deepcopy as copy


def find_mon(s: Union[str, int, None], **kwargs) -> pk.BareMiniMon | pk.Mon:
    """Use **kwargs to pass additional arguments to the Mon.__init__() statement."""
    if kwargs.get("use_bare"):
        return_class = pk.BareMiniMon
    else:
        return_class = pk.Mon

    if isinstance(s, pk.BareMiniMon):
        return s

    if can_int(s) or isinstance(s, int):
        if int(s) < 1 or int(s) > len(pk.nat_dex):
            raise commands.CommandError(f"Use a dex number between 1 and {len(pk.nat_dex)}.")
        return return_class(list(pk.nat_dex.keys())[int(s) - 1], **kwargs)
    if s is None or s.lower() == "null":
        return return_class.null()
    if ret := pk.species_and_forms.get(pk.fix(s)):
        return return_class(ret.species.name, form=ret.form.name, **kwargs)
    for mon in pk.nat_dex:
        if set(pk.fix(mon, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            ret = mon, pk.fix("-".join(re.split(pk.fix(mon), pk.fix(s))))
            break
    else:
        if pk.fix(s) == "nidoran":
            ret = "Nidoran-F", ""
        else:
            if kwargs.get("fail_silently") or kwargs.get("return_on_fail"):
                return kwargs.get("return_on_fail", return_class.null())
            else:
                guess = sorted(list(pk.fixed_dex), key=lambda c: wr.levenshtein(c, pk.fix(s)))
                raise commands.CommandError(f"`{s}` not found. Did you mean {pk.fixed_dex[guess[0]]}?")
    for form in pk.nat_dex[ret[0]].forms:
        if set(pk.fix(form, "_").split("_")) <= set(pk.fix(s, "_").split("_")):
            return return_class(ret[0], form=form, **kwargs)
    else:
        return return_class(ret[0], **kwargs)


def find_move(s: str) -> pk.Move:
    try:
        return [j.copy() for g, j in pk.move_dex.items() if pk.fix(g) == pk.fix(s)][0]
    except IndexError:
        lis = {pk.fix(g): g for g in pk.move_dex}
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
    def __init__(self, start: pk.BareMiniMon, **kwargs):
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
        self.funcs["!jump"] = self.jump
        self.funcs["!wait"] = self.do_nothing
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
            self.mon = find_mon(self.jumpDest, use_bare=True)
        self.jumpDest = None
        self.mode = None
        self.last_guess = None

    @property
    def con(self):
        if not self.mode:
            return self.emol.con(
                f"#{str(self.mon.dex_no).rjust(4, '0')} {self.mon.full_name}",
                thumb=self.mon.dex_image, d=display_mon(self.mon, "dex")
            )
        elif self.mode == "forms":
            return self.emol.con(
                f"{self.mon.species.name} Forms",
                d=scroll_list(self.mon.form_names, self.mon.form_names.index(self.mon.full_name)),
                thumb=self.mon.dex_image
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
                self.mon = find_mon(self.mon.dex_no + direction, use_bare=True)
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
                        self.jumpDest = find_mon(mess.content, use_bare=True)
                    except commands.CommandError as e:
                        self.last_guess = str(e)
                        return "!wait"
                    return "!jump"
                return "!jump"
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
        "atk": lambda m: m.form.atk,
        "def": lambda m: m.form.dfn,
        "spa": lambda m: m.form.spa,
        "spd": lambda m: m.form.spd,
        "spe": lambda m: m.form.spe
    }

    def __init__(self, **kwargs):
        super().__init__(ball_emol(), [], 8, "",  # only the `per` param matters; the table gets rewritten
                         prev=zeph.emojis["dex_prev"], nxt=zeph.emojis["dex_next"])
        self.mode = kwargs.get("mode", None)
        self.dex = copy(pk.nat_dex)
        self.funcs["⏯"] = self.jump_to_midpoint
        self.funcs[zeph.emojis["settings"]] = self.settings_mode
        self.funcs[zeph.emojis["help"]] = self.help_mode
        self.funcs[zeph.emojis["no"]] = self.close
        self.funcs["!wait"] = self.do_nothing

        self.gen = None
        self.types = ()
        self.name = None
        self.sort = "number"
        self.forms = False
        self.has = None
        self.learns = []
        self.ability = None

        self.reapply_search()

    @property
    def sort_name(self):
        return {
            "number": "National Dex no.",
            "name": "Alphabetical",
            "height": "Height",
            "weight": "Weight",
            "stats": "Total base stats",
            "hp": "Base HP",
            "atk": "Base Attack",
            "def": "Base Defense",
            "spa": "Base Sp. Attack",
            "spd": "Base Sp. Defense",
            "spe": "Base Speed"
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
        if self.learns:
            funcs.append(lambda m: all(m.can_learn(g, "SV") for g in self.learns))
        if self.ability:
            funcs.append(lambda m: self.ability in m.legal_abilities)

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
        elif self.sort == "atk":
            return f"{mon_name} (**{mon.form.atk}** Atk)"
        elif self.sort == "def":
            return f"{mon_name} (**{mon.form.dfn}** Def)"
        elif self.sort == "spa":
            return f"{mon_name} (**{mon.form.spa}** SpA)"
        elif self.sort == "spd":
            return f"{mon_name} (**{mon.form.spd}** SpD)"
        elif self.sort == "spe":
            return f"{mon_name} (**{mon.form.spe}** Spe)"

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
        if value == "any" and option not in ["forms", "sort", "learns"]:
            return True

        value = str(value.replace("_", " "))

        if option == "gen":
            return can_int(value) and int(value) in range(1, 10)  # ALLOW RANGE VALUES ?
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
        elif option == "learns":
            return all(pk.fix(g.strip(", ")) in pk.fixed_legal_moves for g in re.split(r",\s*?(?=[a-z])", value)) or \
                value == "none"
        elif option == "ability":
            return pk.fix(value) in [pk.fix(g) for g in pk.abilities]
        else:
            return False

    def apply_settings_change(self, option: str, value: str):
        """Assumes that the string <option>:<value> passes is_valid_setting()."""

        value = str(value.replace("_", " "))

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
        if option == "learns":
            if value == "none":
                self.learns = []
            else:  # returns a list of correctly-formatted move names
                self.learns = [pk.fixed_legal_moves[pk.fix(g.strip(", "))] for g in re.split(r",\s*?(?=[a-z])", value)]
        if option == "ability":
            self.ability = None if value == "any" else [g for g in pk.abilities if pk.fix(g) == pk.fix(value)][0]

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
                    "Has Mega/Alolan? (`has`)": ain(self.has), "Include alt forms? (`forms`)": yesno(self.forms),
                    "Learns the moves... (`learns`)": none_list(self.learns), "Ability (`ability`)": ain(self.ability)},
                footer=f"Total Pokémon meeting criteria: {len(self.table)}"
            )

        if self.mode == "help":
            return self.emol.con(
                "Search Criteria",
                d="`gen:<n>` - filters by generation. `<n>` must be between 1 and 9, e.g. `gen:4`. `gen:any` resets "
                  "the filter.\n\n"
                  "`type:<types>` (or `types:<types>`) - filters by type. `<types>` can be either one type, or two "
                  "types separated by a comma or slash, e.g. `type:fire,flying`. `type:any` resets the filter.\n\n"
                  "`name:<letter>` - filters by first letter of the mon's name. `<letter>` must be one letter, "
                  "e.g. `name:A`. `name:any` resets the filter.\n\n"
                  "`sort:<method>` - sorts the results in a certain order. `<method>` can be `name`, to sort A→Z; "
                  "`number`, to sort by National Dex number; `height`, to sort by height; `weight`, to sort by "
                  "weight; `stats`, to sort by total base stats; or any of `hp`, `atk`, `def`, `spa`, "
                  "`spd`, or `spe`, to sort by the respective stat. Default is `sort:number`.\n\n"
                  "`has:<form>` - filters by species which have a certain form. `<form>` can be `mega` or `alolan`. "
                  "`has:any` resets the filter.\n\n"
                  "`forms:yes` / `forms:no` - includes or excludes alternate forms in the filter. This includes Mega "
                  "Evolutions, Alolan forms, Primal forms, Rotom forms, etc., but does *not* include forms which are "
                  "solely aesthetic (like those of Vivillon or Gastrodon) or only change the Pokémon's type (like "
                  "Arceus and Silvally). Default is `forms:no`.\n\n"
                  "`learns:<move(s)>` - filters by mons which can learn a given move or moves. Separate multiple moves "
                  "using commas, e.g. `learns:earthquake, swords dance`. `learns:none` resets the filter.\n\n"
                  "`ability:<ability>` - filters by mons which have a given ability, including as a Hidden Ability. "
                  "`ability:any` resets the filter."
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

    def jump_to_midpoint(self):
        self.page = ceil(self.pgs / 2)

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
                return "!wait"
            elif isinstance(mess, discord.Reaction):
                return mess.emoji

        return (await zeph.wait_for(
            'reaction_add', timeout=300, check=lambda r, u: r.emoji in self.legal and
            r.message.id == self.message.id and u == ctx.author
        ))[0].emoji


@zeph.command(
    name="pokedex", hidden=True,
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

    def __init__(self, type1: str, type2: str = None, initial_mon: pk.Mon = find_mon("NULL")):
        super().__init__(ball_emol(), [], 1, "", prev="", nxt="")
        self.type1 = type1
        self.type2 = type2
        self.funcs[zeph.emojis["left1"]] = self.type1bac
        self.funcs[zeph.emojis["right1"]] = self.type1for
        self.funcs[zeph.emojis["left2"]] = self.type2bac
        self.funcs[zeph.emojis["right2"]] = self.type2for
        self.initial_mon = initial_mon

    @property
    def eff_dict(self):
        def eff(atk: str, dfn1: str, dfn2: str = None):
            return pk.effectiveness[atk].get(dfn1, 1) * pk.effectiveness[atk].get(dfn2, 1)

        ret = {
            "4x": ", ".join([f"{zeph.emojis[g]} {g}" for g in pk.types if eff(g, self.type1, self.type2) == 4]),
            "2x": ", ".join([f"{zeph.emojis[g]} {g}" for g in pk.types if eff(g, self.type1, self.type2) == 2]),
            "1x": ", ".join([f"{zeph.emojis[g]} {g}" for g in pk.types if eff(g, self.type1, self.type2) == 1]),
            "½x": ", ".join([f"{zeph.emojis[g]} {g}" for g in pk.types if eff(g, self.type1, self.type2) == 0.5]),
            "¼x": ", ".join([f"{zeph.emojis[g]} {g}" for g in pk.types if eff(g, self.type1, self.type2) == 0.25]),
            "0x": ", ".join([f"{zeph.emojis[g]} {g}" for g in pk.types if eff(g, self.type1, self.type2) == 0])
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
        if (self.type1 or self.type2) and (self.initial_mon.types_with_none == [str(self.type1), str(self.type2)]):
            return self.initial_mon.dex_image
        try:
            return find_mon(choice(pk.exemplary_mons[frozenset([self.type1, self.type2])])).dex_image
        except KeyError:
            return None

    @property
    def con(self):
        second_type = f"{zeph.emojis[self.type2.title()]} `{self.type2}`" if self.type2 else "`None`"
        return self.emol.con(
            "Type Effectiveness", thumb=self.image,
            d=f"{zeph.emojis['left1']} [{zeph.emojis[self.type1.title()]} `{self.type1}`] {zeph.emojis['right1']} / "
              f"{zeph.emojis['left2']} [{second_type}] {zeph.emojis['right2']}\n\n" +
              "\n\n".join([f"**{g}:** {j}" for g, j in self.eff_dict.items()])
        )


def display_raid(raid: pk.TeraRaid, mode: str):
    mon = find_mon(raid.species, use_bare=True)

    if mode == "default":
        ret = []
        if raid.game != "Both":
            ret.append(f"Only available in **{raid.game}**.")
        if raid.type not in ["Random", "Default"]:
            ret.append(f"Always **{raid.type}-type**.")
        if ret:
            ret.append("")

        if raid.battle_level == raid.catch_level:
            ret.append(f"**Level:** {raid.battle_level}")
        else:
            ret.append(f"**Battled** at Lv. {raid.battle_level}; **caught** at Lv. {raid.catch_level}.")

        if raid.ability == "Hidden Ability":
            ret.append(f"**Ability:** {mon.hidden_ability} (Hidden Ability)")
        elif raid.ability == "Standard":
            ret.append(f"**Ability:** {mon.regular_abilities[0]}")
        else:
            if len(mon.legal_abilities) == 1:
                ret.append(f"**Ability:** {mon.legal_abilities[0]}")
            else:
                ret.append(f"**Possible Abilities:** {grammatical_join(mon.legal_abilities, 'or')}")

        ret.append(f"**Moves:** {', '.join(raid.moves)}")
        if raid.additional_moves:
            ret.append(f"**Additional Moves:** {', '.join(raid.additional_moves)}")
        else:
            ret.append("No additional moves.")

        return "\n".join(ret)

    elif mode == "drops":
        return "\n".join(str(g) for g in raid.drops)

    elif mode == "dex":
        return display_mon(mon, "dex")


class RaidNavigator(Navigator):
    def __init__(self, raid: pk.TeraRaid, **kwargs):
        super().__init__(
            kwargs.get("emol", ball_emol("master")), [], 1, raid.name, prev="", nxt=""
        )
        self.raid = raid
        self.mon = find_mon(raid.species, use_bare=True)
        self.mode = "default"
        self.funcs[zeph.emojis["moves"]] = partial(self.change_mode, "default")
        self.funcs[zeph.emojis["rare_candy"]] = partial(self.change_mode, "drops")
        self.funcs[zeph.emojis["poke_ball"]] = partial(self.change_mode, "dex")

    def change_mode(self, mode: str):
        self.mode = mode

    async def after_timeout(self):
        await self.remove_buttons()

    @property
    def con(self):
        return self.emol.con(
            f"#{str(self.mon.dex_no).rjust(4, '0')} {self.mon.full_name}" if self.mode == "dex" else
            f"{self.raid.name} Drops" if self.mode == "drops" else self.raid.name,
            d=display_raid(self.raid, self.mode), thumb=self.mon.dex_image
        )


class LearnsetNavigator(Navigator):
    mode_titles = {
        "level": "Level-up moves",
        "evo": "Evolution moves",
        "prior": "Moves from prior evolutions",
        "reminder": "Move Reminder moves",
        "egg": "Egg moves",
        "tm": "Compatible TMs"
    }

    def __init__(self, mon: pk.Mon, gen: str = "SV", **kwargs):
        super().__init__(
            kwargs.get("emol", ball_emol()), [], 8, "", prev=zeph.emojis["dex_prev"], nxt=zeph.emojis["dex_next"]
        )
        self.mon = mon
        self.gen = gen
        self.mode = "level"
        if self.learnset:
            self.funcs[zeph.emojis["rare_candy"]] = partial(self.change_mode, "level")
            if self.learnset.evo:
                self.funcs[zeph.emojis["thunder_stone"]] = partial(self.change_mode, "evo")
            if self.learnset.prior:
                self.funcs[zeph.emojis["eviolite"]] = partial(self.change_mode, "prior")
            if self.learnset.reminder:
                self.funcs[zeph.emojis["heart_scale"]] = partial(self.change_mode, "reminder")
            if self.learnset.egg:
                self.funcs[zeph.emojis["pokemon_egg"]] = partial(self.change_mode, "egg")
            if self.learnset.tm:
                self.funcs[zeph.emojis["technical_machine"]] = partial(self.change_mode, "tm")
        else:
            self.prev = ""
            self.next = ""

    def change_mode(self, mode: str):
        if mode != self.mode:
            self.page = 1
        self.mode = mode

    @property
    def learnset(self):
        return self.mon.get_learnset(self.gen)

    @property
    def selected_table(self):
        return self.learnset.__getattribute__(self.mode)

    @property
    def pgs(self):
        return ceil(len(self.selected_table) / self.per)

    @property
    def formatted_page(self):
        if self.mode == "level":
            return "\n".join(f"Lv. {g}: {j}" for g, j in page_list(self.selected_table, self.per, self.page))
        elif self.mode == "tm":
            return "\n".join(f"{k}: {v}" for k, v in page_list(list(self.selected_table.items()), self.per, self.page))
        else:
            return "\n".join(f"\\- {g}" for g in page_list(self.selected_table, self.per, self.page))

    @property
    def con(self):
        if self.learnset:
            return self.emol.con(
                f"{self.mon.name} ({self.gen}): {self.mode_titles[self.mode]}",
                d=self.formatted_page,
                footer=f"{pk.full_game_names[self.gen]} / page {self.page} of {self.pgs}"
            )
        else:
            self.closed_elsewhere = True  # just end the protocol
            return self.emol.con(
                f"{self.mon.name} ({self.gen})",
                d=f"{self.mon.name} is not available in {pk.full_game_names[self.gen]}."
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
    return Emol(zeph.emojis[typ.title()], hexcol(pk.type_colors[typ]))


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
                return general_pred(self.ctx)(mr) and mr.content.lower() in self.editable_properties
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
            "message", check=lambda m: general_pred(self.ctx)(m) and bool(necessary_check(m.content)), timeout=300
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
            thumbnail=self.mon.dex_image
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


class CatchRateNavigator(Navigator):
    editable_parameters = [
        "species", "level", "ball", "status", "surfing", "dark", "my_level", "my_species", "gender", "my_gender",
        "fishing", "turn", "repeat", "dex", "badges", "hp"
    ]

    def __init__(self, **kwargs):
        super().__init__(ball_emol(), [], 1, "", prev="", nxt="", close_on_timeout=True)
        self.calculator = pk.CatchRate(kwargs.get("ball", "poke"), kwargs.get("mon", find_mon(1)))

    @property
    def wild_mon(self):
        return self.calculator.mon

    @property
    def player_mon(self):
        return self.calculator.player_mon

    def advance_page(self, direction: int):
        self.calculator.ball_type = pk.poke_ball_types[
            (pk.poke_ball_types.index(self.calculator.ball_type) + direction) % len(pk.poke_ball_types)
        ]

    async def get_emoji(self, ctx: commands.Context):
        def pred(mr: MR, u: User = ctx.author):
            if isinstance(mr, discord.Message):
                return general_pred(ctx)(mr) and mr.content.lower() in self.editable_parameters
            elif isinstance(mr, discord.Reaction):
                return mr.emoji in self.legal and mr.message.id == self.message.id and u == ctx.author

        user_input = (await zeph.wait_for("reaction_or_message", check=pred, timeout=300))[0]
        if isinstance(user_input, discord.Message):
            await user_input.delete()
            return user_input.content.lower()
        elif isinstance(user_input, discord.Reaction):
            return user_input.emoji

    async def close(self):
        self.closed_elsewhere = True
        return await self.message.edit(embed=self.con)

    async def wait_for(self, message_type: str, ctx: commands.Context) -> str:
        def is_yesno(s: str):
            return s.lower() in ["y", "yes", "n", "no"]

        additional_checks = {
            "species": lambda c: find_mon(c, fail_silently=True),
            "level": lambda c: can_int(c) and (1 <= int(c) <= 100),
            "ball": lambda c: caseless_match(c.split()[0], pk.poke_ball_types),
            "status": lambda c: caseless_match(c, ["None", *pk.status_conditions]),
            "surfing": is_yesno,
            "dark": is_yesno,
            "my_level": lambda c: can_int(c) and (1 <= int(c) <= 100),
            "my_species": lambda c: find_mon(c, fail_silently=True),
            "gender": lambda c: (c.lower() in ["male", "female"]) and self.wild_mon.default_gender == "random",
            "my_gender": lambda c: (c.lower() in ["male", "female"]) and self.player_mon.default_gender == "random",
            "fishing": is_yesno,
            "turn": lambda c: can_int(c) and int(c) > 0,
            "repeat": is_yesno,
            "dex": lambda c: can_int(c) and int(c) >= 0,
            "badges": is_yesno,
            "hp": lambda c: can_int(c.strip("%")) and (1 <= int(c.strip("%")) <= 100),
        }
        necessary_check = additional_checks.get(message_type, lambda m: True)
        mess = await zeph.wait_for(
            "message", check=lambda m: general_pred(ctx)(m) and bool(necessary_check(m.content)), timeout=300
        )
        await mess.delete()
        return mess.content.lower()

    async def run_nonstandard_emoji(self, emoji: Union[discord.Emoji, str], ctx: commands.Context):
        if emoji in self.legal:
            return

        if emoji == "gender" and self.wild_mon.default_gender != "random":
            mess = await self.emol.send(ctx, f"{self.wild_mon.species.name} is {self.wild_mon.default_gender} only.")
            await asyncio.sleep(2)
            return await mess.delete()
        if emoji == "my_gender" and self.player_mon.default_gender != "random":
            mess = await self.emol.send(
                ctx, f"{self.player_mon.species.name} is {self.player_mon.default_gender} only."
            )
            await asyncio.sleep(2)
            return await mess.delete()

        messages = {
            "species": "What species is the wild mon?",
            "level": "What level is the wild mon?",
            "ball": "What type of Pok\u00e9 Ball are you using?",
            "status": "What's the wild mon's status condition, if any?",
            "surfing": "Are you currently surfing?",
            "dark": "Are you currently in a cave, or is it nighttime?",
            "my_level": "What level is your mon?",
            "my_species": "What species is your mon?",
            "gender": "What gender is the wild mon?",
            "my_gender": "What gender is your mon?",
            "fishing": "Are you currently fishing?",
            "turn": "What turn is it?",
            "repeat": "Have you caught this species before?",
            "dex": "How many species are registered as caught in your dex?",
            "badges": "Do you have all eight Gym Badges?",
            "hp": "What's the wild mon's current HP percentage?"
        }
        mess = await ball_emol(self.calculator.ball_type).send(
            ctx, messages[emoji].split("\n")[0], d="\n".join(messages[emoji].split("\n")[1:]),
        )
        user_input = await self.wait_for(emoji, ctx)
        if emoji == "species":
            mon = find_mon(user_input)
            pack = self.wild_mon.pack
            pack["spc"] = mon.species
            pack["form"] = mon.form.name
            self.calculator.mon = pk.Mon.unpack(pack)
        if emoji == "level":
            self.calculator.mon.level = int(user_input)
        if emoji == "ball":
            self.calculator.ball_type = user_input.split()[0]
        if emoji == "status":
            if user_input == "none":
                self.calculator.mon.status_condition = None
            self.calculator.mon.status_condition = caseless_match(user_input, pk.status_conditions)
        if emoji == "surfing":
            self.calculator.is_surfing = user_input in ["y", "yes"]
        if emoji == "dark":
            self.calculator.is_night = user_input in ["y", "yes"]
        if emoji == "my_level":
            self.calculator.player_mon.level = int(user_input)
        if emoji == "my_species":
            mon = find_mon(user_input)
            pack = self.wild_mon.pack
            pack["spc"] = mon.species
            pack["form"] = mon.form
            self.calculator.player_mon = pk.Mon.unpack(pack)
        if emoji == "gender":
            self.calculator.mon.gender = user_input
        if emoji == "my_gender":
            self.calculator.player_mon.gender = user_input
        if emoji == "fishing":
            self.calculator.is_fishing = user_input in ["y", "yes"]
        if emoji == "turn":
            self.calculator.turn = int(user_input)
        if emoji == "repeat":
            self.calculator.caught_previously = user_input in ["y", "yes"]
        if emoji == "dex":
            self.calculator.dex_caught = int(user_input)
        if emoji == "badges":
            self.calculator.has_all_badges = user_input in ["y", "yes"]
        if emoji == "hp":
            self.calculator.hp_percentage = int(user_input.strip("%"))

        return await mess.delete()

    @property
    def con(self):
        descriptions = {
            "beast": "5x catch rate if used on an Ultra Beast. 0.1x otherwise.",
            "cherish": "Flat 1x catch rate.",
            "dive": f"3.5x catch rate if surfing or fishing. 1x otherwise.\n\n"
                    f"Are you surfing or fishing (`surfing`)?: **{yesno(self.calculator.is_surfing)}**",
            "dream": "4x catch rate if used on a sleeping mon. 1x otherwise.",
            "dusk": f"3x catch rate if used in a cave or at night. 1x otherwise.\n\n"
                    f"Are you in a cave, or is it nighttime (`dark`)?: **{yesno(self.calculator.is_night)}**",
            "fast": f"4x catch rate if used on a mon with >=100 base Speed. 1x otherwise.\n\n"
                    f"This mon **does{'' if self.calculator.mon.form.spe >= 100 else ' not'}** have a base Speed "
                    f"greater than 100.",
            "friend": "Flat 1x catch rate.",
            "great": "Flat 1.5x catch rate.",
            "heal": "Flat 1x catch rate.",
            "heavy": "-20 added to mon's catch rate if its weight is less than 100 kg.\n"
                     "0 added if its weight is greater than or equal to 100 kg, but less than 200 kg.\n"
                     "20 added if its weight is greater than or equal to 200 kg, but less than 300 kg.\n"
                     "30 added if its weight is greater than or equal to 300 kg.\n"
                     f"This mon has a weight of **{self.calculator.mon.weight} kg**.",
            "level": f"8x catch rate if your mon's level is at least four times higher than the wild mon's.\n"
                     f"4x if your mon's level is at least double, but not quadruple, the wild mon's.\n"
                     f"2x if your mon's level is higher than, but not twice as high as, the wild mon's.\n"
                     f"1x if your mon's level is less than or equal to the wild mon's.",
            "love": f"8x if used on a mon of the same species and opposite gender of your mon.\n\n"
                    f"What's the wild mon's gender (`gender`)?: **{self.calculator.mon.gender}**\n"
                    f"What's your mon's species (`my_species`)?: **{self.calculator.mon.species.name}**\n"
                    f"What's your mon's gender (`my_gender`)?: **{self.calculator.player_mon.gender}**",
            "lure": f"4x catch rate when fishing. 1x otherwise.\n\n"
                    f"Are you fishing (`fishing`)?: **{yesno(self.calculator.is_fishing)}**",
            "luxury": "Flat 1x catch rate.",
            "master": "Never fails.",
            "moon": "4x catch rate if used against a mon that evolves by Moon Stone (i.e. any member of the Nidoran, "
                    "Clefairy, Jigglypuff, Skitty, or Munna families). 1x otherwise.",
            "nest": "Between 1x and 4x catch rate if the mon's level is below 30, with lower levels giving higher "
                    "catch rates. 1x otherwise.",
            "net": "3.5x if the mon is Bug- or Water-type. 1x otherwise.",
            "park": "Never fails. Unavailable in Scarlet/Violet.",
            "poke": "Flat 1x catch rate.",
            "premier": "Flat 1x catch rate.",
            "quick": f"5x catch rate if used on the first turn. 1x otherwise.\n\n"
                     f"What's the current turn (`turn`)?: **{self.calculator.turn}**",
            "repeat": f"3.5x catch rate if used on a previously-caught species. 1x otherwise.\n\n"
                      f"Have you caught this species before (`repeat`)?: **"
                      f"{yesno(self.calculator.caught_previously)}**",
            "safari": "Flat 1x catch rate.",
            "sport": "Flat 1x catch rate.",
            "timer": f"Catch rate increases by 0.3x every turn, starting at 1x on turn 1, and going up to a maximum of "
                     f"4x from turn 11 onward.\n\n"
                     f"What's the current turn (`turn`)?: **{self.calculator.turn}**",
            "ultra": "Flat 2x catch rate."
        }
        return ball_emol(self.calculator.ball_type).con(
            "S/V Catch Rate Calculator",
            d=f"**Species**: {self.wild_mon.species.name} (catch rate: {self.wild_mon.species.catch_rate}) "
              f"/ **Level**: {self.wild_mon.level}\n"
              f"**HP**: {self.calculator.hp_percentage}% / **Status**: {self.wild_mon.status_condition}\n\n"
              f"**Ball**: {self.calculator.ball_type.title()} Ball\n"
              f"{descriptions[self.calculator.ball_type]}\n\n"
              f"What's your mon's level (`my_level`)?: **{self.player_mon.level}**\n"
              f"Do you have all eight Gym Badges (`badges`)?: **{yesno(self.calculator.has_all_badges)}**\n"
              f"How many species are registered as caught in your dex (`dex`)?: **{self.calculator.dex_caught}**\n\n"
              f"Capture chance: **{round(100 * self.calculator.capture_chance, 2)}%** per ball.\n"
              f"Chance to capture within 5 throws: {round(100 * self.calculator.chance_after_throws(5), 2)}%\n"
              f"Throws needed for 95% capture chance: {self.calculator.throws_for_95_percent_capture}",
            thumb=self.wild_mon.dex_image,
            footer=None if self.closed_elsewhere else "To change any value, say its name in chat."
        )


class PokemonInterpreter(Interpreter):
    redirects = {
        "t": "type", "e": "eff", "m": "move", "s": "test", "b": "build", "c": "catch", "h": "help", "x": "dex",
        "r": "raid", "cf": "compare", "l": "learnset"
    }

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
            # "move": "`z!pokemon move <move>` shows various information about a move - including type, power, "
            #         "accuracy, etc.",
            "dex": "`z!pokemon dex [mon...]` opens the dex.\n"
                   "- If `mon` is a number, the dex opens on that number.\n"
                   "- If `mon` is a name, the dex opens on that mon. Form names may also be included, e.g. "
                   "`z!pk dex giratina-origin` or `z!pk dex alolan raichu`.\n"
                   "- If `mon` is not given, the dex opens on #0001 Bulbasaur.\n\n"
                   "`z!pokemon dex search [args...]` allows searching and filtering of the dex based on certain "
                   "search terms. For more info on these terms, see `z!pk dex search`.",
            "catch": "`z!pokemon catch [ball] [species...]` opens the Scarlet/Violet catch rate calculator.\n"
                     "- If `ball` is given, it must be a valid type of Pok\u00e9 Ball (e.g. Ultra, Quick, Dusk), and "
                     "it must be the first argument.\n"
                     "- If `species` is given, it must be a valid species of Pok\u00e9mon.\n"
                     "- Both arguments are optional.\n\n"
                     "Note that this calculator is only guaranteed to be accurate for Scarlet and Violet. Some catch "
                     "rates (e.g. box legendaries) change between generations, and the formula itself has also "
                     "changed several times.",
            "raid": "`z!pokemon raid <# stars> <species...>` shows relevant info for a Tera Raid Battle. Note that "
                    "only 5- and 6-star raids are currently included, and event raids are not included.\n"
                    f"\\- {zeph.emojis['moves']} lists the possible abilities and moves for the raid mon.\n"
                    f"\\- {zeph.emojis['rare_candy']} lists the raid item drops.\n"
                    f"\\- {zeph.emojis['poke_ball']} opens the dex entry for the raid mon.\n\n"
                    "`z!pk 5` may be used as a shortcut for `z!pokemon raid 5`, e.g. `z!pk 5 grimmsnarl`. The same "
                    "goes for `z!pk 6`.",
            "compare": "`z!pokemon compare <mon1> <mon2>` compares the base stats of two different species. If you "
                       "want to specify a particular form, use the hyphenated version of the name (e.g. `Raichu-Alola` "
                       "for Alolan Raichu). If you want to input a species with a space in the name, such as Mr. Mime, "
                       "surround the name in \"double quotes\", or replace the spaces with hyphens.",
            "learnset": "`z!pokemon learnset <species...>` shows the Scarlet/Violet learnset for a given species.\n"
                        f"\\- {zeph.emojis['rare_candy']} lists its level-up moves.\n"
                        f"\\- {zeph.emojis['thunder_stone']} lists its evolution moves.\n"
                        f"\\- {zeph.emojis['eviolite']} lists moves it only learns as a previous evolution.\n"
                        f"\\- {zeph.emojis['heart_scale']} lists its Move Reminder moves.\n"
                        f"\\- {zeph.emojis['pokemon_egg']} lists its egg moves.\n"
                        f"\\- {zeph.emojis['technical_machine']} lists its compatible TMs."
        }
        desc_dict = {
            "type": "Shows type effectiveness for a type.",
            "eff": "Checks type matchups against a combination of types.",
            # "move": "Shows info about a move.",
            "dex": "Browses the dex.",
            "catch": "Opens the Scarlet/Violet catch rate calculator.",
            "raid": "Displays info about a given Tera Raid Battle.",
            "compare": "Compares the base stats of two species.",
            "learnset": "Shows the moves learned by a given species."
        }
        shortcuts = {j: g for g, j in self.redirects.items() if len(g) <= 2}

        def get_command(s: str):
            return f"**`{s}`** (or **`{shortcuts[s]}`**)" if shortcuts.get(s) else f"**`{s}`**"

        if len(args) == 0 or (args[0].lower() not in help_dict and args[0].lower() not in self.redirects):
            return await ball_emol().send(
                self.ctx, "z!pokemon help",
                d="Available functions:\n\n" + "\n".join(f"{get_command(g)} - {j}" for g, j in desc_dict.items()) +
                  "\n\nFor information on how to use these, use `z!pokemon help <function>`."
            )

        ret = self.redirects.get(args[0].lower(), args[0].lower())

        return await ball_emol().send(self.ctx, f"z!pokemon {ret}", d=help_dict[ret])

    async def _type(self, *args):
        if not args:
            raise commands.CommandError("Format: `z!pokemon type <type>`")
        typ = str(args[0]).title()
        if typ.title() not in pk.types:
            raise commands.CommandError(f"{typ} isn't a type.")

        eff = {
            "2x damage against": [f"{zeph.emojis[g]} {g}" for g in pk.types if pk.effectiveness[typ][g] > 1],
            "½x damage against": [f"{zeph.emojis[g]} {g}" for g in pk.types if 0 < pk.effectiveness[typ][g] < 1],
            "0x damage against": [f"{zeph.emojis[g]} {g}" for g in pk.types if not pk.effectiveness[typ][g]],
            "0x damage from": [f"{zeph.emojis[g]} {g}" for g in pk.types if not pk.effectiveness[g][typ]],
            "½x damage from": [f"{zeph.emojis[g]} {g}" for g in pk.types if 0 < pk.effectiveness[g][typ] < 1],
            "2x damage from": [f"{zeph.emojis[g]} {g}" for g in pk.types if pk.effectiveness[g][typ] > 1]
        }
        return await type_emol(typ).send(
            self.ctx, f"{typ}-type", fs={g: "\n".join(j) for g, j in eff.items() if j}, same_line=True
        )

    async def _eff(self, *args):
        args = re.split(r"\s|/", " ".join(args))  # to account for inputs like "grass/steel"
        mon = find_mon(" ".join(args), fail_silently=True, use_bare=True)
        if mon:
            types = mon.types
        else:
            if set(g.title() for g in args).issubset(set(EffNavigator.types)) \
                    and 0 < len(args) < 3:
                types = [g.title() for g in args]
            else:
                types = ["Normal"]

        return await EffNavigator(*types, initial_mon=mon).run(self.ctx)

    async def _test(self, *args):
        admin_check(self.ctx)

        field = pk.Field()
        a = pk.Team("Red Team")
        d = pk.Team("Blue Team")
        emol = ball_emol()

        a.add(find_mon(
            "Leafeon",
            moves=["Leaf Blade", "X-Scissor", "Sunny Day", "Quick Attack"],
            ability="Chlorophyll"
        ))
        a.add(find_mon(
            "Glaceon",
            moves=["Ice Beam", "Shadow Ball", "Hail", "Calm Mind"],
            ability="Snow Cloak",
            tera=pk.ghost
        ))
        a.add(find_mon(
            "Flareon",
            moves=["Flamethrower", "Trailblaze", "Dig", "Will-O-Wisp"],
            ability="Flash Fire",
            tera=pk.grass
        ))

        d.add(find_mon(
            "Aron",
            moves=["Flash Cannon", "Earthquake", "Stone Edge", "Ice Punch"],
            ability="Sturdy"
        ))
        d.add(find_mon(
            "Lairon",
            moves=["Flamethrower", "Thunderbolt", "Ice Beam", "Energy Ball"],
            ability="Sturdy"
        ))

        if len(args) > 0 and args[0].lower() in ["custom", "build"]:
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

        nav = DexNavigator(find_mon(mon, use_bare=True), starting_mode=("help" if mon.lower() == "help" else None))
        return await nav.run(self.ctx)

    async def _catch(self, *args):
        if args:
            if not (ball_type := caseless_match(args[0], pk.poke_ball_types)):
                ball_type = "poke"
                starting_mon = find_mon(" ".join(args))
            else:
                starting_mon = find_mon(" ".join(args[1:]), return_on_fail=find_mon(1))
        else:
            ball_type = "poke"
            starting_mon = find_mon(1)

        return await CatchRateNavigator(mon=starting_mon, ball=ball_type).run(self.ctx)

    async def specify_raid_form(self, species: str) -> str:
        async def wait_for(*allowable_responses: str) -> str:
            try:
                mess = await zeph.wait_for(
                    "message", check=lambda c: general_pred(self.ctx)(c) and (pk.fix(c.content) in allowable_responses),
                    timeout=60
                )
            except asyncio.TimeoutError:
                return allowable_responses[0]
            else:
                return pk.fix(mess.content)

        if species == "Tauros":
            await ball_emol("master").send(self.ctx, "Is this Tauros Combat, Aqua, or Blaze Breed?")
            return await wait_for("combat", "aqua", "blaze")
        if species == "Toxtricity":
            await ball_emol("master").send(self.ctx, "Is this Toxtricity Amped or Low Key?")
            return await wait_for("amped", "low-key")
        if species == "Indeedee":
            await ball_emol("master").send(self.ctx, "Is this Indeedee male or female?")
            return await wait_for("male", "female")

    async def _raid(self, *args):
        if (len(args) < 2) or (not can_int(args[0])):
            raise commands.CommandError("Format: `z!pk raid <# stars> <species...>`")

        stars = int(args[0])
        if stars not in [5, 6]:
            raise commands.CommandError("Currently only 5- and 6-star raids are included in this command.")

        mon = find_mon(" ".join(args[1:]))
        if (mon.species.name in ["Tauros", "Indeedee", "Toxtricity"]) and \
                (pk.fix(" ".join(args[1:])) != pk.fix(mon.species_and_form)):
            mon.change_form(await self.specify_raid_form(mon.species.name))

        if mon.species_and_form in pk.raids[stars]:
            raid = pk.raids[stars][mon.species_and_form]
        elif mon.species.name in pk.raids[stars]:
            raid = pk.raids[stars][mon.species.name]
        else:
            raise commands.CommandError(f"There is no {stars}\u2605 {mon.species.name} raid.")

        return await RaidNavigator(raid).run(self.ctx)

    async def _5(self, *args):
        return await self._raid(5, *args)

    async def _6(self, *args):
        return await self._raid(6, *args)

    async def _compare(self, *args):
        if len(args) != 2:
            raise commands.CommandError(
                "Format: `z!pk cf <mon1> <mon2>`\nTo specify a form, use the hyphenated version (e.g. `Raichu-Alola`)."
            )

        def stat_comparison(stat: int):
            if stat == 6:
                n1 = sum(mon1.base_stats)
                n2 = sum(mon2.base_stats)
            else:
                n1 = mon1.base_stats[stat]
                n2 = mon2.base_stats[stat]
            rule = 1 if n1 > n2 else 2 if n1 < n2 else 3
            return f"{'**' if rule != 2 else ''}{n1}{'**' if rule != 2 else ''} " + \
                   f"{'>' if rule == 1 else '<' if rule == 2 else '='}" + \
                   f" {'**' if rule != 1 else ''}{n2}{'**' if rule != 1 else ''}"

        mon1 = find_mon(args[0])
        mon2 = find_mon(args[1])

        return await ball_emol().send(
            self.ctx, "Stat Comparison",
            d=f"**{mon1.species_and_form}** vs. **{mon2.species_and_form}**\n\n"
              f"**HP:** {stat_comparison(0)}\n"
              f"**Atk:** {stat_comparison(1)}\n"
              f"**Def:** {stat_comparison(2)}\n"
              f"**SpA:** {stat_comparison(3)}\n"
              f"**SpD:** {stat_comparison(4)}\n"
              f"**Spe:** {stat_comparison(5)}\n\n"
              f"**Total:** {stat_comparison(6)}"
        )

    async def _learnset(self, *args):
        if not args:
            raise commands.CommandError("Format: `z!pk learnset <species...>`")

        try:
            mon = find_mon(" ".join(args))
        except ValueError:
            raise commands.CommandError(f"Unknown Pok\u00e9mon `{' '.join(args)}`.")

        return await LearnsetNavigator(mon).run(self.ctx)


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
    if move.name in pk.move_dex:
        await ctx.send(embed=Emol(zeph.emojis["yield"], hexcol("DD2E44")).con("This move already exists."))

    await ctx.send(f"```py\n{move.json}```", embed=PokemonInterpreter.move_embed(move))
    try:
        assert await confirm(f"{'Overwrite' if move.name in pk.move_dex else 'Save'} this move?", ctx, yes="save")
    except AssertionError:
        pass
    else:
        pk.move_dex[move.name] = move.copy()
        with open("pokemon/moves.json", "w") as f:
            json.dump({g: j.json for g, j in pk.move_dex.items()}, f, indent=4)
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
        species = pk.Species(name, 0, [])
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

        try:
            await emol.send(
                ctx, f"What Abilities does {mon.species_and_form} have?",
                d="Separate standard Abilities with a comma, and Hidden Abilities with a slash."
            )
            ability_input = (await zeph.wait_for("message", check=general_pred(ctx), timeout=300)).content
        except asyncio.TimeoutError:
            return await emol.send(ctx, "Request timed out.")
        if "/" in ability_input:
            standard_abilities = [g.strip() for g in ability_input.split("/")[0].split(",")]
            hidden_ability = ability_input.split("/")[1].strip()
        else:
            standard_abilities = [g.strip() for g in ability_input.split(",")]
            hidden_ability = ""
        if len(standard_abilities) < 2:
            standard_abilities.append("")
        pk.legal_abilities[mon.species_and_form] = [*standard_abilities, hidden_ability, ""]

        await emol.send(ctx, f"#{existing_mon.dex_no} {name}", d=display_mon(mon, "dex"), thumbnail=mon.dex_image)
        if await confirm("Does this look right?", ctx, desc_override="", allow_text_response=True):
            if force_exit or not (await confirm("Add another form?", ctx, desc_override="", allow_text_response=True)):
                pk.rewrite_abilities()
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


class WalkerStroll:
    def __init__(self, user: pk.WalkerUser, location: pk.Locale, balls: int = 30, berries: int = 20):
        self.user = user
        self.location = location
        self.balls = balls
        self.berries = berries
        self.remaining_encounters = 30
        self.shiny_odds = (3/4096) if any(g.effects.get("shiny") for g in self.user.equipped_charms) else (1/4096)

    def generate_encounter(self):
        mon = self.location.encounter(active_charms=self.user.equipped_charms)
        mon.randomize_gender()
        if random() < self.shiny_odds:
            mon.shiny = True
        return mon


def caught_indicator(user: pk.WalkerUser, mon: Union[pk.BareMiniMon, str]) -> str:
    if isinstance(mon, pk.BareMiniMon):
        mon = mon.species.name
    return f" {zeph.emojis['caught']}" if mon in user.dex else ""


def display_tokens(tokens: dict[str, int], joiner: str = " // ", if_empty: str = "none") -> str:
    return none_list([f"{zeph.emojis[g + '_token']} x{j}" for g, j in tokens.items()], joiner, if_empty)


class EncounterNavigator(Navigator):
    def __init__(self, mon: pk.BareMiniMon, stroll: WalkerStroll, message: discord.Message):
        super().__init__(ball_emol("safari"), [], 0, f"Encounter: {mon.name}!", remove_immediately=True)
        self.mon = mon
        self.stroll = stroll
        self.berry_level = 0
        self.caught = False
        self.message = message
        rarity = pk.rarity_stars[self.stroll.location.get_rarity(self.mon)]
        if self.mon.shiny:
            self.last_action = f"{zeph.emojis[rarity]} **Whoa! A :sparkles: shiny {mon.name} appeared!**"
        else:
            self.last_action = f"{zeph.emojis[rarity]} **A wild {mon.name} appeared!**"
        self.funcs[zeph.emojis["safari_ball"]] = self.ball
        self.funcs[zeph.emojis["razz_berry"]] = self.berry
        self.funcs["\U0001f45f"] = self.flee
        self.funcs[zeph.emojis["no"]] = self.exit

    @property
    def catch_chance(self):
        return ((self.mon.species.catch_rate + 50) / 700) + self.berry_level * 0.12

    @property
    def chance_indicator(self):
        if self.catch_chance >= 0.42:
            return ":green_square:"
        elif self.catch_chance >= 0.3:
            return ":yellow_square:"
        elif self.catch_chance >= 0.18:
            return ":orange_square:"
        else:
            return ":red_square:"

    def ball(self):
        self.stroll.balls -= 1
        if random() < self.catch_chance:
            self.last_action = f":tada: Gotcha! {self.mon.name} was caught!"
            self.caught = True
            self.closed_elsewhere = True
        else:
            messages = [
                ":boom: Oh no! The Pokémon broke free!",
                ":boom: Gah! It was so close, too!",
                ":boom: Aargh! Almost had it!"
            ]
            if self.last_action not in messages:
                self.last_action = messages[0]
            else:
                self.last_action = choice([g for g in messages if self.last_action != g])
        if self.stroll.balls == 0:
            self.closed_elsewhere = True

    def berry(self):
        if self.stroll.berries == 0:
            self.last_action = ":no_entry_sign: No more Berries to throw!"
        elif self.berry_level == 3:
            self.last_action = f":olive: {self.mon.name} doesn't seem interested in more Berries."
        else:
            self.stroll.berries -= 1
            self.berry_level += 1
            self.last_action = [
                f":strawberry: {self.mon.name} seems to be on edge.",
                f":grapes: {self.mon.name} is eyeing you curiously.",
                f":blueberries: {self.mon.name} looks content."
            ][self.berry_level - 1]

    def flee(self):
        self.last_action = "run"
        self.closed_elsewhere = True

    def exit(self):
        self.last_action = "exit"
        self.closed_elsewhere = True

    @property
    def con(self):
        action = "Out of Safari Balls! Come back another time." if not self.stroll.balls else \
            (f"Throw a {zeph.emojis['safari_ball']} **ball** (x{self.stroll.balls}), "
             f"throw a {zeph.emojis['razz_berry']} **berry** (x{self.stroll.berries}), or \U0001f45f **run**!")
        berries = "" if self.berry_level == 0 else f" ({zeph.emojis['razz_berry']} x{self.berry_level})"
        return self.emol.con(
            f"Encounter: {self.mon.name} {caught_indicator(self.stroll.user, self.mon)}",
            d=f"{self.last_action}\n\n{display_mon_types(self.mon, sep=' ')} // "
              f"Catch chance: {self.chance_indicator} {berries}\n\n{action}",
            image=self.mon.home_sprite, footer=f"Encounters remaining: {self.stroll.remaining_encounters}"
        )


class LocaleSelector(NumSelector):
    def __init__(self, locale_override: list[pk.Locale] = None):
        super().__init__(
            ball_emol("safari"), locale_override if locale_override else list(pk.walker_locales.values()), 8
        )
        self.selection = None

    def select(self, n: int):
        self.selection = self.page_list[n]
        self.closed_elsewhere = True

    @property
    def con(self):
        return self.emol.con(
            f"Select a locale! [{self.page}/{self.pgs}]",
            d="\n".join(f"**`[{n+1}]`** {g.name}" for n, g in enumerate(self.page_list)),
            footer="Say the number in chat to select a stroll destination."
        )


class WalkerBoxNavigator(Navigator):
    def __init__(self, user: pk.WalkerUser):
        super().__init__(Emol(":desktop:", hexcol("5DADEC")), user.box)
        self.user = user
        self.mode = "browse"
        self.filters = {"types": set(), "shiny": False, "sort": "date"}
        self.transfer_selection = []
        self.just_transferred = 0
        self.funcs[zeph.emojis["search"]] = self.change_filter
        self.funcs[zeph.emojis["moves"]] = self.back
        self.funcs[zeph.emojis["transfer"]] = self.transfer
        self.funcs[zeph.emojis["no"]] = self.close

        for g in range(self.per):
            self.funcs[f"!view {g+1}"] = partial(self.view_mon, g)

        for g in range(8):
            self.funcs[f"!evolve {g+1}"] = partial(self.select_evolution, g)

    async def close(self):
        await self.remove_buttons()

    def view_mon(self, n: int):
        if n + 1 > len(self.page_mons):
            return
        self.mode = f"view {n+1}"

    @property
    def viewed_mon(self) -> pk.BareMiniMon:
        if self.mode.startswith("view"):
            return self.page_mons[int(self.mode[-1]) - 1]

    def back(self):
        if self.mode != "filter":
            self.transfer_selection = []
        self.mode = "browse"

    def advance_page(self, direction: int):
        if self.mode.startswith("view"):
            viewed = int(self.mode[-1])
            if viewed + direction < 1:
                self.page = (self.page - 2) % self.pgs + 1
                self.mode = f"view {len(self.page_list)}"
            elif viewed + direction > len(self.page_list):
                self.page = self.page % self.pgs + 1
                self.mode = "view 1"
            else:
                self.mode = f"view {viewed + direction}"
        elif self.mode in ["browse", "transfer"]:
            self.page = (self.page + direction - 1) % self.pgs + 1

    @property
    def sorted_box(self):
        if self.filters["sort"] == "date":
            return list(enumerate(self.user.box))
        if self.filters["sort"] == "dex":
            return sorted(list(enumerate(self.user.box)), key=lambda c: c[1][0])
        if self.filters["sort"] == "name":
            return sorted(list(enumerate(self.user.box)), key=lambda c: pk.nat_dex_order[c[1][0] - 1])

    @property
    def filtered_box(self):
        return [g for g in self.sorted_box if self.filter_mon(pk.BareMiniMon.from_walker_pack(g[1]))]

    @property
    def sort_desc(self):
        return {
            "date": "Catch date", "dex": "National Dex no.", "name": "Alphabetical"
        }[self.filters["sort"]]

    def change_filter(self):
        if self.mode == "filter":
            if self.transfer_selection:
                self.mode = "transfer"
            else:
                self.mode = "browse"
        else:
            self.mode = "filter"

    def apply_filter(self):
        self.page = 1
        self.table = [g[1] for g in self.filtered_box]

    def filter_mon(self, mon: pk.BareMiniMon):
        if self.filters["types"] and (self.filters["types"].intersection(set(mon.types)) != self.filters["types"]):
            return False
        if self.filters["shiny"] and not mon.shiny:
            return False
        return True

    def transfer(self):
        if self.mode == "browse":
            self.mode = "transfer"
        elif self.mode == "transfer":
            if not self.transfer_selection:
                self.mode = "browse"
            else:
                self.mode = "confirm_transfer"
        elif self.mode == "confirm_transfer":
            for i in sorted(self.transfer_selection, reverse=True):
                self.user.transfer(i)
            self.just_transferred = len(self.transfer_selection)
            self.apply_filter()
            self.back()
        elif self.mode.startswith("view"):
            self.transfer_selection.append(self.box_index(int(self.mode[-1]) - 1))
            self.mode = f"confirm_transfer_{self.mode[-1]}"

    @property
    def page_mons(self) -> list[pk.BareMiniMon]:
        return [pk.BareMiniMon.from_walker_pack(g) for g in self.page_list]

    def box_index(self, page_index: int) -> int:
        return self.filtered_box[(self.page - 1) * self.per + page_index][0]

    def is_transferred(self, index: int) -> bool:
        return self.box_index(index) in self.transfer_selection

    @staticmethod
    def display_evo_reqs(mon: pk.BareMiniMon, evo: pk.Evolution):
        return " // ".join(
            f"{zeph.emojis[g + '_token'] if g in pk.types else '**'+g+'**'} x{j}"
            for g, j in pk.evolution_tokens(mon, evo).items()
        )

    def you_have(self, mon: pk.BareMiniMon) -> dict[str, int]:
        """What a Trainer already has of the required evolution items for a mon."""
        return {
            g: self.user.all_items.get(g) for g in pk.walker_items
            if any(g in self.user.has_of(pk.evolution_tokens(mon, e)) for e in mon.evolutions.values())
            and self.user.all_items.get(g)
        }

    def display_you_have(self, mon: pk.BareMiniMon):
        return none_list([
            f"{zeph.emojis[g + '_token'] if g in pk.types else '**' + g + '**'} x{j}"
            for g, j in self.you_have(mon).items()
        ], joiner=" // ")

    def meets_evo_reqs(self, mon: pk.BareMiniMon, evo: pk.Evolution):
        return self.user.can_afford(pk.evolution_tokens(mon, evo))

    def met_evolutions(self, mon: pk.BareMiniMon) -> list[pk.Evolution]:
        return [g for g in mon.accessible_evolutions.values() if self.meets_evo_reqs(mon, g)]

    def is_valid_evolution(self, s: str) -> bool:
        if s.lower() == "evolve":
            if len(self.met_evolutions(self.viewed_mon)) > 1:
                return False
            return bool(self.met_evolutions(self.viewed_mon))
        if re.fullmatch(r"evolve [1-8]", s.lower()):
            return int(s[-1]) <= len(self.met_evolutions(self.viewed_mon))
        return False

    async def select_evolution(self, n: int):
        if n >= len(self.met_evolutions(self.viewed_mon)):
            return
        evo = self.met_evolutions(self.viewed_mon)[n]
        old_name = self.viewed_mon.name
        emol = Emol(zeph.emojis["evolution"], hexcol("7B8F9E"))
        await emol.edit(self.message, f"What? {self.viewed_mon.name} is evolving!", image=self.viewed_mon.home_sprite)
        await asyncio.sleep(2)
        self.user.spend(pk.evolution_tokens(self.viewed_mon, evo))
        self.evolve_viewed_mon(evo)
        self.user.add_to_dex(self.viewed_mon)
        self.user.exp += 20
        await emol.edit(
            self.message, f"Congratulations! Your {old_name} evolved into {self.viewed_mon.species.name}!",
            image=self.viewed_mon.home_sprite
        )
        await asyncio.sleep(4)

    def evolve_viewed_mon(self, evo: pk.Evolution):
        mon = self.viewed_mon
        mon.evolve(evo)
        old_mon = self.user.box[self.box_index(int(self.mode[-1]) - 1)]
        old_mon[:2] = mon.walker_pack[:2]

    async def get_emoji(self, ctx: commands.Context):
        if self.mode.startswith("confirm_transfer"):
            reaction = (await zeph.wait_for(
                'reaction_add', timeout=300, check=lambda r, u: r.emoji in self.legal and
                r.message.id == self.message.id and u == ctx.author
            ))[0].emoji
            if reaction != zeph.emojis["transfer"]:
                try:
                    await self.message.remove_reaction(reaction, ctx.author)
                except discord.HTTPException:
                    pass
                return "cancel transfer"
            else:
                return reaction

        if self.mode == "filter":
            def pred(mr: MR, u: User):
                if isinstance(mr, discord.Message):
                    return u == ctx.author and mr.channel == ctx.channel and \
                        mr.content.lower() in ["type", "types", "shiny", "sort"]
                else:
                    return u == ctx.author and mr.emoji in self.funcs and mr.message.id == self.message.id

            mess = (await zeph.wait_for(
                'reaction_or_message', timeout=300, check=pred
            ))[0]
            if isinstance(mess, discord.Message):
                await mess.delete()
                return mess.content.lower()
            elif isinstance(mess, discord.Reaction):
                return mess.emoji

        if self.mode == "transfer":
            def pred(mr: MR, u: User):
                if isinstance(mr, discord.Message):
                    return u == ctx.author and mr.channel == ctx.channel and \
                        all((g == " " or can_int(g)) for g in mr.content)
                else:
                    return u == ctx.author and mr.message == self.message and mr.emoji in self.legal

            mess = (await zeph.wait_for('reaction_or_message', timeout=300, check=pred))[0]

            if isinstance(mess, discord.Message):
                try:
                    await mess.delete()
                except discord.HTTPException:
                    pass
                return f"transfer {mess.content}"
            else:
                return mess.emoji

        if self.mode.startswith("view"):
            def pred(mr: MR, u: User):
                if isinstance(mr, discord.Message):
                    return u == ctx.author and mr.channel == ctx.channel and self.is_valid_evolution(mr.content)
                else:
                    return u == ctx.author and mr.message == self.message and mr.emoji in self.legal

            mess = (await zeph.wait_for('reaction_or_message', timeout=300, check=pred))[0]

            if isinstance(mess, discord.Message):
                try:
                    await mess.delete()
                except discord.HTTPException:
                    pass
                if mess.content.lower() == "evolve":
                    return "!evolve 1"
                return "!" + mess.content.lower()
            else:
                return mess.emoji

        def pred(mr: MR, u: User):
            if isinstance(mr, discord.Message):
                return u == ctx.author and mr.channel == ctx.channel and f"!view {mr.content}" in self.legal
            else:
                return u == ctx.author and mr.message == self.message and mr.emoji in self.legal

        mess = (await zeph.wait_for('reaction_or_message', timeout=300, check=pred))[0]

        if isinstance(mess, discord.Message):
            try:
                await mess.delete()
            except discord.HTTPException:
                pass
            return f"!view {mess.content}"
        else:
            return mess.emoji

    async def run_nonstandard_emoji(self, emoji: Union[discord.Emoji, str], ctx: commands.Context):
        if emoji == "cancel transfer":
            if can_int(self.mode[-1]):
                self.transfer_selection.clear()
                self.mode = f"view {self.mode[-1]}"
            else:
                self.mode = "transfer"
            return

        if isinstance(emoji, str) and emoji.startswith("transfer "):
            for n in emoji[9:]:
                if can_int(n):
                    if 0 < int(n) <= len(self.page_list):
                        if self.is_transferred(int(n) - 1):
                            self.transfer_selection.remove(self.box_index(int(n) - 1))
                        else:
                            self.transfer_selection.append(self.box_index(int(n) - 1))

        if emoji in ["type", "types"]:
            mess = await self.emol.send(
                ctx, "What type(s) would you like to filter for?", d="Enter `none` to clear the filter."
            )
            user_input = await zeph.wait_for(
                'message', check=lambda m: general_pred(ctx)(m) and
                (all(g.title() in pk.types or g.title() == "None" for g in re.split(r"[/,\s]+", m.content)) or
                 m.content.lower() in ["cancel", "exit", "back"])
            )
            if user_input.content.lower() not in ["cancel", "exit", "back"]:
                if user_input.content.lower() == "none":
                    self.filters["types"] = set()
                else:
                    self.filters["types"] = set(g.title() for g in re.split(r"[/,\s]+", user_input.content)[:2])
                self.apply_filter()
            await user_input.delete()
            return await mess.delete()

        if emoji == "sort":
            mess = await self.emol.send(
                ctx, "What method should the box be sorted by?",
                d="\\- **`date`**: Sort mons by catch date. (default)\n"
                  "\\- **`dex`**: Sort mons by National Dex number.\n"
                  "\\- **`name`**: Sort mons alphabetically by name."
            )
            user_input = await zeph.wait_for(
                'message', check=lambda m: general_pred(ctx)(m) and
                m.content.lower() in ["cancel", "exit", "back", "date", "dex", "name"]
            )
            if user_input.content.lower() not in ["cancel", "exit", "back"]:
                self.filters["sort"] = user_input.content.lower()
                self.apply_filter()
            await user_input.delete()
            return await mess.delete()

        if emoji == "shiny":
            self.filters["shiny"] = not self.filters["shiny"]
            self.apply_filter()

    @property
    def con(self):
        if self.mode == "filter":
            return self.emol.con(
                "Filters", d="Enter the name of a filter to change it.", same_line=True,
                fs={
                    "Types": none_list(list(self.filters["types"]), "/"), "Shiny?": checked(self.filters["shiny"]),
                    "Sort": self.sort_desc
                }
            )
        elif self.mode.startswith("view"):
            viewed = int(self.mode[-1]) - 1
            mon = self.viewed_mon
            if mon.accessible_evolutions:
                evo_mons = {g: pk.get_saf(g) for g in mon.accessible_evolutions}
                evo = "\n".join(
                    f"Evolve into **{j.into if evo_mons[j.into].species.name in self.user.dex else '???'}:** "
                    f"{self.display_evo_reqs(mon, j)}" +
                    (("\n\\- Type **`evolve`** to evolve this mon!" if len(self.met_evolutions(mon)) == 1 else
                      f"\n\\- Type **`evolve {self.met_evolutions(mon).index(j)+1}`** to select this evolution!")
                     if self.meets_evo_reqs(mon, j) else "")
                    for g, j in mon.accessible_evolutions.items() if g not in pk.cannot_evolve_walker
                ) + f"\nYou have: {self.display_you_have(mon)}"
            else:
                evo = "Does not evolve."
            return self.emol.con(
                f"{mon.name}{mon.shiny_indicator} "
                f"{':male_sign:' if mon.gender == 'male' else ':female_sign:' if mon.gender == 'female' else ''}",
                thumbnail=mon.home_sprite,
                d=f"{display_mon_types(mon, sep=' / ', include_names=True)}\n\n{evo}\n\n"
                  f"Caught at {pk.walker_locale_ids[self.page_list[viewed][-2]].name} on "
                  f"{datetime.date.fromordinal(self.page_list[viewed][-1] + 719163).strftime('%B %d, %Y')}."
            )
        elif self.mode.startswith("confirm_transfer"):
            selected_mons = [pk.BareMiniMon.from_walker_pack(self.user.box[g]) for g in self.transfer_selection]
            selected_types = [t for m in selected_mons for t in m.types]
            tokens = {g: selected_types.count(g) for g in pk.types if g in selected_types}
            tokens = display_tokens(dict(sorted(list(tokens.items()), key=lambda c: -c[1])))
            selected_names = [g.species_and_form for g in selected_mons if not g.shiny]
            aggregate_mons = {
                g: selected_names.count(g) for g in sorted(selected_names, key=lambda m: -selected_names.count(m))
            }
            aggregate_mons = "\n".join(
                f"{display_mon(pk.get_saf(g), 'typed_list', saf=True)} x{j}"
                for g, j in list(aggregate_mons.items())[:10]
            ) + (f"\n*...and {len(aggregate_mons) - 10} more species*" if len(aggregate_mons) > 10 else "")
            selected_shiny = [g.species_and_form for g in selected_mons if g.shiny]
            aggregate_shiny = {
                g: selected_shiny.count(g) for g in sorted(selected_shiny, key=lambda m: -selected_shiny.count(m))
            }
            aggregate_shiny = ("\n".join(
                f"{display_mon(pk.get_saf(g), 'typed_list', saf=True)} :sparkles: x{j}"
                for g, j in list(aggregate_shiny.items())
            ) + "\n") if aggregate_shiny else ""
            return self.emol.con(
                "Confirm Transfer",
                d="**Are you sure you want to transfer these Pok\u00e9mon? This cannot be undone.**\n"
                  f"{aggregate_shiny}{aggregate_mons}\n\n**You'll receive:**\n{tokens}",
                footer="Press the transfer button again to confirm. Press any other button to cancel."
            )
        else:
            if self.just_transferred:
                additional_info = f":white_check_mark: **{self.just_transferred} Pok\u00e9mon transferred.**\n\n"
                self.just_transferred = 0
            elif self.mode == "transfer":
                additional_info = "Select Pok\u00e9mon to transfer to the Professor in exchange for tokens. You'll " \
                    "get one token for each type of each transferred mon.\n\n" \
                    f"Press the {zeph.emojis['transfer']} **transfer** button to transfer " \
                    f"**{len(self.transfer_selection)}** selected Pok\u00e9mon.\nPress the " \
                    f"{zeph.emojis['moves']} **browse** button to cancel.\n\n"
            else:
                additional_info = ""
            return self.emol.con(
                f"Cypress's PC [{self.page}/{self.pgs}]",
                d=additional_info + none_list(
                    [f"**`[{n+1}]`**{(' ' + str(checked(self.is_transferred(n)))) if self.mode == 'transfer' else ''} "
                     f"{display_mon(g, 'typed_list')}{g.shiny_indicator}"
                     for n, g in enumerate(self.page_mons)], "\n", "No mons found."
                ),
                footer="Enter the number beside a mon to select or unselect it.\nYou can also select "
                       "multiple at once, e.g. \"123\" or \"3 6 8\"." if self.mode == "transfer" else
                       "Enter the number beside a mon in chat to view it in more detail."
            )


class WalkerLevelNavigator(Navigator):
    def __init__(self, user: pk.WalkerUser, start_at: int = 1):
        super().__init__(ball_emol("safari"))
        self.user = user
        self.page = start_at

    @property
    def pgs(self):
        return len(pk.walker_exp_levels)

    @property
    def con(self):
        return self.emol.con(
            f"Trainer Level {self.page}",
            d=f"**EXP:** {self.user.exp}/**{pk.walker_exp_levels[self.page - 1]}**\n"
              f"Catch a Pok\u00e9mon: +1 // New dex entry: +20 // Evolve a Pok\u00e9mon: +20",
            fs={"Unlockables": pk.walker_level_desc(self.page)}
        )


class WalkerCharmNavigator(NumSelector):
    def __init__(self, user: pk.WalkerUser):
        super().__init__(ball_emol("safari"), per=4)
        self.user = user
        self.slot = 0
        self.replacing_id = -1  # charm initially equipped in self.slot
        self.selected_id = -1  # charm currently equipped in self.slot
        self.last_equipped_ids = []
        self.funcs["↩"] = self.back
        self.funcs[zeph.emojis["no"]] = self.close

    def back(self):
        self.slot = 0
        self.replacing_id = -1
        self.selected_id = -1
        self.last_equipped_ids = []

    async def close(self):
        await self.remove_buttons()

    @property
    def charm_in_slot(self) -> pk.Charm | None:
        if len(self.user.equipped_charms) >= self.slot:
            return self.user.equipped_charms[self.slot - 1]

    @property
    def charm_list(self) -> list[pk.Charm]:
        if self.slot == 0:
            return []
        else:
            return ([pk.charm_ids[self.replacing_id]] if self.replacing_id != -1 else []) + \
                [g for g in self.user.unreplaced_charms
                 if (g.id not in self.last_equipped_ids or g.id == self.selected_id) and g.id != self.replacing_id]

    @property
    def pgs(self):
        return ceil(len(self.charm_list) / self.per)

    @property
    def page_list(self) -> list[pk.Charm]:
        return page_list(self.charm_list, self.per, self.page)

    def is_valid_user_selection(self, n: int):
        return 1 <= n <= (3 if self.slot == 0 else min(self.per, len(self.page_list)))

    def select(self, n: int):
        if self.slot == 0:
            self.slot = n + 1
            if n < len(self.user.equipped_charm_ids):
                self.replacing_id = self.user.equipped_charm_ids[n]
                self.selected_id = self.replacing_id + 0  # so they aren't linked
            else:
                self.replacing_id = -1
                self.selected_id = -1
            self.last_equipped_ids = self.user.equipped_charm_ids
            return
        else:
            selection = self.page_list[n].id
            if selection in self.user.equipped_charm_ids:
                self.user.equipped_charm_ids.remove(selection)
            else:
                try:
                    self.user.equipped_charm_ids.remove(self.selected_id)
                except ValueError:
                    pass
                self.user.equipped_charm_ids.append(selection)
                self.selected_id = selection

    @property
    def con(self):
        if self.slot == 0:
            equipped = [self.user.equipped_charms[n] if len(self.user.equipped_charms) > n else "" for n in range(3)]
            return self.emol.con(
                "Equipped Charms",
                d="You can equip up to three Charms.",
                fs={"Currently Equipped": "\n\n".join([
                    f"**`[{n+1}]` {g.name}**\n\\- {g.desc}" if g else f"**`[{n+1}]`** *empty*"
                    for n, g in enumerate(equipped)
                ])},
                footer="To add, remove, or replace a Charm, enter the number beside it below."
            )
        else:
            if not self.charm_list:
                return self.emol.con(
                    "Owned Charms", d="You have no more Charms to equip! Visit `z!pw market` to buy more."
                )
            desc = f"Currently equipped in slot {self.slot}: **{self.charm_in_slot.name}**\n{self.charm_in_slot.desc}" \
                if self.charm_in_slot else f"Currently equipped in slot {self.slot}:\n*empty*"
            return self.emol.con(
                f"Owned Charms",
                d=desc, footer="To select or unselect a Charm, enter the number beside it below.",
                fs={f"Available Charms [{self.page}/{self.pgs}]": "\n\n".join([
                    f"**`[{n+1}]` {checked(g.id in self.user.equipped_charm_ids)} {g.name}**\n\\- {g.desc}"
                    for n, g in enumerate(self.page_list)
                ])}
            )


class WalkerMarketNavigator(NumSelector):
    def __init__(self, user: pk.WalkerUser):
        super().__init__(ball_emol("safari"), s="Pok\u00e9Marketplace")
        self.user = user
        self.mode = "main"
        self.buying_item = {}
        self.last_bought = ""
        self.funcs["↩"] = self.back
        self.funcs[zeph.emojis["no"]] = self.attempt_close

    def back(self):
        if self.mode == "main":
            return
        if self.buying_item.get("name"):
            if self.mode == "Charms":
                self.user.owned_charm_ids.append(self.buying_item["id_no"])
                if self.buying_item["replaces"] in self.user.equipped_charm_ids:
                    self.user.equipped_charm_ids[self.user.equipped_charm_ids.index(self.buying_item["replaces"])] = \
                        self.buying_item["id_no"]
            else:
                self.user.other_items[self.buying_item["name"]] = \
                    self.user.other_items.get(self.buying_item["name"], 0) + 1
            self.user.spend(self.buying_item["price"])
            self.last_bought = self.buying_item["name"]
            self.buying_item = {}
            if self.page > self.pgs:
                self.page -= 1
        else:
            self.mode = "main"

    async def attempt_close(self):
        if self.buying_item.get("name"):
            self.buying_item = {}
        else:
            await self.remove_buttons()
            self.closed_elsewhere = True

    def select(self, n: int):
        if self.mode == "main":
            self.mode = list(pk.walker_marketplace.keys())[n]
        else:
            self.attempt_to_buy(n)

    def attempt_to_buy(self, n: int):
        item = self.page_list[n]
        if self.user.can_afford(item["price"]):
            self.buying_item = item
        else:
            self.buying_item = {"afford": item["name"]}

    def advance_page(self, direction: int):
        if self.buying_item.get("name") and direction:
            self.buying_item = {}
        else:
            self.page = (self.page + direction - 1) % self.pgs + 1

    @property
    def section_per(self):
        if self.mode == "Charms":
            return 4
        if self.mode in pk.walker_marketplace:
            return 6
        return 100

    @property
    def item_list(self) -> list[dict]:
        if self.mode == "Charms":
            return [
                g.json for g in pk.charms.values()
                if self.user.meets_prereqs_for(g) and g.id not in self.user.owned_charm_ids
            ]
        elif self.mode in pk.walker_marketplace:
            return list(pk.walker_marketplace[self.mode].values())
        elif self.mode == "main":
            return list(pk.walker_marketplace)

    @property
    def pgs(self):
        return ceil(len(self.item_list) / self.section_per)

    @property
    def page_list(self) -> list:
        return page_list(self.item_list, self.section_per, self.page)

    @property
    def con(self):
        if self.mode == "main":
            return self.emol.con(
                self.title,
                d=f"Welcome to the Marketplace! Select a category to shop from the options below.\n\n" +
                  ("\n".join(f"**`[{n+1}]` {g}**" for n, g in enumerate(list(pk.walker_marketplace.keys())))),
                footer="Enter the number beside an item in chat to select it."
            )

        if self.buying_item.get("name"):
            name = f"the **{self.buying_item['name']}**" if self.mode == "Charms" else \
                a_or_an('**' + self.buying_item['name'] + '**')
            desc = f"\\- {self.buying_item.get('desc')}\n" if self.buying_item.get("desc") else ""
            return self.emol.con(
                self.title,
                d=f"Do you want to buy {name}?\n{desc}\n"
                  f"**Price:** {display_tokens(self.buying_item['price'])}\n"
                  f"**You have:** {display_tokens(self.user.has_of(self.buying_item['price']))}",
                footer="Press the return ↩ button to confirm. Press any other button to cancel."
            )

        # ONLY SHOP SCREENS BELOW THIS POINT

        add_info = f"You can't afford {a_or_an('**' + self.buying_item['afford'] + '**')}!\n\n" \
            if self.buying_item.get("afford") else f":white_check_mark: Purchased the **{self.last_bought}**." \
            f"{' Equip it using `z!pw charms`!' if self.mode == 'Charms' else ''}\n\n" if self.last_bought else ""
        you_have = display_tokens(self.user.tokens)
        self.last_bought = ""

        if self.mode == "Charms":
            if not self.item_list:
                if self.user.level < 3:
                    desc = "Charms are unlocked at **Level 3.** Go catch some more Pok\u00e9mon and come back!"
                else:
                    desc = "You've bought all the Charms you can buy!"
            else:
                desc = f"{add_info}You have: {you_have}\n\n" + \
                       ("\n\n".join(f"**`[{n+1}]` {g['name']}**\n\\- {g['desc']}\nPrice: {display_tokens(g['price'])}"
                                    for n, g in enumerate(self.page_list)))
            return self.emol.con(
                f"{self.title}: Charms [{self.page}/{self.pgs}]", d=desc,
                footer="Enter the number beside an item in chat to select it."
            )

        if self.mode in pk.walker_marketplace:
            return self.emol.con(
                f"{self.title}: {self.mode} [{self.page}/{self.pgs}]",
                d=f"{add_info}You have: {you_have}\n\n" +
                  ("\n\n".join(f"**`[{n + 1}]` {g['name']}**\nPrice: {display_tokens(g['price'])}"
                               for n, g in enumerate(self.page_list))),
                footer="Enter the number beside an item in chat to select it."
            )


class PokeWalkerInterpreter(Interpreter):
    redirects = {
        "s": "stroll", "l": "locale", "b": "box", "locales": "locale", "p": "profile", "h": "help", "c": "charms",
        "m": "market", "level": "levels", "lv": "levels", "pc": "box", "mart": "market"
    }

    @property
    def user(self) -> pk.WalkerUser:
        return zeph.walker_users[self.au.id]

    async def _help(self, *args):
        help_dict = {
            "stroll": "Go for a stroll in one of your unlocked locales. While on a stroll, you can encounter up to "
                      "30 Pok\u00e9mon, randomly determined by the encounter table for that locale.\n\nDuring an "
                      f"encounter, you have three options: throw a {zeph.emojis['safari_ball']} **ball** to try to "
                      f"catch the Pok\u00e9mon; throw a {zeph.emojis['razz_berry']} **berry** to make it easier to "
                      f"catch; or :athletic_shoe: **run away**. A Razz Berry increases a Pok\u00e9mon's catch rate "
                      f"somewhat, and you can stack up to 3. Each stroll starts with 30 Safari Balls and 20 Razz "
                      f"Berries; use them wisely!\n\n"
                      f"When a Pok\u00e9mon is caught, you earn one \"token\" {zeph.emojis['Grass_token']} for each "
                      f"of its types. These can be spent on many things in the `z!pw market`.\n\n"
                      "`z!pw stroll` opens the locale browser to select the destination for a stroll.\n\n"
                      "`z!pw stroll <locale...>` jumps straight into a stroll at the specified locale.",
            "locale": "Check the wild Pok\u00e9mon available at a certain location.\n\n"
                      "`z!pw locale` opens the locale browser to select a location.\n\n"
                      "`z!pw locale <locale...>` shows the details of the specified locale.",
            "box": "`z!pw box` opens the PC. While in the PC, you can view all your caught Pok\u00e9mon, as well as "
                   "filter for certain types, shinies, etc.",
            "charms": "`z!pw charms` allows you to equip and unequip Charms - items which provide passive effects "
                      "during strolls like increased spawn or catch rate.\n\nCharms are available for purchase from "
                      "`z!pw market` using type tokens. They do not expire, but you can only equip up to 3 at a time.",
            "market": "`z!pw market` opens the Pok\u00e9Marketplace, where you can buy Charms, evolution stones, "
                      "and more in exchange for type tokens. Earn tokens by catching and transferring Pok\u00e9mon. "
                      "Navigate the menu and make purchases by entering numbers in chat: i.e., type `1` to select "
                      "option `[1]`.",
            "profile": "`z!pw profile` shows your Trainer profile, which includes how many Pok\u00e9mon you've caught, "
                       "your dex completion rate, and your tokens.",
            "levels": "`z!pw levels` shows you the XP requirements and rewards for each Trainer Level, as well as "
                      "details on how to gain XP.\n\n"
                      "`z!pw level <n>` shows you the requirements and rewards for the given level."
        }
        desc_dict = {
            "stroll": "Starts a stroll in a certain locale.",
            "locale": "Shows the wild Pok\u00e9mon available at a locale.",
            "box": "Opens the PC, where you can view your Pok\u00e9mon.",
            "charms": "Manages your equipped Charms.",
            "market": "Opens the Charm/item marketplace.",
            "profile": "Shows your Trainer profile.",
            "levels": "Displays information about Trainer Levels."
        }
        shortcuts = {j: g for g, j in self.redirects.items() if len(g) <= 2}

        def get_command(s: str):
            return f"**`{s}`** (or **`{shortcuts[s]}`**)" if shortcuts.get(s) else f"**`{s}`**"

        if len(args) == 0 or (args[0].lower() not in help_dict and args[0].lower() not in self.redirects):
            return await ball_emol().send(
                self.ctx, "z!pokewalker help",
                d="Available functions:\n\n" + "\n".join(f"{get_command(g)} - {j}" for g, j in desc_dict.items()) +
                  "\n\nFor information on how to use these, use `z!pokewalker help <function>`."
            )

        ret = self.redirects.get(args[0].lower(), args[0].lower())

        return await ball_emol("safari").send(self.ctx, f"z!pokewalker {ret}", d=help_dict[ret])

    @property
    def unlocked_locales(self):
        return {g: j for g, j in pk.walker_locales.items() if self.user.meets_prereqs_for(j)}

    async def select_locale(self):
        nav = LocaleSelector(list(self.unlocked_locales.values()))
        await nav.run(self.ctx)
        if nav.selection is not None:
            return nav.selection
        else:
            raise commands.CommandError("Locale selector timed out.")

    async def _locale(self, *args):
        if not args:
            loc = await self.select_locale()
        else:
            if args[0].lower() in self.unlocked_locales:
                loc = self.unlocked_locales[args[0].lower()]
            else:
                fixed_locales = {pk.fix(g.name): g for g in self.unlocked_locales.values()}
                if pk.fix(" ".join(args)) in fixed_locales:
                    loc = fixed_locales[pk.fix(" ".join(args))]
                else:
                    loc = await self.select_locale()

        mons = {g: [pk.get_saf(p) for p in j] for g, j in loc.encounter_table.items()}
        return await ball_emol("safari").send(
            self.ctx, loc.name, d=loc.desc, same_line=True,
            fs={
                f"{g} {zeph.emojis[pk.rarity_stars[g]]}":
                "\n".join([display_mon(p, "typed_list") + caught_indicator(self.user, p) for p in j])
                for g, j in mons.items()
            }
        )

    async def _stroll(self, *args):
        emol = ball_emol("safari")
        caught_mons = []
        if len(args) > 0 and args[0].lower() in self.unlocked_locales:
            destination = self.unlocked_locales[args[0].lower()]
        else:
            destination = await self.select_locale()

        log_message = await emol.send(self.ctx, "Logbook")
        encounter_history = []
        message = await emol.send(
            self.ctx, f"Let's go for a stroll in {destination.name}!",
            d=f"**Equipped Charms:** {none_list([g.name for g in self.user.equipped_charms])}"
              if self.user.owned_charm_ids else None
        )
        for button in [zeph.emojis["safari_ball"], zeph.emojis["razz_berry"], "\U0001f45f", zeph.emojis["no"]]:
            await message.add_reaction(button)

        stroll = WalkerStroll(self.user, destination)
        token_reward = max([*[g.effects.get("tokens", 1) for g in self.user.equipped_charms], 1])
        starting_exp = self.user.exp
        starting_level = self.user.level
        await asyncio.sleep(2)

        for i in range(30):
            mon = stroll.generate_encounter()
            encounter_history.append(f"{i+1}\\. Encountered a wild {':sparkles: ' if mon.shiny else ''}{mon.name}.")
            stroll.remaining_encounters -= 1

            nav = EncounterNavigator(mon, stroll, message)
            await nav.update_message()
            await emol.edit(log_message, "Logbook", d="\n".join(encounter_history))
            await nav.run(self.ctx, skip_setup=True)

            if nav.caught:
                self.user.catch(mon, destination, time.time(), token_reward)
                caught_mons.append(mon)
                encounter_history[-1] = f"{i+1}\\. Caught {'sparkles:' if mon.shiny else ''}{mon.name}."

            if nav.stroll.balls == 0:
                await nav.update_message()
                break
            elif nav.caught:
                await nav.update_message()
                await asyncio.sleep(3)
            elif nav.last_action == "run":
                encounter_history[-1] = f"{i+1}\\. Ran from {'sparkles:' if mon.shiny else ''}{mon.name}."
            elif nav.last_action == "exit":
                break
            else:
                await emol.send(self.ctx, "Stroll timed out.")
                break

        if not caught_mons:
            return await emol.send(self.ctx, "Tough luck!", d="You didn't catch anything this time.")
        else:
            caught_types = [t for m in caught_mons for t in m.types]
            tokens = {g: round(caught_types.count(g) * token_reward) for g in pk.types if g in caught_types}
            tokens = display_tokens(dict(sorted(list(tokens.items()), key=lambda c: -c[1])))
            caught_names = [g.species_and_form for g in caught_mons]
            aggregate_mons = {
                g: caught_names.count(g) for g in sorted(caught_names, key=lambda m: destination.get_rarity(m))
            }
            xp = "" if starting_level == len(pk.walker_exp_levels) else \
                f"\n\n**+{self.user.exp - starting_exp} XP!**\n" \
                f"Next level: {self.user.exp}/{pk.walker_exp_levels[starting_level]}"
            return await emol.send(
                self.ctx, "Congratulations!",
                d="**You caught:**\n" +
                  ("\n".join(f"{zeph.emojis[pk.rarity_stars[destination.get_rarity(m)]]} {m} x{n}"
                             for m, n in aggregate_mons.items())) +
                  f"\n\n**Tokens collected:**\n{tokens}{xp}"
            )

    async def _box(self, *args):
        nativity = Nativity(self.ctx, block_all=True)
        zeph.nativities.append(nativity)
        await WalkerBoxNavigator(self.user).run(self.ctx)
        return zeph.nativities.remove(nativity)

    async def _profile(self, *args):
        tokens = none_list([f"{zeph.emojis[g + '_token']} x{j}" for g, j in self.user.tokens.items() if j > 0])
        star = zeph.emojis[
            "diamond_star" if self.user.level == len(pk.walker_exp_levels) else
            "gold_star" if self.user.level >= 7 else "silver_star" if self.user.level >= 4 else "bronze_star"
        ]
        next_level = "-" if self.user.level == len(pk.walker_exp_levels) else pk.walker_exp_levels[self.user.level]
        return await ball_emol("safari").send(
            self.ctx, f"Trainer Profile: {self.au.global_name}",
            d=f"{star} **Trainer Level {self.user.level}** {star}\n"
              f"XP: {self.user.exp} // Next Level: {next_level}\n\n"
              f"PC Pok\u00e9mon: {len(self.user.box)} // Pok\u00e9dex: {len(self.user.dex)}\n\nTokens: {tokens}"
        )

    async def _levels(self, *args):
        if args and can_int(args[0]):
            start_at = int(args[0]) if 1 <= int(args[0]) <= len(pk.walker_exp_levels) else 1
        else:
            start_at = 1
        return await WalkerLevelNavigator(self.user, start_at).run(self.ctx)

    async def _charms(self, *args):
        nativity = Nativity(self.ctx, block_all=True)
        zeph.nativities.append(nativity)
        await WalkerCharmNavigator(self.user).run(self.ctx)
        return zeph.nativities.remove(nativity)

    async def _market(self, *args):
        nativity = Nativity(self.ctx, block_all=True)
        zeph.nativities.append(nativity)
        await WalkerMarketNavigator(self.user).run(self.ctx)
        return zeph.nativities.remove(nativity)


def load_walker_users():
    with open("storage/walker.txt", "r") as read:
        for i in read.read().split("\n"):
            if i:
                us = pk.WalkerUser.from_str(i)
                zeph.walker_users[us.id] = us


@zeph.command(
    name="pokewalker", aliases=["pw"],
    usage="z!pw help",
    description="Go for a stroll with your Pok\u00e9mon.",
    help="Similar to the Pok\u00e9walker from HeartGold/SoulSilver. Go for a stroll in one of many locations, "
         "catch Pok\u00e9mon, and... probably other stuff eventually. See `z!pw` for more information."
)
async def pokewalker_command(ctx: commands.Context, func: str = None, *args):
    if not func:
        return await ball_emol("safari").send(
            ctx, "The Pok\u00e9walker... kind of.",
            d="**This game is a work in progress.** It was inspired by the Pok\u00e9walker, a pedometer accessory "
              "that came bundled with Pok\u00e9mon HeartGold/SoulSilver and included its own catch & battle "
              "minigame. I've taken a bit of liberty in translating that to Discord, and also added some features "
              "inspired by Pok\u00e9mon GO, to create **`z!pw`**.\n\n"
              "While on a `z!pw stroll`, you can encounter and catch up to 30 Pok\u00e9mon. (They can be shiny, by "
              "the way.) For each Pok\u00e9mon you catch, you'll earn one token for each of its types - e.g. after "
              f"catching a {zeph.emojis['Grass']} Grass / {zeph.emojis['Poison']} Poison Bulbasaur, you'll earn "
              f"one {zeph.emojis['Grass_token']} Grass and one {zeph.emojis['Poison_token']} Poison token.\n\n"
              "Pok\u00e9mon you catch get sent to your `z!pw box`, where you can view them, transfer them to the "
              "Professor to earn additional tokens, or spend tokens to evolve them. You can also spend tokens in the "
              "`z!pw market` to buy Charms - equippable items that provide passive effects while you're on a stroll "
              "- and evolution items like Stones. As you progress through the game, you'll unlock more stroll "
              "locales, more Charms, and more Pok\u00e9mon. Check `z!pw help` for a full list of commands!"
        )

    if ctx.author.id not in zeph.walker_users:
        zeph.walker_users[ctx.author.id] = pk.WalkerUser.new(ctx.author.id)
    previous_level = zeph.walker_users[ctx.author.id].level

    await PokeWalkerInterpreter(ctx).run(str(func).lower(), *args)

    if zeph.walker_users[ctx.author.id].level > previous_level:
        await asyncio.sleep(1)
        await ball_emol("safari").send(
            ctx, "Level Up!",
            d=f"Congratulations! You've reached **Trainer Level {zeph.walker_users[ctx.author.id].level}!**\n\n"
              f"{pk.walker_level_up_rewards(zeph.walker_users[ctx.author.id].level)}"
        )
