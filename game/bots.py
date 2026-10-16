import copy
import random

from game.board import Board, P1, P2
from game.solver import BDDSolver, board_to_move_sequence

_P2_SAFETY_PLIES = 4


class RandomBot:
    """Plays a random legal move. Placeholder until we swap in a real solver."""

    def choose_move(self, board: Board) -> int | None:
        moves = board.legal_moves()
        return random.choice(moves) if moves else None


class PerfectBot:
    def __init__(self, solver: BDDSolver) -> None:
        self.solver = solver

    def choose_move(self, board: Board) -> int:
        winning_moves = board.winning_moves(board.current_player)
        if winning_moves:
            return max(winning_moves, key=lambda col: -abs(col - 3))

        move_sequence = board_to_move_sequence(board)
        opponent = P2 if board.current_player == P1 else P1
        legal_moves = board.legal_moves()
        if board.current_player == P1:
            opponent_winning_moves = board.winning_moves(opponent)
            blocking_moves = []
            if opponent_winning_moves:
                for col in legal_moves:
                    candidate = copy.deepcopy(board)
                    candidate.drop(col)
                    if not candidate.winning_moves(opponent):
                        blocking_moves.append(col)
                if len(blocking_moves) == 1:
                    return blocking_moves[0]
                if blocking_moves:
                    move = self.solver.best_move(
                        move_sequence, search_distance=False
                    )
                    if move in blocking_moves:
                        return move
                    return max(blocking_moves, key=lambda col: -abs(col - 3))

        if board.current_player == P2:
            safe_moves = []
            for col in legal_moves:
                candidate = copy.deepcopy(board)
                candidate.drop(col)
                if not self._can_force_win(candidate, opponent, _P2_SAFETY_PLIES):
                    safe_moves.append(col)
            if safe_moves:
                if len(safe_moves) == 1:
                    return safe_moves[0]
                return self.solver.best_move(
                    move_sequence, allowed_moves=safe_moves
                )

        return self.solver.best_move(move_sequence)

    def _can_force_win(self, board: Board, player: int, plies_left: int) -> bool:
        if board.winner is not None:
            return board.winner == player
        if plies_left == 0:
            return False

        moves = board.legal_moves()
        if board.current_player == player:
            for col in moves:
                board.drop(col)
                can_win = self._can_force_win(board, player, plies_left - 1)
                board.undo()
                if can_win:
                    return True
            return False

        for col in moves:
            board.drop(col)
            can_win = self._can_force_win(board, player, plies_left - 1)
            board.undo()
            if not can_win:
                return False
        return True
