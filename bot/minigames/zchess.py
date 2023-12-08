import chess
import re
import datetime
from termcolor import colored
from typing import Union


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
    def from_san(san: Union[SAN, str], **kwargs):
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

    def try_find_move(self, from_square: Union[int, str], to_square: Union[int, str]):
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

    def run_san(self, san: Union[SAN, str]):
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
    def __init__(self, eco_book: str, name: str, fen: str, uci: Union[list, str]):
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
        return Opening(*tsv.split("\t"))


eco = {}
opening_fen_dict = {}


for book in "ABCDE":  # openings taken from github.com/niklasf/eco
    with open(f"eco/{book.lower()}.tsv" if __name__ == "__main__" else f"minigames/eco/{book.lower()}.tsv", "r") as fp:
        book_openings = [Opening.from_tsv(g) for g in fp.read().splitlines()[1:]]
        eco[book] = {
            f"{book}{str(g).rjust(2, '0')}":
                [j for j in book_openings if j.eco == f"{book}{str(g).rjust(2, '0')}"]
            for g in range(100)
        }
        opening_fen_dict.update({g.fen: g for g in book_openings})


if __name__ == "__main__":
    b = BoardWrapper.from_san("e4 e5 Nf3 Nc6 d4 exd4 Nxd4 Nf6")
    print(b.emote_names())
    print(b.emote_names(False))
