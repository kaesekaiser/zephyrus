from startup import *
from random import randrange, sample, random
from minigames import connectfour as cf, jotto as jo, hangman as hm, boggle as bg, zchess as ch
import time


@zeph.command(
    aliases=["conn4", "c4"], usage="z!connect4 <@opponent>",
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
    desc = f"{ctx.author.display_name} rolled a {zeph.emojis['attack' + str(author_roll)]}."
    await four.edit(init, "Rolling for priority...", d=desc)
    await asyncio.sleep(1)
    desc += f"\n{opponent.display_name} rolled a {zeph.emojis['defense' + str(opponent_roll)]}."
    await four.edit(init, "Rolling for priority...", d=desc)
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


@zeph.command(
    usage="z!jotto", aliases=["giotto", "jt"],
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
    aliases=["anagram", "an"], usage="z!anagrams",
    description="Play a game of Anagrams.",
    help="Plays a game of Anagrams. I'll randomly pick eight letters, and you name as many words as possible "
         "that you can spell with those eight letters."
)
async def anagrams(ctx: commands.Context):
    ana = ClientEmol(":closed_book:", hexcol("dd2e44"), ctx)
    message = await ana.say("Picking letters...")

    while True:
        vowels = sample([g for g in wr.anagramsDist if g in "aeiou"], 1)  # just guarantee at least one vowel
        letters = vowels + sample(wr.anagramsDist, 7)
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


class BoggleGame(Navigator):
    def __init__(self):
        super().__init__(Emol(":hourglass:", hexcol("ffac33")), title="Boggle", prev=None, nxt=None)
        self.board = bg.Board()
        self.possible_words = self.find_possible_words()
        self.timeout = 180
        self.last_action_time = time.time()
        self.paused = False
        self.funcs["⏬"] = self.resend
        self.funcs["⏸️"] = self.pause
        self.funcs["⏹️"] = self.close

    def find_possible_words(self) -> list[str]:
        possible = [
            g for g in wr.wordList if set(c.upper() for c in re.sub("qu", "q", g)) <= set(self.board.board)
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
            elif emoji.lower() not in self.possible_words:
                self.title = f"`{emoji.upper()}` isn't a word."
            elif emoji.lower() in self.board.guessed:
                self.title = f"You've already guessed `{emoji.upper()}`."
            else:
                self.board.guess(emoji.lower())
                self.title = f"Scored `{emoji.upper()}` for {bg.score(emoji)} {plural('point', bg.score(emoji))}!"

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


@zeph.command(
    aliases=["bg"], usage="z!boggle",
    description="Play a game of Boggle.",
    help="Plays a game of Boggle. I'll generate a board by rolling some letter dice, and you name as many "
         "words as possible that you can spell by stringing those letters together. The letters have to be next "
         "to each other on the board, and you can't use the same die more than once in a word.\n\n"
         "In the board below, `EARS`, `CAR`, `RAN`, or `SAC` would all be valid guesses. `SCARE` "
         "and `NEAR` would be invalid because those letters aren't adjacent. `REAR` would be invalid because it "
         "reuses a square.\n"
         "```\nE R N\nS A C```"
)
async def boggle(ctx: commands.Context):
    return await BoggleGame().run(ctx)


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


chess_emol = Emol(":chess_pawn:", hexcol("5C913B"))


class CustomChessNavigator(Navigator):
    color = None
    starting_fen = ch.chess.STARTING_FEN
    moves = None

    def __init__(self, author: User):
        super().__init__(chess_emol, prev="", nxt="", timeout=300)
        self.author = author
        self.view_mode = False
        self.funcs[zeph.emojis["yes"]] = self.close
        self.funcs["🔍"] = self.view_board
        self.funcs["color"] = self.change_color
        self.funcs["setup"] = self.change_setup
        self.funcs["moves"] = self.change_moves

    def standard_pred(self, m: discord.Message):
        return m.channel == self.message.channel and m.author == self.author

    def view_board(self):
        self.view_mode = not self.view_mode

    async def change_color(self):
        await self.emol.edit(self.message, "Will you play White, Black, or random?")
        try:
            col = await zeph.wait_for(
                "message", timeout=300,
                check=lambda m: self.standard_pred(m) and m.content.lower() in ["white", "black", "random", "cancel"]
            )
        except asyncio.TimeoutError:
            await self.emol.edit(self.message, "Custom challenge timed out.")
            self.closed_elsewhere = True
            return await self.remove_buttons()
        else:
            try:
                await col.delete()
            except discord.HTTPException:
                pass

            if col.content.lower() == "cancel":
                return
            self.color = {"random": None, "black": False, "white": True}[col.content.lower()]

    async def change_setup(self):
        await self.emol.edit(
            self.message, "What's the FEN of the initial position?",
            d="FEN is [Forsyth-Edwards Notation](https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation). "
              "I'd suggest just copy-pasting it from somewhere; you can use an online tool like "
              "[lichess](https://lichess.org/editor) (the FEN field below the board) to get this from a position.",
            footer="Say \"cancel\" to cancel."
        )
        try:
            col = await zeph.wait_for("message", timeout=60, check=self.standard_pred)
        except asyncio.TimeoutError:
            await self.emol.edit(self.message, "Custom challenge timed out.")
            self.closed_elsewhere = True
            return await self.remove_buttons()
        else:
            try:
                await col.delete()
            except discord.HTTPException:
                pass

            if col.content.lower() == "cancel":
                return

            try:
                ch.BoardWrapper(fen=col.content)
            except ValueError:
                await self.emol.edit(self.message, "Invalid FEN. Make sure you've copied it correctly.")
                await asyncio.sleep(2)
                return
            else:
                self.starting_fen = col.content
                self.moves = None

    async def change_moves(self):
        await self.emol.edit(
            self.message, "What moves have been played so far?",
            d="Enter the full list of moves in [Standard Algebraic Notation]"
              "(https://en.wikipedia.org/wiki/Algebraic_notation_(chess)). You can get this from a PGN file (such as "
              "one from a past Zephyrus game), where it's the lower section of the file. It'll look something like "
              "`1. e4 e5 2. Nc3` and so on. You can also get this from an online tool like "
              "[lichess](https://lichess.org/analysis) (copy-paste the PGN field below the board).",
            footer="Say \"cancel\" to cancel."
        )
        try:
            col = await zeph.wait_for(
                "message", timeout=60,
                check=lambda m: self.standard_pred(m) and (ch.seems_san(m.content) or m.content.lower() == "cancel")
            )
        except asyncio.TimeoutError:
            await self.emol.edit(self.message, "Custom challenge timed out.")
            self.closed_elsewhere = True
            return await self.remove_buttons()
        else:
            try:
                await col.delete()
            except discord.HTTPException:
                pass

            if col.content.lower() == "cancel":
                return
            try:
                b = ch.BoardWrapper.from_san(col.content, fen=self.starting_fen)
            except ValueError:
                await self.emol.edit(
                    self.message, "Invalid SAN.",
                    d="Double-check the moves line up with your initial position."
                    if self.starting_fen != ch.chess.STARTING_FEN else None
                )
                await asyncio.sleep(2)
                return
            else:
                if b.inclusive_result() != "*":
                    await self.emol.edit(self.message, "Invalid SAN. This would mean the game is already over.")
                    await asyncio.sleep(3)
                    return

                self.moves = b.san

    async def get_emoji(self, ctx: commands.Context):
        def pred(mr: MR, u: User):
            if isinstance(mr, discord.Message):
                return self.standard_pred(mr) and mr.content.lower() in self.legal
            elif isinstance(mr, discord.Reaction):
                return mr.emoji in self.legal and mr.message == self.message and u == self.author

        ret = (await zeph.wait_for('reaction_or_message', timeout=self.timeout, check=pred))[0]

        if isinstance(ret, discord.Reaction):
            return ret.emoji
        elif isinstance(ret, discord.Message):
            try:
                await ret.delete()
            except discord.HTTPException:
                pass
            return ret.content

    @property
    def board(self):
        if self.moves:
            return ch.BoardWrapper.from_san(self.moves, fen=self.starting_fen)
        else:
            return ch.BoardWrapper(fen=self.starting_fen)

    def con(self):
        if self.view_mode:
            return chess_emol.con(
                "Starting Board State",
                d=f"{'White' if self.board.turn else 'Black'} to move.\n\n"
                f"{ChessPlayNavigator.get_emoji_chessboard(self.board)}"
            )

        return chess_emol.con(
            "Chess Game Options",
            d="To change an option, say the part in (`parentheses`). Hit :mag: to view the current board state, and "
              f"hit {zeph.emojis['yes']} when you're done to start the game.\n\n"
              f"`color` sets what color you, {self.author.name}, play. `setup` sets the initial position of all the "
              f"pieces on the board. `moves` sets what moves have been played up to this point; this is only really "
              f"useful for continuing a game that got interrupted.",
            fs={
                "You play... (`color`)": ("random" if self.color is None else "White" if self.color else "Black"),
                "Starting Position (`setup`)":
                    ("default" if self.starting_fen == ch.chess.STARTING_FEN else f"`{self.starting_fen}`"),
                "Continuing after... (`moves`)": (self.moves.history_range(0, 6, ell=True) if self.moves else "none")
            },
            same_line=True
        )


class ChessNavigator(Navigator):
    """Somewhat in beta."""

    fir = re.compile(r"(rook|knight|pawn|king|queen|bishop)\s((from\s[a-h][1-8]\s)?((to|takes?|x)\s))?[a-h][1-8]")
    fir_castle = re.compile(r"castles?(\s(short|long|queen\s?side|king\s?side))?")
    help_str = "If you don't know how to play chess, you're probably in the wrong place. "\
        "Maybe read [this](https://www.chess.com/learn-how-to-play-chess) or another article first.\n\n"\
        "To move a piece, send a message with the type of piece you're moving, and the square you're moving "\
        "it to (e.g. `pawn to e4`). If a pawn is promoting, you'll be asked what to promote it to, so don't "\
        "worry about including that information. To castle, say `castle` + `short` or `kingside` to castle "\
        "on the kingside, or `long` or `queenside` to castle on the queenside.\n\n"\
        "You can also use [Standard Algebraic Notation]"\
        "(https://en.wikipedia.org/wiki/Algebraic_notation_(chess)) to input moves."

    def __init__(self, white: User, black: User, board: ch.BoardWrapper):
        super().__init__(chess_emol, prev="", nxt="", timeout=300)
        self.white = white
        self.black = black
        self.board = board
        self.notification = None  # the message displayed above the board
        self.messages = []
        self.mode = "board"

    @property
    def turn(self):
        return self.board.turn

    @property
    def at_play(self):
        return self.white if self.turn else self.black

    @property
    def not_at_play(self):
        return self.black if self.turn else self.white

    @property
    def is_game_over(self):
        return self.board.inclusive_result() != "*"

    def set_mode(self, mode: str):
        if self.mode == mode:
            self.mode = "board"
        else:
            self.mode = mode

    async def send_everywhere(self, s: str):
        for mess in self.messages:
            await self.emol.send(mess.channel, s)

    @staticmethod
    def get_emoji_chessboard(board: ch.BoardWrapper, white_perspective: bool = True):
        def get_followup(rf: Union[int, str]):
            if rf in [1, 8, "A", "H"]:
                return str(rf) + ("W" if white_perspective else "B")
            return str(rf) + "A"

        ss = zeph.strings  # calling this only once makes this function literally dozens of times faster

        return "\n".join(
            ss[f"L{get_followup(8 - n if white_perspective else n + 1)}"] +
            ("".join(ss[j] for j in g)) for n, g in enumerate(board.emote_names(white_perspective))
        ) + "\n" + ss["__"] + \
            ("".join(ss[f"L{get_followup(g)}"] for g in ("ABCDEFGH" if white_perspective else "HGFEDCBA")))

    def board_con(self, title: str, top: str = None, perspective: bool = True):
        if top is None:
            top = f"{self.board.end_condition()}\n\n" if self.board.end_condition() else \
                f"{self.notification}\n\n" if self.notification else ""

        return self.emol.con(title, d=top+self.get_emoji_chessboard(self.board, perspective), footer=self.board.footer)

    async def parse_input(self, s: str, personal: bool = True) -> str:
        def pred(m: discord.Message):
            return m.author == self.at_play and m.channel == self.message.channel

        if ch.san_regex.fullmatch(s):
            return s
        elif self.fir.fullmatch(s.lower()):
            s = s.lower()
            piece_type = re.split(r"\s", s)[0]
            piece = ch.chess.Piece(ch.chess.PIECE_NAMES.index(piece_type), self.turn)
            try:
                from_square = re.search(r"(?<=from\s)[a-h][1-8]", s)[0]
            except TypeError:
                from_square = None
            to_square = re.split(r"\s", s)[-1]
            if from_square:
                piece_at = self.board.piece_at(ch.chess.SQUARE_NAMES.index(from_square))
                if piece_at != piece:
                    raise ValueError(
                        f"You don't control a {piece_type} at {from_square}." if personal else
                        f"There is no {'white' if piece.color else 'black'} {piece_type} at {from_square}."
                    )
                if not self.board.is_pseudo_legal(ch.chess.Move.from_uci(from_square + to_square)):
                    raise ValueError(
                        f"{'Your' if personal else 'White' if piece.color else 'Black'} "
                        f"{piece_type} at {from_square} can't reach {to_square}."
                    )
            else:
                valid_from = [
                    g for g in ch.chess.SQUARES
                    if self.board.piece_at(g) == piece and self.board.try_find_move(g, to_square)
                ]
                if len(valid_from) == 0:
                    rot = "take on" if self.board.piece_at(ch.chess.SQUARE_NAMES.index(to_square)) else "reach"
                    if len([g for g in ch.chess.SQUARES if self.board.piece_at(g) == piece]) == 1:
                        raise ValueError(
                            f"{'Your' if personal else 'White' if piece.color else 'Black'} "
                            f"{piece_type} can't {rot} {to_square}."
                        )
                    else:
                        raise ValueError(
                            f"You don't have a {piece_type} that can {rot} {to_square}." if personal else
                            f"{'White' if piece.color else 'Black'} has no {piece_type} that can {rot} {to_square}."
                        )
                elif len(valid_from) == 1:
                    from_square = ch.chess.SQUARE_NAMES[valid_from[0]]
                else:
                    valid_from_names = [ch.chess.SQUARE_NAMES[g] for g in valid_from]
                    m2 = await self.emol.send(
                        self.message.channel, f"The {piece_type} on {grammatical_join(valid_from_names, 'or')}?"
                    )
                    fsm = await zeph.wait_for(
                        "message", timeout=300, check=lambda m: pred(m) and m.content.lower() in valid_from_names
                    )
                    await m2.delete()
                    try:
                        await fsm.delete()
                    except discord.HTTPException:
                        pass
                    from_square = fsm.content.lower()
            if piece_type == "pawn":
                if (self.turn == ch.chess.WHITE and to_square[1] == "8") or \
                        (self.turn == ch.chess.BLACK and to_square[1] == "1"):
                    m2 = await self.emol.send(self.message.channel, "Promote to what piece?")
                    prom = await zeph.wait_for(
                        "message", timeout=300, check=lambda m: pred(m) and m.content.lower() in ch.chess.PIECE_NAMES
                    )
                    await m2.delete()
                    try:
                        await prom.delete()
                    except discord.HTTPException:
                        pass
                    promotion = "=" + ch.chess.PIECE_SYMBOLS[ch.chess.PIECE_NAMES.index(prom.content.lower())]
                else:
                    promotion = ""
            else:
                promotion = ""
            return ("" if piece_type == "pawn" else piece.symbol().upper()) + from_square + to_square + promotion
        elif self.fir_castle.fullmatch(s.lower()):
            if "short" in s.lower() or "king" in s.lower():
                return "O-O"
            elif "long" in s.lower() or "queen" in s.lower():
                return "O-O-O"
            else:
                if not self.board.is_legal_san("O-O"):
                    return "O-O-O"
                if not self.board.is_legal_san("O-O-O"):
                    return "O-O"
                m2 = await self.emol.send(self.message.channel, "Castle short (kingside) or long (queenside)?")
                cas = await zeph.wait_for(
                    "message", timeout=300,
                    check=lambda m: pred(m) and m.content.lower() in ["short", "kingside", "long", "queenside"]
                )
                await m2.delete()
                try:
                    await cas.delete()
                except discord.HTTPException:
                    pass
                return {"short": "O-O", "kingside": "O-O", "long": "O-O-O", "queenside": "O-O-O"}[cas.content.lower()]

    async def get_emoji(self, ctx: commands.Context):
        def pred(mr: MR, u: User):
            if isinstance(mr, discord.Message) and self.mode == "board":
                return mr.channel == self.message.channel and u == self.at_play and \
                       (ch.san_regex.fullmatch(mr.content) or self.fir.fullmatch(mr.content.lower()) or
                        self.fir_castle.fullmatch(mr.content.lower()) or mr.content.lower() in self.legal)
            elif isinstance(mr, discord.Reaction):
                return mr.emoji in self.legal and mr.message == self.message and u == self.at_play

        ret = (await zeph.wait_for('reaction_or_message', timeout=self.timeout, check=pred))[0]

        if isinstance(ret, discord.Reaction):
            return ret.emoji
        elif isinstance(ret, discord.Message):
            try:
                await ret.delete()
            except discord.HTTPException:
                pass
            return ret.content

    async def after_timeout(self):
        return await self.notify_timeout()

    async def notify_timeout(self):
        await self.send_everywhere("Chess game timed out.")
        self.closed_elsewhere = True
        return await self.close()

    async def close(self):
        for message in self.messages:
            await self.remove_buttons(message)


class ChessPlayNavigator(ChessNavigator):
    """For multiplayer use."""

    def __init__(self, white: User, black: User, board: ch.BoardWrapper, running_score: list = (0, 0)):
        super().__init__(white, black, board)
        self.perspectives = [False, True]
        self.funcs["🔃"] = self.flip_board
        self.funcs["⏬"] = self.bring_down
        self.funcs["resign"] = self.resign
        self.funcs["🏳️"] = self.resign
        self.funcs["draw"] = self.draw_offer
        self.funcs[zeph.emojis["draw_offer"]] = self.draw_offer
        self.funcs[zeph.emojis["help"]] = partial(self.set_mode, "help")
        self.running_score = running_score

    @property
    def players(self):
        return self.black, self.white

    def flip_board(self):
        self.perspectives[self.turn] = not self.perspectives[self.turn]

    async def bring_down(self):
        await self.emol.edit(self.message, "This board has been moved. Scroll down a bit.")
        mess = await self.message.channel.send(embed=self.con)
        self.messages[self.turn] = mess
        self.message = mess
        for button in self.legal:
            try:
                await self.message.add_reaction(button)
            except discord.HTTPException:
                pass

    async def resign(self):
        self.board.resignation = self.turn

    async def draw_offer(self):
        if await confirm(
            f"{self.at_play.name} offers a draw. Do you accept?", self.not_at_play.dm_channel, caller=self.not_at_play,
            emol=self.emol, yes="accept a draw", no="decline"
        ):
            self.board.draw_offer_accepted = True
        else:
            await self.emol.send(self.at_play.dm_channel, "Draw offer **declined.** Play continues.")

    def help(self):
        if self.mode == "help":
            self.mode = "board"
        else:
            self.mode = "help"

    def score_for(self, color: bool):
        return f"{round(self.running_score[color], 1)}-{round(self.running_score[not color], 1)}"

    def con_for(self, color: bool, force_top: str = None):
        if force_top:
            top = force_top + "\n\n"
        elif self.is_game_over:
            top = self.board.end_condition() + "\n\n"
        elif color != self.board.turn:
            top = f"{'White' if self.board.turn else 'Black'}'s move{'; check.' if self.board.is_check() else '.'}\n\n"
        else:
            top = (self.notification + "\n\n") if self.notification else \
                f"Your move{'; check.' if self.board.is_check() else '.'}\n\n"

        return self.board_con(
            f"Chess vs. {self.players[not color].name}" +
            (f", Round {self.board.round} ({self.score_for(color)})" if self.board.round > 1 else ""),
            top=top, perspective=self.perspectives[color]
        )

    def con(self):
        if self.mode == "help":
            return self.emol.con(
                "Help",
                d=self.help_str + "\n\n"
                "🔃 flips the board around.\n"
                "⏬ re-sends the message with the board, so you don't have to keep scrolling.\n"
                "🏳️ resigns the game.\n"
                f"{zeph.emojis['draw_offer']} offers a draw to your opponent.\n"
                f"{zeph.emojis['help']} opens and closes this menu."
            )
        return self.con_for(self.message == self.messages[1])

    def public_con(self):
        return self.board_con(
            f"{self.white.name} vs. {self.black.name}" +
            (f", Round {self.board.round} ({self.score_for(True)})" if self.board.round > 1 else "")
        )

    async def run_nonstandard_emoji(self, emoji: Union[discord.Emoji, str], ctx: commands.Context):
        try:
            move = await self.parse_input(emoji)
        except asyncio.TimeoutError:
            return await self.notify_timeout()
        except ValueError as e:
            self.notification = str(e)
        else:
            try:
                self.board.move_by_san(move)
            except ValueError:
                self.notification = "Illegal move."

    async def post_process(self):
        if self.message != self.messages[self.turn]:
            self.message = self.messages[self.turn]
            await self.message.edit(embed=self.con)
            await self.messages[2].edit(embed=self.public_con())

        if self.is_game_over:
            await self.send_everywhere(self.board.end_condition())
            self.closed_elsewhere = True
            return await self.close()

    async def play(self, ctx: commands.Context):
        if not self.at_play.dm_channel:
            await self.at_play.create_dm()
        if not self.not_at_play.dm_channel:
            await self.not_at_play.create_dm()

        self.messages.append(await self.not_at_play.dm_channel.send(
            embed=self.con_for(False, "You have the black pieces; White's move.")
        ))
        self.messages.append(await self.at_play.dm_channel.send(
            embed=self.con_for(True, "You have the white pieces; your move.")
        ))

        self.message = self.messages[1]

        for button in self.legal:
            try:
                await self.messages[0].add_reaction(button)
                await self.messages[1].add_reaction(button)
            except discord.HTTPException:
                pass

        self.messages.append(await ctx.send(embed=self.public_con()))
        await self.run(ctx, skip_setup=True)


class SoloChessNavigator(ChessNavigator):
    def __init__(self, user: User, board: ch.BoardWrapper):
        super().__init__(user, user, board)
        self.title = "Chess"
        self.perspective = True
        self.funcs["🔃"] = self.flip_board
        self.funcs["📥"] = partial(self.set_mode, "save")
        self.funcs["🆕"] = self.reset
        self.funcs[zeph.emojis["help"]] = partial(self.set_mode, "help")
        self.funcs[zeph.emojis["no"]] = self.close

    def standard_pred(self, m: discord.Message):
        return m.channel == self.message.channel and m.author == self.white

    def flip_board(self):
        self.perspective = not self.perspective

    async def reset(self):
        self.board = ch.BoardWrapper(self.board.setup)
        self.notification = "Board reset."

    def con(self):
        if self.mode == "help":
            return self.emol.con(
                "Help",
                d=self.help_str + "\n\n"
                "🔃 flips the board around.\n"
                "📥 displays the FEN and PGN for the board, so you can save it if you need.\n"
                "🆕 resets the board to the starting position, removing all moves.\n"
                f"{zeph.emojis['help']} opens and closes this menu.\n"
                f"{zeph.emojis['no']} exits the board editor."
            )

        elif self.mode == "save":
            return self.emol.con(
                "Board Data",
                fs={"FEN": f"```{self.board.fen()}```", "PGN": f"```{self.board.san.history_range(space_out=True)}```"},
            )

        return self.board_con(self.title, perspective=self.perspective)

    async def run_nonstandard_emoji(self, emoji: Union[discord.Emoji, str], ctx: commands.Context):
        try:
            move = await self.parse_input(emoji, personal=False)
        except asyncio.TimeoutError:
            return await self.notify_timeout()
        except ValueError as e:
            self.notification = e
        else:
            try:
                self.board.move_by_san(move)
            except ValueError:
                self.notification = "Illegal move."

    async def play(self, ctx: commands.Context):
        self.message = await ctx.send(embed=self.board_con(self.title))
        self.messages = [self.message]
        await self.run(ctx, on_new_message=False)


@zeph.command(
    name="chess", aliases=["xiaqi", "xq"], usage="z!chess <@opponent>\nz!chess custom <@opponent>",
    description="Challenges someone to a game of chess.",
    help="Challenges someone to a nice game of chess, played in DMs. Somewhat in beta.\n\n"
         "`z!chess <@opponent>` challenges an opponent to a standard game of chess, with a normal starting position "
         "and random colors. If you want more control, such as setting the starting colors, using a custom piece "
         "setup, or continuing from an unfinished game, use `z!chess custom <@opponent>`."
)
async def chess_command(ctx: commands.Context, *args):
    async def rematch():
        def pred(r: discord.Reaction, u: User):
            return (r.emoji == "🔄" or r.emoji == "📥") and r.message == mess and (u == ctx.author or u == opponent)

        states = {ctx.author: False, opponent: False, "dl": 1}
        mess = await chess_emol.send(ctx, "To rematch, hit 🔄. To download this game, hit 📥.")
        cont = "If you want to pick this back up where you left off, use `z!chess custom <@opponent>`, and copy-" \
               "paste the moves into the `moves` field.\n\n" if cpn.board.inclusive_result() == "*" else ""
        await mess.add_reaction("🔄")
        await mess.add_reaction("📥")
        while True:
            try:
                rem = await zeph.wait_for("reaction_add", timeout=120, check=pred)
            except asyncio.TimeoutError:
                if states["dl"] == 2:
                    await chess_emol.edit(mess, "Rematch option timed out.", d=f"{cont}```\n{cpn.board.pgn()}```")
                    return
                await chess_emol.edit(mess, "Rematch + download option timed out.")
                await asyncio.sleep(2)
                return await mess.delete()
            else:
                if rem[0].emoji == "📥" and states["dl"] == 1:
                    await chess_emol.edit(mess, "To rematch, hit 🔄.", d=f"{cont}```\n{cpn.board.pgn()}```")
                    states["dl"] = 2
                elif rem[0].emoji == "🔄":
                    states[rem[1]] = True
                    if all(states.values()):
                        return True

    if not args:
        return await chess_emol.send(
            ctx, "[BETA] Chess",
            d="Challenges someone to a game of chess, played in DMs.\n\n"
              "`z!chess <@opponent>` challenges an opponent to a standard game of chess, with a normal starting "
              "position and random colors. If you want more control, such as setting the starting colors, using a "
              "custom initial setup, or continuing from an unfinished game, use `z!chess custom <@opponent>`."
        )

    opponent = args[-1]

    if opponent.lower() == "solo":
        return await SoloChessNavigator(ctx.author, ch.BoardWrapper()).play(ctx)
    else:
        opponent = await commands.MemberConverter().convert(ctx, opponent)

    if opponent == ctx.author:
        return await chess_emol.send(ctx, "You can't challenge yourself.")
    if opponent.bot:
        return await chess_emol.send(ctx, "Bots can't play chess.")

    if len(args) == 2:
        if args[0].lower() != "custom":
            raise commands.BadArgument
        options = CustomChessNavigator(ctx.author)
        await options.run(ctx)
        b, w = (opponent, ctx.author) if options.color is True else (ctx.author, opponent) if options.color is False \
            else ((ctx.author, opponent) if random() < 0.5 else (opponent, ctx.author))
        board = options.board
        board.black_player = str(b)
        board.white_player = str(w)

    elif len(args) == 1:
        options = None
        b, w = (ctx.author, opponent) if random() < 0.5 else (opponent, ctx.author)
        board = ch.BoardWrapper(white=str(w), black=str(b))

    else:
        raise commands.BadArgument

    if await confirm(
            f"{opponent.name}, do you accept the challenge{' with these rules' if options else ''}?",
            ctx, opponent, yes="accept", no="deny", emol=chess_emol,
            add_info="This will be played via DMs, so that each player can see the board from the right side. "
                     "However, spectators will be able to watch in this channel.\n\n"
    ):
        cpn = ChessPlayNavigator(w, b, board)
        try:
            await cpn.play(ctx)
        except discord.Forbidden:
            return await Emol(zeph.emojis["yield"], hexcol("DD2E44")).send(
                ctx, "Make sure both your DMs are open.",
                d="`z!chess` is played via DM, and I can't seem to reach one of you."
            )
        else:
            while await rematch():
                results = {"1-0": [0, 1], "1/2-1/2": [0.5, 0.5], "0-1": [1, 0], "*": [0, 0]}
                cpn = ChessPlayNavigator(
                    cpn.black, cpn.white,
                    ch.BoardWrapper(
                        white=str(cpn.black), black=str(cpn.white), round=int(cpn.board.round + 1), fen=board.setup
                    ),
                    running_score=list(tsum(cpn.running_score, results[cpn.board.inclusive_result()]).__reversed__())
                )
                try:
                    await cpn.play(ctx)
                except discord.Forbidden:
                    return await Emol(zeph.emojis["yield"], hexcol("DD2E44")).send(
                        ctx, "Make sure both your DMs are open.",
                        d="`z!chess` is played via DM, and I can't seem to reach one of you."
                    )

    else:
        return await chess_emol.send(ctx, f"{opponent.name} chickened out.")
