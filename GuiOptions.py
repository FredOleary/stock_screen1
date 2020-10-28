#!/usr/bin/env python3

import tkinter as tk
from tkinter.ttk import Style
import sys

import math
import matplotlib.pyplot as plt
# noinspection SpellCheckingInspection
import numpy as np
import datetime
# noinspection SpellCheckingInspection
import matplotlib.dates as mdates
from matplotlib.colors import Normalize
import matplotlib.cm as cm
from DbFinance import FinanceDB


class GuiOptions(tk.ttk.Frame):

    def __init__(self, root):
        super().__init__()
        self.symbol_var = tk.StringVar(self)
        self.expiration_var = tk.StringVar(self)
        self.init_ui()
        self.clear_symbol_menu()
        self.clear_expiration_menu()
        self.options_db = FinanceDB()
        self.get_symbols()

    def get_symbols(self):
        self.options_db.initialize()
        df_symbols = self.options_db.get_all_symbols()
        symbol_set = set()
        for i_row, symbol_row in df_symbols.iterrows():
            symbol_set.add(symbol_row["symbol"])

        self.update_symbols(symbol_set)

    def quit(self, event):
        print("Exit command")
        sys.exit()

    def clear_symbol_menu(self):
        self.symbol_var.set('')
        self.popup_symbol_menu['menu'].delete(0, 'end')

    def update_symbols(self, choices):
        for choice in choices:
            self.popup_symbol_menu['menu'].add_command(label=choice,
                                                       command=lambda value=choice: self.symbol_var.set(value))

    def symbol_selection_event(self, *args):
        print("symbol_selection_event", self.symbol_var.get())
        self.clear_expiration_menu()
        df_options_expirations = self.options_db.get_all_options_expirations(self.symbol_var.get())
        expiration_set = set()
        for index, row in df_options_expirations.iterrows():
            expiration_set.add(row["expire_date"].strftime('%Y-%m-%d'))
        self.update_expiration(expiration_set)

    def clear_expiration_menu(self):
        self.expiration_var.set('')
        self.popup_expiration_menu['menu'].delete(0, 'end')

    def update_expiration(self, choices):
        for choice in choices:
            self.popup_expiration_menu['menu'].add_command(label=choice,
                                                           command=lambda value=choice: self.expiration_var.set(value))

    def expiration_var_selection_event(self, *args):
        print("expiration_var_selection_event", self.expiration_var.get())

    def init_ui(self):
        self.master.title("Options")
        self.style = Style()
        self.style.theme_use("default")

        self.style.configure('My.TFrame', background='red')

        # frame2 = Frame(self, relief=RAISED, borderwidth=1, style='My.TFrame')
        tool_bar = tk.ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        tool_bar.pack(fill=tk.X, side=tk.TOP, expand=False)

        self.pack(fill=tk.BOTH, expand=True)

        closeButton = tk.ttk.Button(tool_bar, text="Close")
        closeButton.pack(side=tk.RIGHT, padx=5, pady=5)
        closeButton.bind('<Button-1>', self.quit)

        self.symbol_var.set('')
        self.symbol_choices = {''}
        self.symbol_var.trace('w', self.symbol_selection_event)

        self.expiration_choices = {''}
        self.expiration_var.set('')
        self.expiration_var.trace('w', self.expiration_var_selection_event)

        self.popup_symbol_menu = tk.OptionMenu(tool_bar, self.symbol_var,
                                            *self.symbol_choices)
        self.popup_symbol_menu .config(width=8)
        self.popup_symbol_menu.pack(side=tk.LEFT, padx=5, pady=5)

        self.popup_expiration_menu = tk.OptionMenu(tool_bar, self.expiration_var,
                                                *self.expiration_choices)
        self.popup_expiration_menu .config(width=16)
        self.popup_expiration_menu.pack(side=tk.LEFT, padx=5, pady=5)



def main():
    root = tk.Tk()
    root.geometry("600x400+300+300")
    app = GuiOptions(root)
    root.mainloop()


if __name__ == '__main__':
    main()
