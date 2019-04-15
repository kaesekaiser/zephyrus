from startup import *
from random import randrange, sample, random
from minigames import connectfour as cf, jotto as jo, hangman as hm, boggle as bg, risk as rk
from utilities import words as wr
from copy import deepcopy as copy
from math import floor
import time


@zeph.command(aliases=["conn4"])
async def connect4(ctx: commands.Context, opponent: User):
    four = ClientEmol(":four:", blue, ctx)

    if opponent == ctx.author:
        raise commands.CommandError("You can't challenge yourself.")
    if opponent.bot:
        raise commands.CommandError("Bots can't play Connect Four.")
    con = await confirm(f"{opponent.display_name}, do you accept the challenge?", ctx, opponent,
                        yes="accept", no="deny", emol=four)
    if not con:
        return await four.say(f"{opponent.display_name} chickened out.")

    init = await four.say("Rolling for priority...")
    await asyncio.sleep(2)
    author_roll = randrange(6) + 1
    opponent_roll = randrange(6) + 1
    await four.edit(init, "Rolling for priority...",
                    d=f"{ctx.author.display_name} rolled a {zeph.emojis['attack' + str(author_roll)]}.")
    await asyncio.sleep(1)
    await four.edit(init, "Rolling for priority...", d=init.embeds[0].description +
                    f"\n{opponent.display_name} rolled a {zeph.emojis['defense' + str(opponent_roll)]}.")
    await asyncio.sleep(2)

    if author_roll > opponent_roll:
        embed = f"{ctx.author.display_name} is {zeph.emojis['checkerred']}, " \
                f"{opponent.display_name} is {zeph.emojis['checkeryellow']}."
        players = {1: ctx.author, -1: opponent}
    else:
        embed = f"{opponent.display_name} is {zeph.emojis['checkerred']}, " \
                f"{ctx.author.display_name} is {zeph.emojis['checkeryellow']}."
        players = {1: opponent, -1: ctx.author}
    await four.edit(init, embed, d="To make a move, reply with the **column number**. Left is ``1``, right is ``7``.")
    await asyncio.sleep(2)

    board = cf.Board(
        zeph.strings["conn4empty"], zeph.strings["conn4red"], zeph.strings["conn4yellow"], zeph.strings["conn4white"],
        zeph.strings["c4left"] + zeph.strings["c4top"] * 5 + zeph.strings["c4right"]
    )
    message = await four.say("Initializing...")
    at_bat = 1
    checkers = {1: zeph.strings["checkerred"], -1: zeph.strings["checkeryellow"]}

    def pred(m: discord.Message):
        return m.channel == ctx.channel and m.content in [str(g + 1) for g in range(7)] and m.author == players[at_bat]

    while True:
        await four.edit(message, f"{players[at_bat].display_name}'s turn. ({checkers[at_bat]})", d=str(board))

        try:
            move = await zeph.wait_for("message", timeout=300, check=pred)
        except asyncio.TimeoutError:
            return await four.say("Connect Four game timed out.")
        else:
            await move.delete()
            move = int(move.content)
            if board[move - 1].full:
                await message.edit(embed=message.embeds[0].set_footer("That column is full."))
                continue
            board.drop(move - 1, at_bat)
            at_bat = -at_bat

        if board.victor:
            return await four.edit(message, f"{players[board.victor].display_name} wins!", d=str(board))
        if board.full:
            return await four.edit(message, "It's a draw!", d=str(board))


@zeph.command()
async def jotto(ctx: commands.Context):
    jot = ClientEmol(":green_book:", hexcol("65c245"), ctx)

    game = jo.Jotto(choice(wr.wordDict[4]))
    await jot.say("The word has been chosen. Start guessing!",
                  d="To guess, reply with a four-letter word. To see your guess history, say "
                    "``history``. To forfeit, say ``forfeit``.")

    def pred(m: discord.Message):
        return m.author == ctx.author and m.channel == ctx.channel and \
            (len(m.content) == 4 or m.content.lower() in ["history", "forfeit"])

    while True:
        try:
            guess = (await zeph.wait_for("message", timeout=180, check=pred)).content.lower()
        except asyncio.TimeoutError:
            return await jot.say("Jotto game timed out.")
        else:
            if guess == "history":
                await jot.say("Guess History", d="\n".join([f"**``{g}``**: ``{j}``" for g, j in game.history.items()]))
                continue
            if guess == "forfeit":
                return await jot.say(f"The word was **{game.word}**.")
            if guess not in wr.wordDict[4]:
                await jot.say("That's not a valid word.")
                continue
            if guess in game.history:
                await jot.say("You already guessed that word.")
                continue

            score = game.guess(guess)
            if score == 4:
                return await jot.say(f"Correct! It took you **{len(game.history)}** guesses.")
            await jot.say(f"There {'is' if score == 1 else 'are'} {hm.numbers[game.guess(guess)]} "
                          f"correct {plural('letter', score)} in ``{guess}``.")


@zeph.command()
async def anagrams(ctx: commands.Context):
    ana = ClientEmol(":closed_book:", hexcol("dd2e44"), ctx)
    message = await ana.say("Picking letters...")

    while True:
        letters = sample(wr.anagramsDist, 8)
        if len(wr.anagrams("".join(letters))) > 20:
            break

    def form(lts: list):
        return f"```prolog\n|\u00a0{chr(160).join([g.upper() for g in lts])}\u00a0|```\n"

    def pred(mr: MR, u: User):
        if type(mr) == discord.Message:
            return u == ctx.author and mr.channel == ctx.channel and wr.canform(mr.content.lower(), letters)
        else:
            return u == ctx.author and mr.emoji in ["🔄", "⏹"] and mr.message.id == message.id

    def timer():
        return 180 + start - time.time()

    def embed():
        return {"d": f"{form(letters)}Time remaining: {round(timer())} s",
                "footer": f"Used words: {none_list(sorted(guesses))}"}

    words = wr.anagrams("".join(letters))
    guesses = []
    start = time.time()
    await ana.edit(
        message, "Your Letters", footer=f"There are {len(words)} usable words.",
        d=f"React with :arrows_counterclockwise: to shuffle the letters, or with :stop_button: to finish."
        f"\n{form(letters)}Time remaining: 180 s"
    )
    await message.add_reaction("🔄")
    await message.add_reaction("⏹")

    while True:
        try:
            guess = (await zeph.wait_for("reaction_or_message", timeout=timer(), check=pred))[0]
        except asyncio.TimeoutError:
            missed = sorted([g for g in words if g not in guesses])
            return await ana.say("Time's up!", d=f"Words you missed: {none_list(missed)} ({len(missed)})")
        else:
            if type(guess) == discord.Reaction:
                await message.remove_reaction(guess.emoji, ctx.author)
                if guess.emoji == "🔄":
                    letters = sample(letters, len(letters))
                    await ana.edit(message, "Shuffled!", **embed())
                    continue
                if guess.emoji == "⏹":
                    missed = sorted([g for g in words if g not in guesses])
                    return await ana.say("Game over!", d=f"Words you missed: {none_list(missed)} ({len(missed)})")

            await guess.delete()
            guess = guess.content.lower()
            if guess in guesses:
                await ana.edit(message, "You already guessed that word.", **embed())
                continue
            if guess in words:
                guesses.append(guess)
                await ana.edit(message, f"Scored '{guess}'!", **embed())


@zeph.command()
async def boggle(ctx: commands.Context):
    bog = ClientEmol(":hourglass:", hexcol("ffac33"), ctx)

    board = bg.Board()
    possible = [g for g in wr.wordList if set(c.upper() for c in "q".join(g.split("qu"))) <= set(board.board)
                and g[0].upper() in board.board and len(g) >= 3]
    possible = [g for g in possible if board.find(g)]

    def timer():
        return 180 + start - time.time()

    def missed():
        return sorted([g for g in possible if g not in board.guessed])

    def embed():
        return {"d": f"```ml\n{str(board)}```\nTime remaining: {round(timer())} s",
                "footer": f"Used words: {none_list(sorted(board.guessed))}"}

    def pred(m: discord.Message):
        return m.channel == ctx.channel and m.author == ctx.author and board.find(m.content.lower())

    screen = await bog.say("Boggle", d=f'```ml\n{str(board)}```\nYou have three minutes. Go!')
    start = time.time()

    while True:
        try:
            guess = await zeph.wait_for("message", timeout=timer(), check=pred)
        except asyncio.TimeoutError:
            return await bog.say("Time's up!", d=f"You scored **{board.points}** points!\n\n"
                                                 f"Words you missed: {none_list(missed())} ({len(missed())})")
        else:
            await guess.delete()
            guess = guess.content.lower()
            if guess not in possible:
                await bog.edit(screen, "That's not a word.", **embed())
                continue
            board.guess(guess)
            await bog.edit(screen, f"Scored '{guess}' for {bg.score(guess)} {plural('point', bg.score(guess))}!",
                           **embed())


@zeph.command()
async def duel(ctx: commands.Context, opponent: User):
    du = ClientEmol(":gun:", hexcol("9AAAB4"), ctx)

    if opponent == ctx.author:
        raise commands.CommandError("You can't challenge yourself.")
    if opponent.bot:
        raise commands.CommandError("You can't duel a bot.")

    if not await confirm(f"{opponent.display_name}, do you accept the challenge?", ctx, opponent,
                         emol=du, yes="accept", no="chicken out"):
        return await du.say(f"{opponent.display_name} chickened out.")
    await du.say("A duel has been declared!", d="When I say \"draw\", send the gun emoji (``:gun:`` :gun:) "
                                                "in chat as fast as you can.")
    await asyncio.sleep(2)
    await du.say("Ready...")

    def pred(m: discord.Message):
        return m.author in [ctx.author, opponent] and m.channel == ctx.channel and m.content in [":gun:", "🔫"]

    try:
        premature = await zeph.wait_for("message", timeout=(5 + random() * 5), check=pred)
        return await du.say(f"{premature.author.display_name} drew early. Shame.")
    except asyncio.TimeoutError:
        await du.say("Draw!!")
        try:
            winner = await zeph.wait_for("message", timeout=10, check=pred)
        except asyncio.TimeoutError:
            return await du.say("Nobody drew. :pensive:")
        else:
            return await du.say(f"{winner.author.display_name} wins!!")


class DiscordRisk(rk.Game):
    def __init__(self, dest: commands.Context, *players, **kwargs):
        super().__init__(password=kwargs.get("password"))
        self.dest = dest
        self.emol = ClientEmol(":drum:", hexcol("9D0522"), self.dest)
        self.users = {rk.playerOrder[g]: players[g] for g in range(len(players))}
        self.image = rk.Image.open(rk.directory + "nqr.png")
        self.statusMessage = None
        self.tempMessage = None
        self.saveState = rk.Game(str(self))
        self.rewrite()

    def rewrite(self):
        self.image = copy(rk.main_map)
        for province in self.board.provinces.values():
            rk.merge_down(
                rk.images[province.name][province.owner],
                self.image,
                *rk.imageCorners[province.name]
            )
        for province in self.board.provinces.values():
            if province.name in self.capitals:
                rk.merge_down(
                    rk.capitals[self.capitals[province.name]],
                    self.image,
                    *rk.province_centers[province.name], True
                )
            if province.owner is not None:
                rk.merge_down(
                    rk.numbers[province.troops],
                    self.image,
                    *rk.province_centers[province.name], True
                )

    @property
    async def should_quit(self):
        reaction = [g for g in self.statusMessage.reactions if g.emoji == zeph.emojis["no"]][0]
        users = set(await reaction.users().flatten())
        if set(self.players.values()) <= users:
            return True
        return False

    async def update_status(self, phase: str):
        string = "\n".join([
            f"{g}: {len([j for j in self.board.provinces.values() if j.owner == g])} provinces / "
            f"{sum([j.troops for j in self.board.provinces.values() if j.owner == g])} troops / "
            f"{floor(len([j for j in self.board.provinces.values() if j.owner == g]) / 2)} TPT" for g in self.players
        ])
        self.image.save(f"images/risk-{str(self)[0]}.png")
        kwargs = {
            "s": f"{self.playerOrder[self.atBat]}'s turn - {phase} Phase".upper(),
            "d": string,
            "footer": str(self.saveState),
            "image": await image_url(f"images/risk-{str(self)[0]}.png")
        }
        try:
            await self.emol.edit(self.statusMessage, **kwargs)
        except AttributeError:
            self.statusMessage = await self.emol.say(**kwargs)
            await self.statusMessage.add_reaction("🗺")
            await self.statusMessage.add_reaction(zeph.emojis["yes"])
            await self.statusMessage.add_reaction(zeph.emojis["no"])

    async def say(self, s: str, **kwargs):
        try:
            await self.tempMessage.delete()
        except AttributeError:
            pass
        self.tempMessage = await self.emol.say(s, **kwargs)

    def owned(self, plr: str):
        return {g for g in rk.borders if self.board.provinces[g].owner == plr}

    def empty(self):
        return {g for g in rk.borders if self.board.provinces[g].owner is None}

    def contiguous(self, fro: rk.Province, to: rk.Province):
        neighbors = {g for g in rk.borders[fro.name]
                     if self.board.provinces[g].owner == fro.owner}.union({fro.name})
        while True:
            length = len(neighbors)
            neighbors = {
                g for j in neighbors for g in rk.borders[j]
                if self.board.provinces[g].owner == fro.owner
            }.union(neighbors)
            if to.name in neighbors:
                return True
            if len(neighbors) == length:
                return False

    def randomize(self):
        def no_neighbors(s: str):  # if the intersect with empty() is the set, it has no owned neighbors
            return s in self.empty() and set(rk.borders[s]).intersection(self.empty()) == set(rk.borders[s])

        self.capitals = dict()
        self.inverseCapitals = dict()
        self.atBat = 0
        for i in self.board.provinces.values():
            i.owner = None
            i.troops = 1
        for i in range(len(self.players)):  # sets capital + claims surrounding provinces
            player = self.playerOrder[i]
            try:  # tries to find province with no claimed neighbors first
                province = choice([g for g in self.board.provinces if no_neighbors(g)])
            except IndexError:
                province = choice(list(self.board.provinces))
            self.capitals[province] = player
            self.inverseCapitals[player] = province
            self.players[player].capital = province
            for prov in set(rk.borders[province]).union({province}):
                if self.board.provinces[prov].owner is None:
                    self.board.provinces[prov].owner = self.playerOrder[i]
        while True:  # claims all provinces
            player = self.playerOrder[self.atBat]
            valid_provinces = [
                g for g in self.board.provinces if player in [
                    self.board.provinces[j].owner for j in rk.borders[g]
                ] and self.board.provinces[g].owner is None
            ]
            try:
                province = choice(valid_provinces)
                self.board.provinces[province].owner = player
            except IndexError:
                province = choice([g for g in self.board.provinces if self.board.provinces[g].owner == player])
                self.board.provinces[province].troops += 1
            if None not in [g.owner for g in self.board.provinces.values()]:
                break
            self.atBat = (self.atBat + 1) % len(self.players)
        self.atBat = 0
        self.playerOrder = sorted(
            self.playerOrder, key=lambda c: len([g for g in self.board.provinces.values() if g.owner == c])
        )
        for i in range(20):
            for player in self.playerOrder:
                valid_provinces = [g for g in self.board.provinces.values() if g.owner == player]
                self.board.provinces[choice(valid_provinces).name].troops += 1
        self.rewrite()
        self.saveState = rk.Game(str(self))

    async def move(self, fro: rk.Province, to: rk.Province, n: int):
        if not self.contiguous(fro, to):
            return await self.say(f"{fro.name} and {to.name} aren't contiguous.")
        if n >= fro.troops:
            return await self.say("You can't abandon a province.")
        fro.troops -= n
        to.troops += n
        self.rewrite()

    async def attack(self, fro: rk.Province, attack: int, to: rk.Province):
        if fro.name not in rk.borders[to.name]:
            return await self.say(f"{to.name} doesn't border {fro.name}.")
        if attack > fro.troops - 1:
            return await self.say("You can't abandon a province.")
        attack = sorted([randrange(6) + 1 for g in range(attack)], reverse=True)
        defense = sorted([randrange(6) + 1 for g in range(min(2, to.troops))], reverse=True)
        if len(attack) > len(defense):
            hold = [defense[n] >= attack[n] for n in range(len(defense))]
        else:
            hold = [defense[n] >= attack[n] for n in range(len(attack))]
        attack_str = " ".join([zeph.strings[f"attack{g}"] for g in attack])
        defense_str = " ".join([zeph.strings[f"defense{g}"] for g in defense])
        losses_str = (f"Attacker loses **{hm.numbers[hold.count(True)]}** {plural('regiment', hold.count(True))}."
                      if True in hold else "") + \
                     ("\n" if True in hold and False in hold else "") + \
                     (f"Defender loses **{hm.numbers[hold.count(False)]}** {plural('regiment', hold.count(False))}."
                      if False in hold else "")
        for item in hold:
            if item:
                fro.troops -= 1
            else:
                to.troops -= 1
        if to.troops < 1:
            transfer_str = f"\n**{fro.owner} captures {to.name}!**"
            to.owner = fro.owner
            to.troops = len(attack) - hold.count(True)
            fro.troops -= to.troops
        else:
            transfer_str = ""
        self.rewrite()
        await self.say(f"Battle of {to.name}",
                       d=f"``ATTACKER:`` {attack_str}\n``DEFENDER:`` {defense_str}\n\n{losses_str}{transfer_str}")

    async def quit(self, reason: str="Quitting game."):
        return await self.say(reason, d="Use the password at the bottom of the screen if you want to come back "
                                        "to this game.")

    async def wait_for(self, timeout: int=None, author: User=None, check: callable=None):
        def pred(mr: MR, u: User):
            if type(mr) == discord.Message:
                return (author is None or u == author) and mr.channel == self.dest.channel
            if type(mr) == discord.Reaction:
                print("real hi")
                if mr.emoji == zeph.emojis["no"]:
                    return author in self.players.values() and mr.message.id == self.statusMessage.id
                else:
                    return (author is None or u == author) and mr.message.id == self.statusMessage.id and \
                        mr.emoji in ["🗺", zeph.emojis["yes"]]

        while True:
            try:
                message = (await zeph.wait_for(
                    "reaction_or_message", timeout=timeout
                ))
            except asyncio.TimeoutError:
                return await self.quit("Game timed out.")
            if type(message[0]) == discord.Reaction:
                if pred(*message):
                    message = message[0]
                    if message.emoji == "🗺":
                        await message.message.remove_reaction(message.emoji, author)
                        await self.say("Map Link", url="https://cdn.discordapp.com/attachments/405184040627601410/"
                                                       "527965910556999701/nqr_names.png")
                        continue
                    if message.emoji == zeph.emojis["no"]:
                        if await self.should_quit:
                            return await self.quit()
                    if message.emoji == zeph.emojis["yes"]:
                        await message.message.remove_reaction(message.emoji, author)
                        return message
            await asyncio.sleep(0.1)
            await message[0].delete()
            if (check is None or check(message[0])) and pred(*message):
                return message[0]

    async def startup(self):
        pass

    async def run(self):
        def is_int_str(s: str):
            try:
                int(s)
            except ValueError:
                return False
            return True

        def valid_reinforce(s: str, plr: str):
            s = s.title().split()
            if not set(s).intersection(self.owned(plr)):
                return False  # "You didn't name an owned province to reinforce."
            dest = [g for g in s if g in rk.borders and self.board.provinces[g].owner == plr][0]
            if True not in [is_int_str(g) for g in s]:
                return False  # You didn't specify how many regiments to reinforce."
            num = int([g for g in s if is_int_str(g)][0])
            return {"prov": dest, "num": num}

        def valid_attack(s: str, plr: str):
            s = s.title().split()
            if not set(s).intersection(self.owned(plr)):
                return False  # "You didn't name a province you own to attack from."
            src = [g for g in s if g in rk.borders and self.board.provinces[g].owner == plr][0]
            if True not in [(g in rk.borders and self.board.provinces[g].owner != plr) for g in s]:
                return False  # "You didn't name an enemy province to attack."
            dest = [g for g in s if g in rk.borders and self.board.provinces[g].owner != plr][0]
            if True not in [is_int_str(g) for g in s]:
                return False  # "You didn't specify how many regiments to attack with."
            num = int([g for g in s if is_int_str(g)][0])
            return {"from": src, "to": dest, "with": num}

        def valid_move(s: str, plr: str):
            s = s.title().split()
            if "To" not in s or "From" not in s:
                return False
            if s.index("From") == len(s) - 1 or not (s[s.index("From") + 1] in self.owned(plr)):
                return False
            src = s[s.index("From") + 1]
            if s.index("To") == len(s) - 1 or not (s[s.index("To") + 1] in self.owned(plr)):
                return False
            dest = s[s.index("To") + 1]
            if True not in [is_int_str(g) for g in s]:
                return False
            num = int([g for g in s if is_int_str(g)][0])
            return {"from": src, "to": dest, "num": num}

        while True:
            player = self.playerOrder[self.atBat]

            # REINFORCEMENT PHASE
            if self.board.provinces[self.inverseCapitals[player]].owner == player:
                reinforcements = floor(len([g for g in self.board.provinces.values() if g.owner == player]) / 2)
                while True:
                    await self.update_status("Reinforcement")
                    await self.say(f"You have {reinforcements} reinforcements remaining.",
                                   d=f"To reinforce, say ``<province> <number>``. Hit {zeph.strings['yes']} if "
                                     f"you're done reinforcing before you've used all your troops.")
                    command = await self.wait_for(
                        timeout=300,  # author=self.users[player],
                        check=lambda c: valid_reinforce(c.content, player)
                    )
                    if command is None:
                        return
                    if type(command) == discord.Reaction:
                        break
                    command = valid_reinforce(command.content, player)
                    troops = command["num"]
                    province = self.board.provinces[command["prov"]]
                    if not self.contiguous(province, self.board.provinces[self.inverseCapitals[player]]):
                        await self.say(f"{province.name} isn't connected to your capital.")
                        continue
                    if province.troops + troops > 32:
                        await self.say("You can't station more than 32 troops in one province.")
                        continue
                    if troops > reinforcements:
                        await self.say(f"You only have {reinforcements} reinforcements left.")
                        continue
                    province.troops += troops
                    reinforcements -= troops
                    self.rewrite()
                    if reinforcements == 0:
                        break
            else:
                await self.update_status("Reinforcement")
                await self.say(f"Because you don't own your capital province of {self.inverseCapitals[player]}, "
                               f"you **cannot reinforce.**")
                await asyncio.sleep(3)

            # ATTACK PHASE
            await self.say("ATTACK PHASE", d=f"To attack, say ``<target> from <source> with "
                                             f"<number>``. When you're done, hit {zeph.strings['yes']}.")
            while True:
                await self.update_status("Attack")
                command = await self.wait_for(
                    timeout=300,  # author=self.users[player],
                    check=lambda c: valid_attack(c.content, player)
                )
                if command is None:
                    return
                if type(command) == discord.Reaction:
                    break
                command = valid_attack(command.content, player)
                # this is where the fight or flight decision will go
                await self.attack(
                    self.board.provinces[command["from"]], command["with"], self.board.provinces[command["to"]]
                )

            # MOVE PHASE
            await self.say("MOVE PHASE", d=f"To move, say ``<number> from <source> to <destination>``. "
                                           f"When you're done moving, hit {zeph.strings['yes']}.")
            while True:
                await self.update_status("Move")
                command = await self.wait_for(
                    timeout=300,  # author=self.users[player],
                    check=lambda c: valid_move(c.content, player)
                )
                if command is None:
                    return
                if type(command) == discord.Reaction:
                    break
                command = valid_move(command.content, player)
                await self.move(
                    self.board.provinces[command["from"]], self.board.provinces[command["to"]], command["num"]
                )

            # POST-TURN SAVE STATE
            self.atBat = (self.atBat + 1) % len(self.players)
            self.saveState = rk.Game(str(self))


@zeph.command()
async def risk(ctx: commands.Context, cmd: str=None):
    if cmd is None:
        b = DiscordRisk(ctx)
        b.randomize()
        await b.startup()
        await b.run()

    else:
        try:
            b = DiscordRisk(ctx, password=cmd)
            await b.run()
        except IndexError:
            raise commands.CommandError("Invalid password.")
