from collections.abc import Iterable
import csv
import logging
import os
import re
import subprocess
from pathlib import Path

if __package__:
    from .board import Board, COLS, ROWS
else:
    from board import Board, COLS, ROWS

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_EVALUATION_RE = re.compile(r"Overall evaluation =\s*(-?\d+)")
_BOOK_PLY = 8
_SUBPROCESS_TIMEOUT = 10
_DISTANCE_SEARCH_TIMEOUT = 120
_DISTANCE_SEARCH_MAX_DEPTH = ROWS * COLS
_PROJECT_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_SOLVER_DIR = (
    _PROJECT_DIR
    / "vendor"
    / "Connect4-Strong-Solver"
    / "src"
    / "connect4"
    / "build"
)
_DEFAULT_TABLE_DIR = _PROJECT_DIR / "data"
_LEGACY_TABLE_DIR = Path.home() / "Desktop" / "cod" / "Connect_4_7x6"


def board_to_move_sequence(board: Board) -> str:
    return "".join(str(col) for _, col, _ in board.history)


def _board_from_move_sequence(move_sequence: str) -> Board:
    if any(character < "0" or character >= str(COLS) for character in move_sequence):
        raise ValueError(f"Move sequence must contain only column digits 0-{COLS - 1}")
    if len(move_sequence) > ROWS * COLS:
        raise ValueError(f"Move sequence cannot exceed {ROWS * COLS} moves")

    board = Board()
    for character in move_sequence:
        if board.is_game_over():
            raise ValueError("Move sequence contains moves after the game ended")
        board.drop(int(character))
    return board


def _position_key(board: Board) -> int:
    mask = 0
    current_player_bits = 0
    for row in range(ROWS):
        for col in range(COLS):
            cell = board.grid[row][col]
            if cell:
                bit = (ROWS - 1 - row) + (ROWS + 1) * col
                mask |= 1 << bit
                if cell == board.current_player:
                    current_player_bits |= 1 << bit

    bottom_mask = sum(1 << ((ROWS + 1) * col) for col in range(COLS))
    position = (
        current_player_bits
        if len(board.history) % 2
        else mask ^ current_player_bits
    )
    return ((mask << 1) | bottom_mask) ^ position


class BDDSolver:
    """Queries the exact 7x6 WDL solver using its fast per-move probe."""

    def __init__(
        self,
        solver_dir: str | Path | None = None,
        table_dir: str | Path | None = None,
    ) -> None:
        if solver_dir is None:
            solver_dir = os.environ.get("CONNECT4_SOLVER_DIR", _DEFAULT_SOLVER_DIR)
        if table_dir is None:
            configured_table_dir = os.environ.get("CONNECT4_TABLE_DIR")
            if configured_table_dir:
                table_dir = configured_table_dir
            elif _LEGACY_TABLE_DIR.is_dir():
                table_dir = _LEGACY_TABLE_DIR
            else:
                table_dir = _DEFAULT_TABLE_DIR
        self.solver_dir = Path(solver_dir).expanduser().resolve()
        self.table_dir = Path(table_dir).expanduser().resolve()
        if not self.table_dir.is_dir():
            raise FileNotFoundError(
                f"BDD table directory does not exist: {self.table_dir}. "
                "Download and extract the 7 x 6 solution from "
                "https://doi.org/10.5281/zenodo.14582823, or set "
                "CONNECT4_TABLE_DIR to the extracted directory."
            )

        self.executable = self._find_executable()
        self.distance_executable = self._find_distance_executable()
        self.opening_book = self._load_opening_book()

    def _find_executable(self) -> Path:
        name = "wdl_w7_h6.out"
        candidates = (
            self.solver_dir / name,
            self.solver_dir / "src" / "connect4" / "build" / name,
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(
            f"Could not find {name} in {self.solver_dir} "
            "or its src/connect4/build directory; build with "
            "`make -C src/connect4 wdl WIDTH=7 HEIGHT=6 COMPRESSED_ENCODING=1`"
        )

    def _find_distance_executable(self) -> Path:
        name = "bestmove_w7_h6.out"
        candidates = (
            self.solver_dir / name,
            self.solver_dir / "src" / "connect4" / "build" / name,
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(
            f"Could not find {name} in {self.solver_dir} "
            "or its src/connect4/build directory; build with "
            "`make -C src/connect4 bestmove WIDTH=7 HEIGHT=6 COMPRESSED_ENCODING=1`"
        )

    def _load_opening_book(self) -> dict[int, int]:
        path = self.table_dir / "openingbook_w7_h6_d8.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Opening book does not exist: {path}")

        book = {}
        with path.open(newline="", encoding="ascii") as book_file:
            for row in csv.reader(book_file):
                if len(row) != 2:
                    raise ValueError(f"Malformed opening-book row in {path}: {row!r}")
                try:
                    key, score = (int(value.strip()) for value in row)
                except ValueError as error:
                    raise ValueError(f"Malformed opening-book row in {path}: {row!r}") from error
                book[key] = score
        return book

    def _query(self, move_sequence: str) -> tuple[int, list[str]]:
        _board_from_move_sequence(move_sequence)
        result = subprocess.run(
            [str(self.executable), str(self.table_dir), move_sequence],
            check=False,
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
        )
        if result.returncode:
            raise RuntimeError(
                f"WDL solver exited with status {result.returncode}: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )

        output = _ANSI_RE.sub("", result.stdout)
        evaluation_match = _EVALUATION_RE.search(output)
        if evaluation_match is None:
            raise RuntimeError(f"WDL output did not contain an evaluation:\n{result.stdout}")
        evaluation = int(evaluation_match.group(1))
        if evaluation not in (-1, 0, 1):
            raise RuntimeError(f"WDL solver returned an invalid evaluation: {evaluation}")

        move_scores = []
        if "move evaluation:" in output:
            for line in output.split("move evaluation:", 1)[1].splitlines():
                values = line.split()
                if len(values) == COLS and set(values) <= {".", "-1", "0", "1"}:
                    move_scores = values
                    break
        return evaluation, move_scores

    def best_move(
        self,
        move_sequence: str,
        search_distance: bool = True,
        allowed_moves: Iterable[int] | None = None,
    ) -> int:
        board = _board_from_move_sequence(move_sequence)
        if board.is_game_over():
            raise ValueError("Cannot choose a move for a finished game")

        allowed_move_set = None if allowed_moves is None else set(allowed_moves)
        if allowed_move_set is not None:
            illegal_moves = allowed_move_set.difference(board.legal_moves())
            if illegal_moves:
                raise ValueError(f"Allowed moves are not legal: {sorted(illegal_moves)}")
            if not allowed_move_set:
                raise ValueError("At least one allowed move is required")

        evaluation, move_scores = self._query(move_sequence)
        if not move_scores:
            raise RuntimeError("WDL output did not contain a valid move-score row")

        scores = {
            col: int(move_scores[col])
            for col in board.legal_moves()
            if move_scores[col] != "."
        }
        if not scores:
            raise RuntimeError("WDL output contained no legal moves")

        best_outcome = max(scores.values())
        if best_outcome != evaluation:
            raise RuntimeError(
                "WDL root evaluation disagrees with its legal-move evaluations: "
                f"{evaluation} != {best_outcome}"
            )
        if allowed_move_set is not None:
            scores = {
                col: score for col, score in scores.items()
                if col in allowed_move_set
            }
            if not scores:
                raise RuntimeError("WDL output contained no allowed legal moves")
            best_outcome = max(scores.values())
        safe_moves = [col for col, score in scores.items() if score == best_outcome]
        if best_outcome != 0 and search_distance:
            move = self._distance_best_move(move_sequence, safe_moves)
            if move in safe_moves:
                return move
        return max(safe_moves, key=lambda col: -abs(col - COLS // 2))

    def _distance_best_move(self, move_sequence: str, safe_moves: list[int]) -> int | None:
        try:
            result = subprocess.run(
                [
                    str(self.distance_executable),
                    str(self.table_dir),
                    move_sequence,
                    "-Xdepth",
                    str(_DISTANCE_SEARCH_MAX_DEPTH),
                    "-Xevalmoves",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=_DISTANCE_SEARCH_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logging.info(
                "Distance search reached the %d-second limit; using a WDL-safe move",
                _DISTANCE_SEARCH_TIMEOUT,
            )
            return None
        if result.returncode:
            error_output = result.stderr.strip() or result.stdout.strip()
            if "Illegal move!" in error_output:
                logging.warning(
                    "Distance solver failed internally; using a WDL-safe move instead: %s",
                    error_output,
                )
                return None
            raise RuntimeError(
                f"Distance solver exited with status {result.returncode}: "
                f"{error_output}"
            )

        output = _ANSI_RE.sub("", result.stdout)
        match = re.search(r"\bBest move is\s+(\d+)", output)
        if match is None:
            raise RuntimeError(f"Distance solver output did not contain a best move:\n{output}")
        move = int(match.group(1))
        if move not in safe_moves:
            return None
        return move

    def evaluate(self, move_sequence: str) -> int:
        board = _board_from_move_sequence(move_sequence)
        if len(move_sequence) == _BOOK_PLY:
            score = self.opening_book.get(_position_key(board))
            if score is not None:
                return (score > 0) - (score < 0)
        return self._query(move_sequence)[0]
