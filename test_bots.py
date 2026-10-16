import unittest
from unittest.mock import Mock, patch

from game.board import Board, P1, P2
from game.bots import PerfectBot


class PerfectBotTests(unittest.TestCase):
    def test_takes_immediate_win_without_calling_solver(self):
        board = Board()
        for col in (0, 1, 0, 1, 0, 2):
            board.drop(col)

        original_grid = [row[:] for row in board.grid]
        original_history = board.history[:]
        original_player = board.current_player
        solver = Mock()

        move = PerfectBot(solver).choose_move(board)

        self.assertEqual(0, move)
        solver.best_move.assert_not_called()
        self.assertEqual(original_grid, board.grid)
        self.assertEqual(original_history, board.history)
        self.assertEqual(original_player, board.current_player)

    def test_uses_solver_when_there_is_no_immediate_win(self):
        board = Board()
        solver = Mock()
        solver.best_move.return_value = 3

        move = PerfectBot(solver).choose_move(board)

        self.assertEqual(3, move)
        solver.best_move.assert_called_once_with("")

    def test_blocks_opponents_immediate_win_without_calling_solver(self):
        board = Board()
        for col in (6, 0, 6, 1, 5, 2):
            board.drop(col)
        solver = Mock()

        move = PerfectBot(solver).choose_move(board)

        self.assertEqual(3, move)
        solver.best_move.assert_not_called()

    def test_blocks_screenshot_immediate_win_instead_of_playing_center(self):
        board = Board()
        for col in "2132533334424":
            board.drop(int(col))
        solver = Mock()
        solver.best_move.return_value = 2

        move = PerfectBot(solver).choose_move(board)

        self.assertEqual([2], board.winning_moves(P1))
        self.assertEqual(2, move)
        solver.best_move.assert_not_called()

    def test_p2_avoids_moves_that_allow_a_forced_win_within_four_plies(self):
        board = Board()
        board.drop(0)
        solver = Mock()
        solver.best_move.return_value = 2

        with patch.object(
            PerfectBot,
            "_can_force_win",
            side_effect=lambda candidate, _player, _plies: (
                candidate.history[-1][1] == 3
            ),
        ):
            move = PerfectBot(solver).choose_move(board)

        self.assertEqual(2, move)
        solver.best_move.assert_called_once_with(
            "0", allowed_moves=[0, 1, 2, 4, 5, 6]
        )

    def test_four_ply_search_finds_a_non_immediate_forced_win(self):
        board = Board()
        for col in "345260464121142461":
            board.drop(int(col))
        original_history = board.history[:]
        bot = PerfectBot(Mock())

        self.assertEqual([], board.winning_moves(P1))
        self.assertEqual([], board.winning_moves(P2))
        self.assertFalse(bot._can_force_win(board, P1, 2))
        self.assertTrue(bot._can_force_win(board, P1, 4))
        self.assertEqual(original_history, board.history)

    def test_p2_uses_solver_if_every_move_allows_a_forced_win(self):
        board = Board()
        board.drop(0)
        solver = Mock()
        solver.best_move.return_value = 3

        with patch.object(PerfectBot, "_can_force_win", return_value=True):
            move = PerfectBot(solver).choose_move(board)

        self.assertEqual(3, move)
        solver.best_move.assert_called_once_with("0")

    def test_uses_full_solver_when_opponent_has_multiple_unblockable_wins(self):
        board = Board()
        for col in (6, 1, 6, 2, 5, 3):
            board.drop(col)
        solver = Mock()
        solver.evaluate.return_value = 0
        solver.best_move.return_value = 4

        move = PerfectBot(solver).choose_move(board)

        self.assertEqual([0, 4], board.winning_moves(P2))
        self.assertEqual(4, move)
        solver.best_move.assert_called_once_with("616253")


if __name__ == "__main__":
    unittest.main()
