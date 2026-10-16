import tkinter as tk

from game.bots import PerfectBot, RandomBot
from game.solver import BDDSolver
from gui.app import Connect4GUI


def main(use_random_bot=False):
    if use_random_bot:
        bot = RandomBot()
    else:
        solver = BDDSolver()
        bot = PerfectBot(solver)

    root = tk.Tk()
    Connect4GUI(root, bot=bot)
    root.mainloop()


if __name__ == "__main__":
    main()
