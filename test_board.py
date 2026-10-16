import random
import unittest

from game.board import Board, P1, P2


class BoardTests(unittest.TestCase):
    def test_vertical_win(self):
        board = Board()
        for col in (0, 1, 0, 1, 0, 2):
            board.drop(col)

        board.drop(0)

        self.assertEqual(P1, board.winner)
        self.assertTrue(board.is_game_over())

    def test_winning_moves_detects_current_and_opponent_wins_without_mutation(self):
        board = Board()
        for col in (6, 0, 6, 1, 5, 2):
            board.drop(col)
        original_grid = [row[:] for row in board.grid]
        original_history = board.history[:]

        self.assertEqual([3], board.winning_moves(P2))
        self.assertEqual([], board.winning_moves(P1))
        self.assertEqual(original_grid, board.grid)
        self.assertEqual(original_history, board.history)

    def test_winning_moves_matches_legal_move_simulation(self):
        rng = random.Random(20261016)
        board = Board()

        for _ in range(150):
            if board.is_game_over():
                board = Board()
            for player in (P1, P2):
                expected = []
                for col in board.legal_moves():
                    candidate = Board()
                    for _, move_col, _ in board.history:
                        if candidate.is_game_over():
                            break
                        candidate.drop(move_col)
                    candidate.current_player = player
                    candidate.drop(col)
                    if candidate.winner == player:
                        expected.append(col)
                self.assertEqual(expected, board.winning_moves(player))

            if board.is_game_over() or not board.legal_moves():
                board = Board()
            else:
                board.drop(rng.choice(board.legal_moves()))

    def test_undo_restores_last_player_and_disc(self):
        board = Board()
        board.drop(3)
        board.drop(4)

        board.undo()

        self.assertEqual(P2, board.current_player)
        self.assertEqual(0, board.grid[5][4])
        self.assertEqual(1, board.move_count)

if __name__ == "__main__":
    unittest.main()
