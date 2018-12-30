from calc import *
import dnd.mons as dd
from random import randrange

'''
async def battlesay(s, **kwargs):
    await emolsay(":crossed_swords:", s, hexcol("ccd4de"), **kwargs)


class Team:
    def __init__(self, name, *mons):
        self.mons = list(mons)
        self.player = (dd.Player in [type(m) for m in mons])
        self.name = name

    def live(self):
        return True in [m.hpc > 0 for m in self.mons]

    def __str__(self):
        return "\n".join(str(i) for i in self.mons)


class Battle:
    def __init__(self, p: Team, o: Team, u: discord.Member):
        self.teams = {"p": p, "o": o}
        for i in self.teams:
            for j in range(len(self.teams[i].mons)):
                self[i, j].index = i, j
        self.messages = {}
        self.turnno = 1
        self.player = u
        self.timeout = False

    def __setitem__(self, item: tuple, value):
        self.teams[item[0]].mons[item[1]] = value

    def __getitem__(self, item):
        return self.teams[item[0]].mons[item[1]] if type(item) == tuple else self.teams[item]

    @staticmethod
    def dice(n: int=1):
        return [randrange(20) + 1 for g in range(n)]

    @staticmethod
    def bound(n, min=1, max=20):
        return min if n < min else max if n > max else n

    @staticmethod
    def hitChance(m, a, d):
        return round(21 - (m + 5 * (a - d)) / 5)

    @staticmethod
    def formatRolls(r, n):
        return f"[{', '.join([f'**{str(g)}**' if g >= n else f'~~{str(g)}~~' for g in r])}]"

    @staticmethod
    def weakness(m: dd.Move, p: dd.Mon):
        for i, j in list(dd.weakness.items()):
            if i in m.attrs and j in p.attrs:
                return f"\nDamage doubled due to {p.breed}'s weakness to {i}!"
            elif i in m.attrs and i in p.attrs:
                return f"\nDamage halved due to {p.breed}'s resistance to {i}!"
        return ""

    def statdate(self):
        for t in self.teams:
            for p in self[t].mons:
                p.hpc = self.bound(p.hpc, 0, p.hp)

    def move(self, m: dd.Move, a: dd.Mon, d: dd.Mon):
        dice = self.dice(m.power)
        if "heal" in m.attrs:
            rolls = [g for g in dice if g >= self.bound(self.hitChance(m.acc, 1, 1))]
            self.messages[f"{a.breed} used {m.name}!"] = \
                f"healing roll: **{self.bound(self.hitChance(m.acc, 1, 1))}+**\n" \
                f"{self.formatRolls(sorted(dice), self.bound(self.hitChance(m.acc, 1, 1)))}\n" \
                f"Rolled for {len(rolls)} health recovered!"
            a.hpc = self.bound(a.hpc + len(rolls), max=a.hp)
            return
        if "shield" in m.attrs:
            self.messages[f"{a.breed} used {m.name}!"] = "All incoming damage reduced to 1 HP!"
            a.shield = True
            return
        rolls = [g for g in dice if g >= self.bound(self.hitChance(m.acc, a.dex, d.dex))]
        weak = self.weakness(m, d)
        raw = round(len(rolls) * (2 if "doubled" in weak else 0.5 if "halved" in weak else 1))
        if raw > 1 and d.shield:
            dmg, shield = 1, "\nDamage reduced to 1!"
        else:
            dmg, shield = raw, ""
        self.messages[f"{a.breed} used {m.name}!"] =\
            f"damage roll: **{self.bound(self.hitChance(m.acc, a.dex, d.dex))}+**\n"\
            f"{self.formatRolls(sorted(dice), self.bound(self.hitChance(m.acc, a.dex, d.dex)))}" \
            f"{weak}\n"\
            f"Rolled for {raw} damage on {d.breed}!" \
            f"{shield}"
        d.hpc -= dmg
        if d.hpc <= 0:
            self.messages[f"{d.breed} fainted!"] = ""
        self.statdate()

    async def turn(self):
        self.messages = {}
        await battlesay(f"TURN {self.turnno}")
        await asyncio.sleep(2)
        for i in self["p"].mons:
            if i.hpc > 0:
                await battlesay(f"What will {i.breed} do?", d=" | ".join([g.name for g in list(i.moves.values())]))
                while True:
                    putin = await client.wait_for_message(timeout=180, author=self.player)
                    if putin is None:
                        self.timeout = True
                        return
                    if putin.content.lower() in i.moves:
                        break
                    await errsay("Unrecognized action.")
                m = i.moves[putin.content.lower()]
                self.move(m, i, self["o", 0])
        for i in self["o"].mons:
            if i.hpc > 0:
                m = i.moves[choice(list(i.moves.keys()))]
                self.move(m, i, self["p", choice([g for g in range(len(self["p"].mons)) if self["p", g].hpc > 0])])
        await self.print()
        await self.status()
        self.turnno += 1

    async def status(self):
        await battlesay(f"TURN {self.turnno} STATUS", fs={t.name: str(t) for t in list(self.teams.values())})
        for i in "p", "o":
            for j in self[i].mons:
                j.shield = False

    def checkLive(self):
        return self["p"].live() and self["o"].live() and not self.timeout

    async def run(self):
        self.checkLive()
        while True:
            await self.turn()
            await asyncio.sleep(2)
            if not self.checkLive():
                await battlesay("Oh shit somebody dead" if not self.timeout else "Game timed out.")
                break

    async def print(self):
        for k in self.messages:
            await battlesay(k, d=self.messages[k] if len(self.messages[k]) > 0 else None)
            await asyncio.sleep(1)


@client.command(pass_context=True)
async def battle(ctx, *args):
    b = Battle(Team("some assholes", copy(dd.samplePlayer), dd.Player(("Bill", 10, 4, [], 5), ["fuck", "magnet", "recover"])),
               Team("jack-off #3", dd.Mon("boss1", ["stomp"])), ctx.message.author)
    await b.run()


@client.command(pass_context=True)
async def dungeons(ctx, *args):
    speaker = ctx.message.author

    def addinfo(i, n):
        return "{}{}{}".format(i, "\n" if len(i) > 0 else "", n)

    async def dungsay(s, **kwargs):
        await emolsay(":european_castle:", s, hexcol("3a589e"), **kwargs)

    async def run(dung):
        delay = False
        while True:
            info, desc = "", ""
            command = await client.wait_for_message(timeout=12000 if delay else 120, author=speaker)
            if command is None:
                return await errsay("Dungeons game timed out.")
            comm = command.content.lower()
            if comm in dung.dirs:
                await move(dung, comm)
            elif comm == "open":
                if dung.pos != dung.bigchest:
                    if dung.pos not in dung.chests:
                        info = "There is no chest in this room."
                    elif dung.chests[dung.pos][0] is True:
                        info = "The chest in this room is already open."
                    else:
                        info, desc = "Opened chest.", f"Found a {dung.chests[dung.pos][1]}."
                        dung.explorer.inv.append(dung.chests[dung.pos][1])
                        dung.chests[dung.pos][0] = True
                else:
                    if f"bossKey{dung.lvl}" in dung.explorer.inv:
                        info = "You already have the big key."
                    else:
                        info, desc = "Opened the big chest.", "Obtained the Big Key for this dungeon."
                        dung.explorer.inv.append(f"bossKey{dung.lvl}")
                await dungsay(info, d=addinfo(desc, dung.exitlist(dung.pos)))
            elif comm == "delay":
                delay = not delay
                await dungsay("Delaying game." if delay else "No longer delaying game.")
            if dung.pos not in dung.rooms:
                return dung.explorer

    async def move(dung, d):
        new, info, desc = dung.move(dung.pos, d), "", None
        if d not in dung.doors[dung.pos] and not (dung.pos in dung.exit and dung.exit[1] == d) and not \
                (dung.pos in dung.boss and dung.boss[1] == d):
            return await dungsay("There is no door in that direction.", d=dung.exitlist(dung.pos))
        if new in dung.rooms:
            info = f"Moved {dung.names[d]}."
            desc = dung.exitlist(new)
        elif dung.pos in dung.exit and dung.exit[1] == d:
            info = "Exited the dungeon."
        elif dung.pos in dung.boss and dung.boss[1] == d:
            if f"bossKey{dung.lvl}" not in dung.explorer.inv:
                return await dungsay("You don't have the Boss Key.", d=dung.exitlist(dung.pos))
            info = "Entered the boss chamber."
        await dungsay(info, d=desc)
        dung.pos = new

    if len(args) > 1 and args[0] not in dg.shapes:
        return await errsay("Invalid shape.")
    shape = (args[0], tuple(int(g) for g in args[1:])) if len(args) > 1 else ("rect", (3, 3, 3))
    if len(shape[1]) == 1:
        shape = shape[0], shape[1][0]
    if len(list(dg.shapes[shape[0]](shape[1]))) < 5:
        return await errsay("Dungeon size too small.")
    dungeon = dg.RingMaze(shape, dg.samplePlayer) if args[0] in ["cylindrical", "conical"]\
        else dg.HexMaze(shape, dg.samplePlayer) if args[0] in ["hexagonal", "hexatronas"]\
        else dg.FourMaze(shape, dg.samplePlayer) if args[0] in ["four"]\
        else dg.PrimMaze(shape, dg.samplePlayer)
    await dungsay(f"Entered a {'x'.join([str(g) for g in shape[1]]) if len(args) == 3 else args[0]} dungeon.",
                  d=dungeon.exitlist(dungeon.pos))
    await run(dungeon)'''
