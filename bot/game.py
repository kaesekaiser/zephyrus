import asyncio
import discord
import random
import re
import time
from classes.bot import Zeph
from classes.embeds import blue, ClientEmol, Emol
from classes.menus import Navigator
from discord.ext import commands
from functions import hex_to_color, none_list, plural
from utilities.words import anagrams_dist, subset_words, word_dict, word_list

import minigames.connectfour as connectfour
import minigames.boggle as boggle
import minigames.jotto as jotto
import minigames.zchess as chess


class BoggleGame(Navigator):
    def __init__(self, bot: Zeph):
        super().__init__(bot, Emol(":hourglass:", hex_to_color("ffac33")), title="Boggle", prev=None, nxt=None)
        self.board = boggle.Board()
        self.possible_words = self.find_possible_words()
        self.timeout = 180
        self.last_action_time = time.time()
        self.paused = False
        self.funcs["⏬"] = self.resend
        self.funcs["⏸️"] = self.pause
        self.funcs["⏹️"] = self.close

    def find_possible_words(self) -> list[str]:
        possible = [
            g for g in word_list if set(c.upper() for c in re.sub("qu", "q", g)) <= set(self.board.board)
            and g[0].upper() in self.board.board and len(g) >= 3
        ]
        return [g for g in possible if self.board.find(g)]

    def missed(self) -> list[str]:
        return [g for g in self.possible_words if g not in self.board.guessed]

    async def resend(self):
        self.title = "Boggle"
        await self.emol.edit(self.message, "This game has been moved. Scroll down.")
        self.message = await self.message.channel.send(embed=self.con())
        await self.add_buttons()

    def pause(self):
        self.paused = not self.paused

    def pre_process(self):
        current_time = time.time()
        if not self.paused:
            self.timeout -= current_time - self.last_action_time
        self.last_action_time = current_time

    def dynamic_timeout(self) -> int | float:
        return 600 if self.paused else self.timeout

    def is_valid_non_emoji(self, emoji: str):
        return self.board.find(emoji) or emoji.lower() == "forfeit"

    async def run_nonstandard_emoji(self, emoji: discord.Emoji | str, ctx: commands.Context):
        if not self.paused:
            if emoji.lower() == "forfeit":
                return await self.close()
            elif len(emoji) < 3:
                self.title = f"`{emoji.upper()}` is too short to score."
            elif emoji.lower() not in self.possible_words:
                self.title = f"`{emoji.upper()}` isn't a word."
            elif emoji.lower() in self.board.guessed:
                self.title = f"You've already guessed `{emoji.upper()}`."
            else:
                self.board.guess(emoji.lower())
                self.title = f"Scored `{emoji.upper()}` for {boggle.score(emoji)} {plural('point', boggle.score(emoji))}!"

    async def close(self):
        self.closed_elsewhere = True
        await self.emol.send(
            self.message.channel, "Game over!",
            d=f"You scored **{self.board.points}** points!\n\n"
              f"Words you missed: {none_list(self.missed())} ({len(self.missed())})"
        )

    def con(self):
        board_state = "|            |\n|   PAUSED   |\n|            |\n|            |" if self.paused else \
            str(self.board)
        return self.emol.con(
            self.title,
            d=("This menu will time out after 10 minutes.\n\n" if self.paused else "") +
            f"```ml\n{board_state}```\nTime remaining: {round(self.timeout)} s",
            footer=f"Words found: {none_list(sorted(self.board.guessed))}"
        )


def tsum(*lists: iter):
    try:
        assert [len(g) for g in lists].count(len(lists[0])) == len(lists)  # all lists are the same length
    except AssertionError:
        raise ValueError("All lists must be the same length.")
    else:
        return [sum(g[j] for g in lists) for j in range(len(lists[0]))]


class GamesCog(commands.Cog):
    def __init__(self, bot: Zeph):
        self.bot = bot

    @commands.command(
        aliases=["conn4", "c4"], usage="z!connect4 <@opponent>",
        description="Challenges someone to Connect Four.",
        help="Challenges an opponent to a nice game of Connect Four. Nothing is at stake - except your pride."
    )
    async def connect4(self, ctx: commands.Context, opponent: discord.User | discord.Member):
        four = ClientEmol(":four:", blue, ctx)

        if opponent == ctx.author:
            raise commands.CommandError("You can't challenge yourself.")
        if opponent.bot:
            raise commands.CommandError("Bots can't play Connect Four.")
        con = await self.bot.confirm(f"{opponent.display_name}, do you accept the challenge?", ctx, opponent,
                                     yes="accept", no="deny", emol=four)
        if not con:
            return await four.say(f"{opponent.display_name} chickened out.")

        init = await four.say("Rolling for priority...")
        await asyncio.sleep(2)
        author_roll = random.randrange(6) + 1
        opponent_roll = random.randrange(6) + 1
        desc = f"{ctx.author.display_name} rolled a {self.bot.emojis['attack' + str(author_roll)]}."
        await four.edit(init, "Rolling for priority...", d=desc)
        await asyncio.sleep(1)
        desc += f"\n{opponent.display_name} rolled a {self.bot.emojis['defense' + str(opponent_roll)]}."
        await four.edit(init, "Rolling for priority...", d=desc)
        await asyncio.sleep(2)

        if author_roll > opponent_roll:
            embed = f"{ctx.author.display_name} is {self.bot.emojis['checkerred']}, " \
                    f"{opponent.display_name} is {self.bot.emojis['checkeryellow']}."
            players = {1: ctx.author, -1: opponent}
        else:
            embed = f"{opponent.display_name} is {self.bot.emojis['checkerred']}, " \
                    f"{ctx.author.display_name} is {self.bot.emojis['checkeryellow']}."
            players = {1: opponent, -1: ctx.author}
        await four.edit(
            init, embed, d="To make a move, reply with the **column number**. Left is `1`, right is `7`.\n"
                           "If the board gets too far away, reply with the ⏬ emoji to bring it back down."
        )
        await asyncio.sleep(2)

        board = connectfour.Board(
            self.bot.strings["conn4empty"], self.bot.strings["conn4red"], self.bot.strings["conn4yellow"],
            self.bot.strings["conn4white"], "".join([self.bot.strings[f"c4c{g}"] for g in range(1, 8)])
        )
        message = await four.say("Initializing...")
        at_bat = 1
        checkers = {1: self.bot.strings["checkerred"], -1: self.bot.strings["checkeryellow"]}

        def pred(m: discord.Message):
            return m.channel == ctx.channel and m.author == players[at_bat] \
                and m.content in ["1", "2", "3", "4", "5", "6", "7", "⏬"]

        while True:
            await four.edit(message, f"{players[at_bat].display_name}'s turn. ({checkers[at_bat]})", d=str(board))

            try:
                move = await self.bot.wait_for("message", timeout=300, check=pred)
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
                        warning = await four.say("That column is full.")
                        await asyncio.sleep(2)
                        await warning.delete()
                        continue
                    board.drop(move - 1, at_bat)
                    at_bat = -at_bat

            if board.victor:
                return await four.edit(message, f"{players[board.victor].display_name} wins!", d=str(board))
            if board.full:
                return await four.edit(message, "It's a draw!", d=str(board))

    @commands.command(
        usage="z!jotto", aliases=["giotto", "jt"],
        description="Play a game of Jotto against the bot.",
        help="Plays a game of Jotto. Similar to Mastermind, but with words. I'll choose a random four-letter word, "
             "and you start guessing other four-letter words. I'll tell you how many of the letters in your guess "
             "are also in my word. The goal is to figure out my word.\n\ne.g. if my word is `area`, then the guess "
             "`cats` returns `1`, `near` returns `3`, and `away` returns `2`. It doesn't matter what "
             "position the letters are in - `acts` and `cats` are functionally the same guess."
    )
    async def jotto(self, ctx: commands.Context):
        jot = ClientEmol(":green_book:", hex_to_color("65c245"), ctx)

        game = jotto.Jotto(random.choice(word_dict[4]))
        await jot.say("The word has been chosen. Start guessing!",
                      d="To guess, reply with a four-letter word. To see your guess history, say **`history`**. "
                        "To forfeit, say **`forfeit`**. If you don't know what this is, do **`z!help jotto`**.")

        def pred(m: discord.Message):
            return m.author == ctx.author and m.channel == ctx.channel and \
                (len(m.content) == 4 or m.content.lower() in ["history", "forfeit"])

        while True:
            try:
                guess = (await self.bot.wait_for("message", timeout=180, check=pred)).content.lower()
            except asyncio.TimeoutError:
                return await jot.say("Jotto game timed out.")
            else:
                if guess == "history":
                    await jot.say("Guess History", d="\n".join([f"**`{g}`**: `{j}`" for g, j in game.history.items()]))
                    continue
                if guess == "forfeit":
                    return await jot.say(f"The word was **{game.word}**.")
                if guess not in word_dict[4]:
                    await jot.say("That's not a valid word.")
                    continue
                if guess in game.history:
                    await jot.say("You already guessed that word.")
                    continue

                score = game.guess(guess)
                if score == 4:
                    return await jot.say(f"Correct! It took you **{len(game.history)}** guesses.")
                await jot.say(f"There {'is' if score == 1 else 'are'} {score} "
                              f"correct {plural('letter', score)} in `{guess}`.")

    @commands.command(
        aliases=["anagram", "an"], usage="z!anagrams",
        description="Play a game of Anagrams.",
        help="Plays a game of Anagrams. I'll randomly pick eight letters, and you name as many words as possible "
             "that you can spell with those eight letters."
    )
    async def anagrams(self, ctx: commands.Context):
        ana = ClientEmol(":closed_book:", hex_to_color("dd2e44"), ctx)
        message = await ana.say("Picking letters...")

        while True:
            vowels = random.sample([g for g in anagrams_dist if g in "aeiou"], 1)  # guarantee at least one vowel
            letters = vowels + random.sample(anagrams_dist, 7)
            if len(subset_words("".join(letters))) > 20:
                break

        def form(lts: list):
            return f"```prolog\n|\u00a0{chr(160).join([g.upper() for g in lts])}\u00a0|```\n"

        def pred(mr: discord.Message | discord.Reaction, u: discord.User):
            if isinstance(mr, discord.Message):
                return u == ctx.author and mr.channel == ctx.channel and mr.content.lower() in [*words, "🔄", "⏹", "⏬"]
            else:
                return u == ctx.author and mr.emoji in ["🔄", "⏹", "⏬"] and mr.message.id == message.id

        def timer():
            return 180 + start - time.time()

        def embed():
            return {"d": f"{form(letters)}Time remaining: {round(timer())} s",
                    "footer": f"Used words: {none_list(sorted(guesses))} ({len(guesses)}/{len(words)})"}

        words = subset_words("".join(letters))
        guesses = []
        start = time.time()
        await ana.edit(
            message, "Your Letters", footer=f"There are {len(words)} usable words.",
            d=f"React with :arrows_counterclockwise: to shuffle the letters, :arrow_double_down: to bring the screen "
            f"back to the bottom of the channel, or with :stop_button: to finish."
            f"\n{form(letters)}Time remaining: 180 s"
        )
        await message.add_reaction("🔄")
        await message.add_reaction("⏹")
        await message.add_reaction("⏬")

        while True:
            try:
                guess = (await self.bot.wait_for("reaction_or_message", timeout=timer(), check=pred))[0]
            except asyncio.TimeoutError:
                missed = sorted([g for g in words if g not in guesses])
                return await ana.say("Time's up!", d=f"Words you missed: {none_list(missed)} ({len(missed)})")
            else:
                if isinstance(guess, discord.Reaction) or guess.content.lower() not in words:
                    if isinstance(guess, discord.Message):
                        emoji = guess.content.lower()
                    else:
                        emoji = guess.emoji
                        try:
                            await message.remove_reaction(guess.emoji, ctx.author)
                        except discord.HTTPException:
                            pass
                    if emoji == "🔄":
                        letters = random.sample(letters, len(letters))
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

    @commands.command(
        name="boggle", aliases=["bg"], usage="z!boggle",
        description="Play a game of Boggle.",
        help="Plays a game of Boggle. I'll generate a board by rolling some letter dice, and you name as many "
             "words as possible that you can spell by stringing those letters together. The letters have to be next "
             "to each other on the board, and you can't use the same die more than once in a word.\n\n"
             "In the board below, `EARS`, `CAR`, `RAN`, or `SAC` would all be valid guesses. `SCARE` "
             "and `NEAR` would be invalid because those letters aren't adjacent. `REAR` would be invalid because it "
             "reuses a square.\n"
             "```\nE R N\nS A C```"
    )
    async def boggle_command(self, ctx: commands.Context):
        return await BoggleGame(self.bot).run(ctx)

    @commands.command(
        usage="z!duel <@opponent>",
        description="Challenge an opponent to a duel.",
        help="Challenges an opponent to a duel. Prove you're quicker on the draw - but don't draw too early, or you'll "
             "lose out of sheer embarrassment."
    )
    async def duel(self, ctx: commands.Context, opponent: discord.User | discord.Member):
        du = ClientEmol(":gun:", hex_to_color("9AAAB4"), ctx)

        if opponent == ctx.author:
            raise commands.CommandError("You can't challenge yourself.")
        if opponent.bot:
            raise commands.CommandError("You can't duel a bot.")
        if opponent not in ctx.guild.members:
            raise commands.CommandError("User is not in this server.")

        if not await self.bot.confirm(f"{opponent.display_name}, do you accept the challenge?", ctx, opponent,
                                      emol=du, yes="accept", no="chicken out"):
            return await du.say(f"{opponent.display_name} chickened out.")
        await du.say("A duel has been declared!", d="When I say \"draw\", send the gun emoji (`:gun:` :gun:) "
                                                    "in chat as fast as you can.")
        await asyncio.sleep(2)
        await du.say("Ready...")

        def pred(m: discord.Message):
            return m.author in [ctx.author, opponent] and m.channel == ctx.channel and m.content in [":gun:", "🔫"]

        try:
            premature = await self.bot.wait_for("message", timeout=(5 + random.random() * 5), check=pred)
            return await du.say(f"{premature.author.display_name} drew early. Shame.")
        except asyncio.TimeoutError:
            await du.say("Draw!!")
            try:
                winner = await self.bot.wait_for("message", timeout=10, check=pred)
            except asyncio.TimeoutError:
                return await du.say("Nobody drew. :pensive:")
            else:
                return await du.say(f"{winner.author.display_name} wins!!")

    @commands.command(
        name="chess", aliases=["xiaqi", "xq"], usage="z!chess <@opponent>\nz!chess custom <@opponent>",
        description="Challenges someone to a game of chess.",
        help="Challenges someone to a nice game of chess, played in DMs. Somewhat in beta.\n\n"
             "`z!chess <@opponent>` challenges an opponent to a standard game of chess, with a normal starting position "
             "and random colors. If you want more control, such as setting the starting colors, using a custom piece "
             "setup, or continuing from an unfinished game, use `z!chess custom <@opponent>`."
    )
    async def chess_command(self, ctx: commands.Context, *args):
        async def rematch():
            def pred(r: discord.Reaction, u: discord.User):
                return (r.emoji == "🔄" or r.emoji == "📥") and r.message == mess and (u == ctx.author or u == opponent)

            states = {ctx.author: False, opponent: False, "dl": 1}
            mess = await chess.chess_emol.send(ctx, "To rematch, hit 🔄. To download this game, hit 📥.")
            cont = "If you want to pick this back up where you left off, use `z!chess custom <@opponent>`, and copy-" \
                   "paste the moves into the `moves` field.\n\n" if cpn.board.inclusive_result() == "*" else ""
            await mess.add_reaction("🔄")
            await mess.add_reaction("📥")
            while True:
                try:
                    rem = await self.bot.wait_for("reaction_add", timeout=120, check=pred)
                except asyncio.TimeoutError:
                    if states["dl"] == 2:
                        await chess.chess_emol.edit(mess, "Rematch option timed out.", d=f"{cont}```\n{cpn.board.pgn()}```")
                        return
                    await chess.chess_emol.edit(mess, "Rematch + download option timed out.")
                    await asyncio.sleep(2)
                    return await mess.delete()
                else:
                    if rem[0].emoji == "📥" and states["dl"] == 1:
                        await chess.chess_emol.edit(mess, "To rematch, hit 🔄.", d=f"{cont}```\n{cpn.board.pgn()}```")
                        states["dl"] = 2
                    elif rem[0].emoji == "🔄":
                        states[rem[1]] = True
                        if all(states.values()):
                            return True

        if not args:
            return await chess.chess_emol.send(
                ctx, "[BETA] Chess",
                d="Challenges someone to a game of chess, played in DMs.\n\n"
                  "`z!chess <@opponent>` challenges an opponent to a standard game of chess, with a normal starting "
                  "position and random colors. If you want more control, such as setting the starting colors, using a "
                  "custom initial setup, or continuing from an unfinished game, use `z!chess custom <@opponent>`."
            )

        opponent = args[-1]

        if opponent.lower() == "solo":
            return await chess.SoloChessNavigator(self.bot, ctx.author, chess.BoardWrapper()).play(ctx)
        else:
            opponent = await commands.MemberConverter().convert(ctx, opponent)

        if opponent == ctx.author:
            return await chess.chess_emol.send(ctx, "You can't challenge yourself.")
        if opponent.bot:
            return await chess.chess_emol.send(ctx, "Bots can't play chess.")

        if len(args) == 2:
            if args[0].lower() != "custom":
                raise commands.BadArgument
            options = chess.CustomChessNavigator(self.bot, ctx.author)
            await options.run(ctx)
            b, w = (opponent, ctx.author) if options.color is True else (ctx.author, opponent) if options.color is False \
                else ((ctx.author, opponent) if random.random() < 0.5 else (opponent, ctx.author))
            board = options.board
            board.black_player = str(b)
            board.white_player = str(w)

        elif len(args) == 1:
            options = None
            b, w = (ctx.author, opponent) if random.random() < 0.5 else (opponent, ctx.author)
            board = chess.BoardWrapper(white=str(w), black=str(b))

        else:
            raise commands.BadArgument

        if await self.bot.confirm(
                f"{opponent.name}, do you accept the challenge{' with these rules' if options else ''}?",
                ctx, opponent, yes="accept", no="deny", emol=chess.chess_emol,
                add_info="This will be played via DMs, so that each player can see the board from the right side. "
                         "However, spectators will be able to watch in this channel.\n\n"
        ):
            cpn = chess.ChessPlayNavigator(self.bot, w, b, board)
            try:
                await cpn.play(ctx)
            except discord.Forbidden:
                return await Emol(self.bot.emojis["yield"], hex_to_color("DD2E44")).send(
                    ctx, "Make sure both your DMs are open.",
                    d="`z!chess` is played via DM, and I can't seem to reach one of you."
                )
            else:
                while await rematch():
                    results = {"1-0": [0, 1], "1/2-1/2": [0.5, 0.5], "0-1": [1, 0], "*": [0, 0]}
                    cpn = chess.ChessPlayNavigator(
                        self.bot, cpn.black, cpn.white,
                        chess.BoardWrapper(
                            white=str(cpn.black), black=str(cpn.white), round=int(cpn.board.round + 1), fen=board.setup
                        ),
                        running_score=list(tsum(cpn.running_score, results[cpn.board.inclusive_result()]).__reversed__())
                    )
                    try:
                        await cpn.play(ctx)
                    except discord.Forbidden:
                        return await Emol(self.bot.emojis["yield"], hex_to_color("DD2E44")).send(
                            ctx, "Make sure both your DMs are open.",
                            d="`z!chess` is played via DM, and I can't seem to reach one of you."
                        )

        else:
            return await chess.chess_emol.send(ctx, f"{opponent.name} chickened out.")
