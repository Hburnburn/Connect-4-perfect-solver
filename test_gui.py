import unittest
from unittest.mock import Mock, patch

from game.board import Board, P1, P2
from gui.app import Connect4GUI


class Connect4GUITests(unittest.TestCase):
    def test_player_buttons_start_a_new_game_for_selected_side(self):
        buttons = []

        def make_button(*args, **kwargs):
            button = Mock()
            buttons.append(kwargs["command"])
            return button

        with (
            patch("gui.app.tk.Canvas", return_value=Mock()),
            patch("gui.app.tk.Label", return_value=Mock()),
            patch("gui.app.tk.Frame", return_value=Mock()),
            patch("gui.app.tk.Button", side_effect=make_button),
        ):
            app = Connect4GUI(Mock(), bot=Mock(), human_player=P1)
            buttons[0]()
            self.assertEqual(P1, app.human_player)
            buttons[1]()
            self.assertEqual(P2, app.human_player)
            self.assertEqual([], app.board.history)

    def test_starting_as_p1_resets_game_and_bot_waits(self):
        app = Connect4GUI.__new__(Connect4GUI)
        app.root = Mock()
        app.bot = Mock()
        app.human_player = P2
        app.board = Board()
        app.board.drop(3)
        app.winning_cells = [(5, 3)]
        app._bot_thinking = True
        app._bot_request_id = 4
        app.draw = Mock()
        app.update_status = Mock()
        app.maybe_bot_move = Mock()

        app.start_game(P1)

        self.assertEqual(P1, app.human_player)
        self.assertEqual([], app.board.history)
        self.assertEqual([], app.winning_cells)
        self.assertFalse(app._bot_thinking)
        self.assertEqual(5, app._bot_request_id)
        app.maybe_bot_move.assert_called_once_with()

    def test_starting_as_p2_schedules_bot_opening_move(self):
        app = Connect4GUI.__new__(Connect4GUI)
        app.root = Mock()
        app.bot = Mock()
        app.human_player = P1
        app.board = Board()
        app._bot_thinking = False
        app._bot_request_id = 0
        app.draw = Mock()
        app.update_status = Mock()
        app.maybe_bot_move = Mock()

        app.start_game(P2)

        self.assertEqual(P2, app.human_player)
        app.maybe_bot_move.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
