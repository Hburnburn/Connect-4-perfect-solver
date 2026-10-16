# Connect Four Bot

A desktop Connect Four game with a solver-backed bot. The app is written in Python with Tkinter, and its native search probes are adapted from Markus Böck's Connect4 Strong Solver.

## Features

- Choose to play as Player 1 or Player 2.
- The bot takes an immediate win when one is available.
- When the bot plays as Player 2, it checks candidate moves with a four-ply tactical search and avoids moves that let Player 1 force a win within that search when a safer alternative exists.
- The exact 7 x 6 win/draw/loss (WDL) table selects moves that preserve the best available outcome. A separate distance search ranks eligible winning or losing lines, with a 42-ply and 120-second limit.

The tactical check is limited to four plies; it is not a proof that every move losing later has been avoided. Results from the exact WDL solver depend on using the matching, complete 7 x 6 solution tables. In standard Connect Four, Player 1 can force a win with perfect play, so Player 2 cannot guarantee a draw against perfect play.

## Requirements

- Python 3.10 or later with Tkinter
- A C compiler and `make`
- The 7 x 6 solution dataset (download instructions below)

## Build the native probes

From the project root, run:

```sh
make -C vendor/Connect4-Strong-Solver/src/connect4 bestmove wdl WIDTH=7 HEIGHT=6 COMPRESSED_ENCODING=1
```

The probes are built in `vendor/Connect4-Strong-Solver/src/connect4/build/`, which is excluded from Git.

## Install the solution tables

Download and extract the 7 x 6 solution dataset from [Zenodo](https://doi.org/10.5281/zenodo.14582823). The dataset is very large and is not included in this repository.

By default, the app looks for the dataset in `~/Desktop/cod/Connect_4_7x6` if that directory exists; otherwise, place it in the project's `data/` directory. The directory must contain the BDD table files and `openingbook_w7_h6_d8.csv`. Set `CONNECT4_TABLE_DIR` to use another directory. Set `CONNECT4_SOLVER_DIR` if the compiled probes are elsewhere.

## Run the app

```sh
python3 main.py
```

Use **Play as P1** or **Play as P2** below the board to start a new game on that side. The bot moves first when you choose P2.

## Run the tests

```sh
python3 -m unittest -v test_board test_bots test_solver test_gui
```

## Third-party work and references

The native solver code in [`vendor/Connect4-Strong-Solver/`](vendor/Connect4-Strong-Solver/) is adapted from [Markus Böck's Connect4 Strong Solver](https://github.com/markus7800/Connect4-Strong-Solver). The upstream project is licensed under [CC BY-SA 4.0](vendor/Connect4-Strong-Solver/LICENSE). This project modifies `ab.c`, `bestmove.c`, `generate_openingbook.c`, and `tt.c` to support bounded distance searches and reliable root-move selection; see the [vendor notes](vendor/Connect4-Strong-Solver/README.md) for details.

The solver's methods refer to the following research:

- Edelkamp, S. and Kissmann, P. (2008). “Symbolic classification of general two-player games.” *KI 2008*, pp. 185–192.
- Edelkamp, S. and Kissmann, P. (2011). “On the complexity of BDDs for state space search: A case study in Connect Four.” *Proceedings of the AAAI Conference on Artificial Intelligence*, 25(1), pp. 18–23.
- Böck, M. (2025). *Connect4 7 x 6 Strong Solution*. [Zenodo](https://doi.org/10.5281/zenodo.14582823).

The application and tests in this repository are licensed under the [MIT License](LICENSE). The vendored solver code retains its separate upstream license.
