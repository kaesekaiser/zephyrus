import asyncio
import discord
import random
from classes.bot import Zeph
from classes.embeds import Emol
from classes.menus import Navigator
from discord.ext import commands

from pokemon import walker as pk


def pokeround(n: float | int):  # for whatever reason, Game Freak rounds down on 0.5
    return ceil(n) if n % 1 > 0.5 else floor(n)


class BattleTeamNavigator(Navigator):
    def __init__(self, bot: Zeph, emol: Emol, team: pk.Team, close_on_switch: bool = False,
                 allow_manual_close: bool = True):
        super().__init__(bot, emol, team.mons, 1, prev="🔼", nxt="🔽", timeout=180)
        self.team = team
        self.funcs["🔀"] = self.switch
        self.funcs[self.bot.emojis["search"]] = self.view_summary
        self.funcs[self.bot.emojis["moves"]] = self.view_moves
        if allow_manual_close:
            self.funcs[self.bot.emojis["no"]] = self.close
        self.switched = False
        self.timed_out = False
        self.close_on_switch = close_on_switch
        self.mode = "list"

    async def switch(self):
        if self.page != 1:
            self.team.switch(0, self.page - 1)
            self.switched = True
            if self.close_on_switch:
                self.closed_elsewhere = True
                await self.close()
            else:
                self.page = 1

    async def after_timeout(self):
        self.timed_out = True
        return await self.close()

    def view_summary(self):
        if self.mode == "summary":
            self.mode = "list"
        else:
            self.mode = "summary"

    def view_moves(self):
        if self.mode == "moves":
            self.mode = "list"
        else:
            self.mode = "moves"

    @property
    def mon(self):
        return pk.Mon.unpack(self.team.get_mon(self.page))

    def mon_info(self, team_index: int) -> str:
        mon = pk.Mon.unpack(self.team.mons[team_index])
        return f"{'**' if team_index == self.page - 1 else ''}" \
            f"{self.bot.display_mon(mon, 'inline')}" \
            f"{'**' if team_index == self.page - 1 else ''}"

    def con(self):
        mon = self.mon
        if self.mode == "summary":
            return self.emol.con(
                f"{mon.name}'s Status",
                d=self.bot.display_mon(mon)
            )
        if self.mode == "moves":
            return self.emol.con(
                f"{mon.name}'s Moves",
                d="\n".join(self.bot.display_move(g, 'partial') for g in mon.moves)
            )
        if self.mode == "list":
            return self.emol.con(
                "Team Status",
                d="\n".join(self.mon_info(n) for n in range(self.pgs))
            )


class Battle:
    """The catch-all for most functions related to Pokémon battling, including actually running battles."""
    def __init__(self, bot: Zeph, field: pk.Field, ctx: commands.Context, red: pk.Team, blu: pk.Team, **kwargs):
        self.bot = bot
        self.emol = kwargs.get("emol", self.bot.ball_emol())
        self.format = kwargs.get("format", "singles")
        self.field = field
        self.ctx = ctx
        self.channel = []  # text output goes here; printed and cleared at the end of mons' turns
        self.closed = False
        self.teams = [red, blu]
        self.active_mons = [pk.Mon.null() for _ in range(2 if self.format == "singles" else 4)]
        self.sleep_time = kwargs.get("sleep_time", 0.25)
        self.tera_enabled = kwargs.get("tera_enabled", True)
        self.winner = None

    def close(self):
        self.closed = True

    async def send(self, s: str, **kwargs):
        await self.emol.send(self.ctx, s, **kwargs)
        if self.sleep_time:
            await asyncio.sleep(self.sleep_time)

    async def print(self, skip_hp_check: bool = False):
        if self.channel:
            await self.send(self.channel[0], d="\n".join(self.channel[1:]))
            self.channel.clear()
            if not skip_hp_check:
                for mon in self.active_mons:
                    if mon.hpc <= 0:
                        if not self.teams[mon.team_id].can_fight:
                            self.winner = int(not mon.team_id)
                            return
                        await self.prompt_switch(mon.team_id)

    def send_out_lead_quietly(self, pos: int, print_recall: bool = True):
        if self.format == "singles":
            team = pos
        else:
            team = pos // 2
        if self.active_mons[pos].hpc and self.active_mons[pos].species.name != "NULL":
            manual_switch = True
            if print_recall:
                self.channel.append(f"That's enough, {self.active_mons[pos].name}!")
        else:
            manual_switch = False
        mon = self.active_mons[pos] = pk.Mon.unpack(self.teams[team].lead)
        if manual_switch:
            mon.just_manually_switched = True
        mon.team_id = team
        self.channel.append(f"Go! {mon.name}!")
        self.print_ability(mon, only_if_needed=True)
        if mon.ability == "Drizzle":
            self.change_weather(pk.rain, duration=(8 if mon.held_item == "Damp Rock" else 5))

    async def call_out_lead(self, team: int, print_recall: bool = True):
        self.send_out_lead_quietly(team, print_recall=print_recall)
        await self.print(skip_hp_check=True)

    async def prompt_switch(self, team: int, browsing: bool = False, print_recall: bool = True):
        self.teams[team].update_mon(self.active_mons[team])
        bat = BattleTeamNavigator(self.bot, self.emol, self.teams[team], True, browsing)
        await bat.run(self.ctx)
        if bat.timed_out:
            raise commands.CommandError("Switch prompt timed out.")
        if (not bat.switched) and (not browsing):
            raise commands.CommandError("Switching is required here.")
        if not browsing:
            await self.call_out_lead(team, print_recall=print_recall)
        return bat

    def can_tera(self, mon: pk.Mon):
        return self.tera_enabled and not mon.terastallized

    def move_select(self, mon: pk.Mon):
        return self.emol.con(
            f"What will {mon.name} do?",
            d="\n".join(self.bot.display_move(g, 'inline') for g in mon.moves) +
              (f"\n\n[ {self.bot.emojis[mon.tera_type]} **`      TERASTALLIZE      `** "
               f"{self.bot.checked(mon.activating_tera)} ]" if self.can_tera(mon) else "")
        )

    def priorities(self, mon: pk.Mon):
        move = mon.selection.unpack()
        return (
            move.priority,
            0,  # will eventually include effects which cause a mon to go earlier or later within the priority bracket
            (-self.invisible_stat(mon, "spe") if self.field.trick_room else self.invisible_stat(mon, "spe")),
            random.random()
        )

    async def turn(self):
        """One complete turn of a single battle."""
        async def select_move(r: pk.Mon):
            if r.can_move:
                mess = await self.ctx.send(embed=self.move_select(r))
                try:
                    def pred(m: discord.Message):
                        return m.channel == self.ctx.channel and m.author == self.ctx.author and \
                               r.retrieve_move(m.content)

                    while True:
                        user_input = await self.bot.wait_for("message", timeout=300, check=pred)
                        if (move := r.retrieve_move(user_input.content)).name == "Status":
                            await BattleStatusNavigator(self.bot, self).run(self.ctx)
                            mess = await self.ctx.send(embed=self.move_select(r))
                            continue
                        if (move.name == "Terastallize") and self.can_tera(r):
                            r.activating_tera = not r.activating_tera
                            await mess.edit(embed=self.move_select(r))
                            continue
                        if move.name == "Switch":
                            bat = await self.prompt_switch(mon.team_id, True)
                            if not bat.switched:
                                mess = await self.ctx.send(embed=self.move_select(r))
                                continue
                        break
                except asyncio.TimeoutError:
                    await self.send("Battle timed out.")
                    return self.close()
                r.selection = move  # pk.PackedMove
                if r.selection.name == "Exit":
                    await self.send("Exiting.")
                    return self.close()
            elif r.resting:
                await self.send(f"{r.name} is resting.")
            else:
                await self.send(f"{r.name} will use {r.selection.name}.")

        # move selection
        for mon in self.active_mons:
            await select_move(mon)
            if self.closed:
                return

        # setup
        self.start_of_turn()
        await self.print()

        # go
        for mon in reversed(sorted(self.active_mons, key=lambda c: self.priorities(c))):
            if mon.hpc > 0:
                self.use_move(mon, self.active_mons[not mon.team_id], mon.selection)
                await self.print()

            if self.winner is not None:
                return self.close()

            if mon.just_manually_switched == -1:
                self.channel.append(f"{mon.name} went back to its Trainer!")
                await self.prompt_switch(mon.team_id, print_recall=False)
                await self.print()

        self.end_of_turn()
        await self.print()

        if self.winner is not None:
            return self.close()

        # show the field status
        await self.send(
            "Status",
            d="\n\n".join(self.bot.display_mon(g, "turn_status") for g in self.active_mons)
        )

    def start_of_turn(self):
        """Everything done at the start of a turn, before any moves are executed."""
        def one_way(r: pk.Mon):
            if r.activating_tera:
                r.activating_tera = False
                r.terastallize()
                self.channel.append(f"{r.name} terastallized to the {r.tera_type} type!")
            if r.raging:
                if not r.selection.unpack().rage:
                    r.raging = False
            if r.thrashing:
                if not r.selection.unpack():
                    r.thrashing = False
                    r.thrash_counter = 0

        for mon in self.active_mons:
            one_way(mon)

    def end_of_turn(self):
        """Everything done at the end of a complete turn."""
        def one_way(r: pk.Mon):
            if r.charging:
                if r.has_charged:
                    r.charging = False
                    r.has_charged = False
                else:  # this ensures that a mon can never "charge" a two-turn attack for multiple turns
                    r.has_charged = True
            if r.resting:
                if r.has_rested:
                    r.resting = False
                    r.has_rested = False
                else:
                    r.has_rested = True
            if r.drowsy:
                if r.almost_drowsy:
                    r.drowsy = False
                    r.almost_drowsy = False
                    if not r.status_condition:
                        r.apply(pk.StatusEffect(100, pk.asleep))
                        self.channel.append(f"{r.name} fell asleep!")
                else:
                    r.almost_drowsy = True
            if r.flying:
                if r.has_flown:
                    r.flying = False
                    r.has_flown = False
                else:
                    r.has_flown = True
            if r.digging:
                if r.has_dug:
                    r.digging = False
                    r.has_dug = False
                else:
                    r.has_dug = True
            if r.enduring:
                r.enduring = False
            if r.protecting:
                r.protecting = False
            if r.flinching:
                r.flinching = False

            if r.status_condition == pk.burned:
                self.inflict(r, max(floor(r.hp / 16), 1), "damage from its burn")
            elif r.status_condition == pk.poisoned:
                self.inflict(r, max(floor(r.hp / 16), 1), "damage from poison")
            elif r.status_condition == pk.badly_poisoned:
                self.inflict(r, max(floor(r.hp * (r.stat_con_time + 1) / 16), 1), "damage from poison")
                r.stat_con_time += 1
            if r.hpc <= 0:
                return

            if r.seeded:
                dmg = self.inflict(r, max(floor(r.hp / 8), 1), "damage from Leech Seed")
                self.heal(self.active_mons[not r.team_id], dmg)
            if r.hpc <= 0:
                return

            if r.bound:
                self.inflict(
                    r, max(floor(r.hp / (6 if r.binding_banded else 8)), 1),
                    f"binding damage from {r.bound}"
                )
                r.bind_timer -= 1
                if r.bind_timer == 0:
                    r.bound = False
                    r.binding_banded = False
            if r.hpc <= 0:
                return

            if r.ability == "Speed Boost" and not r.just_manually_switched:
                self.print_ability(r)
                self.apply(pk.StatChange(100, {"spe": 1}), r)

            if r.just_manually_switched:
                r.just_manually_switched = False

        if self.field.weather_timer > 0:
            self.field.weather_timer -= 1
            if self.field.weather_timer <= 0:
                self.channel.append(pk.weather_end[self.weather])
                self.change_weather(None)
            else:
                self.channel.append(pk.weather_continue[self.weather])
                for mon in self.active_mons:
                    self.weather_effects(mon)
        if self.field.trick_room:
            self.field.trick_room -= 1
            if self.field.trick_room == 0:
                self.channel.append(f"The effects of Trick Room faded!")

        for mon in self.active_mons:
            one_way(mon)

        for team in self.teams:
            if team.reflect:
                team.reflect -= 1
                if team.reflect == 0:
                    self.channel.append(f"{team.name}'s Reflect wore off!")
            if team.light_screen:
                team.light_screen -= 1
                if team.light_screen == 0:
                    self.channel.append(f"{team.name}'s Light Screen wore off!")
            if team.aurora_veil:
                team.aurora_veil -= 1
                if team.aurora_veil == 0:
                    self.channel.append(f"{team.name}'s Aurora Veil wore off!")

    @staticmethod
    def crit_chance(n):
        return 0 if n < 0 else 1/24 if n == 0 else 1/8 if n == 1 else 1/2 if n == 2 else 1

    def inhibitors(self, a: pk.Mon):
        """Things that can prevent a mon from moving at all on their turn."""
        if a.resting:
            self.channel.append(f"{a.name} is recharging.")
            return False

        # these need to be done before status effects are applied:
        # if a pokemon is paralyzed while in the air, it comes back down and can be hit for the remainder of the turn
        if a.has_dug:
            a.digging = False
        if a.has_flown:
            a.flying = False

        if a.status_condition == pk.frozen:
            if random.random() < 0.2:
                self.channel.append(f"{a.name} thawed out!")
                a.status_condition = None
            else:
                self.channel.append(f"{a.name} is frozen solid!")
                return False
        if a.status_condition == pk.asleep:
            if a.stat_con_time == 0:
                self.channel.append(f"{a.name} woke up!")
                a.status_condition = None
            else:
                self.channel.append(f"{a.name} is fast asleep.")
                a.stat_con_time -= 1
                return False
        if a.status_condition == pk.paralyzed:
            if random.random() < 0.5:
                self.channel.append(f"{a.name} is paralyzed! It can't move!")
                return False

        if a.flinching:
            self.channel.append(f"{a.name} flinched!")
            return False
        if a.confused:  # CHECK *AFTER* NON-VOLATILE STATUS CONDITIONS / FLINCH
            a.confusion_time -= 1
            if a.confusion_time:
                self.channel.append(f"{a.name} is confused!")
                if random.random() < 1/3:
                    damage = max(
                        floor(self.blind_damage(a.atk_base, a.dfn_base, 40, a.level) * random.randrange(85, 101) / 100),
                        1
                    )
                    self.channel.append("It hurt itself in its confusion!")
                    self.inflict(a, damage)
                    return False
            else:
                self.channel.append(f"{a.name} snapped out of its confusion!")

        return True

    def but_it_failed(self, a: pk.Mon, d: pk.Mon, m: pk.Move):
        """Things that prevent a move from continuing after being called (such as the charging of two-turn moves)."""
        if m.two_turn and not a.charging:
            self.channel.append(pk.two_turn_texts[m.name].format(name=a.name))
            if not (m.solar and self.weather == pk.sun):
                a.charging = True
                return False
        if m.fly:
            if a.has_flown:
                a.flying = a.has_flown = False
            else:
                a.flying = True
                return self.channel.append(f"{a.name} flew up high!")
        if m.dig:
            if a.has_dug:
                a.digging = a.has_dug = False
            else:
                a.digging = True
                return self.channel.append(f"{a.name} burrowed its way underground!")
        if m.leech_seed and pk.grass in d.types:
            return self.channel.append("But it failed!")
        if m.used_in_succession:
            if (random.random() > 1 / (3 ** min(a.successive_uses, 6))) and (a.last_used == m.name):
                self.channel.append("But it failed!")
                a.successive_uses = 0  # reset the counter if it fails. i almost forgot to include this critical step
                return False
            a.successive_uses += 1
        else:
            a.successive_uses = 0
        if m.weather and (m.weather == self.weather):
            return self.channel.append("But it failed!")
        if m.mimic and (not d.last_used or d.last_used in ["Sketch", "Transform", "Struggle", "Metronome", "Chatter"]):
            return self.channel.append("But it failed!")
        if m.fake_out and bool(a.last_used):
            return self.channel.append("But it failed!")
        if m.add_type and (m.add_type in d.types):
            return self.channel.append(f"{d.name} is already {m.add_type}-type!")
        if m.change_type and (d.ability == "Multitype"):
            return self.channel.append(f"{d.name}'s type cannot be changed!")
        if m.powder_based and (pk.grass in d.types or d.ability == "Overcoat" or d.held_item == "Safety Goggles"):
            return self.channel.append(f"{d.name} is immune to powder moves!")
        if m.reflect and self.teams[a.team_id].reflect:
            return self.channel.append("Reflect is already in effect!")
        if m.light_screen and self.teams[a.team_id].light_screen:
            return self.channel.append("Light Screen is already in effect!")
        if m.aurora_veil:
            if self.weather not in [pk.hail, pk.snow]:
                return self.channel.append("But it failed!")
            if self.teams[a.team_id].aurora_veil:
                return self.channel.append("Aurora Veil is already in effect!")
        if m.belly_drum:
            if a.stat_stages["atk"] == 6:
                return self.channel.append(f"{a.name}'s Attack is already maximized!")
            if a.hpc <= floor(a.hp / 2):
                return self.channel.append("But it failed!")
        if m.switch_self and m.fails_if_cant_switch:
            if not self.teams[a.team_id].can_fight:
                return self.channel.append("There are no party Pok\u00e9mon to switch to!")
        if m.focus_energy and a.focused_energy:
            return self.channel.append(f"{a.name} is already pumped!")
        if m.dream_eater and d.status_condition != pk.asleep:
            return self.channel.append("But it failed!")
        return True

    def accuracy_check(self, a: pk.Mon, d: pk.Mon, m: pk.Move, silent: bool = False):
        if m.hits_in_rain:
            if self.weather == pk.sun:
                m.accuracy = 50
            elif self.weather == pk.rain:
                m.accuracy = 0
        if m.hits_in_hail:
            if self.weather == pk.hail:
                m.accuracy = 0
        if m.stomp and d.minimized:
            m.accuracy = 0

        if m.poison_never_miss and pk.poison in a.types:
            m.accuracy = 0
        else:
            # SEMI-INVULNERABILITY
            if d.flying and not m.can_hit_fly:
                if not silent:
                    self.channel.append(f"{d.name} avoided the attack!")
                return False
            if d.digging and not m.can_hit_dig:
                if not silent:
                    self.channel.append(f"{d.name} avoided the attack!")
                return False

        if d.ability == "Snow Cloak" and self.weather in [pk.snow, pk.hail]:
            m.accuracy *= 0.8
        if d.ability == "Sand Veil" and self.weather == pk.sandstorm:
            m.accuracy *= 0.8

        if (m.category != pk.status or m.still_typed) and d.eff(m.type) == 0:
            if not silent:
                self.channel.append(f"It doesn't affect {d.name}...")
            return False
        if d.protecting and m.can_protect:
            if not silent:
                self.channel.append(f"{d.name} protected itself!")
            return False
        if m.ohko and (a.level < d.level or random.random() > (a.level - d.level + 30) / 100):
            if not silent:
                self.channel.append(f"{a.name}'s attack missed!")
            return False
        if m.accuracy and not m.ohko:
            if random.random() > (m.accuracy / 100 * a.stat_level("acc", -d.stat_stages["eva"])):
                if not silent:
                    self.channel.append(f"{a.name}'s attack missed!")
                return False

        if m.type == pk.fire and d.ability == "Flash Fire":
            if not silent:
                self.print_ability(d)
                self.channel.append(f"{d.name}'s Fire-type moves were powered up!")
            d.has_activated_ability = True
            return False

        return True

    def set_up_move(self, a: pk.Mon, m: pk.Move):
        """Things which happen immediately before using a move, once you know the mon can move."""
        if a.ability == "Protean" and not a.has_activated_ability:
            a.type1 = m.type
            a.type2 = None
            a.type3 = None
            a.has_activated_ability = True
            self.print_ability(a)
            self.channel.append(f"{a.name} became {m.type}-type!")

    def use_move(self, a: pk.Mon, d: pk.Mon, move: pk.PackedMove):
        """One single mon's turn."""
        if move.name == "Switch":
            return self.send_out_lead_quietly(a.team_id)

        if not self.inhibitors(a):
            return

        m = move.unpack()  # creating an actual Move object from the storage object

        self.set_up_move(a, m)

        self.channel.append(f"{a.name} used **{m.name}**!")
        a.last_used = m.name
        if not (m.two_turn and a.has_charged):  # don't deduct 2 PP for two-turn moves
            move.ppc -= 1  # deduct from the stored PackedMove object rather than the Move itself

        if not self.but_it_failed(a, d, m):
            return

        if not self.accuracy_check(a, d, m):
            if m.crash:
                self.inflict(a, floor(a.hp / 2), "crash damage")
            return

        # MOVE CONNECTS
        self.move_conditionals(a, d, m)

        if m.category != pk.status and not (m.ohko or m.exact_damage):
            if d.eff(m.type) > 1:
                self.channel.append("It's super effective!")
            elif d.eff(m.type) < 1:
                self.channel.append("It's not very effective...")

        if m.multi2:
            strikes = 2
        elif m.multi25:
            if a.ability == "Skill Link":
                strikes = 5
            elif a.held_item == "Loaded Dice":
                strikes = random.choice([4, 5])
            else:
                strikes = random.choice([2, 2, 3, 3, 4, 5])
        elif m.triple_kick:
            if a.ability == "Skill Link" or a.held_item == "Loaded Dice":
                strikes = 3
            else:
                strikes = 1
                while strikes < 3 and self.accuracy_check(a, d, m, silent=True):
                    strikes += 1
        elif m.population_bomb:
            if a.ability == "Skill Link":
                strikes = 10
            elif a.held_item == "Loaded Dice":
                strikes = random.randrange(4, 11)
            else:
                strikes = 1
                while strikes < 10 and self.accuracy_check(a, d, m, silent=True):
                    strikes += 1
        else:
            strikes = 1

        strikes_done = 0

        for x in range(strikes):
            if m.category != pk.status:
                if m.triple_kick:
                    m2 = m.copy()
                    m2.power = m.power + x * m.power
                    damage = self.strike_damage(a, d, m2)
                else:
                    damage = self.strike_damage(a, d, m)
                damage_done = self.inflict(d, damage, swipe=m.false_swipe)

                self.move_user_effects(a, d, m, damage_done)

                strikes_done += 1

                if d.hpc <= 0:
                    return self.hit_x_times(strikes_done, m)  # exit before applying any secondary effects

                if m.contact:
                    self.contact(a, d)
                if d.hpc <= 0 or a.hpc <= 0:
                    return self.hit_x_times(strikes_done, m)  # try to exit again
            else:
                self.move_user_effects(a, d, m, 0)

            self.move_target_effects(a, d, m)

        return self.hit_x_times(strikes_done, m)

    def move_conditionals(self, a: pk.Mon, d: pk.Mon, m: pk.Move):
        """Changes to a move's power, type, etc. before execution."""
        if m.thrash:
            a.thrashing = True
            a.thrash_counter += 1
        else:
            a.thrash_counter = 0

        if m.brine and d.hpc <= d.hp / 2:
            m.power *= 2
        if m.can_hit_fly and d.flying:
            m.power *= 2
        if m.can_hit_dig and d.digging:
            m.power *= 2

        if self.weather == pk.sun:
            if m.type == pk.fire:
                m.power *= 1.5
            if m.type == pk.water:
                m.power *= 0.5
        if self.weather == pk.rain:
            if m.type == pk.fire:
                m.power *= 0.5
            if m.type == pk.water:
                m.power *= 1.5
            if m.solar:
                m.power *= 0.5
        if self.weather == pk.hail:
            if m.solar:
                m.power *= 0.5
        if self.weather == pk.sandstorm:
            if m.solar:
                m.power *= 0.5

        if m.tera_blast:
            if a.terastallized:
                m.type = a.tera_type
            if self.invisible_stat(a, "atk") > self.invisible_stat(a, "spa"):
                m.category = pk.physical

        if m.weight_based:
            cutoffs = {0: 20, 10: 40, 25: 60, 50: 80, 100: 100, 200: 120}
            m.power = cutoffs[max(g for g in cutoffs if d.weight >= g)]

        if a.ability == "Flash Fire" and a.has_activated_ability is True and m.type == pk.fire:
            m.power *= 1.5  # technically it's more correct to change the mon's attacking stat. but this is easier

    def hit_x_times(self, x: int, m: pk.Move):
        """Appends a 'hit x times!' statement to the channel if the move hits more than once. Called on exiting."""
        if any([m.multi2, m.multi25, m.triple_kick, m.population_bomb]):
            self.channel.append(f"Hit {x} {plural('time', x)}!")

    @staticmethod
    def blind_damage(atk: int, dfn: int, pwr: int, level: int):
        """Base damage for an attack, given attack and defense stats, move power, and attacker level."""
        return floor(floor(floor(2 * level / 5 + 2) * pwr * atk / dfn / 50) + 2)

    def strike_damage(self, a: pk.Mon, d: pk.Mon, m: pk.Move):
        """Actual damage done in one strike given attacker, defender, and move."""
        if m.exact_damage:
            return m.exact_damage
        if m.level_damage:
            return a.level
        if m.ohko:
            return d.hpc

        crit = random.random() < self.crit_chance(a.crt + m.raised_crit_ratio)

        # calculating damage based on category
        if m.psyshock:
            a_stat = "spa"
            d_stat = "def"
        elif m.category == pk.physical:
            a_stat = "atk"
            d_stat = "def"
        elif m.category == pk.special:
            a_stat = "spa"
            d_stat = "spd"
        else:  # should be no reason for this to happen, but jic
            return 0

        dam = self.blind_damage(
            self.invisible_stat(a, a_stat, (crit and a.stat_stages[a_stat] < 0)),
            self.invisible_stat(d, d_stat, (crit and d.stat_stages[d_stat] > 0)),
            m.power, a.level
        )

        if crit:
            if d.ability != "Battle Armor":
                self.channel.append("A critical hit!")
                dam *= 2 if a.ability == "Sniper" else 1.5

        if a.terastallized:
            stab = 1
            if m.type in a.original_types:
                stab += (1 if a.ability == "Adaptability" else 0.5)
            if m.type == a.tera_type:
                stab += 0.5
        else:
            if m.type in a.types:
                stab = 2 if a.ability == "Adaptability" else 1.5
            else:
                stab = 1

        dam = floor(pokeround(floor(dam * random.randrange(85, 101) / 100) * stab) * d.eff(m.type))
        mod = 1

        if a.status_condition == pk.burned and a.ability != "Guts" and m.category == pk.physical and not m.facade:
            dam = floor(dam / 2)  # applied before the final mod for some reason

        if m.stomp and d.minimized:
            mod *= 2
        if m.category == pk.physical and (self.teams[d.team_id].reflect or self.teams[d.team_id].aurora_veil):
            mod *= 0.5 if self.format == "singles" else (2732/4096)
        if m.category == pk.special and (self.teams[d.team_id].light_screen or self.teams[d.team_id].aurora_veil):
            mod *= 0.5 if self.format == "singles" else (2732/4096)

        return pokeround(max(1, dam * mod))

    def ability_on_field(self, ability: str) -> bool:
        return any(g.ability == ability for g in self.active_mons)

    def invisible_stat(self, mon: pk.Mon, stat: str, ignore_stat_changes: bool = False) -> int:
        mod = 1
        if stat == "atk":
            ret = mon.atk_without_sc if ignore_stat_changes else mon.atk
            if self.ability_on_field("Tablets of Ruin") and mon.ability != "Tablets of Ruin":
                mod *= 0.75
            return round(ret * mod)
        if stat == "spa":
            ret = mon.spa_without_sc if ignore_stat_changes else mon.spa
            if self.ability_on_field("Vessel of Ruin") and mon.ability != "Vessel of Ruin":
                mod *= 0.75
            return round(ret * mod)
        if stat == "def":
            ret = mon.dfn_without_sc if ignore_stat_changes else mon.dfn
            if self.ability_on_field("Sword of Ruin") and mon.ability != "Sword of Ruin":
                mod *= 0.75
            if pk.ice in mon.types and self.weather == pk.snow:
                mod *= 0.5
            return round(ret * mod)
        if stat == "spd":
            ret = mon.spd_without_sc if ignore_stat_changes else mon.spd
            if self.ability_on_field("Beads of Ruin") and mon.ability != "Beads of Ruin":
                mod *= 0.75
            return round(ret * mod)
        if stat == "spe":
            ret = mon.spe_without_sc if ignore_stat_changes else mon.spe
            if mon.ability == pk.weather_speed_abilities.get(self.weather, "x"):
                mod *= 2
            return round(ret * mod)

    def stats_display(self, mon: pk.Mon):
        return " / ".join(f"{self.invisible_stat(mon, g.lower())} {g}" for g in ["Atk", "Def", "SpA", "SpD", "Spe"])

    def inflict(self, mon: pk.Mon, dmg: int, s: str = "damage", swipe: bool = False, **kwargs):
        """Does damage to a mon. Returns the amount of damage done."""
        if mon.hpc <= 0:
            return 0
        start = mon.hpc
        mon.hpc -= dmg
        if swipe:
            if mon.hpc < 1:
                mon.hpc = 1
        elif mon.enduring:
            if mon.hpc < 1:
                mon.hpc = 1
                self.channel.append(f"{mon.name} endured the hit!")
        elif start == mon.hp and mon.ability == "Sturdy":
            if mon.hpc < 1:
                mon.hpc = 1
                self.print_ability(mon)
                self.channel.append(f"{mon.name} endured the hit!")
        else:
            if mon.hpc <= 0:
                mon.hpc = 0
                mon.status_condition = pk.fainted
        if kwargs.get("message"):
            self.channel.append(kwargs.get("message"))
        else:
            self.channel.append(f"{mon.name} took {start - mon.hpc} {s}!")
        if not mon.hpc:
            self.channel.append(f"{mon.name} fainted!")
        return start - mon.hpc

    def heal(self, mon: pk.Mon, amt: int, s: str = "HP"):
        if mon.hpc <= 0:
            return
        start = mon.hpc
        mon.hpc += amt
        if mon.hpc > mon.hp:
            mon.hpc = mon.hp
        self.channel.append(f"{mon.name} regained {mon.hpc - start} {s}!")

    @property
    def weather(self):
        return self.field.weather

    def change_weather(self, weather: str | None, duration: int = 5):
        self.field.weather = weather
        self.field.weather_timer = duration if weather else 0
        if weather:
            self.channel.append(pk.weather_start[weather])
        for mon in self.active_mons:
            if mon.ability == "Forecast":
                if txt := mon.change_form(pk.castform_weathers.get(weather, "")):
                    self.print_ability(mon)
                    self.channel.append(txt)

    def weather_effects(self, mon: pk.Mon):
        """End-of-turn weather effects for a mon."""
        if not (weather := self.weather):
            return
        if weather == pk.hail:
            if pk.ice not in mon.types and mon.held_item != "Safety Goggles" and \
                    mon.ability not in ["Ice Body", "Snow Cloak", "Magic Guard", "Overcoat"]:
                self.inflict(mon, max(floor(mon.hp / 16), 1), "damage from hail")
        if weather == pk.sandstorm:
            if not {pk.rock, pk.ground, pk.steel}.intersection(set(mon.types)) and mon.held_item != "Safety Goggles" \
                    and mon.ability not in ["Sand Force", "Sand Rush", "Sand Veil", "Magic Guard", "Overcoat"]:
                self.inflict(mon, max(floor(mon.hp / 16), 1), "damage from the sandstorm")

    def print_ability(self, mon: pk.Mon, only_if_needed: bool = False):
        additional_text = {
            "Vessel of Ruin": f"{mon.name} lowers the Special Attack of all other mons except itself!",
            "Sword of Ruin": f"{mon.name} lowers the Defense of all other mons except itself!",
            "Tablets of Ruin": f"{mon.name} lowers the Attack of all other mons except itself!",
            "Beads of Ruin": f"{mon.name} lowers the Special Defense of all other mons except itself!",
        }
        if only_if_needed and (mon.ability not in additional_text):
            return
        self.channel.append(f"= {mon.name}'s **{mon.ability}**! =")
        if mon.ability in additional_text:
            self.channel.append(additional_text[mon.ability])

    def print_item(self, mon: pk.Mon, use_up: bool = False):
        self.channel.append(f"= {mon.name}'s {self.bot.display_item(mon.held_item)}! =")
        if use_up:
            mon.held_item = "No Item"

    def apply(self, stat: pk.StatChange | pk.StatusEffect, mon: pk.Mon):
        if isinstance(stat, pk.StatChange):
            change = mon.apply(stat)
            for k, v in change.items():
                self.channel.append(pk.stat_change_text(mon, k, v))
        elif isinstance(stat, pk.StatusEffect):
            if stat.effect == pk.paralyzed and mon.ability == "Limber":
                self.print_ability(mon)
                self.channel.append(f"{mon.name} cannot be paralyzed!")
                return
            change = mon.apply(stat)
            if change:
                self.channel.append(change[0].format(name=mon.name))
                if mon.status_condition in pk.status_berries.get(mon.held_item, []):
                    self.print_item(mon, use_up=True)
                    self.channel.append(f"{mon.name} ate its Berry to heal its status condition!")
                    mon.status_condition = None

    def contact(self, a: pk.Mon, d: pk.Mon):
        if d.ability == "Static" and pk.electric not in a.types and random.random() < 0.3:
            self.print_ability(d)
            self.apply(pk.StatusEffect(100, pk.paralyzed), a)

    def move_user_effects(self, a: pk.Mon, d: pk.Mon, m: pk.Move, damage: int):
        """Secondary effects applied as soon as a move connects, even if d has fainted. Mostly self/field effects."""
        if d.raging and damage > 0:
            self.apply(pk.StatChange(100, {"atk": 1}), d)

        if m.user_stat_changes:
            self.apply(m.user_stat_changes, a)
        if m.reset_low_stats:
            for k, v in a.stat_stages.items():
                if v < 0:
                    a.stat_stages[k] = 0
            self.channel.append(f"{a.name}'s lowered stats were reset!")
        if m.reset_all_stats:
            for mon in self.active_mons:
                for k in mon.stat_stages:
                    mon.stat_stages[k] = 0
            self.channel.append("All stat changes were reset!")
        if m.recoil:
            self.inflict(a, max([1, floor(damage / m.recoil)]), "recoil damage")
        if m.absorbent:
            self.channel.append(f"{d.name} had its energy drained!")
            self.heal(a, max([1, floor(damage / 2)]))

        if m.weather:
            self.change_weather(m.weather, duration=(8 if a.held_item == pk.weather_extenders.get(m.weather) else 5))
        if m.must_recharge:  # this triggers if and only if the move lands, so it goes here
            a.resting = True
        if m.endure:
            a.enduring = True
            self.channel.append(f"{a.name} braced itself!")
        if m.protect:
            a.protecting = True
            self.channel.append(f"{a.name} protected itself!")
        if m.growth:
            n = 2 if self.weather == pk.sun else 1
            self.apply(pk.StatChange(100, {"atk": n, "spa": n}), a)
        if m.thrash:
            if a.thrash_counter > 2 or (a.thrash_counter == 2 and random.random() < 0.5):
                a.confused = True
                a.thrashing = False
                a.thrash_counter = 0
                self.channel.append(f"{a.name} became confused!")
        if m.rage:
            a.raging = True
        if m.mimic:
            new_move = pk.battle_moves[d.last_used].pack
            if mimic_index := a.has_move("Mimic"):
                a.moves[mimic_index - 1] = new_move
            a.selection = new_move
            return self.use_move(a, d, new_move)
        if m.half_heal:
            self.heal(a, floor(a.hp / 2))
        if m.full_heal:
            self.heal(a, a.hp)
        if m.reflect:
            self.teams[a.team_id].reflect = 5
            self.channel.append(f"Reflect strengthened {a.name}'s team against physical moves!")
        if m.light_screen:
            self.teams[a.team_id].light_screen = 5
            self.channel.append(f"Light Screen strengthened {a.name}'s team against special moves!")
        if m.aurora_veil:
            self.teams[a.team_id].aurora_veil = 5
            self.channel.append(f"Aurora Veil strengthened {a.name}'s team against physical and special moves!")
        if m.removes_barriers:
            self.teams[d.team_id].reflect = 0
            self.teams[d.team_id].light_screen = 0
            self.teams[d.team_id].aurora_veil = 0
        if m.trick_room:
            if self.field.trick_room:
                self.field.trick_room = 0
                self.channel.append("The effects of Trick Room were lifted!")
            else:
                self.field.trick_room = 5
                self.channel.append(f"{a.name} twisted the dimensions!")
        if m.belly_drum:
            if a.ability == "Contrary":
                a.stat_stages["atk"] = -6
            else:
                a.stat_stages["atk"] = 6
            self.inflict(
                a, floor(a.hp / 2),
                message=f"{a.name} cut its own HP by {floor(a.hp / 2)} and maximized its Attack!"
            )
        if m.minimize:
            a.minimized = True
        if m.curl:
            a.curled_up = True
        if m.focus_energy:
            self.channel.append(f"{a.name} is getting pumped!")
            a.focused_energy = True

        if m.switch_self:  # requires async, must be done outside of this command
            a.just_manually_switched = -1

    def move_target_effects(self, a: pk.Mon, d: pk.Mon, m: pk.Move):
        """Secondary/status effects applied at the end of a move. NOT performed if d is fainted."""
        if m.target_stat_changes:
            self.apply(m.target_stat_changes, d)
        if m.reset_target_stats:
            for k in d.stat_stages:
                d.stat_stages[k] = 0
            self.channel.append(f"{d.name}'s stat changes were reset!")

        if m.status_effect:
            invulnerables = {
                pk.burned: {pk.fire}, pk.paralyzed: {pk.electric}, pk.poisoned: {pk.poison, pk.steel},
                pk.badly_poisoned: {pk.poison, pk.steel}, pk.frozen: {pk.ice}
            }
            can_activate = (not d.status_condition) and \
                ((not invulnerables.get(m.status_effect.effect, set()).intersection(set(d.types))) or
                 (a.ability == "Corrosion" and m.status_effect.effect in [pk.poisoned, pk.badly_poisoned]))
            # 1) the mon is not already afflicted with something, and 2) either a) is not immune to the status effect,
            # or b) the attacker has the ability that allows them to poison them anyway
            if can_activate:
                self.apply(m.status_effect, d)
        if random.random() < m.confuse / 100:
            d.confused = True
            d.confusion_time = random.randrange(2, 6)  # snap out after 1-4 attacking turns; if 1 at start of turn, snap out
            self.channel.append(f"{d.name} became confused!")

        if d.status_condition not in [pk.asleep, pk.frozen]:  # flinch odds
            if m.flinch:
                if random.random() < m.flinch / 100:
                    d.flinching = True
            elif a.held_item in ["King's Rock", "Razor Fang"] and m.category != pk.status:
                if random.random() < 0.1:
                    d.flinching = True
            elif a.ability == "Stench" and m.category != pk.status:
                if random.random() < 0.1:
                    d.flinching = True

        if m.leech_seed:
            d.seeded = True
            self.channel.append(f"{d.name} was seeded!")
        if m.yawn:
            d.drowsy = True
            self.channel.append(f"{d.name} grew drowsy!")
        if m.binding and not d.bound:
            special_descriptions = {
                "Fire Spin": "became trapped in a whirlwind of fire!"
            }
            d.bound = m.name
            if a.held_item == "Binding Band":
                d.binding_banded = True
            if a.held_item == "Grip Claw":
                d.bind_timer = 7
            else:
                d.bind_timer = random.choice([4, 5])
            self.channel.append(f"{d.name} {special_descriptions.get(m.name, 'became bound by ' + m.name + '!')}")
        if m.add_type:
            d.type3 = m.add_type
            self.channel.append(f"{d.name} became {m.add_type}-type!")
        if m.change_type:
            d.type1 = None
            d.type2 = None
            d.type3 = m.change_type
            self.channel.append(f"{d.name} became pure {m.change_type}-type!")

    async def run(self):
        for team in self.teams:
            for mon in team.mons:
                if mon["gender"] == "random":
                    mon["gender"] = random.choice(["male", "female"])

        await self.call_out_lead(0)
        await self.call_out_lead(1)

        while (self.winner is None) and not self.closed:
            await self.turn()


class BattleStatusNavigator(Navigator):
    def __init__(self, bot: Zeph, battle: Battle):
        super().__init__(bot, battle.emol, [battle.field, *battle.active_mons], 1, timeout=180)
        self.battle = battle
        self.funcs[self.bot.emojis["no"]] = self.close

    def con(self):
        sel = self.table[self.page - 1]
        if isinstance(sel, pk.Field):
            return self.emol.con(
                "Field Status",
                d=f"{sel.status_screen}\n\n{self.bot.display_team(self.battle.teams[0])}"
                  f"\n\n{self.bot.display_team(self.battle.teams[1])}"
            )
        elif isinstance(sel, pk.Mon):
            return self.emol.con(
                sel.name,
                d=f"{self.bot.display_mon(sel, 'battle', stats_display=self.battle.stats_display(sel))}\n\n"
                  f"{self.bot.display_team(self.battle.teams[sel.team_id])}"
            )
