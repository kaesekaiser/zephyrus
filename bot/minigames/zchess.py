import asyncio
import chess
import datetime
import discord
import re
from classes.bot import Zeph
from classes.embeds import Emol
from classes.menus import Navigator
from discord.ext import commands
from functions import grammatical_join, hex_to_color
from termcolor import colored


san_regex = re.compile(r"^([0-9]+\.{1,3})?((O-O(-O)?|0-0(-0)?)|" + chess.SAN_REGEX.pattern[1:-2] + r")\Z")


def seems_san(s: str):
    return bool(SAN.from_str(s).moves)


def wrap_lines(s: str, line_length: int):
    """Assumes words will always be shorter than line_length."""
    ret, words, line = [], s.split(), ""
    for word in words:
        if len(line + " " + word) > line_length:
            ret.append(line)
            line = word
        else:
            line += " " + word
    ret.append(line)
    return "\n".join(ret).strip()


class SAN:
    def __init__(self, moves: list, turn: bool = True):
        self.moves = (["..."] if not turn else []) + moves

    @staticmethod
    def from_str(san: str):
        return SAN([re.sub(r"^[0-9]+\.+", "", move) for move in san.split() if san_regex.fullmatch(move)])

    def append(self, move: str):
        self.moves.append(move)

    def with_next(self, *moves: str):
        return SAN(self.moves + list(moves))

    def __len__(self):
        return len(self.moves)

    def __bool__(self):
        return bool(self.moves)

    def __lt__(self, other):
        assert isinstance(other, SAN)
        return other.moves[:len(self.moves)] == self.moves and len(other.moves) > len(self.moves)

    def __gt__(self, other):
        assert isinstance(other, SAN)
        return other < self

    def __eq__(self, other):
        assert isinstance(other, SAN)
        return other.moves == self.moves

    def history_range(self, start_hm: int = 0, stop_hm: int = None, space_out: bool = False, ell: bool = False) -> str:
        """Starts at zero! Stops before stop. If no stop, goes to the end."""
        if not self.moves:
            return ""

        if self.moves[0] == "...":
            start_hm += 1
            stop_hm = None if stop_hm is None else (stop_hm + 1)

        if start_hm < 0 and stop_hm is None:
            return self.history_range(max(0, len(self.moves) + start_hm), space_out=space_out, ell=ell)

        if start_hm >= len(self.moves) or start_hm < 0:
            raise ValueError("Starting halfmove number must be between 0 and the length of the game.")

        full_moves = [[f"{g+1}."] + self.moves[g*2:g*2+2]
                      for g in range(int(len(self.moves) / 2) + 1) if self.moves[g*2:g*2+2]]

        if stop_hm is not None:
            if stop_hm < 0:
                stop_hm = len(self.moves) + stop_hm

            full_moves = full_moves[:int((stop_hm + 1) / 2)]
            if stop_hm % 2:
                full_moves[-1] = full_moves[-1][:2]

        full_moves = full_moves[int(start_hm / 2):]

        if start_hm % 2:
            full_moves[0] = [full_moves[0][0] + "..", full_moves[0][2]]

        if not space_out:  # exclude space after move number for inline notation
            full_moves = [["".join(g[:2])] + g[2:] for g in full_moves]

        return " ".join(" ".join(g) for g in full_moves).strip() + (" ..." if ell and stop_hm < len(self.moves) else "")

    def __str__(self):
        return self.history_range()

    def diff(self, other) -> str:
        assert isinstance(other, SAN)
        if self < other:
            return other.diff(self)
        return self.history_range(-(len(self) - len(other)))


class BoardWrapper(chess.Board):
    def __init__(self, fen: str = chess.STARTING_FEN, white: str = "?", black: str = "?", **kwargs):
        super().__init__(fen=fen)
        self.setup = self.fen()
        self.fen_history = [self.repetition_fen]
        self.san = SAN([])
        self.opening = None
        self.date = datetime.date.today()
        self.track_opening = bool(kwargs.pop("track_opening", self.setup == chess.STARTING_FEN))
        self.white_player = white
        self.black_player = black
        self.draw_offer_accepted = False
        self.resignation = None
        self.timed_out = False
        self.round = int(kwargs.pop("round", 1))

    @staticmethod
    def from_san(san: SAN | str, **kwargs):
        ret = BoardWrapper(**kwargs)
        ret.run_san(san)
        return ret

    @staticmethod
    def from_uci(uci: str, **kwargs):
        ret = BoardWrapper(**kwargs)
        ret.run_uci(uci)
        return ret

    def colored_str(self, color_last_move: bool = True):
        pieces = self.piece_map()

        def get_color(r: int, f: int):
            if color_last_move and self.move_stack:
                if r * 8 + f in [self.peek().from_square, self.peek().to_square]:
                    return "yellow"  # if self.color_at(self.peek().to_square) else "cyan"
            if self.piece_at(r * 8 + f):
                return "red" if pieces.get(r * 8 + f).color else "blue"
            else:
                return "grey" if (r + f) % 2 else None

        return "\n".join(" ".join(colored(
            "." if not pieces.get(rank * 8 + file) else pieces.get(rank * 8 + file).symbol(),
            color=get_color(rank, file)
        ) for file in range(8)) for rank in range(7, -1, -1))

    def piece_emote(self, piece: chess.Piece):
        if piece.piece_type == 6 and self.is_check() and self.turn == piece.color:
            return ("W" if piece.color else "B") + "x"
        return ("W" if piece.color else "B") + piece.symbol().lower()

    def emote_names(self, white_perspective: bool = True):
        def color(rank: int, file: int) -> str:
            if self.move_stack and rank * 8 + file in [self.peek().to_square, self.peek().from_square]:
                return "V" if (rank + file) % 2 else "P"
            else:
                return "W" if (rank + file) % 2 else "B"

        pieces = self.piece_map()
        return [
            [(self.piece_emote(pieces[rank * 8 + file]) if pieces.get(rank * 8 + file) else "X") + color(rank, file)
             for file in (range(8) if white_perspective else range(7, -1, -1))]
            for rank in (range(7, -1, -1) if white_perspective else range(8))
        ]

    @property
    def repetition_fen(self):
        return " ".join(self.fen().split()[:4])

    def try_find_move(self, from_square: int | str, to_square: int | str):
        if isinstance(from_square, str):
            from_square = chess.SQUARE_NAMES.index(from_square)
        if isinstance(to_square, str):
            to_square = chess.SQUARE_NAMES.index(to_square)
        try:
            return self.find_move(from_square, to_square)
        except ValueError:
            return None

    def is_legal_san(self, san: str):
        try:
            self.parse_san(san)
        except ValueError:
            return False
        else:
            return True

    def move_by_uci(self, uci: str):
        self.move_by_san(self._algebraic(chess.Move.from_uci(uci)))

    def run_uci(self, uci: str):
        for move in uci.split():
            self.move_by_uci(move)

    def move_by_san(self, san: str):
        if san == "...":
            pass

        move = self.parse_san(san)
        self.san.append(self.san_and_push(move))
        self.fen_history.append(self.repetition_fen)

        if self.track_opening and self.repetition_fen in opening_fen_dict:
            self.opening = opening_fen_dict[self.repetition_fen]  # only update the opening after each move

    def run_san(self, san: SAN | str):
        if isinstance(san, str):
            return self.run_san(SAN.from_str(san))
        for move in san.moves:
            self.move_by_san(move)

    def is_threefold_repetition(self):
        return self.fen_history.count(self.fen_history[-1]) >= 3

    def end_condition(self, result: bool = False):
        if self.resignation is not None:
            return f"{'Black' if self.resignation else 'White'} wins by resignation."
        if self.draw_offer_accepted:
            return "Draw by mutual agreement."
        if self.is_checkmate():
            return self.result() if result else f"{'White' if self.result() == '1-0' else 'Black'} wins by checkmate."
        if self.is_check():
            return "*" if result else f"{'White' if self.turn else 'Black'} in check."
        if self.is_insufficient_material():
            return "1/2-1/2" if result else "Draw by insufficient material."
        if self.is_stalemate():
            return "1/2-1/2" if result else "Draw by stalemate."
        if self.is_fifty_moves():
            return "1/2-1/2" if result else "Draw by fifty-move rule."
        if self.is_threefold_repetition():
            return "1/2-1/2" if result else "Draw by threefold repetition."
        return "*" if result else None

    @property
    def full_san(self) -> str:
        return self.san.history_range()

    @property
    def abbreviated_san(self) -> str:
        """The last six halfmoves."""
        return self.san.history_range(-6)

    def state_after_halfmove(self, hm: int):
        ret = BoardWrapper(fen=self.fen_history[hm] + " 0 0")
        if hm:
            ret.move_stack.append(self.move_stack[hm - 1])
        return ret

    def inclusive_result(self):
        return self._manual_result() if self._manual_result() else self.end_condition(True)

    def _manual_result(self):
        """The result of the game if ended by the players rather than the rules (i.e. resignation or draw offer)."""
        if self.draw_offer_accepted:
            return "1/2-1/2"
        if self.resignation is not None:
            return "1-0" if self.resignation == chess.BLACK else "0-1"
        return None

    def pgn(self):
        tags = [
            "[Event \"z!chess\"]",
            "[Site \"discord.com\"]",
            f"[Date \"{self.date.strftime('%Y.%m.%d')}\"]",
            "[Round \"-\"]",
            f"[White \"{self.white_player}\"]",
            f"[Black \"{self.black_player}\"]",
            f"[Result \"{self.inclusive_result()}\"]"
        ]
        if self.setup != chess.STARTING_FEN:
            tags.append(f"[SetUp \"1\"]\n[FEN \"{self.setup}\"]")

        return "\n".join(tags) + \
            f"\n\n{wrap_lines(self.san.history_range(space_out=True) + ' ' + self.inclusive_result(), 80)}"

    @property
    def footer(self):
        if self.opening:
            return f"📗 [{self.opening.eco}] {self.opening.name}\n{self.abbreviated_san}"
        else:
            return ("📗 Custom Position\n" if self.setup != chess.STARTING_FEN else "") + self.abbreviated_san


class Opening:
    def __init__(self, eco_book: str, name: str, fen: str, uci: list | str):
        self.name = name
        self.eco = eco_book
        self.fen = fen
        if isinstance(uci, list):
            self.uci = " ".join(uci)
            self.moves = uci
        else:
            self.uci = uci
            self.moves = uci.split()

    def __len__(self):
        return len(self.moves)

    @property
    def san(self):
        return BoardWrapper.from_uci(self.uci, track_opening=False).san

    def union(self, other) -> list:
        assert isinstance(other, Opening)
        if len(other) < len(self):
            return other.union(self)
        try:
            return self.moves[:min(g for g in range(len(self)) if other.moves[g] != self.moves[g])]
        except ValueError:
            return self.moves

    @staticmethod
    def from_tsv(tsv: str):
        s = tsv.split("\t")
        return Opening(s[0], s[1], BoardWrapper.from_san(s[2], track_opening=False).repetition_fen, s[2])


def load_eco() -> tuple[dict[str, dict[str, list[Opening]]], dict[str, Opening]]:
    codes = {}
    fen = {}
    for book in "ABCDE":  # openings taken from github.com/niklasf/eco
        book_openings = [
            Opening.from_tsv(g)
            for g in open(f"minigames/eco/{book.lower()}.tsv", "r", encoding="utf8").read().splitlines()[1:]
        ]
        codes[book] = {
            f"{book}{str(g).rjust(2, '0')}":
                [j for j in book_openings if j.eco == f"{book}{str(g).rjust(2, '0')}"]
            for g in range(100)
        }
        fen.update({g.fen: g for g in book_openings})

    return codes, fen


eco, opening_fen_dict = load_eco()


chess_emol = Emol(":chess_pawn:", hex_to_color("5C913B"))


def emoji_chessboard(bot: Zeph, board: BoardWrapper, white_perspective: bool = True):
    def get_followup(rf: int | str):
        if rf in [1, 8, "A", "H"]:
            return str(rf) + ("W" if white_perspective else "B")
        return str(rf) + "A"

    ss = bot.strings  # calling this only once makes this function literally dozens of times faster

    return "\n".join(
        ss[f"L{get_followup(8 - n if white_perspective else n + 1)}"] +
        ("".join(ss[j] for j in g)) for n, g in enumerate(board.emote_names(white_perspective))
    ) + "\n" + ss["__"] + \
        ("".join(ss[f"L{get_followup(g)}"] for g in ("ABCDEFGH" if white_perspective else "HGFEDCBA")))


class CustomChessNavigator(Navigator):
    color = None
    starting_fen = chess.STARTING_FEN
    moves = None

    def __init__(self, bot: Zeph, author: discord.User | discord.Member):
        super().__init__(bot, chess_emol, prev="", nxt="", timeout=300)
        self.author = author
        self.view_mode = False
        self.funcs[self.bot.emojis["yes"]] = self.close
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
            col = await self.bot.wait_for(
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
            col = await self.bot.wait_for("message", timeout=60, check=self.standard_pred)
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
                BoardWrapper(fen=col.content)
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
            col = await self.bot.wait_for(
                "message", timeout=60,
                check=lambda m: self.standard_pred(m) and (seems_san(m.content) or m.content.lower() == "cancel")
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
                b = BoardWrapper.from_san(col.content, fen=self.starting_fen)
            except ValueError:
                await self.emol.edit(
                    self.message, "Invalid SAN.",
                    d="Double-check the moves line up with your initial position."
                    if self.starting_fen != chess.STARTING_FEN else None
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
        def pred(mr: discord.Message | discord.Reaction, u: discord.User):
            if isinstance(mr, discord.Message):
                return self.standard_pred(mr) and mr.content.lower() in self.legal
            elif isinstance(mr, discord.Reaction):
                return mr.emoji in self.legal and mr.message == self.message and u == self.author

        ret = (await self.bot.wait_for('reaction_or_message', timeout=self.timeout, check=pred))[0]

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
            return BoardWrapper.from_san(self.moves, fen=self.starting_fen)
        else:
            return BoardWrapper(fen=self.starting_fen)

    def con(self):
        if self.view_mode:
            return chess_emol.con(
                "Starting Board State",
                d=f"{'White' if self.board.turn else 'Black'} to move.\n\n"
                f"{emoji_chessboard(self.bot, self.board)}"
            )

        return chess_emol.con(
            "Chess Game Options",
            d="To change an option, say the part in (`parentheses`). Hit :mag: to view the current board state, and "
              f"hit {self.bot.emojis['yes']} when you're done to start the game.\n\n"
              f"`color` sets what color you, {self.author.name}, play. `setup` sets the initial position of all the "
              f"pieces on the board. `moves` sets what moves have been played up to this point; this is only really "
              f"useful for continuing a game that got interrupted.",
            fs={
                "You play... (`color`)": ("random" if self.color is None else "White" if self.color else "Black"),
                "Starting Position (`setup`)":
                    ("default" if self.starting_fen == chess.STARTING_FEN else f"`{self.starting_fen}`"),
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

    def __init__(self, bot: Zeph, white: discord.User, black: discord.User, board: BoardWrapper):
        super().__init__(bot, chess_emol, prev="", nxt="", timeout=300)
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

    def board_con(self, title: str, top: str = None, perspective: bool = True):
        if top is None:
            top = f"{self.board.end_condition()}\n\n" if self.board.end_condition() else \
                f"{self.notification}\n\n" if self.notification else ""

        return self.emol.con(title, d=top+emoji_chessboard(self.bot, self.board, perspective), footer=self.board.footer)

    async def parse_input(self, s: str, personal: bool = True) -> str:
        def pred(m: discord.Message):
            return m.author == self.at_play and m.channel == self.message.channel

        if san_regex.fullmatch(s):
            return s
        elif self.fir.fullmatch(s.lower()):
            s = s.lower()
            piece_type = re.split(r"\s", s)[0]
            piece = chess.Piece(chess.PIECE_NAMES.index(piece_type), self.turn)
            try:
                from_square = re.search(r"(?<=from\s)[a-h][1-8]", s)[0]
            except TypeError:
                from_square = None
            to_square = re.split(r"\s", s)[-1]
            if from_square:
                piece_at = self.board.piece_at(chess.SQUARE_NAMES.index(from_square))
                if piece_at != piece:
                    raise ValueError(
                        f"You don't control a {piece_type} at {from_square}." if personal else
                        f"There is no {'white' if piece.color else 'black'} {piece_type} at {from_square}."
                    )
                if not self.board.is_pseudo_legal(chess.Move.from_uci(from_square + to_square)):
                    raise ValueError(
                        f"{'Your' if personal else 'White' if piece.color else 'Black'} "
                        f"{piece_type} at {from_square} can't reach {to_square}."
                    )
            else:
                valid_from = [
                    g for g in chess.SQUARES
                    if self.board.piece_at(g) == piece and self.board.try_find_move(g, to_square)
                ]
                if len(valid_from) == 0:
                    rot = "take on" if self.board.piece_at(chess.SQUARE_NAMES.index(to_square)) else "reach"
                    if len([g for g in chess.SQUARES if self.board.piece_at(g) == piece]) == 1:
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
                    from_square = chess.SQUARE_NAMES[valid_from[0]]
                else:
                    valid_from_names = [chess.SQUARE_NAMES[g] for g in valid_from]
                    m2 = await self.emol.send(
                        self.message.channel, f"The {piece_type} on {grammatical_join(valid_from_names, 'or')}?"
                    )
                    fsm = await self.bot.wait_for(
                        "message", timeout=300, check=lambda m: pred(m) and m.content.lower() in valid_from_names
                    )
                    await m2.delete()
                    try:
                        await fsm.delete()
                    except discord.HTTPException:
                        pass
                    from_square = fsm.content.lower()
            if piece_type == "pawn":
                if (self.turn == chess.WHITE and to_square[1] == "8") or \
                        (self.turn == chess.BLACK and to_square[1] == "1"):
                    m2 = await self.emol.send(self.message.channel, "Promote to what piece?")
                    prom = await self.bot.wait_for(
                        "message", timeout=300, check=lambda m: pred(m) and m.content.lower() in chess.PIECE_NAMES
                    )
                    await m2.delete()
                    try:
                        await prom.delete()
                    except discord.HTTPException:
                        pass
                    promotion = "=" + chess.PIECE_SYMBOLS[chess.PIECE_NAMES.index(prom.content.lower())]
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
                cas = await self.bot.wait_for(
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
        def pred(mr: discord.Message | discord.Reaction, u: discord.User):
            if isinstance(mr, discord.Message) and self.mode == "board":
                return mr.channel == self.message.channel and u == self.at_play and \
                       (san_regex.fullmatch(mr.content) or self.fir.fullmatch(mr.content.lower()) or
                        self.fir_castle.fullmatch(mr.content.lower()) or mr.content.lower() in self.legal)
            elif isinstance(mr, discord.Reaction):
                return mr.emoji in self.legal and mr.message == self.message and u == self.at_play

        ret = (await self.bot.wait_for('reaction_or_message', timeout=self.timeout, check=pred))[0]

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

    def __init__(self, bot: Zeph, white: discord.User, black: discord.User, board: BoardWrapper,
                 running_score: list = (0, 0)):
        super().__init__(bot, white, black, board)
        self.perspectives = [False, True]
        self.funcs["🔃"] = self.flip_board
        self.funcs["⏬"] = self.bring_down
        self.funcs["resign"] = self.resign
        self.funcs["🏳️"] = self.resign
        self.funcs["draw"] = self.draw_offer
        self.funcs[self.bot.emojis["draw_offer"]] = self.draw_offer
        self.funcs[self.bot.emojis["help"]] = partial(self.set_mode, "help")
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
        if await self.bot.confirm(
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
                f"{self.bot.emojis['draw_offer']} offers a draw to your opponent.\n"
                f"{self.bot.emojis['help']} opens and closes this menu."
            )
        return self.con_for(self.message == self.messages[1])

    def public_con(self):
        return self.board_con(
            f"{self.white.name} vs. {self.black.name}" +
            (f", Round {self.board.round} ({self.score_for(True)})" if self.board.round > 1 else "")
        )

    async def run_nonstandard_emoji(self, emoji: discord.Emoji | str, ctx: commands.Context):
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
    def __init__(self, bot: Zeph, user: discord.User, board: BoardWrapper):
        super().__init__(bot, user, user, board)
        self.title = "Chess"
        self.perspective = True
        self.funcs["🔃"] = self.flip_board
        self.funcs["📥"] = partial(self.set_mode, "save")
        self.funcs["🆕"] = self.reset
        self.funcs[self.bot.emojis["help"]] = partial(self.set_mode, "help")
        self.funcs[self.bot.emojis["no"]] = self.close

    def standard_pred(self, m: discord.Message):
        return m.channel == self.message.channel and m.author == self.white

    def flip_board(self):
        self.perspective = not self.perspective

    async def reset(self):
        self.board = BoardWrapper(self.board.setup)
        self.notification = "Board reset."

    def con(self):
        if self.mode == "help":
            return self.emol.con(
                "Help",
                d=self.help_str + "\n\n"
                "🔃 flips the board around.\n"
                "📥 displays the FEN and PGN for the board, so you can save it if you need.\n"
                "🆕 resets the board to the starting position, removing all moves.\n"
                f"{self.bot.emojis['help']} opens and closes this menu.\n"
                f"{self.bot.emojis['no']} exits the board editor."
            )

        elif self.mode == "save":
            return self.emol.con(
                "Board Data",
                fs={"FEN": f"```{self.board.fen()}```", "PGN": f"```{self.board.san.history_range(space_out=True)}```"},
            )

        return self.board_con(self.title, perspective=self.perspective)

    async def run_nonstandard_emoji(self, emoji: discord.Emoji | str, ctx: commands.Context):
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


if __name__ == "__main__":
    b = BoardWrapper.from_san("e4 e5 Nf3 Nc6 d4 exd4 Nxd4 Nf6")
    print(b.emote_names())
    print(b.emote_names(False))
