import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from game.solver import BDDSolver


class SolverTests(unittest.TestCase):
    def test_default_prefers_existing_legacy_table_directory(self):
        with (
            patch.dict("os.environ", {}, clear=True),
            patch.object(Path, "is_dir", return_value=True),
            patch.object(BDDSolver, "_find_executable", return_value=Path("/tmp/wdl")),
            patch.object(
                BDDSolver,
                "_find_distance_executable",
                return_value=Path("/tmp/bestmove"),
            ),
            patch.object(BDDSolver, "_load_opening_book", return_value={}),
        ):
            solver = BDDSolver()

        self.assertEqual(
            (Path.home() / "Desktop" / "cod" / "Connect_4_7x6").resolve(),
            solver.table_dir,
        )

    def test_solver_paths_can_be_configured_through_environment(self):
        with (
            patch.dict(
                "os.environ",
                {
                    "CONNECT4_SOLVER_DIR": "/tmp/solver-bin",
                    "CONNECT4_TABLE_DIR": "/tmp/solver-tables",
                },
            ),
            patch.object(Path, "is_dir", return_value=True),
            patch.object(BDDSolver, "_find_executable", return_value=Path("/tmp/wdl")),
            patch.object(
                BDDSolver,
                "_find_distance_executable",
                return_value=Path("/tmp/bestmove"),
            ),
            patch.object(BDDSolver, "_load_opening_book", return_value={}),
        ):
            solver = BDDSolver()

        self.assertEqual(Path("/tmp/solver-bin").resolve(), solver.solver_dir)
        self.assertEqual(Path("/tmp/solver-tables").resolve(), solver.table_dir)

    def test_wdl_safe_move_is_chosen_without_distance_search(self):
        solver = BDDSolver.__new__(BDDSolver)
        with (
            patch.object(
                solver,
                "_query",
                return_value=(1, ["-1", "0", "1", "1", "0", "-1", "."]),
            ),
            patch.object(solver, "_distance_best_move") as distance_search,
        ):
            move = solver.best_move("", search_distance=False)

        self.assertEqual(3, move)
        distance_search.assert_not_called()

    def test_best_move_restricts_selection_to_allowed_legal_moves(self):
        solver = BDDSolver.__new__(BDDSolver)
        with (
            patch.object(
                solver,
                "_query",
                return_value=(1, ["-1", "0", "1", "1", "0", "-1", "."]),
            ),
            patch.object(solver, "_distance_best_move") as distance_search,
        ):
            move = solver.best_move("", search_distance=False, allowed_moves=[1, 2])

        self.assertEqual(2, move)
        distance_search.assert_not_called()

    def test_best_move_rejects_illegal_allowed_moves(self):
        solver = BDDSolver.__new__(BDDSolver)

        with self.assertRaisesRegex(ValueError, "not legal"):
            solver.best_move("", allowed_moves=[7])

    def test_distance_search_is_bounded_and_timeout_preserves_safe_move(self):
        solver = BDDSolver.__new__(BDDSolver)
        solver.distance_executable = "/solver/bestmove"
        solver.table_dir = "/tables"
        completed = type(
            "Result",
            (),
            {"returncode": 0, "stdout": "Best move is 2\n", "stderr": ""},
        )()

        with patch("game.solver.subprocess.run", return_value=completed) as run:
            move = solver._distance_best_move("012", [2, 3])

        self.assertEqual(2, move)
        args, kwargs = run.call_args
        self.assertEqual(
            [
                "/solver/bestmove",
                "/tables",
                "012",
                "-Xdepth",
                "42",
                "-Xevalmoves",
            ],
            args[0],
        )
        self.assertEqual(120, kwargs["timeout"])

    def test_distance_search_rejects_move_outside_exact_safe_set(self):
        solver = BDDSolver.__new__(BDDSolver)
        solver.distance_executable = "/solver/bestmove"
        solver.table_dir = "/tables"
        completed = type(
            "Result",
            (),
            {"returncode": 0, "stdout": "Best move is 1\n", "stderr": ""},
        )()

        with patch("game.solver.subprocess.run", return_value=completed):
            self.assertIsNone(solver._distance_best_move("012", [2, 3]))

    def test_distance_search_cannot_override_exact_wdl_outcome(self):
        solver = BDDSolver.__new__(BDDSolver)
        with (
            patch.object(
                solver,
                "_query",
                return_value=(0, ["-1", "0", "0", "-1", ".", ".", "."]),
            ),
            patch.object(solver, "_distance_best_move", return_value=0),
        ):
            move = solver.best_move("", search_distance=True)

        self.assertIn(move, (1, 2))

    def test_timeout_falls_back_to_wdl_safe_move(self):
        solver = BDDSolver.__new__(BDDSolver)
        solver.distance_executable = "/solver/bestmove"
        solver.table_dir = "/tables"

        with patch(
            "game.solver.subprocess.run",
            side_effect=subprocess.TimeoutExpired("bestmove", 120),
        ):
            self.assertIsNone(solver._distance_best_move("012", [2, 3]))

    def test_opening_book_position_still_uses_exact_wdl_for_move(self):
        solver = BDDSolver.__new__(BDDSolver)
        solver.opening_book = {}
        with (
            patch.object(solver, "_query", return_value=(0, ["0", "0", "0", "0", "0", "0", "0"])) as query,
            patch.object(solver, "_distance_best_move") as distance_search,
        ):
            move = solver.best_move("03030616", search_distance=False)

        self.assertEqual(3, move)
        query.assert_called_once_with("03030616")
        distance_search.assert_not_called()

    def test_rejects_inconsistent_root_and_move_evaluations(self):
        solver = BDDSolver.__new__(BDDSolver)
        with patch.object(
            solver,
            "_query",
            return_value=(0, ["-1", "-1", "0", "1", "0", "-1", "-1"]),
        ):
            with self.assertRaisesRegex(RuntimeError, "root evaluation disagrees"):
                solver.best_move("")


if __name__ == "__main__":
    unittest.main()
