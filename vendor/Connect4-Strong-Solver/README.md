# Vendored Connect4 Strong Solver source

This directory contains source code adapted from [Markus Böck's Connect4 Strong Solver](https://github.com/markus7800/Connect4-Strong-Solver). The upstream project is licensed under CC BY-SA 4.0; see [`LICENSE`](LICENSE).

The source snapshot is based on upstream commit `c148209dff0b34c397a04dd8066e04b3202eb335`. The following probe files have local changes:

- `src/connect4/probe/ab.c`: adds a maximum-depth parameter to iterative deepening and initializes a legal root move at the depth limit.
- `src/connect4/probe/bestmove.c`: parses and applies the optional `-Xdepth` limit.
- `src/connect4/probe/generate_openingbook.c`: updates the iterative-deepening call for the new parameter.
- `src/connect4/probe/tt.c`: permits root move lookup when the transposition-table entry is a bound rather than exact.

The full 7 x 6 solution dataset is not included. Download it from the [Zenodo record](https://doi.org/10.5281/zenodo.14582823).
