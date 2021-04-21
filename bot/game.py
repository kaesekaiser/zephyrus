from startup import *
from random import randrange, sample, random
from minigames import connectfour as cf, jotto as jo, hangman as hm, boggle as bg, zchess as ch
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


chess_emol = Emol(":chess_pawn:", hexcol("5C913B"))


class ChessPlayNavigator(Navigator):
    """Somewhat in beta."""

    fir = re.compile(r"(rook|knight|pawn|king|queen|bishop)\s((from\s[a-h][1-8]\s)?((to|takes?|x)\s))?[a-h][1-8]")
    fir_castle = re.compile(r"castles?(\s(short|long|queen\s?side|king\s?side))?")

    def __init__(self, white: User, black: User, board: ch.BoardWrapper, running_score: list = (0, 0)):
        super().__init__(chess_emol, [], 0, "", prev="", nxt="")
        self.white = white
        self.black = black
        self.board = board
        self.notification = None  # the message displayed above the board
        self.messages = []
        self.perspectives = [False, True]
        self.funcs["🔃"] = self.flip_board
        self.funcs["⏬"] = self.bring_down
        self.funcs["🏳️"] = self.resign
        self.funcs[zeph.emojis["draw_offer"]] = self.draw_offer
        self.funcs[zeph.emojis["help"]] = self.help
        self.help_mode = False
        self.turn = True
        self.running_score = running_score

    @property
    def players(self):
        return self.black, self.white

    @property
    def at_play(self):
        return self.white if self.turn else self.black

    @property
    def not_at_play(self):
        return self.black if self.turn else self.white

    @property
    def is_game_over(self):
        return self.board.inclusive_result() != "*"

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
        self.help_mode = not self.help_mode

    async def send_everywhere(self, s: str):
        for mess in self.messages:
            await self.emol.send(mess.channel, s)

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

        return self.emol.con(
            f"Chess vs. {self.players[not color].name}" +
            (f", Round {self.board.round} ({self.score_for(color)})" if self.board.round > 1 else ""),
            d=top + self.get_emoji_chessboard(self.board, self.perspectives[color]),
            footer=f"📗 [{self.board.opening.eco}] {self.board.opening.name}\n{self.board.abbreviated_san}"
            if self.board.opening else self.board.abbreviated_san
        )

    @property
    def con(self):
        if self.help_mode:
            return self.emol.con(
                "Help",
                d="If you don't know how to play chess, you probably shouldn't have accepted this challenge. "
                "Read [this](https://www.chess.com/learn-how-to-play-chess) or another article though.\n\n"
                "To move a piece, send a message with the type of piece you're moving, and the square you're moving "
                "it to (e.g. `pawn to e4`). If a pawn is promoting, you'll be asked what to promote it to, so don't "
                "worry about including that information. To castle, say `castle` + `short` or `kingside` to castle "
                "on the kingside, or `long` or `queenside` to castle on the queenside.\n\n"
                "You can also use [Standard Algebraic Notation]"
                "(https://en.wikipedia.org/wiki/Algebraic_notation_(chess)) to input moves.\n\n"
                "🔃 flips the board around.\n"
                "⏬ re-sends the message with the board, so you don't have to keep scrolling.\n"
                "🏳️ resigns the game.\n"
                f"{zeph.emojis['draw_offer']} offers a draw to your opponent.\n"
                f"{zeph.emojis['help']} opens and closes this menu."
            )
        return self.con_for(self.turn)

    def public_con(self):
        return self.emol.con(
            f"{self.white.name} vs. {self.black.name}" +
            (f", Round {self.board.round} ({self.score_for(True)})" if self.board.round > 1 else ""),
            d=(f"{self.board.end_condition()}\n\n" if self.board.end_condition() else "") +
            self.get_emoji_chessboard(self.board),
            footer=f"📗 [{self.board.opening.eco}] {self.board.opening.name}\n{self.board.abbreviated_san}"
                   if self.board.opening else self.board.abbreviated_san
        )

    @staticmethod
    def get_emoji_chessboard(board: ch.BoardWrapper, white_perspective: bool = True):
        def get_followup(rf: Union[int, str]):
            if rf in [1, 8, "A", "H"]:
                return str(rf) + ("W" if white_perspective else "B")
            return str(rf) + "A"

        return "\n".join(
            zeph.strings[f"L{get_followup(8 - n if white_perspective else n + 1)}"] +
            ("".join(zeph.strings[j] for j in g)) for n, g in enumerate(board.emote_names(white_perspective))
        ) + "\n" + zeph.strings["__"] + \
            ("".join(zeph.strings[f"L{get_followup(g)}"] for g in ("ABCDEFGH" if white_perspective else "HGFEDCBA")))

    async def get_emoji(self, ctx: commands.Context):
        def pred(mr: MR, u: User):
            if isinstance(mr, discord.Message) and not self.help_mode:
                return mr.channel == self.message.channel and u == self.at_play and \
                       (ch.san_regex.fullmatch(mr.content) or self.fir.fullmatch(mr.content.lower()) or
                        self.fir_castle.fullmatch(mr.content.lower()))
            elif isinstance(mr, discord.Reaction):
                return mr.emoji in self.legal and mr.message == self.message and u == self.at_play

        ret = (await zeph.wait_for('reaction_or_message', timeout=300, check=pred))[0]

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

    async def parse_input(self, s: str) -> str:
        def pred(m: discord.Message):
            return m.author == self.at_play and m.channel == self.message.channel

        if ch.san_regex.fullmatch(s):
            return s
        elif self.fir.fullmatch(s):
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
                    raise ValueError(f"You don't control a {piece_type} at {from_square}.")
                if not self.board.is_pseudo_legal(ch.chess.Move.from_uci(from_square + to_square)):
                    raise ValueError(f"Your {piece_type} at {from_square} can't reach {to_square}.")
            else:
                valid_from = [
                    g for g in ch.chess.SQUARES
                    if self.board.piece_at(g) == piece and self.board.try_find_move(g, to_square)
                ]
                if len(valid_from) == 0:
                    rot = "take on" if self.board.piece_at(ch.chess.SQUARE_NAMES.index(to_square)) else "reach"
                    if len([g for g in ch.chess.SQUARES if self.board.piece_at(g) == piece]) == 1:
                        raise ValueError(f"Your {piece_type} can't {rot} {to_square}.")
                    else:
                        raise ValueError(f"You don't have a {piece_type} that can {rot} {to_square}.")
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

    async def run_nonstandard_emoji(self, emoji: Union[discord.Emoji, str], ctx: commands.Context):
        if emoji in self.legal:
            return

        try:
            move = await self.parse_input(emoji)
        except asyncio.TimeoutError:
            return await self.notify_timeout()
        except ValueError as e:
            self.notification = e
        else:
            try:
                self.board.move_by_san(move)
                self.notification = self.board.end_condition()
            except ValueError:
                self.notification = "Illegal move."

    async def post_process(self):
        if self.turn != self.board.turn:
            self.turn = self.board.turn
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

    async def close(self):
        self.message = self.messages[0]
        await self.remove_buttons()
        self.message = self.messages[1]
        await self.remove_buttons()


@zeph.command(
    name="chess", aliases=["xiaqi", "xq"], usage="z!chess <@opponent>",
    description="Challenges someone to a game of chess.",
    help="Challenges someone to a nice game of chess, played in DMs. Somewhat in beta."
)
async def chess_command(ctx: commands.Context, opponent: User):
    async def rematch():
        def pred(r: discord.Reaction, u: User):
            return (r.emoji == zeph.emojis["yes"] or r.emoji == zeph.emojis["no"]) and r.message == mess and \
                (u == ctx.author or u == opponent)

        states = {ctx.author: None, opponent: None}
        mess = await chess_emol.send(ctx, "Rematch?")
        await mess.add_reaction(zeph.emojis["yes"])
        await mess.add_reaction(zeph.emojis["no"])
        while True:
            try:
                rem = await zeph.wait_for("reaction_add", timeout=60, check=pred)
            except asyncio.TimeoutError:
                await chess_emol.edit(mess, "Rematch timed out.")
                await asyncio.sleep(2)
                return await mess.delete()
            else:
                if rem[0].emoji.name == "no":
                    await asyncio.sleep(2)
                    return await mess.delete()
                states[rem[1]] = True
                if all(states.values()):
                    return True

    if opponent == ctx.author:
        return await chess_emol.send(ctx, "You can't challenge yourself.")
    if opponent.bot:
        return await chess_emol.send(ctx, "Bots can't play chess.")

    if await confirm(
            f"{opponent.name}, do you accept the challenge?", ctx, opponent, yes="accept", no="deny", emol=chess_emol,
            add_info="This will be played via DMs, so that each player can see the board from the right side. "
                     "However, spectators will be able to watch in this channel.\n\n"
    ):
        b, w = (ctx.author, opponent) if random() < 0.5 else (opponent, ctx.author)
        cpn = ChessPlayNavigator(w, b, ch.BoardWrapper(white=str(w), black=str(b)))
        try:
            await cpn.play(ctx)
        except discord.Forbidden:
            return await Emol(zeph.emojis["yield"], hexcol("DD2E44")).send(
                ctx, "Make sure both your DMs are open.",
                d="`z!chess` is played via DM, and I can't seem to reach one of you."
            )
        else:
            while await rematch():
                results = {"1-0": [0, 1], "1/2-1/2": [0.5, 0.5], "0-1": [1, 0], None: [0, 0]}
                cpn = ChessPlayNavigator(
                    cpn.black, cpn.white,
                    ch.BoardWrapper(white=str(cpn.black), black=str(cpn.white), round=int(cpn.board.round + 1)),
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
