from startup import *
from random import randrange, sample, random
from minigames import connectfour as cf, jotto as jo, hangman as hm, boggle as bg, risk as rk
from utilities import words as wr
from copy import deepcopy as copy
from math import floor
import time


@zeph.command(
    aliases=["conn4"], usage="z!connect4 <@opponent>",
    description="Challenges someone to Connect Four.",
    help="Challenges an opponent to a nice game of Connect Four. Nothing is at stake - except your pride."
)
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
    await four.edit(
        init, embed, d="To make a move, reply with the **column number**. Left is `1`, right is `7`.\n"
                       "If the board gets too far away, reply with the ⏬ emoji to bring it back down."
    )
    await asyncio.sleep(2)

    board = cf.Board(
        zeph.strings["conn4empty"], zeph.strings["conn4red"], zeph.strings["conn4yellow"], zeph.strings["conn4white"],
        "".join([zeph.strings[f"c4c{g}"] for g in range(1, 8)])
    )
    message = await four.say("Initializing...")
    at_bat = 1
    checkers = {1: zeph.strings["checkerred"], -1: zeph.strings["checkeryellow"]}

    def pred(m: discord.Message):
        return m.channel == ctx.channel and m.author == players[at_bat] \
            and m.content in ["1", "2", "3", "4", "5", "6", "7", "⏬"]

    while True:
        await four.edit(message, f"{players[at_bat].display_name}'s turn. ({checkers[at_bat]})", d=str(board))

        try:
            move = await zeph.wait_for("message", timeout=300, check=pred)
        except asyncio.TimeoutError:
            return await four.say("Connect Four game timed out.")
        else:
            try:
                await move.delete()
            except discord.HTTPException:
                pass

            if move.content == "⏬":
                await four.edit(message, "This game was moved. Scroll down a bit.")
                message = await four.say("Hold on a second...")
            else:
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


@zeph.command(
    usage="z!jotto", aliases=["giotto"],
    description="Play a game of Jotto against the bot.",
    help="Plays a game of Jotto. Similar to Mastermind, but with words. I'll choose a random four-letter word, "
         "and you start guessing other four-letter words. I'll tell you how many of the letters in your guess "
         "are also in my word. The goal is to figure out my word.\n\ne.g. if my word is `area`, then the guess "
         "`cats` returns `1`, `near` returns `3`, and `away` returns `2`. It doesn't matter what "
         "position the letters are in - `acts` and `cats` are functionally the same guess."
)
async def jotto(ctx: commands.Context):
    jot = ClientEmol(":green_book:", hexcol("65c245"), ctx)

    game = jo.Jotto(choice(wr.wordDict[4]))
    await jot.say("The word has been chosen. Start guessing!",
                  d="To guess, reply with a four-letter word. To see your guess history, say **`history`**. "
                    "To forfeit, say **`forfeit`**. If you don't know what this is, do **`z!help jotto`**.")

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
                await jot.say("Guess History", d="\n".join([f"**`{g}`**: `{j}`" for g, j in game.history.items()]))
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
                          f"correct {plural('letter', score)} in `{guess}`.")


@zeph.command(
    usage="z!anagrams",
    description="Play a game of Anagrams.",
    help="Plays a game of Anagrams. I'll randomly pick eight letters, and you name as many words as possible "
         "that you can spell with those eight letters."
)
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
            return u == ctx.author and mr.channel == ctx.channel and mr.content.lower() in [*words, "🔄", "⏹", "⏬"]
        else:
            return u == ctx.author and mr.emoji in ["🔄", "⏹", "⏬"] and mr.message.id == message.id

    def timer():
        return 180 + start - time.time()

    def embed():
        return {"d": f"{form(letters)}Time remaining: {round(timer())} s",
                "footer": f"Used words: {none_list(sorted(guesses))} ({len(guesses)}/{len(words)})"}

    words = wr.anagrams("".join(letters))
    guesses = []
    start = time.time()
    await ana.edit(
        message, "Your Letters", footer=f"There are {len(words)} usable words.",
        d=f"React with :arrows_counterclockwise: to shuffle the letters, :arrow_double_down: to bring the screen back "
        f"to the bottom of the channel, or with :stop_button: to finish."
        f"\n{form(letters)}Time remaining: 180 s"
    )
    await message.add_reaction("🔄")
    await message.add_reaction("⏹")
    await message.add_reaction("⏬")

    while True:
        try:
            guess = (await zeph.wait_for("reaction_or_message", timeout=timer(), check=pred))[0]
        except asyncio.TimeoutError:
            missed = sorted([g for g in words if g not in guesses])
            return await ana.say("Time's up!", d=f"Words you missed: {none_list(missed)} ({len(missed)})")
        else:
            if type(guess) == discord.Reaction or guess.content.lower() not in words:
                if type(guess) == discord.Message:
                    emoji = guess.content.lower()
                else:
                    emoji = guess.emoji
                    try:
                        await message.remove_reaction(guess.emoji, ctx.author)
                    except discord.HTTPException:
                        pass
                if emoji == "🔄":
                    letters = sample(letters, len(letters))
                    await ana.resend_if_dm(message, "Shuffled!", **embed())
                    continue
                if emoji == "⏹":
                    missed = sorted([g for g in words if g not in guesses])
                    return await ana.say("Game over!", d=f"Words you missed: {none_list(missed)} ({len(missed)})")
                if emoji == "⏬":
                    await ana.edit(message, "This game was moved. Scroll down a bit.")
                    message = await ana.say("Hold on...")
                    await message.add_reaction("🔄")
                    await message.add_reaction("⏹")
                    await message.add_reaction("⏬")
                    await ana.edit(message, "Carry on!", **embed())
                    continue

            try:
                await guess.delete()
            except discord.HTTPException:
                pass
            guess = guess.content.lower()
            if guess in guesses:
                await ana.resend_if_dm(message, "You already guessed that word.", **embed())
                continue
            if guess in words:
                guesses.append(guess)
                await ana.resend_if_dm(message, f"Scored '{guess}'!", **embed())


@zeph.command(
    usage="z!boggle",
    description="Play a game of Boggle.",
    help="Plays a game of Boggle. I'll generate a board by rolling some letter dice, and you name as many "
         "words as possible that you can spell by stringing those letters together. The letters have to be next "
         "to each other on the board, and you can't use the same die more than once in a word.\n\n"
         "For example, you could use these letters to string together `ears`, `car`, `ran`, or `sac`, but not `scare` "
         "or `near`, because those letters aren't adjacent.\n"
         "```\nE R N\nS A C```"
)
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

    def is_guess(s: str):
        return board.find(s.lower()) or s.lower() == "forfeit"  # there's only one die with an F, so this is fine

    def pred(m: discord.Message):
        return m.channel == ctx.channel and m.author == ctx.author and is_guess(m.content)

    screen = await bog.say("Boggle", d=f'```ml\n{str(board)}```\nYou have three minutes. Go!')
    start = time.time()

    while True:
        try:
            guess = await zeph.wait_for("message", timeout=timer(), check=pred)
        except asyncio.TimeoutError:
            return await bog.say("Time's up!", d=f"You scored **{board.points}** points!\n\n"
                                                 f"Words you missed: {none_list(missed())} ({len(missed())})")
        else:
            try:
                await guess.delete()
            except discord.HTTPException:
                pass
            guess = guess.content.lower()
            if guess == "forfeit":
                return await bog.say("Game over!", d=f"You scored **{board.points}** points!\n\n"
                                                     f"Words you missed: {none_list(missed())} ({len(missed())})")
            if guess not in possible:
                await bog.resend_if_dm(screen, f"`{guess}` isn't a word.", **embed())
                continue
            if guess in board.guessed:
                await bog.resend_if_dm(screen, f"You've already used '{guess}'.", **embed())
                continue

            board.guess(guess)
            await bog.resend_if_dm(
                screen, f"Scored '{guess}' for {bg.score(guess)} {plural('point', bg.score(guess))}!", **embed()
            )


@zeph.command(
    usage="z!duel <@opponent>",
    description="Challenge an opponent to a duel.",
    help="Challenges an opponent to a duel. Prove you're quicker on the draw - but don't draw too early, or you'll "
         "lose out of sheer embarrassment."
)
async def duel(ctx: commands.Context, opponent: User):
    du = ClientEmol(":gun:", hexcol("9AAAB4"), ctx)

    if opponent == ctx.author:
        raise commands.CommandError("You can't challenge yourself.")
    if opponent.bot:
        raise commands.CommandError("You can't duel a bot.")
    if opponent not in ctx.guild.members:
        raise commands.CommandError("User is not in this server.")

    if not await confirm(f"{opponent.display_name}, do you accept the challenge?", ctx, opponent,
                         emol=du, yes="accept", no="chicken out"):
        return await du.say(f"{opponent.display_name} chickened out.")
    await du.say("A duel has been declared!", d="When I say \"draw\", send the gun emoji (`:gun:` :gun:) "
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
