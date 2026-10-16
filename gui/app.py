import copy
import threading
import tkinter as tk
from tkinter import messagebox

from game.board import Board, DRAW, EMPTY, P1, P2

CELL = 90
COLS = 7
ROWS = 6
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL

BOARD_BG = "#1d4ed8"
SLOT_BG = "#f3f4f6"
P1_COLOR = "#dc2626"
P2_COLOR = "#facc15"
WIN_RING = "#16a34a"


def find_winning_line(board, player):
    for r in range(ROWS):
        for c in range(COLS):
            if board.grid[r][c] != player:
                continue
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                cells = []
                rr, cc = r, c
                for _ in range(4):
                    if 0 <= rr < ROWS and 0 <= cc < COLS and board.grid[rr][cc] == player:
                        cells.append((rr, cc))
                        rr += dr
                        cc += dc
                    else:
                        break
                if len(cells) == 4:
                    return cells
    return []


class Connect4GUI:
    def __init__(self, root, bot=None, human_player=P1):
        self.root = root
        self.bot = bot
        self.human_player = human_player
        self.board = Board()
        self.winning_cells = []
        self._bot_thinking = False
        self._bot_request_id = 0

        root.title("Connect 4")
        root.resizable(False, False)

        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg=BOARD_BG, highlightthickness=0
        )
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)

        self.status = tk.Label(root, text="", font=("Helvetica", 14))
        self.status.pack()

        controls = tk.Frame(root)
        controls.pack(pady=10)
        tk.Button(controls, text="Play as P1", command=lambda: self.start_game(P1)).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(controls, text="Play as P2", command=lambda: self.start_game(P2)).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(controls, text="Undo", command=self.undo).pack(
            side=tk.LEFT, padx=5
        )

        self.draw()
        self.update_status()
        self.maybe_bot_move()

    def cell_center(self, row, col):
        return (col * CELL + CELL // 2, row * CELL + CELL // 2)

    def draw(self):
        self.canvas.delete("all")
        radius = CELL // 2 - 8
        for r in range(ROWS):
            for c in range(COLS):
                cx, cy = self.cell_center(r, c)
                val = self.board.grid[r][c]
                if val == EMPTY:
                    color = SLOT_BG
                elif val == P1:
                    color = P1_COLOR
                else:
                    color = P2_COLOR
                is_win = (r, c) in self.winning_cells
                self.canvas.create_oval(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    fill=color,
                    outline=WIN_RING if is_win else "",
                    width=5 if is_win else 0,
                )

    def on_click(self, event):
        if self.board.is_game_over():
            return
        if self._bot_thinking:
            return
        if self.bot and self.board.current_player != self.human_player:
            return
        col = event.x // CELL
        if not self.board.is_legal(col):
            return
        self.play(col)
        self.maybe_bot_move()

    def play(self, col):
        self.board.drop(col)
        self.winning_cells = []
        if self.board.winner in (P1, P2):
            self.winning_cells = find_winning_line(self.board, self.board.winner)
        self.draw()
        self.update_status()

    def undo(self):
        self._bot_request_id += 1
        self._bot_thinking = False
        self.board.undo()
        if self.bot and self.board.history and self.board.current_player != self.human_player:
            self.board.undo()
        self.winning_cells = []
        if self.board.winner in (P1, P2):
            self.winning_cells = find_winning_line(self.board, self.board.winner)
        self.draw()
        self.update_status()
        self.maybe_bot_move()

    def start_game(self, human_player):
        self._bot_request_id += 1
        self._bot_thinking = False
        self.human_player = human_player
        self.board = Board()
        self.winning_cells = []
        self.draw()
        self.update_status()
        self.maybe_bot_move()

    def update_status(self):
        if self.board.winner is None:
            if self.bot and self.board.current_player != self.human_player:
                self.status.config(text="Bot thinking...")
            else:
                self.status.config(text=f"Player {self.board.current_player}'s turn")
        elif self.board.winner == DRAW:
            self.status.config(text="Draw!")
        else:
            self.status.config(text=f"Player {self.board.winner} wins!")
        self.root.update_idletasks()

    def maybe_bot_move(self):
        if (
            self.bot
            and not self.board.is_game_over()
            and self.board.current_player != self.human_player
            and not self._bot_thinking
        ):
            self.root.after(200, self.bot_move)

    def bot_move(self):
        bot = self.bot
        if bot is None or self.board.is_game_over():
            return
        if self._bot_thinking or self.board.current_player == self.human_player:
            return

        self._bot_thinking = True
        self.update_status()
        self._bot_request_id += 1
        request_id = self._bot_request_id
        board_snapshot = copy.deepcopy(self.board)

        def choose_move():
            try:
                move = bot.choose_move(board_snapshot)
            except Exception as error:
                self.root.after(0, self._finish_bot_move, request_id, None, error)
            else:
                self.root.after(0, self._finish_bot_move, request_id, move, None)

        threading.Thread(target=choose_move, daemon=True).start()

    def _finish_bot_move(self, request_id, col, error):
        if request_id != self._bot_request_id:
            return
        self._bot_thinking = False
        if error is not None:
            self.status.config(text="Bot failed; see error message")
            messagebox.showerror("Bot error", str(error), parent=self.root)
            return
        if col is None or not self.board.is_legal(col):
            error_message = f"Bot returned an illegal move: {col!r}"
            self.status.config(text=error_message)
            messagebox.showerror("Bot error", error_message, parent=self.root)
            return
        self.play(col)
