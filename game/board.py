"""Connect 4 game logic. No dependencies."""

ROWS = 6
COLS = 7
EMPTY = 0
P1 = 1
P2 = 2
DRAW = "draw"


class Board:
    def __init__(self):
        self.grid = [[EMPTY] * COLS for _ in range(ROWS)]
        self.current_player = P1
        self.move_count = 0
        self.history = []
        self.winner = None

    def legal_moves(self):
        return [c for c in range(COLS) if self.grid[0][c] == EMPTY]

    def is_legal(self, col):
        return 0 <= col < COLS and self.grid[0][col] == EMPTY

    def winning_moves(self, player):
        if self.is_game_over():
            return []
        moves = []
        for col in self.legal_moves():
            row = ROWS - 1
            while self.grid[row][col] != EMPTY:
                row -= 1
            if self._check_win(row, col, player):
                moves.append(col)
        return moves

    def drop(self, col):
        """Drop a piece in `col`. Returns (row, col) of the placed piece."""
        if not self.is_legal(col):
            raise ValueError(f"Illegal move: column {col}")

        row = ROWS - 1
        while row >= 0 and self.grid[row][col] != EMPTY:
            row -= 1

        self.grid[row][col] = self.current_player
        self.history.append((row, col, self.current_player))
        self.move_count += 1

        if self._check_win(row, col, self.current_player):
            self.winner = self.current_player
        elif self.move_count == ROWS * COLS:
            self.winner = DRAW
        else:
            self.current_player = P2 if self.current_player == P1 else P1

        return row, col

    def undo(self):
        if not self.history:
            return
        row, col, player = self.history.pop()
        self.grid[row][col] = EMPTY
        self.move_count -= 1
        self.current_player = player
        self.winner = None

    def _check_win(self, row, col, player):
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            count = 1
            r, c = row + dr, col + dc
            while 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c] == player:
                count += 1
                r += dr
                c += dc
            r, c = row - dr, col - dc
            while 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 4:
                return True
        return False

    def is_game_over(self):
        return self.winner is not None

    def reset(self):
        self.__init__()

    def __str__(self):
        symbols = {EMPTY: ".", P1: "X", P2: "O"}
        rows = [" ".join(symbols[c] for c in row) for row in self.grid]
        rows.append(" ".join(str(c) for c in range(COLS)))
        return "\n".join(rows)