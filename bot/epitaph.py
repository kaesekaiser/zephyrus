from pkmn import *
from epipile import civs as ep


class Epitaph(ep.Civ):
    def __init__(self, ctx: commands.Context, hands_off: bool = False):
        self.player = ctx.author
        self.ctx = ctx
        self.handsOff = hands_off
        self.yellow = ClientEmol(":rocket:", hexcol("eeff00"), ctx)
        self.red = ClientEmol(":rocket:", hexcol("ff0000"), ctx)
        self.blue = ClientEmol(":rocket:", hexcol("00ffff"), ctx)
        self.grey = ClientEmol(":rocket:", hexcol("adadad"), ctx)
        super().__init__()

    async def eventech(self, eventech: ep.EvenTech, silent: bool = False, edit: discord.Message = None):
        # assumes event / tech is valid and available
        for i in eventech.eventChances:
            self.eventChances[i] = self.eventChances.get(i, 0) + eventech.eventChances[i]
        for i in eventech.setVars:
            self.__setattr__(i, eventech.setVars[i])
        self.knowledge.append(eventech.name)
        self.history.append(f"{self.stardate} - {self.vocabize(eventech.desc, **eventech.vocab)}")
        dic = dict(s=f"Stardate {self.stardate}", d=self.vocabize(eventech.desc, **eventech.vocab),
                   footer=f"{self.birth} - {self.stardate}" if self.extinct else None)
        if not silent:
            if edit:
                await (self.grey if self.extinct else self.yellow).edit(edit, **dic)
            else:
                await (self.grey if self.extinct else self.yellow).say(**dic)
        if not self.extinct:
            return await self.ctx.typing()

    async def tick(self):
        def pred(m: discord.Message):
            return m.content.lower() in lower(self.available_techs) + ["exit"] and m.author == self.player and \
                m.channel == self.ctx.channel

        if self.stardate - self.lastIntervention == 30 and not self.handsOff:
            self.lastIntervention = self.stardate
            form = ", or of ".join(f"__{g}__" for g in self.available_techs)
            message = await self.red.say(
                f"Stardate {self.stardate}", d=f"We could teach them the secrets of {form}.",
                footer="Just say the name of the technology. Time is paused until you do. "
                       "Alternatively, say \"exit\" to exit." if len(self.knowledge) == 0 else None
            )
            try:
                cho = await zeph.wait_for("message", timeout=300, check=pred)
            except asyncio.TimeoutError:
                self.extinct = True
                return await self.yellow.say("Game timed out.")
            if cho.content.lower() == "exit":
                self.extinct = True
                return await self.yellow.say("Exited game.")
            try:
                await cho.delete()
            except discord.HTTPException:
                pass
            await self.eventech(ep.techs[cho.content.lower()], edit=message)
        else:
            for i in self.available_events:
                if random() < self.eventChances[i]:
                    await self.eventech(ep.events[i])
                    break
            else:
                if random() < self.techChance and len(self.available_techs) > 0:
                    await self.eventech(ep.techs[choice(self.available_techs).lower()])
        if self.victorious:
            return await self.blue.say(self.vocabize("In stardate {stardate}, the {civ} joined us."),
                                       footer=f"{self.birth} - {self.stardate}")
        self.stardate += 1

    async def run(self):
        cont = self.contact()
        zeph.epitaph_channels.append(self.ctx.channel)
        await self.yellow.say(f"Stardate {self.stardate}", d=cont)
        self.history.append(f"{self.stardate} - {cont}")
        while not (self.extinct or self.victorious):
            await asyncio.sleep(0.2 if self.handsOff else 0.5)
            await self.tick()
        zeph.epitaph_channels.remove(self.ctx.channel)


@zeph.command(
    usage="z!epitaph\nz!epitaph handsoff",
    description="Runs a game of [Max Kreminski's Epitaph](https://mkremins.github.io/epitaph/).",
    help="Runs a game of [Max Kreminski's Epitaph](https://mkremins.github.io/epitaph/). As an "
         "ascended civilization, lead a burgeoning planet to join you in the stars. Play the original.\n\n"
         "`z!epitaph handsoff` runs a game without player input."
)
async def epitaph(ctx: commands.Context, *, text: str = ""):
    if text and text.casefold() != "handsoff":
        raise commands.BadArgument
    if ctx.channel in zeph.epitaph_channels:
        raise commands.CommandError("There is already an Epitaph game running in this channel.")

    return await Epitaph(ctx, bool(text)).run()
