from cca import *


def space_out(n: int):
    return " " + str(n) if 0 <= n < 10 else str(n)


def move_str(m: pm.Move):
    return f"[ {getemoji(m.type.lower())} **``{pm.lengthen(m.name)} ({space_out(m.ppc)}/{space_out(m.pp)})``**" \
           f" {getemoji(m.category.lower())} ]"


def mon_str(mon: pm.Mon):
    return "\n".join(list(move_str(mon.moves[g]) for g in mon.moves))


def short_str(mon: pm.Mon):
    return f"┏**{mon.name}** ({mon.hpc}/{mon.hp})\n" \
           f"┗*lv{mon.level} {mon.speciesName}* {pm.genDict[mon.gender]} {pm.shortStats[mon.condit]}"


async def pokesay(s, **kwargs):
    print("hi a third time")
    if kwargs.get("emoji") is None:
        emoji = getemoji("poke")
    else:
        emoji = kwargs.get("emoji")
    await emolsay(emoji, s, hexcol(kwargs.get("col", "cf0000")), **kwargs)


class DiscordBattle(pm.Battle):
    def __init__(self, team1: pm.Team, team2: pm.Team, channel: discord.Channel):
        super().__init__(team1, team2)
        self.channel = channel
        self.quit = False

    async def say(self):
        await pokesay(self.desc[0], d="\n".join(self.desc[1:]))
        self.desc = []

    async def get_move(self, mon: pm.Mon):
        def check_move(c: discord.Message):
            return c.content.lower() in mon.lowerMoves or c.content.lower() in ["team", "quit"] or \
                   (c.content.lower()[:5] == "sudo " and c.content.lower()[5:] in pm.lowerMoves)

        if mon.twoTurn is not None:
            if mon.twoTurn in mon.moves:
                return mon.moves[mon.twoTurn]
            return pm.dc(pm.movedict[mon.twoTurn])

        while True:
            await pokesay(f"What will {mon.name} do?", d=mon_str(mon))
            move = await client.wait_for_message(timeout=600, author=self.teams[mon.team].author, channel=self.channel,
                                                 check=check_move)
            if move is None:
                self.quit = True
                return await pokesay("Timed out.")
            if move.content.lower() == "quit":
                self.quit = True
                return await pokesay("Quitting.")
            if move.content.lower()[:5] == "sudo ":
                move = move.content.lower()[5:]
                sudo = True
            else:
                move = move.content.lower()
                sudo = False
            if move == "team":
                while True:
                    await pokesay(mon.team, d="\n".join([short_str(pm.Mon(**g))
                                                         for g in list(self.teams[mon.team].mons.values())]),
                                  footer="To choose a mon, say that mon's name. To go back, say 'back'.")
                    action = await client.wait_for_message(timeout=600, author=self.teams[mon.team].author,
                                                           channel=self.channel, check=lambda c: c.content.lower() in
                                                           [g.lower() for g in self.teams[mon.team].mons] or
                                                           c.content.lower() == "back")
                    if action is None:
                        self.quit = True
                        return await pokesay("Timed out.")
                    if action.content.lower() == "back":
                        break
                    thismon = pm.Mon(**[g for g in list(self.teams[mon.team].mons.values())
                                        if g["nick"].lower() == action.content.lower()][0])
                    sad = thismon.sd()
                    if thismon.name != mon.name:
                        await pokesay(sad["s"], d=sad["d"] + "\n\n" + mon_str(thismon),
                                      footer="To switch, say 'switch'. To go back, say 'back'.")
                        lis = ["switch", "back"]
                    else:
                        await pokesay(sad["s"], d=sad["d"] + "\n\n" + mon_str(thismon),
                                      footer="To go back, say 'back'.")
                        lis = ["back"]
                    action = await client.wait_for_message(timeout=600, author=self.teams[mon.team].author,
                                                           channel=self.channel, check=lambda c: c.content.lower()
                                                           in lis)
                    if action is None:
                        self.quit = True
                        return await pokesay("Timed out.")
                    if action.content.lower() == "switch":
                        mon.switching = thismon.name
                        return pm.dc(pm.confusedMove)
            elif mon.valid_move(move, sudo):
                if move in mon.lowerMoves:
                    return mon.moves[mon.lowerMoves[move]]
                return pm.dc(pm.movedict[pm.lowerMoves[move]])
            elif move.lower() in mon.lowerMoves:
                await pokesay("Not enough PP.")
            else:
                await pokesay("That's not a valid move.")
            await asyncio.sleep(1)

    async def move(self, a: pm.Mon, d: pm.Mon, m: pm.Move):
        if a.switching is not None:
            self.teams[a.team].mons[a.name] = a.pack()
            await pokesay(f"{a.name}, come back!")
            a.__init__(**self.teams[a.team].mons[a.switching])
            await asyncio.sleep(1)
            await pokesay(f"Go! {a.name}!")
        else:
            self.attack(a, d, m)
            self.post_attack(a, d)
            await self.say()
        await asyncio.sleep(2)

    async def turn(self):
        await pokesay(f"TURN {self.turnNo}")
        await asyncio.sleep(1)
        mp = await self.get_move(self.p)
        if self.quit:
            return
        mo = await self.get_move(self.o)
        if self.quit:
            return
        await asyncio.sleep(1)
        if self.priority(self.p, self.o, mp, mo) == "p":
            await self.move(self.p, self.o, mp)
            if self.p.hpc <= 0 or self.o.hpc <= 0:
                return
            await self.move(self.o, self.p, mo)
            if self.p.hpc <= 0 or self.o.hpc <= 0:
                return
        else:
            await self.move(self.o, self.p, mo)
            if self.p.hpc <= 0 or self.o.hpc <= 0:
                return
            await self.move(self.p, self.o, mp)
            if self.p.hpc <= 0 or self.o.hpc <= 0:
                return
        await self.end_of_turn(self.p, self.o)

    async def end_of_turn(self, *mons: pm.Mon):
        self.desc = [f"END OF TURN {self.turnNo}"]
        if self.weatherTime > 0:
            self.weatherTime -= 1
            if self.weatherTime == 0:
                ends = {pm.sun: "The sunlight faded.", pm.rain: "The rain stopped.", pm.snow: "The hail stopped.",
                        pm.sandstorm: "The sandstorm subsided."}
                self.desc.append(ends[self.weather])
                self.weather = None
            else:
                if self.weather == pm.sun:
                    self.desc.append("The sunlight is strong.")
                    for mon in mons:
                        if mon.ability in ["Dry Skin", "Solar Power"]:
                            self.desc.append(mon.print_abil())
                            self.dmg(mon, int(floor(mon.hp / 8)))
                elif self.weather == pm.rain:
                    self.desc.append("Rain continues to fall.")
                    for mon in mons:
                        if mon.ability == "Dry Skin":
                            self.desc.append(mon.print_abil())
                            self.heal(mon, int(floor(mon.hp / 8)))
                        if mon.ability == "Rain Dish":
                            self.desc.append(mon.print_abil())
                            self.heal(mon, int(floor(mon.hp / 16)))
                        if mon.ability == "Hydration" and mon.condit is not None:
                            self.desc.append(mon.print_abil())
                            self.desc.append(f"{mon.name} was cured of its status condition!")
                            mon.condit = None
                elif self.weather == pm.snow:
                    self.desc.append("Hail continues to fall.")
                    for mon in mons:
                        if pm.ice not in mon.types() and mon.heldItem != "Safety Goggles" and\
                                mon.ability not in ["Ice Body", "Snow Cloak", "Slush Rush", "Overcoat", "Magic Guard"]:
                            self.dmg(mon, int(floor(mon.hp / 16)), "hail damage")
                        if mon.ability == "Ice Body":
                            self.desc.append(mon.print_abil())
                            self.heal(mon, int(floor(mon.hp / 16)))
                elif self.weather == pm.sandstorm:
                    self.desc.append("The sandstorm rages.")
                    for mon in mons:
                        if pm.rock not in mon.types() and pm.ground not in mon.types() and pm.steel not in mon.types()\
                                and mon.ability not in ["Sand Force", "Sand Rush", "Sand Veil", "Magic Guard",
                                                        "Overcoat"] and mon.heldItem != "Safety Goggles":
                            self.dmg(mon, int(floor(mon.hp / 16)), "sandstorm damage")
        self.post_attack(*mons)
        for mon in mons:
            if mon.aquaRing:
                self.heal(mon, int(floor(mon.hp / 16)), "HP from its Aqua Ring")
        await self.say()
        for mon in mons:
            mon.protecting = False
            await asyncio.sleep(1)
            await pokesay(**mon.sd(False))
        await asyncio.sleep(3)
        self.turnNo += 1

    def post_attack(self, *mons: pm.Mon):
        for mon in mons:
            for move in list(mon.moves.values()):
                if "weatherBall" in move.effs:
                    move.type = pm.fire if self.weather == pm.sun else pm.water if self.weather == pm.rain else\
                        pm.rock if self.weather == pm.sandstorm else pm.ice if self.weather == pm.snow else pm.normal
            if mon.species.name == "Castform" and mon.ability == "Forecast":
                if mon.type1 != pm.castForms.get(self.weather, pm.normal):
                    mon.type1 = pm.castForms.get(self.weather, pm.normal)
                    self.desc.append(mon.print_abil())
                    self.desc.append(f"{mon.name} became {mon.type1}-type!")

    async def run(self):
        await pokesay(f"{self.teamNames[1]} sent out {self.o.name}!")
        await asyncio.sleep(1)
        await pokesay(f"Go! {self.p.name}!")
        await asyncio.sleep(1)
        while True:
            await self.turn()
            if self.quit:
                return
            if self.p.hpc <= 0:
                return await pokesay(f"{self.p.name} fainted!")
            elif self.o.hpc <= 0:
                return await pokesay(f"{self.o.name} fainted!")


@client.command(pass_context=True, aliases=["pkmn", "poke", "pk"])
async def pokemon(ctx: Context, func=None, *args):
    print("hi")
    if func is None:
        print("hi again")
        await pokesay("Fucking Pokémon.",
                             d="I don't own any of the content in here. Most of it belongs to Nintendo. The emblems I "
                               "use for the types came from Wergan on DeviantArt - except for the Dragon-type emblem, "
                               "which came from the Pokémon Trading Card Game. Some of the code is ripped from "
                               "Pokémon Showdown.\n\nIf you want to know how to actually run this command, use "
                               "``z!pokemon help``.",
                             footer="Type emblems: "
                                    "https://wergan.deviantart.com/art/Pokemon-Artefact-All-types-632308931")

    lowerArgs = " ".join([g.lower() for g in args])

    if func not in ["help", "move", "dex", "type", "eff", "dam", "trees", "whatwill", "run"]:
        return await errsay("Unrecognized function.")

    if func == "help":
        await pokesay("HELP",
                      d="``z!pokemon move <move>`` -> displays data for a move\n"
                        "``z!pokemon dex <species OR dex no.> [form]`` -> displays species data for a mon\n"
                        "``z!pokemon dex search <criteria>`` -> returns a list of mons fitting the criteria\n"
                        "    *``z!pokemon dex search help`` to see a list of criteria*\n"
                        "``z!pokemon type <type>`` -> displays effectiveness of <type>\n"
                        "``z!pokemon eff <mon>`` -> displays effectiveness of all types against <mon>\n"
                        "``z!pokemon dam <attacker> | <defender> | <move>`` -> calculates damage done to <defender> by "
                        "<attacker> using <move>")

    if func == "move":
        if lowerArgs not in pm.lowerMoves:
            return await errsay("Unrecognized move.")
        move = pm.movedict[pm.lowerMoves[lowerArgs]]
        if "func" in move.effs:
            return await errsay("Unrecognized move.")
        await pokesay(**move.sd(), col=pm.colors[move.type],
                      emoji=getemoji(move.type.lower()))

    if func == "trees":
        lowerTrees = {g.lower(): g for g in pm.trees}
        if lowerArgs in lowerTrees:
            mon = pm.getMon(lowerTrees[lowerArgs], **pm.trees[lowerTrees[lowerArgs]].unpack())
        else:
            mon = pm.get_treemons(1)
            # mon.hpc -= 50
            # mon.moves[1].ppc -= 3
            # mon.condit = pm.poisoned
            # mon = pm.Mon(**mon.__dict__())
        sad = mon.sd()
        return await pokesay(sad['s'], d=sad['d'] + "\n\n" + mon_str(mon))

    if func == "whatwill":
        bat = DiscordBattle(pm.Team("lol", *pm.get_treemons(3), author=ctx.message.author),
                            pm.Team("kek", *pm.get_treemons(3), author=ctx.message.author), ctx.message.channel)
        move = await bat.get_move(bat.teams["lol"][0])
        await pokesay(**move.sd())

    if func == "run":
        bat = DiscordBattle(pm.Team("Blue", *pm.get_treemons(3), author=ctx.message.author),
                            pm.Team("Cynthia", *pm.get_treemons(3), author=ctx.message.author), ctx.message.channel)
        await bat.run()

    if func == "dex":
        if lowerArgs == "":
            return await errsay("No function input.")

        try:
            int(lowerArgs)
        except ValueError:
            try:
                mon = pm.getMon(lowerArgs)
            except ValueError as v:
                if "form" in str(v):
                    return await errsay(v)
                if lowerArgs.split()[0] != "search":
                    if lowerArgs.split()[0] != "random":
                        di = {key: wr.levenshtein(lowerArgs, key.lower()) for key in pm.natDex}  # BEST GUESS
                        do = [key for key in di if di[key] == min(list(di.values()))]
                        if len(do) == 1:
                            return await pokesay(**pm.Mon(pm.cap(do[0])).speciesSD())
                        if lowerArgs == "nidoran":
                            return await errsay("Nidoran is split between two entries, NidoranF and NidoranM.")
                        return await errsay("Unrecognized mon. Did you mean {}?".format(do[0]))

                    no = randrange(len(pm.natDex))  # RANDOM
                    return await pokesay(**pm.Mon(list(pm.natDex.keys())[no]).speciesSD())

                if len(args) == 1:  # SEARCH
                    return await errsay("No criteria specified.")
                if lowerArgs.split()[1] == "help":
                    return await pokesay("Search Criteria",
                                         d="``name:<str>`` finds mons whose names start with <str>\n"
                                           "``type:<type>`` finds <type>-type mons\n"
                                           "``mega`` finds mons with Mega Evolutions\n"
                                           "``alolan`` finds mons with Alolan forms\n"
                                           "``gen:<no>`` finds mons from generation <no>")

                def search(mon: pm.Mon, name="", types=(), mega=False, alolan=False, gen=None):
                    for i in types:
                        if i not in [str(mon.type1), str(mon.type2)]:
                            return False
                    if mega and ("Mega" not in mon.species.forms and "Mega-X" not in mon.species.forms):
                        return False
                    if alolan and "Alolan" not in mon.species.forms:
                        return False
                    if gen is not None and mon.generation != gen:
                        return False
                    return mon.species.name.lower()[:len(name)] == name.lower()

                try:
                    nm = [pm.cap(g.split(":")[1]) for g in lowerArgs.split() if g.split(":")[0] == "name"][0]
                except IndexError:
                    nm = ""
                ts = [pm.cap(g.split(":")[1]) for g in lowerArgs.split() if g.split(":")[0] == "type"][:2]
                mg = "mega" in lowerArgs.split()
                al = "alolan" in lowerArgs.split()
                try:
                    gn = [int(g.split(":")[1]) for g in lowerArgs.split() if g.split(":")[0] == "gen"][0]
                except ValueError:
                    return await errsay("gen should be a number between 1 and 7.")
                except IndexError:
                    gn = None
                else:
                    if not (1 <= gn <= 7):
                        return await errsay("gen should be a number between 1 and 7.")
                search = [g for g in sorted(list(pm.natDex.keys())) if search(pm.Mon(g), nm, ts, mg, al, gn)]
                return await pokesay("Search results",
                                     d=", ".join(search) if len(search) > 0 else "No results found.",
                                     footer=f"{len(search)} results" if len(search) > 0 else None)
            else:
                return await pokesay(**mon.speciesSD())
        else:
            if int(lowerArgs) - 1 not in range(len(pm.natDex)):
                return await errsay("Invalid dex number.")
            return await pokesay(**pm.Mon(list(pm.natDex.keys())[int(lowerArgs) - 1]).speciesSD())

    if func == "type":
        if lowerArgs not in [g.lower() for g in pm.superEffective]:
            return await errsay("Invalid type.")
        if lowerArgs == "???":
            return await pokesay("???-type", d="Typeless moves have equal effectiveness on all types; typeless mons "
                                               "have no weaknesses or resistances.",
                                 col=pm.colors[pm.typeless], emoji=getemoji("typeless"))
        await pokesay(f"{pm.cap(lowerArgs)}-type", d=pm.strType(lowerArgs.capitalize()),
                      col=pm.colors[pm.cap(lowerArgs)], emoji=getemoji(lowerArgs))

    if func == "eff":
        try:
            mon = pm.getMon(lowerArgs)
        except ValueError as v:
            return await errsay(v)
        else:
            await pokesay(**mon.typeEffSD(), thumb=mon.pic)

    if func == "dam":
        if args.count("|") != 2:
            return await errsay("Too many \"|\"s." if args.count("|") > 2 else "Too few \"|\"s.")
        attacker, defender, move = lowerArgs.split(" | ")
        try:
            attacker = pm.getMon(attacker)
        except ValueError as v:
            return await errsay(v)
        try:
            defender = pm.getMon(defender)
        except ValueError as v:
            return await errsay(v)
        if move.lower() not in pm.lowerMoves:
            return await errsay("Invalid move.")
        else:
            move = pm.movedict[pm.lowerMoves[move.lower()]]
        b = pm.Battle(pm.Team("lol"), pm.Team("kek"))
        await pokesay(f"{b.damage_amt(attacker, defender, move, 85)}-{b.damage_amt(attacker, defender, move, 100)}"
                      f" damage", d=f"{attacker.name} - {move.name} -> {defender.name}")

'''
@client.command(pass_context=True, aliases=["walker", "pw"])
async def pokewalker(ctx, func=None, *args):
    if func is None:
        return await errsay("no function supplied")

    if func.lower() not in pm.lowerMaps:
        return await errsay("invalid location")

    func = pm.lowerMaps[func.lower()]
    if len(args) == 0:
        s = sum([g.get(func, 0) ** 1.4 for g in list(pm.mapMons.values())])
        vc = [g for g in pm.mapMons if func in pm.mapMons[g] and pm.mapMons[g][func] ** 1.4 / s >= 0.05]
        c = [g for g in pm.mapMons if func in pm.mapMons[g] and 0.05 > pm.mapMons[g][func] ** 1.4 / s >= 0.01]
        r = [g for g in pm.mapMons if func in pm.mapMons[g] and 0.01 > pm.mapMons[g][func] ** 1.4 / s >= 0.005]
        vr = [g for g in pm.mapMons if func in pm.mapMons[g] and 0.005 > pm.mapMons[g][func] ** 1.4 / s]
        dic = {"Very Common": ", ".join(vc), "Common": ", ".join(c), "Rare": ", ".join(r), "Very Rare": ", ".join(vr)}
        return await emolsay(getemoji(func.lower()), f"{func} Species", hexcol(pm.mapColors[func]),
                             fs=dic)'''
