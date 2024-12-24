import asyncio
import discord
import json
import random
import re
import requests
import time
from classes.embeds import Emol
from discord.ext import commands
from functions import general_pred, grammatical_join, hex_to_color, none_list
from PIL import Image
from pokemon import walker as pk, tcgp as tp
from minigames import planes as pn
from pyquery import PyQuery


testing_emote_servers = [  # servers that either are my testing server or that I use only for emote storage
    405184040161771522, 516004299785109516, 516336805151506449, 516017413729419265, 516044646942638090,
    516015721998843904, 516079973447237648, 528460450069872640, 800832873854271528, 826341777837260811
]


ball_colors = {
    "beast": "8FD5F6", "cherish": "E84535", "dive": "81C7EF", "dream": "F4B4D0", "dusk": "30A241", "fast": "F2C63F",
    "friend": "80BA40", "great": "3B82C4", "heal": "E95098", "heavy": "9B9EA4", "level": "F5D617", "love": "E489B8",
    "lure": "49B0BE", "luxury": "D29936", "master": "7E308E", "moon": "00A6BA", "nest": "7EBF41", "net": "0998B4",
    "park": "F4D050", "poke": "F18E38", "premier": "FFFFFF", "quick": "73B5E4", "repeat": "FFF338", "safari": "307D54",
    "sport": "F18E38", "timer": "FFFFFF", "ultra": "FDD23C"
}


def m_to_ft_and_in(m: float) -> str:
    inches = round(m / 0.0254)
    return f"{inches // 12}'{str(inches % 12).rjust(2, '0')}\""


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
            1: Image.open("minigames/minimaps/worldzoom1.png").convert("RGBA"),
            2: Image.open("minigames/minimaps/worldzoom2.png").convert("RGBA"),
            4: Image.open("minigames/minimaps/worldzoom4.png").convert("RGBA")
        }
        self.airport_icon = Image.open("minigames/minimaps/airport_large.png").convert("RGBA")
        for i in self.airport_maps.values():
            assert isinstance(i, Image.Image)
        assert isinstance(self.airport_icon, Image.Image)
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
            if g.available and self.server_settings[g.guild.id].public_emotes
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

    def load_walker_users(self):
        with open("storage/walker.txt", "r") as read:
            for i in read.read().split("\n"):
                if i:
                    us = pk.WalkerUser.from_str(i)
                    self.walker_users[us.id] = us

    async def initialize_planes(self):
        print("Initializing planes...")
        start = time.time()
        for i in re.findall(pn.pattern, pn.readurl(pn.map_url)):
            pn.City.from_html(i)
        if len(pn.cities) == 0:
            return print("Initialization failed.")
        for i in pn.cities.values():
            if i.country not in pn.countries:
                pn.Country.from_name_only(i.country)
        with open("storage/planes.txt", "r") as read:
            for i in read.readlines():
                us = pn.User.from_str(i)
                self.plane_users[us.id] = us
        return print(f"Planes initialized. ({round(time.time() - start, 1)} s)")

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

    async def confirm(self, s: str, dest: discord.abc.Messageable, caller: discord.User | discord.Member = None, **kwargs):
        def pred(r: discord.Reaction, u: discord.User | discord.Member):
            return r.emoji in [self.emojis["yes"], self.emojis["no"]] and r.message.id == message.id and \
                ((caller is None and u != self.user) or u == caller)

        emol = kwargs.get("emol", Emol(self.emojis["yield"], hex_to_color("DD2E44")))

        message = await emol.send(
            dest, s,
            d=kwargs.get("desc_override") if "desc_override" in kwargs else
            (f"{kwargs.get('add_info', '')} To {kwargs.get('yes', 'confirm')}, react with {self.emojis['yes']}. "
             f"To {kwargs.get('no', 'cancel')}, react with {self.emojis['no']}.")
        )
        await message.add_reaction(self.emojis["yes"])
        await message.add_reaction(self.emojis["no"])
        try:
            if kwargs.get("allow_text_response"):
                def mr_pred(mr: discord.Message | discord.Reaction, u: discord.User | discord.Member):
                    if isinstance(mr, discord.Reaction):
                        return pred(mr, u)
                    else:
                        if isinstance(dest, commands.Context):
                            return mr.content.lower() in ["yes", "no"] and general_pred(dest)(mr)
                        else:
                            return mr.content.lower() in ["yes", "no"] and mr.channel == dest and \
                                ((caller is None and u != self.user) or u == caller)

                con = (await self.wait_for("reaction_or_message", timeout=kwargs.get("timeout", 120), check=mr_pred))[0]
                if isinstance(con, discord.Reaction):
                    con = con.emoji.name
                else:
                    con = con.content.lower()
            else:
                con = (await self.wait_for("reaction_add", timeout=kwargs.get("timeout", 120), check=pred))[
                    0].emoji.name
        except asyncio.TimeoutError:
            await emol.edit(message, "Confirmation request timed out.")
            return False
        else:
            if kwargs.get("delete"):  # this should only be used in EXTREME edge cases
                await message.delete()
            return con == "yes"

    def nativity_special_case_match(self, ctx: commands.Context, passcode: str):
        """Returns True iff a matching Nativity exists."""
        for nativity in self.nativities:
            if nativity.match_special_case(ctx, passcode):
                return True
        return False

    async def image_url(self, fp: str):
        return (await self.get_channel(528460450069872642).send(file=discord.File(fp))).attachments[0].url

    def sorted_assignable_roles(self, guild: discord.Guild, only_selfroles: bool = False, only_autoroles: bool = False):
        if only_selfroles:
            return [g for g in self.sorted_assignable_roles(guild) if g.id in self.server_settings[guild.id].selfroles]
        if only_autoroles:
            return [g for g in self.sorted_assignable_roles(guild) if g.id in self.server_settings[guild.id].autoroles]
        return sorted([g for g in guild.roles[1:] if (not g.managed) and g < guild.me.top_role], reverse=True)

    def ball_emol(self, ball: str = None):
        ret = ball if ball else random.choice(list(ball_colors))
        return Emol(self.emojis[f"{ret}_ball"], hex_to_color(ball_colors[ret]))

    def type_emol(self, s: str):
        return Emol(self.emojis[s], hex_to_color(pk.type_colors[s]))

    def display_move(self, move: pk.PackedMove | pk.Move | pk.WikiMove, mode: str) -> str:
        if isinstance(move, pk.PackedMove):
            move = move.unpack()

        if mode == "list":
            return f"{self.emojis[move.type]} {move.name}"
        if mode == "inline":
            nbsp = "\u00a0"
            return f"[ {self.emojis[move.type]} **`{move.name.ljust(16, nbsp)} [{str(move.ppc).rjust(2)}" \
                   f"/{str(move.pp).rjust(2)}]`** {self.emojis[move.category]} ]"
        if mode == "partial":
            return f"{self.display_move(move, 'inline')}\n" \
                   f"{self.emojis['__']} Power: {move.power_str} / Accuracy: {move.accuracy_str}"
        if mode == "wiki":
            return f"**Type:** {self.emojis[move.type]} {move.type} / " \
                   f"**Category:** {self.emojis[move.category]} {move.category}\n" \
                   f"**Power:** {move.power_str} / **Accuracy:** {move.accuracy_str} / **PP:** {move.pp}" \
                   f"\n\n{move.description}\n\n" \
                   f"[Bulbapedia]({move.bulbapedia}) | [Serebii]({move.serebii}) | [Pok\u00e9monDB]({move.pokemondb})"
        if mode == "full":
            priority = f" / **Priority:** {move.priority}" if (isinstance(move, pk.Move) and move.priority) else ""
            return f"**Type:** {self.emojis[move.type]} {move.type} / " \
                   f"**Category:** {self.emojis[move.category]} {move.category}\n" \
                   f"**Power:** {move.power_str} / **Accuracy:** {move.accuracy_str} / **PP:** {move.pp}{priority}" \
                + (f"\n**Target:** {move.target}" if isinstance(move, pk.Move) else "") + \
                f"\n\n{move.description}"

    def display_type(self, s: str, include_name: bool = True) -> str:
        return f"{self.emojis[s]}{(' ' + s) if include_name else ''}"

    def display_mon_types(self, mon: pk.BareMiniMon, sep: str = "", align: str = "right", include_names: bool = False) -> str:
        if len(mon.types) > 1:
            return sep.join(self.display_type(g, include_name=include_names) for g in mon.types)
        else:
            if include_names:
                return self.display_type(mon.type1)
            if align == "left":
                return f"{self.emojis[mon.type1]}{sep}{self.emojis['__']}"
            return f"{self.emojis['__']}{sep}{self.emojis[mon.type1]}"

    def display_mon(self, mon: dict | pk.BareMiniMon, mode: str = "default", **kwargs) -> str:
        """Displays various attributes of a mon in pretty form, using Zeph's emotes."""
        full_knowledge = True if mode == "builder" else kwargs.get("full_knowledge", True)

        name = mon.overworld_saf if kwargs.get("saf") else mon.name

        if isinstance(mon, dict):
            mon = pk.Mon.unpack(mon)

        if mode == "typed_list":
            if mon.type2:
                return f"{self.display_mon_types(mon)} {name}"
            else:
                return f"{self.display_mon_types(mon)} {name}"
        if mode == "dex":
            abilities = f"**{'Abilities' if len(mon.regular_abilities) > 1 else 'Ability'}:** " \
                        f"{' / '.join(mon.regular_abilities)}"
            if mon.hidden_ability:
                abilities += f"\n**Hidden Ability:** {mon.hidden_ability}"
            if mon.special_event_ability:
                abilities += f"\n**Special Event Ability:** {mon.special_event_ability}"
            if mon.evolutions or mon.evolves_from:
                evo = "\n".join(
                    ([mon.evolved_by.sentence("from")] if mon.evolved_by else []) +
                    [g.sentence() for g in mon.evolutions.values()]
                )
            else:
                evo = "Does not evolve."

            return f"**{mon.species_and_form}**\n" \
                   f"{self.display_mon_types(mon, sep=' / ', include_names=True)}\n" \
                   f"**Height:** {mon.height} m ({m_to_ft_and_in(mon.height)})\n" \
                   f"**Weight:** {mon.weight} kg ({round(mon.weight * 2.20462262, 1)} lb)\n\n" \
                   f"{abilities}\n\n" \
                   f"**Stats:** {' / '.join(str(g) + ' ' + pk.six_stat_names[n] for n, g in enumerate(mon.base_stats))}\n" \
                   f"**Total:** {sum(mon.base_stats)}\n\n" \
                   f"{evo}\n\n" \
                   f"[Bulbapedia]({mon.bulbapedia}) | [Serebii]({mon.serebii}) | [Pok\u00e9monDB]({mon.pokemondb})"

        if not isinstance(mon, pk.Mon):
            raise TypeError("Full Mon object needed for that display type.")

        if mode == "inline":
            return f"{mon.nickname_and_species} - {mon.hp_display(full_knowledge)}" + \
                (f" {self.emojis[mon.status_emoji]}" if mon.status_emoji else "")
        if mode == "turn_status":
            ret = [f"{mon.nickname_and_species} - {mon.hp_display(full_knowledge)}"]
            if mon.status_condition:
                ret.append(f"{self.emojis[mon.status_emoji]} {mon.status_condition}")
            if mon.terastallized:
                ret.append(f"- Tera-{mon.tera_type}")
            return "\n\u00a0\u00a0\u00a0\u00a0".join(ret)
        if mode == "team_builder":
            return f"{mon.nickname_and_species} Lv. {mon.level}"

        starter = f"**Species:** {mon.species_and_form}\n**Nickname:** {mon.nickname}\n**Level:** {mon.level}" \
            if mode == "builder" else f"**{mon.name}** (Lv. {mon.level} {mon.species_and_form})"

        lb = "\n"
        ret = [
            f"{starter}"
            f"{(' - ' + mon.hp_display(full_knowledge)) if kwargs.get('hp', True) and (mode != 'builder') else ''}\n"
            f"{' / '.join([str(self.emojis[g]) + ' ' + g for g in mon.types])} "
            f"{'(Terastallized)' if mon.terastallized else ''}\n"
            f"{('**Tera:** ' + str(self.emojis[mon.tera_type]) + ' ' + mon.tera_type + lb) if full_knowledge else ''}"
            f"**Gender:** {mon.gender.title()}\n"
            f"**Ability:** {mon.ability if full_knowledge else '?'}\n"
            f"**Item:** {self.display_item(mon.held_item) if full_knowledge else '?'}" +
            (f"\n\n{kwargs.get('stats_display', mon.stats_display(kwargs.get('stat_changes', True)))}"
             if kwargs.get('basic_stats', True) and (mode != 'builder') else "") +
            (f"\n{self.emojis[mon.status_emoji]} **{mon.status_condition}**" if mon.status_condition else "")
        ]
        if mode == "battle":
            ret.append(mon.battle_status)
        if mode == "builder":
            ret.append("**Moves:**\n" + none_list(['- ' + g.name for g in mon.moves], "\n"))
            ret.append(mon.full_stat_breakdown)
            ret.append(f"**Key:** `{mon.key()}`")
        return "\n\n".join(ret).strip("\n")

    def display_item(self, item: str):
        if emoji := self.emojis.get(f"PKMN{''.join(item.split())}"):
            return f"{emoji} {item}"
        return item

    def display_team(self, team: pk.Team) -> str:
        ret = [f"**{team.name}**"]
        if team.reflect:
            ret.append("- Protected by Reflect")
        if team.light_screen:
            ret.append("- Protected by Light Screen")
        if team.aurora_veil:
            ret.append("- Protected by Aurora Veil")

        if len(ret) == 1:
            ret.append("- no active status effects")
        return "\n".join(ret)

    def display_raid(self, raid: pk.TeraRaid, mode: str):
        mon = pk.find_mon(raid.species, use_bare=True)

        if mode == "default":
            ret = []
            if raid.game != "Both":
                ret.append(f"Only available in **{raid.game}**.")
            if raid.type not in ["Random", "Default"]:
                ret.append(f"Always **{self.display_type(raid.type)}-type**.")
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

            ret.append(f"**Moves:** {', '.join(self.display_move(pk.find_move(g), 'list') for g in raid.moves)}")

            return "\n".join(ret)

        elif mode == "drops":
            return "\n".join(str(g) for g in raid.drops)

        elif mode == "dex":
            return self.display_mon(mon, "dex")

    def add_energy_icons(self, txt: str):
        return re.sub(
            r"\{(" + ("|".join(tp.types)) + r")}",
            lambda x: str(self.emojis[x[0].strip("{}") + "Energy"]),
            txt
        )

    def display_card(self, card: tp.Card) -> discord.Embed:
        variant_notice = f"*Variant of {card.variant_of}.*\n\n" if card.variant_of else ""
        if isinstance(card, tp.PokemonCard):
            return Emol(self.emojis[f"{card.type}Energy"], hex_to_color(tp.type_colors[card.type])).con(
                card.name,
                d=f"{variant_notice}"
                  f"**{'Basic' if card.stage == 0 else ('Stage ' + str(card.stage))} | {card.hp} HP**\n" +
                  (f"\\- Evolves from **{card.evolves_from}**\n" if card.evolves_from else "") +
                  f"**Weakness:** {self.emojis[card.weakness + 'Energy'] if card.weakness else None}"
                  f"{' +20' if card.weakness else ''}\n"
                  f"**Retreat:** {str(self.emojis['ColorlessEnergy']) * card.retreat_cost}",
                fs=({
                    f"Ability: {card.ability.name}": self.add_energy_icons(card.ability.description)
                } if card.ability else {}) |
                {
                    f"{''.join(str(self.emojis[g + 'Energy']) for g in mv.energy_cost)} {mv.name}" +
                    (f" -- {mv.power}" if mv.power else ""):
                    self.add_energy_icons(mv.description) if mv.description else " " for mv in card.moves
                },
                footer=f"{card.id} ({tp.expansion_names[card.expansion]})",
                thumb=card.image_url
            )
        elif isinstance(card, tp.TrainerCard):
            return self.ball_emol("poke").con(
                card.name,
                d=f"{variant_notice}**[{card.category}]**\n{self.add_energy_icons(card.description)}",
                footer=f"{card.id} ({tp.expansion_names[card.expansion]})",
                thumb=card.image_url
            )

    def checked(self, b: bool):
        return self.emojis["checked"] if b else self.emojis["unchecked"]


def get_command_prefix(bot: Zeph, message: discord.Message):
    if not message.guild:
        return "z!"
    if not bot.server_settings.get(message.guild.id):
        return "z!"
    return bot.server_settings.get(message.guild.id).command_prefixes
