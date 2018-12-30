from startup import *
from math import ceil
from random import choice


@client.command(pass_context=True, aliases=["conn4", "connect4"])
async def connectfour(ctx: Context, opp: discord.Member):
    def confour(s: str, **kwargs):  # ambiguously naming functions!
        return conemol(":four:", s, hexcol("5177ca"), **kwargs)

    async def foursay(s: str, **kwargs):
        return await client.say(embed=confour(s, **kwargs))

    if opp.bot:
        return await errsay("Bots can't play Connect Four.")
    if opp == ctx.message.author:
        return await errsay("You can't challenge yourself.")
    conf = await confirm(opp, f"{opp.display_name}, do you accept the challenge?", say=foursay, yes="accept", no="deny")
    if not conf:
        return await errsay(f"{opp.display_name} chickened out.")
    roll = await foursay("Rolling for priority...")
    await asyncio.sleep(1)
    usroll, oproll = randrange(6) + 1, randrange(6) + 1
    await client.edit_message(roll, embed=confour("Rolling for priority...",
                                                  d=f"{ctx.message.author.display_name} rolled a **{usroll}.**"))
    await asyncio.sleep(0.5)
    await client.edit_message(roll, embed=confour("Rolling for priority...",
                                                  d=f"{ctx.message.author.display_name} rolled a **{usroll}.**\n"
                                                  f"{opp.display_name} rolled a **{oproll}.**"))
    if usroll > oproll:
        colors = "{} is **{},** {} is **{}.**"\
            .format(ctx.message.author.display_name, getemoji('checkerred'),
                    opp.display_name, getemoji('checkeryellow'))
        tdic = {1: ctx.message.author, -1: opp}
    else:
        colors = "{} is **{},** {} is **{}.**" \
            .format(opp.display_name, getemoji('checkerred'),
                    ctx.message.author.display_name, getemoji('checkeryellow'))
        tdic = {1: opp, -1: ctx.message.author}
    top = getemoji("c4left") + getemoji("c4top") * 5 + getemoji("c4right")
    b = cf.Board(getemoji("conn4empty"), getemoji("conn4red"), getemoji("conn4yellow"), getemoji("conn4white"), top)
    cols = [str(g + 1) for g in range(7)]
    checker_dict = {1: getemoji("checkerred"), -1: getemoji("checkeryellow")}
    await asyncio.sleep(1.5)
    await client.edit_message(roll, embed=confour(
        colors, d="To make a move, reply using the desired **column number.** 1 is far left, 7 is far right."
    ))
    await asyncio.sleep(0.5)
    screen = await foursay(f"{tdic[1].display_name}'s move ({checker_dict[1]}).", d=b.str())
    while True:
        for p in [1, -1]:
            mcon = await client.wait_for_message(timeout=120.0, author=tdic[p], check=(lambda m: m.content in cols))
            if mcon is None:
                return await errsay("Connect Four game timed out.")
            await delete_message(mcon)
            while b.isfull(int(mcon.content) - 1) is True:
                temp = await client.say("That column is full.")
                mcon = await client.wait_for_message(timeout=120.0, author=tdic[p], check=(lambda m: m.content in cols))
                await delete_message(temp)
                if mcon is None:
                    return await errsay("Connect Four game timed out.")
                await delete_message(mcon)
            b.drop(int(mcon.content) - 1, p)
            if False not in [b.isfull(c) for c in range(7)]:
                return await client.edit_message(screen, embed=confour("It's a draw!", d=b.str()))
            elif b.victor() is False:
                await client.edit_message(screen, embed=confour(f"{tdic[-p].display_name}'s move ({checker_dict[-p]}).",
                                                                d=b.str()))
            else:
                return await client.edit_message(screen, embed=confour(f"{tdic[p].display_name} wins!", d=b.str()))


'''async def getplayers(max, waittime, sayfunc, bedargs: dict, caller: discord.Member, channel: discord.Channel):
    await sayfunc(s=bedargs["s"], d=bedargs["d"], fs=bedargs["fs"])
    membs, start, prog = [caller], time(), 0 if waittime > 120 else 1 if waittime > 60 else 2 if waittime > 30 else 3
    while time() < start + waittime and len(membs) < max:
        if gamechannels[channel.id][0] == 0:
            return
        n = await client.wait_for_message(timeout=0.5, content="join", channel=channel)
        if n is not None and n.author not in membs:
            await sayfunc("{}, you've been added to the game.".format(servnick(n.author)))
            membs.append(n.author)
        if time() > start + waittime - 5 and prog < 4:
            prog = 4
            await sayfunc("Starting in 5 seconds.")
        if time() > start + waittime - 30 and prog < 3:
            prog = 3
            await sayfunc("Starting in 30 seconds.")
        if time() > start + waittime - 60 and prog < 2:
            prog = 2
            await sayfunc("Starting in 1 minute.")
        if time() > start + waittime - 120 and prog < 1:
            prog = 1
            await sayfunc("Starting in 2 minutes.")
    if len(membs) == max:
        await sayfunc("The game is now full. Starting...")
    elif len(membs) == 1:
        gamechannels[channel.id] = [0, "none"]
        return await sayfunc("You can't start a game with just one person.", d="Game cancelled.")
    else:
        await sayfunc("Starting...")
    return membs


@client.command(pass_context=True, aliases=["holdem"])
async def poker(ctx: Context, func=None):
    full, startup = 10, 20 if func == "rematch" else 180
    if func is None:
        return await errsay("Please input a function.")
    if func not in ["hands", "rules", "host", "rematch", "cancel"]:
        return await errsay("{} is not a valid function.".format(func))
    if func == "hands":
        return await client.say(embed=conembed(title="**Hand Ranks**", color=hexcol("ff0000"),
                                               fields={"{}. {}".format(g + 1, pk.handnames[g]):
                                                       "{}\n*ex:* {}".format(pk.handdescs[g], pk.samples[g])
                                                       for g in range(10)}))
    if func == "rules":
        return await client.say("explanation of hold'em goes here")
    if func == "cancel":
        if gamechannels.get(ctx.message.channel.id, [0])[0] == ctx.message.author.id:
            gamechannels[ctx.message.channel.id] = [0, "none"]
            return await succsay("Game cancelled.")
        if type(gamechannels.get(ctx.message.channel.id, [0])[0]) == str:
            return await errsay("You are not the host.")
        if gamechannels.get(ctx.message.channel.id, [0])[0] == 1:
            return await errsay("You can't cancel a game mid-session.")
        if gamechannels.get(ctx.message.channel.id, [0])[0] == 0:
            return await errsay("There is no game running.")
    if gamechannels.get(ctx.message.channel.id, [0])[0] != 0:
        return await errsay("There is already a game running in this channel.")
    if full > 20:
        return await errsay("Games can only hold a maximum of 20 players.")
    if full < 2:
        return await errsay("what even?")
    gamechannels[ctx.message.channel.id] = [ctx.message.author.id, "poker"]
    await client.say("**{} is hosting a game of Texas hold 'em.**\n\nTo join, reply ``join``.\nTo check hand"
                     " ranks, use ``z!poker hands`` at any time.\nTo learn how to play, use ``z!h poker``.\n"
                     "If you don't know the rules of Texas hold 'em, read ``z!poker rules`` and/or watch a game.\n\n"
                     "The game will begin **in {}.**".format(servnick(ctx.message.author),
                                                             "3 minutes" if startup == 180 else "20 seconds"))
    membs, start, prog = [ctx.message.author], time(), 0
    while time() < start + startup and len(membs) < full:
        if gamechannels[ctx.message.channel.id] == 0:
            return
        n = await client.wait_for_message(timeout=1, content="join")
        if n is not None and n.author not in membs:
            await client.say("{}, you've been added to the game.".format(servnick(n.author)))
            membs.append(n.author)
        if time() > start + startup - 120 and prog < 1:
            prog = 1
            await client.say("Starting in **2 minutes.**")
        if time() > start + startup - 60 and prog < 2:
            prog = 2
            await client.say("Starting in **1 minute.**")
        if time() > start + startup - 30 and prog < 3:
            prog = 3
            await client.say("Starting in **30 seconds.**")
        if time() > start + startup - 5 and prog < 4:
            prog = 4
            await client.say("Starting in **5 seconds.**")
    if len(membs) == full:
        await client.say("The game is now full. ***Starting...***")
    elif len(membs) == 1:
        gamechannels[ctx.message.channel.id] = 0
        return await client.say("You can't start a game with just one person.\nGame cancelled.")
    else:
        await client.say("***Starting...***")
    gamechannels[ctx.message.channel.id] = 1
    deck = list(pk.cards())
    pk.shuffle(deck)
    await client.say("**Players:** {}".format(", ".join([servnick(i) for i in membs])))
    await asyncio.sleep(1)
    await client.say("*Determining play order...*")
    bems = membs[1:]
    pk.shuffle(bems)
    membs = [ctx.message.author] + bems
    await asyncio.sleep(2)
    await client.say("**Play Order:**\n{}".format("\n".join(["{}. {}".format(m + 1, servnick(membs[m])) for m in range(len(membs))])))
    await asyncio.sleep(5)
    await client.say("*Dealing cards...*")
    await asyncio.sleep(3)
    hands = pk.hands(len(membs), 2, deck)
    membands, deck = {membs[i].id: hands[0][i] for i in range(len(membs))}, hands[1]
    for i in membs:
        await client.send_message(i, content="Your hand: {}".format(membands[i.id].txt()))
    await client.say("Players, your hands have been DM'd to you. Reply ``ready`` here or in DM once you're ready.\n"
                     "The game will begin when all players are ready.")
    start, prog, readict, dmdict = time(), 0, {mem.id: 0 for mem in membs}, {u.id: await get_dm(u) for u in membs}
    while True:
        m = await client.wait_for_message(timeout=1, content="ready", check=lambda s:
            (s.channel in list(dmdict.values()) or s.channel == ctx.message.channel) and s.author in membs)
        if m is not None and readict[m.author.id] == 0:
            await client.send_message(m.author, content="Confirmed.")
            readict[m.author.id] = 1
        if 0 not in readict.values():
            break
        if prog < (time() - start) // 30:
            prog += 1
            await client.say("Players still not ready: {}".format(", ".join([mem.mention for mem in membs if readict[mem.id] == 0])))
    await client.say("**All players are now ready.** Blinds will now be made.")
    for m in membs:
        initvals(m.id)
    await client.say("{} will place a small blind of $1, and {} will place a large blind of $2."
                     .format(membs[1].mention, membs[2 % len(membs)].mention))
    betdict = {m.id: 0 for m in membs}
    betdict[0] = 2
    addval(membs[1], -1)
    addval(membs[2 % len(membs)], -2)
    betdict[membs[1].id] = 1
    betdict[membs[2 % len(membs)].id] = 2
    comm = "There are no community cards yet."

    def pot():
        return sum([betdict[i] for i in list(betdict.keys()) if i != 0])

    async def bet(pos=0):
        opened = 1 if pos > 0 else 0
        if pos > len(membs):
            pos = pos % len(membs)

        async def fold(u):
            await client.say("{} has folded. A shame.".format(servnick(u)))
            membs.remove(u)

        async def check(u):
            await client.say("{} has checked.".format(servnick(u)))

        async def call(u):
            await client.say(str(betdict[u.id]) + str(betdict[0]))
            if betdict[0] <= betdict[u.id]:
                return await client.say("{} has called, placing no money in the pot.".format(servnick(u)))
            await client.say("{} has called, placing ${} in the pot.".format(servnick(u), betdict[0] - betdict[u.id]))
            addval(u, betdict[u.id] - betdict[0])
            betdict[u.id] = betdict[0]

        async def braise(u, b):
            await client.say("{} has raised the bet by ${}.".format(servnick(u), b))
            addval(u, betdict[u.id] - betdict[0] - b)
            betdict[0] += b
            betdict[u.id] = betdict[0]

        async def pbet(u):
            await client.say("The current bet is ${}. You have put in ${}.".format(betdict[0], betdict[u.id]))

        async def pcomm(u):
            if type(comm) == str:
                return await client.say(comm)
            await client.say("Community cards: {}".format(comm.txt()))

        async def ppot(u):
            await client.say("There is ${} in the pot.".format(pot()))

        async def getplay(u):
            while True:
                comd = await client.wait_for_message(timeout=30, author=u,
                                                     check=lambda c: c.content.split(" ")[0] in cmdict.keys())
                if comd is not None:
                    if comd.content.split(" ")[0] in ["raise", "open"]:
                        try:
                            comd = ["raise", int(comd.content.split(" ")[1])]
                        except ValueError:
                            await client.say("Please use a number.")
                        except IndexError:
                            await client.say("Please include the value when using ``raise <amount>``.")
                        else:
                            break
                    elif comd.content.split(" ")[0] == "check" and opened != 0:
                        await client.say("You can't check after the betting round has been opened.")
                    elif comd.content.split(" ")[0] in ["comm", "pot", "betval"]:
                        await (cmdict[comd.content.split(" ")[0]])(u)
                    else:
                        comd = [comd.content.split(" ")[0]]
                        break
                else:
                    await client.say("{}, it's your turn.".format(u.mention))
            return comd

        cmdict = {"fold": fold, "check": check, "call": call, "raise": braise, "open": braise,
                  "betval": pbet, "comm": pcomm, "pot": ppot}
        await client.say("Commencing betting round...")
        await asyncio.sleep(2)
        while True:
            mem = membs[pos]
            await client.say("{}'s turn.".format(servnick(mem)))
            cmd = await getplay(mem)
            if cmd[0] == "raise":
                await braise(mem, int(cmd[1]))
                opened = 1
            else:
                await (cmdict[cmd[0]])(mem)
                if cmd[0] == "fold":
                    pos -= 1
            if len(membs) == 1:
                return
            if [betdict[i.id] for i in membs].count(betdict[membs[0].id]) == len(membs) and not\
                    (pos != len(membs) - 1 and cmd[0] == "check"):
                await asyncio.sleep(0.5)
                await client.say("Betting round complete.")
                return
            pos += 1
            if pos == len(membs):
                pos = 0

    await client.say("```ml\nROUND ZERO: BLIND BETS```")
    await bet(3)
    crea = pk.hands(1, 3, deck)
    comm, deck = crea[0][0], crea[1]
    if len(membs) == 1:
        await client.say("**{}** wins the ${} pot!".format(membs[0].mention, pot()))
        addval(membs[0], pot())
        gamechannels[ctx.message.channel.id] = 0
        return
    await asyncio.sleep(1)
    await client.say("```ml\nROUND ONE: THE FLOP```")
    await asyncio.sleep(2)
    await client.say("**Community cards:** {}".format(comm.txt()))
    await asyncio.sleep(10)
    await bet()
    if len(membs) == 1:
        await client.say("**{}** wins the ${} pot!".format(membs[0].mention, pot()))
        addval(membs[0], pot())
        gamechannels[ctx.message.channel.id] = 0
        return
    await asyncio.sleep(1)
    await client.say("```ml\nROUND TWO: THE TURN```")
    await asyncio.sleep(2)
    await client.say("**Turn card:** {}".format(str(pk.Card(deck[0]))))
    comm.insert(deck[0])
    await asyncio.sleep(1)
    await client.say("**Community cards:** {}".format(comm.txt()))
    await asyncio.sleep(10)
    await bet()
    if len(membs) == 1:
        await client.say("**{}** wins the ${} pot!".format(membs[0].mention, pot()))
        addval(membs[0], pot())
        gamechannels[ctx.message.channel.id] = 0
        return
    await client.say("```ml\nROUND THREE: THE RIVER```")
    await asyncio.sleep(2)
    await client.say("**River card:** {}".format(str(pk.Card(deck[1]))))
    comm.insert(deck[1])
    await asyncio.sleep(1)
    await client.say("**Community cards:** {}".format(comm.txt()))
    await asyncio.sleep(10)
    await bet()
    if len(membs) == 1:
        await client.say("**{}** wins the ${} pot!".format(membs[0].mention, pot()))
        addval(membs[0], pot())
        gamechannels[ctx.message.channel.id] = 0
        return
    combos, membos = list(pk.combos()), {}
    for mem in membs:
        await client.send_message(mem, "It's time for the final showdown. Which three community cards will you play"
                                       " alongside your hand?\n{}\nReply using any three numbers from 1 to 5,"
                                       " in ascending order and separated by spaces (e.g. ``1 3 4``).\n"
                                       "Card #1 is {}, card #2 is {}, and so on."
                                       .format(comm.txt(), str(comm.cards[0]), str(comm.cards[1])))
    start, prog = time(), 0
    while True:
        m = await client.wait_for_message(timeout=30, check=lambda s:
                                          (s.content in combos and s.author in membs and
                                           s.channel in dmdict.values()))
        if m is not None:
            membos[m.author.id] = membands[m.author.id]
            for i in [int(g) - 1 for g in m.content.split(" ")]:
                membos[m.author.id].insert(str(comm.cards[i]))
            client.send_message(m.author, "**Your play:** {}".format(membos[m.author.id].txt()))
        if len(list(membos.keys())) == len(membs):
            break
        if prog < (time() - start) // 30:
            prog += 1
            await client.say("Players still not ready: {}".format(
                ", ".join([mem.mention for mem in membs if mem.id not in membos])))
    await client.say("All players are now ready.")
    await client.say("```ml\nTHE SHOWDOWN```")
    await asyncio.sleep(1)
    await client.say("**Community cards:** {}".format(comm.txt()))
    await asyncio.sleep(2)
    for u in membs:
        await client.say("{}'s play: {}".format(servnick(u), membos[u.id].txt(True)))
        await asyncio.sleep(0.5)
    sd = pk.showdown([membos[u.id] for u in membs])
    await asyncio.sleep(2)
    await client.say("**{}** wins the showdown and the ${} pot!".format(membs[sd[0][7]].mention, pot()))
    addval(membs[0], pot())
    gamechannels[ctx.message.channel.id] = 0'''


@client.command(pass_context=True)
async def jotto(ctx):
    async def jotsay(s, **kwargs):
        await emolsay(":green_book:", s, hexcol("65c245"), **kwargs)

    word, u = choice(wr.wordDict[4]), ctx.message.author
    game = jo.Jotto(word)
    await jotsay("The word has been chosen. Start guessing!", d="To guess, just say a four-letter word.\n"
                                                                "To check your guess history, say ``history``.\n"
                                                                "To forfeit, say ``forfeit``.")
    while True:
        guess = await client.wait_for_message(timeout=120, author=u, channel=ctx.message.channel,
                                              check=(lambda c: len(c.content) == 4 or
                                                     c.content.lower() in ["forfeit", "history"]))
        if guess is None:
            return await errsay("Jotto game timed out.")
        g = guess.content.lower()
        if g == "forfeit":
            return await jotsay("Game forfeited. The word was \"{}\".".format(word))
        elif g == "history":
            await jotsay("Guess History", d="\n".join(["**{}:** {}".format(i, game.history[i])
                                                      for i in list(game.history.keys())]))
        elif g not in wr.wordList:
            await jotsay("That's not a valid word.")
        elif g in game.history:
            await jotsay("You've already guessed that word.")
        else:
            if g == word:
                return await jotsay("Correct! It took you {} guesses.".format(len(game.history)))
            acc = game.guess(g)
            await jotsay("There {} correct letter{} in \"{}\"."
                         .format(["are no", "is one", "are two", "are three", "are four"][acc], "" if acc == 1 else "s", g))


@client.command(pass_context=True)
async def hangman(ctx: Context, category=None):
    def conhang(s, **kwargs):
        return conemol(":skull_crossbones:", s, hexcol("ccd4de"), **kwargs)

    async def hangsay(s, **kwargs):
        return await client.say(embed=conhang(s, **kwargs))

    if category is None:
        category = choice(list(hm.hangdict.keys()))
    if category.lower() == "categories":
        return await hangsay("Categories: {}".format(", ".join(list(hm.hangdict.keys()))))
    if category is not None and category not in hm.hangdict:
        return await errsay("That is not a valid category.")
    term = choice(hm.hangdict[category][1])
    game = hm.Hangman(term)
    screen = await hangsay(f"The category is {hm.hangdict[category][0]}.", d=f"```{game.blanks()}```")
    while True:
        guess = await client.wait_for_message(timeout=120, author=ctx.message.author, channel=ctx.message.channel,
                                              check=(lambda c: len(c.content) == 1 and c.content.lower() in hm.letters
                                                     or c.content.lower() == game.term))
        if guess is None:
            return await errsay("Hangman game timed out.")
        try:
            await asyncio.sleep(0.1)
            await delete_message(guess)
        except discord.errors.HTTPException:
            pass
        g = guess.content.lower()
        if g.upper() in game.guessed:
            title = "You've already guessed that letter."
        else:
            if len(g) == 1:
                score = game.guess(g)
                title = f"There {hm.verb[score]} {hm.numbers[score]} {g}{hm.suffix[score]}."
            else:
                title = "Correct!"
                break
            if game.miss == 6:
                title = f"You lose! The term was..."
                break
            chex = [c.upper() in game.guessed or c not in hm.letters for c in game.term]
            if chex.count(True) == len(chex):
                title = "Congratulations! The term was \"{}.\"".format(game.upterm)
                break
        await client.edit_message(screen,
                                  embed=conhang(title, d=f"```ml\n{game.blanks()}\n\nguessed: {' '.join(game.guessed)}"
                                                f"\nincorrect guesses remaining: {round(6 - game.miss)}```"))
    await client.edit_message(screen,
                              embed=conhang(title, d=f"```ml\n{game.revealed()}\n\nguessed: {' '.join(game.guessed)}"
                                            f"\nincorrect guesses remaining: {round(6 - game.miss)}```"))


'''@client.command(pass_context=True)
async def yahtzee(ctx: Context, func=None):
    async def yahtsay(s, d=None, fs=None):
        await emolsay(":game_die:", s, hexcol("ec3b63"), d=d, fs=fs)

    if func is None:
        return await yahtsay("Please input a function.")
    if func not in ["host", "scoring", "rules", "rematch", "cancel"]:
        return await errsay("That's not a valid function.")

    if func == "scoring":
        return await yahtsay("Scoring",
                             fs={"Upper Level": IL("A set of dice can be scored in aces (ones), twos, threes, fours, "
                                                   "fives, or sixes. Aces scores 1 point per roll of 1, twos scores "
                                                   "2 points per roll of 2, etc.\nA score of 63 or more from the "
                                                   "upper level will net the player a bonus 35 points."),
                                 "Three of a Kind": "Three of any roll. Scores the sum of all dice.",
                                 "Four of a Kind": "Four of any roll. Scores the sum of all dice.",
                                 "Full House": "Two of one roll, three of another. Scores 25 points.",
                                 "Small Straight": "1-2-3-4, 2-3-4-5, or 3-4-5-6. Scores 30 points.",
                                 "Large Straight": "1-2-3-4-5 or 2-3-4-5-6. Scores 40 points.",
                                 "Yahtzee": "Five of any roll. Scores 50 points.",
                                 "Chance": "Can be used on any roll. Scores the sum of all dice."})

    if func == "rules":
        return await yahtsay("How to Play", d="Each game of Yahtzee consists of thirteen rounds. During each round, "
                                              "each player rolls five dice. They can then choose to keep any of those "
                                              "dice, and re-roll the rest. They do this once more, and the five dice "
                                              "resulting are the player's roll.\n\nThe player then scores their roll. "
                                              "A roll can be scored in any of thirteen categories (``z!yahtzee "
                                              "scoring``), each netting a different number of points. However, *only "
                                              "one roll can be scored for each category.* If all of a roll's categories"
                                              " are already scored, it must be scored in a category where it nets zero "
                                              "points. After thirteen rounds, each player's scores are tallied, and "
                                              "the player with the highest total score wins.")

    if func == "cancel":
        g = gamechannels.get(ctx.message.channel.id, [0, "none"])
        if g[0] == 0:
            return await yahtsay("There is no game running.")
        if g[1] != "yahtzee":
            return await yahtsay("There is no Yahtzee game running.")
        if g[0] == 1:
            return await yahtsay("You can't cancel a game mid-session.")
        if g[0] != ctx.message.author.id:
            return await yahtsay("You are not the host!")
        gamechannels[ctx.message.channel.id] = [0, "none"]
        return await yahtsay("Game cancelled.")

    startup = 20 if func == "rematch" else 120
    if func in ["host", "rematch"]:
        gamechannels[ctx.message.channel.id] = [ctx.message.author.id, "yahtzee"]
        membs = await getplayers(4, 60, yahtsay, {"s": "{} is hosting a game of Yahtzee."
                                                  .format(servnick(ctx.message.author)), "fs": None,
                                                  "d": "To join, say ``join``. To learn how to play, use "
                                                       "``z!yahtzee rules``. To check scoring categories, use "
                                                       "``z!yahtzee scoring``. The game will begin in **{}.**"
                                                  .format("2 minutes" if startup == 120 else "20 seconds")},
                                 ctx.message.author, ctx.message.channel)
        if membs is None:
            gamechannels[ctx.message.channel.id] = [0, "none"]
            return
        if len(membs) < 2:
            gamechannels[ctx.message.channel.id] = [0, "none"]
            return await yahtsay("Not enough players. Cancelling game.")
        await yahtsay("Determining play order...")
        pk.shuffle(membs)
        await asyncio.sleep(2)
        await yahtsay("Play Order", d="\n".join(["{}: {}".format(n + 1, servnick(membs[n])) for n in range(len(membs))]))
        await asyncio.sleep(2)
        await yahtsay("Initializing game...",
                      d="When it's your turn, say ``roll`` to start your turn. The bot will roll dice for you. Choose "
                        "the dice you want to keep, then say ``reroll`` + the dice you want to re-roll: die A, B, C, D,"
                        " or E. For example, if you rolled [1, 4, 2, 3, 6], and you wanted to keep the 4 and the 6, "
                        "say ``reroll A C D``. If you don't want to re-roll any dice, say ``pass``. To check the "
                        "possible scores for a roll, say ``scores``.")
        await asyncio.sleep(10)
        game = yz.Yahtzee(membs)
        for rd in range(13):
            await yahtsay("ROUND {}".format(hm.numbers[rd + 1].upper()))
            for turn in range(len(membs)):
                await yahtsay("{}, it's your turn.".format(servnick(membs[turn])))
                act = await client.wait_for_message(timeout=600, author=membs[turn], content="roll")
                if act is None:
                    gamechannels[ctx.message.channel.id] = [0, "none"]
                    return await yahtsay("Yahtzee game timed out.")
                roll = yz.roll([])
                await yahtsay("Your roll: ``{}``".format(roll))
                throw = 0
                while round(throw) < 2:
                    act = await client.wait_for_message(timeout=600, author=membs[turn],
                                                    check=(lambda c: c.content in ["pass", "scores"] or
                                                           c.content.split(" ")[0] == "reroll" and len(c.content) > 7))
                    if act.content == "pass":
                        break
                    elif act.content == "scores":
                        scar = game.getscores(roll, membs[turn].id)
                        await yahtsay("Scoring for {}:".format(roll),
                                      d="\n".join(["**{}:** {}".format(key, scar[key]) for key in list(scar.keys())]))
                    else:
                        reroll = [g.upper() for g in act.split(" ")[1:]]
                        roll = yz.roll([roll[i] for i in range(5) if chr(i + 65) not in reroll])
                        await yahtsay("Your roll: ``{}``".format(roll))
                        throw += 1
                scar = game.getscores(roll, membs[turn].id)
                await yahtsay("Scoring for {}:".format(roll),
                              d="\n".join(["**{}**: {}".format(key, scar[key]) for key in list(scar.keys())]))
                await yahtsay("Which category do you want to score this roll in?")
                do = await client.wait_for_message(timeout=600, author=membs[turn],
                                                   check=(lambda c: c.content in scar.keys()))
                if do is None:
                    gamechannels[ctx.message.channel.id] = [0, "none"]
                    return await yahtsay("Yahtzee game timed out.")
                game.scores[membs[turn].id][do.content] = scar[do.content]
                if sum([game.scores[membs[turn].id][i] for i in game.cats[:6]]) >= 63:
                    game.scores[membs[turn].id]["Bonus"] = 35
                await yahtsay("Your scores:",
                              d="\n".join(["**{}:** {}".format(i, game.scores[membs[turn].id][i]) for i in game.cats]))
        await asyncio.sleep(1)
        await yahtsay("FINAL SCORING")
        await asyncio.sleep(2)
        for u in membs:
            if sum([game.scores[u.id][i] for i in game.cats[:6]]) < 63:
                game.scores[u.id]["Bonus"] = 0
            await yahtsay("{}'s scores:".format(servnick(u)),
                          d="\n".join(["**{}:** {}".format(i, game.scores[u.id][i]) for i in game.cats]))
            await asyncio.sleep(2)
        endscores = {servnick(u): game.endscore(u.id) for u in membs}
        await yahtsay("Final scores:",
                      d="\n".join(["**{}** - {}".format(key, round(endscores[key])) for key in list(endscores.keys())]))
        await asyncio.sleep(1)
        return await yahtsay("{} wins!".format(sorted(list(endscores.keys()), key=lambda i: endscores[i])[-1]))
'''


'''
@client.command(pass_context=True)
async def uno(ctx: Context, func=None):
    async def unosay(s, d=None, fs=None, footer=None):
        await emolsay(":flag_mu:", s, unocol, d=d, fs=fs, footer=footer)

    if func is None:
        return await errsay("Please input a function.")
    if func not in ["host", "rematch", "cancel", "rules", "cards"]:
        return await errsay("That is not a recognized function.")

    if func == "rules":
        return await unosay("there's gonna be a rules thing here eventually I promise")
    if func == "cards":
        return await unosay("something that explains how this all works")
    if func == "cancel":
        g = gamechannels.get(ctx.message.channel.id, [0, "none"])
        if g[0] == 0:
            return await unosay("There is no game running.")
        if g[1] != "uno":
            return await unosay("There is no Uno game running.")
        if g[0] == 1:
            return await unosay("You can't cancel a game mid-session.")
        if g[0] != ctx.message.author.id:
            return await unosay("You are not the host!")
        gamechannels[ctx.message.channel.id] = [0, "none"]
        return await unosay("Game cancelled.")

    startup = 20 if func == "rematch" else 120
    coldict = {"R": hexcol("ff363b"), "G": hexcol("3cba49"), "B": hexcol("4000ff"), "Y": hexcol("fab300"),
               "W": hexcol("c800ff"), "D": hexcol("ff00ff")}
    if func in ["host", "rematch"]:
        gamechannels[ctx.message.channel.id] = [ctx.message.author.id, "uno"]
        membs = await getplayers(10, startup, unosay, {"s": "{} is hosting a game of Uno."
                                                       .format(servnick(ctx.message.author)), "fs": None,
                                                       "d": "To join, say ``join``. To learn how to play, use "
                                                       "``z!uno rules``. The game will begin in **{}.**"
                                                       .format("2 minutes" if startup == 120 else "20 seconds")},
                                 ctx.message.author, ctx.message.channel)
        if membs is None:
            gamechannels[ctx.message.channel.id] = [0, "none"]
            return
        if len(membs) < 3:
            gamechannels[ctx.message.channel.id] = [0, "none"]
            return await unosay("Not enough players. Cancelling game.")
        await unosay("Determining play order...")
        un.shuffle(membs)
        await asyncio.sleep(2)
        await unosay("Play Order", d="\n".join(["{}: {}".format(n + 1, servnick(membs[n])) for n in range(len(membs))]))
        await asyncio.sleep(2)
        await unosay("Dealing hands...")
        await asyncio.sleep(5)
        hands = un.hands(len(membs))
        memhands, deck, play = {membs[i].id: hands[0][i] for i in range(len(membs))}, hands[1], []
        for i in membs:
            await client.send_message(i, content="Your hand: {}".format(memhands[i.id].txt()))
        await unosay("Players, your hands have been PM'd to you. The game will begin in 30 seconds.")
        await asyncio.sleep(30)
        await unosay("Game starting...", d="When it's your turn, say the name of the card you'd like to play - e.g. "
                                           "``R4`` to play a red 4, or ``BD`` to play a blue draw-2. When playing a "
                                           "wild card (``WC``) or a wild draw-4 (``DF``), add the color you want to "
                                           "switch to after the card name - e.g. ``WC red`` or ``DF green``. If you "
                                           "can't play a card, say ``draw``.")
        await asyncio.sleep(7)
        play.append(deck[0])
        del deck[0]
        await unosay("The first card is a {}.".format(play[0]), d=un.instructions.get(play[0][0], None))
        while play[0] == "DF":
            deck.append(play[0])
            play = []
            await unosay("The first card is a {}.".format(play[0]), d=un.instructions.get(play[0][0], None))
        if play[0][1] == "R":
            dir, pos, drawing, wild = -1, len(membs) - 1, 0, False
        elif play[0][1] == "S":
            dir, pos, drawing, wild = 1, 1, 0, False
        elif play[0][1] == "D":
            dir, pos, drawing, wild = 1, 0, 2, False
        elif play[0][1] == "C":
            dir, pos, drawing, wild = 1, 0, 0, True
        else:
            dir, pos, drawing, wild = 1, 0, 0, False
        while True:
            pos = 0 if pos == len(membs) else len(membs) - 1 if pos == -1 else pos
            await unosay(f"{servnick(membs[pos])}, it's your turn.", footer="**Hands:** {}"
                         .format(", ".join(["{} - {}".format(servnick(u), len(memhands[u.id])) for u in membs])))
            while True:
                card = await client.wait_for_message(timeout=300, author=membs[pos],
                                                     check=lambda c: c.content.split()[0] in un.cards
                                                                     or c.content == "draw")
                if card is None:
                    gamechannels[ctx.message.channel.id] = [0, "none"]
                    return await unosay("Uno game timed out.")
                du = card.content.split()
                if du[0] not in memhands[membs[pos].id] or\
                    ((du[0][0] != play[-1][0] and du[0][1] != play[-1][1]) and du[0] not in ["WC", "DF"] and not wild):
                    await unosay("You can't play that.")
                else:
                    if len(du) == 1:
                        if du[0] in ["WC", "DF"]:
                            await unosay("Please include a color.")
                        else:
                            break
                    else:
                        if du[0] not in ["WC", "DF"]:
                            break
                        elif du[1].lower() not in ["red", "green", "blue", "yellow"]:
                            await unosay("That's not a valid color.")
                        else:
                            break
            if du[0] != "draw":
                await emolsay(":flag_mu:", "{} has played a{} {}."
                              .format(servnick(membs[pos]), "n" if du[0][0] == "R" else "", du[0]), coldict[du[0][0]],
                              footer="The color is now {}.".format(du[1]) if len(du) > 1 else None)
                play.append(du[0])
                if len(memhands[membs[pos]]) == 1:
                    await unosay("UNO!")
                if len(memhands[membs[pos]]) == 0:
                    return await unosay(f"{servnick(membs[pos])} has played their last card!")
            pos = round(pos + dir)'''


@client.command(pass_context=True)
async def boggle(ctx):
    def conbog(s, **kwargs):
        return conemol(":hourglass:", s, hexcol("ffac33"), **kwargs)

    async def bogsay(s, **kwargs):
        return await client.say(embed=conbog(s, **kwargs))

    b = bg.Board()
    possible = [g for g in wr.wordList if set(c.upper() for c in "q".join(g.split("qu"))) <= set(c for c in b.board)
                and g[0].upper() in b.board and len(g) >= 3]
    possible = [g for g in possible if b.find(g)]
    screen = await bogsay("Boggle", d=f'```ml\n{str(b)}```\nYou have three minutes. Go!')
    start = time()
    while time() < start + 180:
        guess = await client.wait_for_message(timeout=ceil(start + 180 - time()), author=ctx.message.author,
                                              channel=ctx.message.channel)
        if guess is None:
            break
        try:
            await asyncio.sleep(0.1)
            await delete_message(guess)
        except discord.errors.HTTPException:
            pass
        guess = guess.content.lower()
        title = "Boggle"
        if len(guess.split()) > 1:
            pass
        elif len(guess) < 3:
            title = "Words must be at least three letters long."
        elif guess == "finishgame":
            break
        elif guess not in wr.wordList:
            title = "That's not a word."
        elif guess in b.guessed:
            title = "You already used that word."
        elif guess not in possible:
            title = "Word not in board."
        else:
            b.guessed.append(guess)
            b.score(guess)
            score = 1 if len(guess) < 5 else 2 if len(guess) == 5 else 3 if len(guess) == 6 else\
                5 if len(guess) == 7 else 11
            title = f"Scored {str(score)} points for '{guess}'!"
        await client.edit_message(screen, embed=conbog(title, d=f'```ml\n{str(b)}```\n'
                                                       f'Time remaining: {round(start + 180 - time())} s',
                                                       footer=f"Used words: {none_list(sorted(b.guessed))}"))
    await bogsay("Time's up!", d=f"**Your words:** *{', '.join(b.guessed)}*\n\n**Your score: {b.points}**\n\n"
                                 f"**Words you missed:** *{', '.join([g for g in possible if g not in b.guessed])}*")


@client.command(pass_context=True)
async def anagrams(ctx):
    def conana(s, **kwargs):
        return conemol(":closed_book:", s, hexcol("dd2e44"), **kwargs)

    async def anasay(s, **kwargs):
        return await client.say(embed=conana(s, **kwargs))

    def form(lts):
        return f"```prolog\n|\u00a0{chr(160).join([g.upper() for g in lts])}\u00a0|```"

    ans, a = [], []
    while len(ans) < 20:
        a = wr.sample(wr.anagramsDist, 8)
        ans = [g for g in wr.anagrams(a) if len(g) >= 3]
    guessed = []
    tut = "Say ``reshuf`` to shuffle the letters. Say ``finishgame`` to finish."
    screen = await anasay("Your Letters", d=tut + form(a), footer=f"There are {len(ans)} usable words.")
    start = time()
    while True:
        guess = await client.wait_for_message(timeout=ceil(start + 180 - time()), author=ctx.message.author,
                                              channel=ctx.message.channel)
        if guess is None:
            break
        try:
            await asyncio.sleep(0.1)
            await delete_message(guess)
        except discord.errors.HTTPException:
            pass
        guess = guess.content.lower()
        title = "Anagrams"
        if len(guess.split()) > 1:
            pass
        elif len(guess) < 3:
            title = "Words must be at least three letters long."
        elif guess == "reshuf":
            bg.shuffle(a)
            title = "Shuffled!"
        elif guess == "finishgame":
            break
        elif guess not in wr.wordList:
            title = "That's not a word."
        elif guess in guessed:
            title = "You already used that word."
        elif guess not in ans:
            title = "You can't form that word."
        else:
            guessed.append(guess)
            title = f"Scored '{guess}'!"
        await client.edit_message(screen, embed=conana(title, d=form(a) + f"\nTime remaining:"
                                                       f" {round(start + 180 - time())} s",
                                                       footer=f"Used words: {none_list(sorted(guessed))}"))
    missed = [g for g in ans if g not in guessed]
    return await anasay("Time's up!",
                        d=f"**Words you missed:** {', '.join(missed)} ({len(missed)})" if len(missed) > 0 else
                          "**Words you missed:** *none!*")


@client.command(pass_context=True)
async def duel(ctx: Context, opponent: discord.Member):
    async def duelsay(s: str, **kwargs):
        return await emolsay(":gun:", s, hexcol("9AAAB4"), **kwargs)

    if opponent is None:
        return await errsay("No opponent input.")
    if type(opponent) != discord.Member:
        return await errsay("Invalid opponent.")
    if opponent.bot:
        return await errsay("Bots can't duel.")
    if opponent == ctx.message.author:
        return await errsay("You can't duel yourself.")

    await duelsay(f"{opponent.display_name}, do you accept the challenge?",
                  d="Say ``yes`` to accept; say ``no`` to chicken out.")
    con = await client.wait_for_message(timeout=60, author=opponent, channel=ctx.message.channel,
                                        check=lambda c: c.content.lower() in ["yes", "no"])
    if con is None:
        return await duelsay("Duel challenge timed out.")
    if con.content.lower() != "yes":
        return await duelsay(f"{opponent.display_name} chickened out.")

    gun_check = lambda c: c.author in [ctx.message.author, opponent] and c.content in [":gun:", "🔫"]
    await duelsay("A duel has been declared!", d="When I say draw, send the gun emoji :gun: as fast as you can.")
    await asyncio.sleep(1)
    await duelsay("Ready...")
    false_start = await client.wait_for_message(timeout=3 + 7 * random(), check=gun_check)
    if false_start is not None:
        return await emolsay(":boom:", f"{false_start.author.display_name} drew early. Shame.", hexcol("880000"))
    await duelsay("Draw!!")

    winner = await client.wait_for_message(timeout=10, check=gun_check)
    if winner is None:
        return await duelsay("Nobody drew. :pensive:")
    loser = await client.wait_for_message(timeout=1, check=lambda c: gun_check(c) and c.author != winner.author)
    if loser is None:
        delta = None
    else:
        if loser.timestamp < winner.timestamp:
            loser, winner = winner, loser
        delta = loser.timestamp - winner.timestamp
        delta = f"{delta.seconds}.{str(delta.microseconds)[:3]}"
    return await duelsay(f"{winner.author.display_name} wins!!",
                         footer=f"by {delta} seconds" if delta else None)


async def risksay(s: str, **kwargs):
    return await emolsay(":drum:", s, hexcol("9D0522"), **kwargs)


def conrisk(s: str, **kwargs):
    return conemol(":drum:", s, hexcol("9D0522"), **kwargs)


def risk_no_title(**kwargs):
    return conembed(col=hexcol("9D0522"), **kwargs)


class DiscordRisk(rk.Game):
    def __init__(self, channel: discord.Channel, *players, **kwargs):
        super().__init__(password=kwargs.get("password"))
        self.channel = channel
        self.users = {rk.playerOrder[g]: players[g] for g in range(len(players))}
        self.image = rk.Image.open(rk.directory + "nqr.png")
        self.statusMessage = null_message()
        self.tempMessage = null_message()
        self.saveState = copy(self)
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

    async def update_status(self, phase: str):
        string = "\n".join([
            f"{g}: {len([j for j in self.board.provinces.values() if j.owner == g])} provinces / "
            f"{sum([j.troops for j in self.board.provinces.values() if j.owner == g])} troops / "
            f"{floor(len([j for j in self.board.provinces.values() if j.owner == g]) / 2)} TPT" for g in self.players
        ])
        self.image.save(f"storage/risk-{str(self)[0]}.png")
        kwargs = {
            "s": f"{self.playerOrder[self.atBat]}'s turn - {phase} Phase".upper(),
            "d": string,
            "footer": str(self.saveState),
            "image": await image_url(f"storage/risk-{str(self)[0]}.png")
        }
        try:
            await client.edit_message(self.statusMessage, embed=conrisk(**kwargs))
        except AttributeError:
            self.statusMessage = await risksay(**kwargs)

    async def say(self, s: str, **kwargs):
        try:
            await delete_message(self.tempMessage)
        except AttributeError:
            pass
        self.tempMessage = await risksay(s, **kwargs)

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
        def no_neighbors(s: str):
            for pro in rk.borders[s]:
                if self.board.provinces[pro].owner is not None:
                    return False
            return True

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
        self.saveState = copy(self)

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
        attack_str = " ".join([getemoji(f"attack{g}") for g in attack])
        defense_str = " ".join([getemoji(f"defense{g}") for g in defense])
        losses_str = (f"Attacker loses **{hm.numbers[hold.count(True)]}** {plural('regiment', hold.count(True))}."
                      if True in hold else "") +\
            ("\n" if True in hold and False in hold else "") +\
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

    async def wait_for_message(self, timeout: int=None, author: discord.Member=None, check: callable=None):
        while True:
            message = await client.wait_for_message(timeout=timeout, author=author, check=check)
            if message is None:
                return await self.quit("Game timed out.")
            message = message.content
            if message.lower() == "quit":
                return await self.quit()
            if message.lower() == "map":
                await self.say("Map Link", url="https://cdn.discordapp.com/attachments/405184040627601410/"
                                               "527965910556999701/nqr_names.png")
                continue
            return message

    async def run(self):
        def is_int_str(s: str):
            try:
                int(s)
            except ValueError:
                return False
            return True

        def is_owned_province(s: str, plr: str):
            return s in rk.borders and self.board.provinces[s].owner == plr

        def valid_reinforce(s: str, plr: str):
            s = s.title().split()
            if True not in [is_owned_province(g, plr) for g in s]:
                return False  # "You didn't name an owned province to reinforce."
            dest = [g for g in s if g in rk.borders and self.board.provinces[g].owner == plr][0]
            if True not in [is_int_str(g) for g in s]:
                return False  # You didn't specify how many regiments to reinforce."
            num = int([g for g in s if is_int_str(g)][0])
            return {"prov": dest, "num": num}

        def valid_attack(s: str, plr: str):
            if s.lower() == "done":
                return {"done": True}
            s = s.title().split()
            if True not in [is_owned_province(g, plr) for g in s]:
                return False  # "You didn't name a province you own to attack from."
            src = [g for g in s if g in rk.borders and self.board.provinces[g].owner == plr][0]
            if True not in [(g in rk.borders and self.board.provinces[g].owner != plr) for g in s]:
                return False  # "You didn't name a neighboring enemy province to attack."
            dest = [g for g in s if g in rk.borders and self.board.provinces[g].owner != plr][0]
            if True not in [is_int_str(g) for g in s]:
                return False  # "You didn't specify how many regiments to attack with."
            num = int([g for g in s if is_int_str(g)][0])
            return {"from": src, "to": dest, "with": num}

        def valid_move(s: str, plr: str):
            if s.lower() == "done":
                return {"done": True}
            s = s.title().split()
            if "To" not in s or "From" not in s:
                return False
            if s.index("From") == len(s) - 1 or not is_owned_province(s[s.index("From") + 1], plr):
                return False
            src = s[s.index("From") + 1]
            if s.index("To") == len(s) - 1 or not is_owned_province(s[s.index("To") + 1], plr):
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
                                   d="To reinforce, say ``<province> <number>``.")
                    command = await self.wait_for_message(
                        timeout=300,  # author=self.users[player],
                        check=lambda c: valid_reinforce(c.content, player)
                    )
                    if command is None:
                        return
                    await delete_message(command)
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
            await self.say("ATTACK PHASE", d="To attack, say ``<target> from <source> with "
                                             "<number>``. When you're done, say ``done``.")
            while True:
                await self.update_status("Attack")
                command = await client.wait_for_message(
                    timeout=300,  # author=self.users[player],
                    check=lambda c: valid_attack(c.content, player)
                )
                if command is None:
                    return await self.quit("Game timed out.")
                await delete_message(command)
                command = valid_attack(command.content, player)
                if command.get("done"):
                    break
                if command.get("quit"):
                    return await self.quit()
                # this is where the fight or flight decision will go
                await self.attack(
                    self.board.provinces[command["from"]], command["with"], self.board.provinces[command["to"]]
                )

            # MOVE PHASE
            await self.say("MOVE PHASE", d="To move, say ``<number> from <source> to <destination>``. Make sure to "
                                           "include the prepositions so that the troops move in the right direction. "
                                           "When you're done moving, say ``done``.")
            while True:
                await self.update_status("Move")
                command = await client.wait_for_message(
                    timeout=300,  # author=self.users[player],
                    check=lambda c: valid_move(c.content, player)
                )
                if command is None:
                    return await self.quit("Game timed out.")
                await delete_message(command)
                command = valid_move(command.content, player)
                if command.get("done"):
                    break
                if command.get("quit"):
                    return await self.quit()
                await self.move(
                    self.board.provinces[command["from"]], self.board.provinces[command["to"]], command["num"]
                )

            # POST-TURN SAVE STATE
            self.atBat = (self.atBat + 1) % len(self.players)
            self.saveState = copy(self)


@client.command(pass_context=True)
async def risk(ctx: Context, cmd: str=None):
    if cmd is None:
        b = DiscordRisk(ctx.message.channel)
        b.randomize()
        await b.run()

    else:
        try:
            b = DiscordRisk(ctx.message.channel, password=cmd)
            await b.run()
        except IndexError:
            await risksay("Invalid password.")
