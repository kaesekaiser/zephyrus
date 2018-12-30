from epipile import civs as ep
from pkmn import *


async def episay(s: str, **kwargs):
    return await emolsay(":rocket:", s, hexcol(kwargs.get("col", "eeff00")), **kwargs)


class DiscordCiv(ep.Civ):
    def __init__(self, player: discord.Member, channel: discord.Channel, hands_off: bool=False):
        self.player = player
        self.channel = channel
        self.handsOff = hands_off
        super().__init__()

    async def eventech(self, eventech: ep.EvenTech, silent: bool=False):  # assumes event / tech is valid and available
        for i in eventech.eventChances:
            self.eventChances[i] = self.eventChances.get(i, 0) + eventech.eventChances[i]
        for i in eventech.setVars:
            self.__setattr__(i, eventech.setVars[i])
        self.knowledge.append(eventech.name)
        self.history.append(f"{self.stardate} - {self.vocabize(eventech.desc, **eventech.vocab)}")
        if not silent:
            return await episay(f"Stardate {self.stardate}", d=self.vocabize(eventech.desc, **eventech.vocab),
                                col="adadad" if self.extinct else "eeff00",
                                footer=f"{self.birth} - {self.stardate}" if self.extinct else None)

    async def tick(self):
        if (self.stardate - self.birth) % 10 == 1:
            await client.send_typing(self.channel)
        if self.stardate - self.lastIntervention == 30 and not self.handsOff:
            self.lastIntervention = self.stardate
            form = ", or of ".join(f"__{g}__" for g in self.available_techs())
            await episay(f"Stardate {self.stardate}",
                         d=f"We could teach them the secrets of {form}.",
                         col="ff0000",
                         footer="Just say the name of the technology. Time is paused until you do."
                         if len(self.knowledge) == 0 else None)
            cho = await client.wait_for_message(timeout=300, author=self.player, channel=self.channel,
                                                check=lambda c: c.content.lower() in lower(self.available_techs()))
            if cho is None:
                self.extinct = True
                return await episay("Game timed out.")
            await self.eventech(ep.techs[cho.content.lower()])
        else:
            for i in self.available_events():
                if random() < self.eventChances[i]:
                    await self.eventech(ep.events[i])
                    break
            else:
                if random() < self.techChance and len(self.available_techs()) > 0:
                    await self.eventech(ep.techs[choice(self.available_techs()).lower()])
        if self.victorious:
            return await episay(self.vocabize("In stardate {stardate}, the {civ} joined us."),
                                col="00FFFF", footer=f"{self.birth} - {self.stardate}")
        self.stardate += 1

    def write(self):
        with open(f"storage/epi{self.player.id}.txt", "w+") as f:
            f.write("\n".join(self.history))

    async def run(self):
        cont = self.contact()
        await episay(f"Stardate {self.stardate}", d=cont)
        self.history.append(f"{self.stardate} - {cont}")
        while not (self.extinct or self.victorious):
            await asyncio.sleep(0.2 if self.handsOff else 0.5)
            await self.tick()
        self.write()


@client.command(pass_context=True)
async def epitaph(ctx, func=None, *args):
    if func is None:
        return await DiscordCiv(ctx.message.author, ctx.message.channel).run()

    if func.lower() not in ["tech", "last", "handsoff"]:
        return await errsay("unrecognized function")

    if func.lower() == "handsoff":
        return await DiscordCiv(ctx.message.author, ctx.message.channel, True).run()

    if func.lower() == "tech":
        args = " ".join(args).lower()
        if args in ["", "chart", "tree"]:
            return await episay("Epitaph Tech Tree", url="https://cdn.discordapp.com/attachments/"
                                                         "405184040627601410/490654114724970496/unknown.png")
        if args not in ep.techs:
            return await errsay("invalid technology")
        return await episay(ep.cap_name(ep.techs[args].name), fs=ep.techs[args].dict())

    if func.lower() == "last":
        return await client.send_file(ctx.message.channel, f"storage/epi{ctx.message.author.id}.txt")
