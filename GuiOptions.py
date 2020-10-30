#!/usr/bin/env python3

import tkinter as tk
from tkinter.ttk import Style
import sys

from tkcalendar import Calendar, DateEntry
import matplotlib.pyplot as plt
# noinspection SpellCheckingInspection
import time
import datetime
# noinspection SpellCheckingInspection
import tkcalendar as cal
from DbFinance import FinanceDB
from ChartOptions import ChartOptions


class GuiOptions(tk.ttk.Frame):

    def __init__(self, root):
        super().__init__()
        self.symbol_var = tk.StringVar(self)
        self.expiration_var = tk.StringVar(self)
        self.is_date_filter_on = tk.IntVar(value=0)
        self.start_date = None
        self.end_date = None

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

        if not self.symbol_var.get():
            pass
        else:
            self.clear_expiration_menu()
            df_options_expirations = self.options_db.get_all_options_expirations(self.symbol_var.get())
            expiration_set = set()
            self.shadow_expiration = dict()
            for index, row in df_options_expirations.iterrows():
                expiration_key = row["expire_date"].strftime('%Y-%m-%d')
                expiration_set.add(expiration_key)
                self.shadow_expiration[expiration_key] = row
            self.update_expiration(expiration_set)

    def clear_expiration_menu(self):
        self.expiration_var.set('')
        self.popup_expiration_menu['menu'].delete(0, 'end')

    def update_expiration(self, choices):
        for choice in choices:
            self.popup_expiration_menu['menu'].add_command(label=choice,
                                                           command=lambda value=choice: self.expiration_var.set(value))

    def expiration_var_selection_event(self, *args):
        if not self.expiration_var.get():
            pass
        else:
            print("expiration_var_selection_event", self.expiration_var.get())
            # Note - app crashes if we plot charts with focus on a DateEntry widget
            self.close_button.focus_force()
            self.update()
            self.update_idletasks()

            chart = ChartOptions()
            row = self.shadow_expiration[self.expiration_var.get()]

            x_dates, y_strikes, z_price = chart.prepare_options(self.options_db, self.symbol_var.get(),
                                                                row["option_expire_id"], put_call="CALL",
                                                                start_date=self.start_date,
                                                                end_date=self.end_date)
            if x_dates is not None:
                chart.chart_option(self.symbol_var.get(), "Call", row["expire_date"], x_dates, y_strikes, z_price)
                plt.show()
            else:
                print("No data available")

    def start_date_changed(self, args):
        self.start_date = datetime.datetime.strptime(self.start_cal.get(), "%m/%d/%y")
        print(self.start_cal.get())

    def end_date_changed(self, args):
        self.end_date = datetime.datetime.strptime(self.end_cal.get(), "%m/%d/%y")
        print(self.end_cal.get())

    def toggle_date_filter(self):
        pass

    def init_ui(self):
        self.master.title("Options")

        # frame2 = Frame(self, relief=RAISED, borderwidth=1, style='My.TFrame')
        tool_bar = tk.ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        tool_bar.pack(fill=tk.X, side=tk.TOP, expand=False)

        self.pack(fill=tk.BOTH, expand=True)

        self.close_button = tk.ttk.Button(tool_bar, text="Close")
        self.close_button.pack(side=tk.RIGHT, padx=5, pady=5)
        self.close_button.bind('<Button-1>', self.quit)

        self.symbol_var.set('')
        self.symbol_choices = {''}
        self.symbol_var.trace('w', self.symbol_selection_event)

        self.expiration_choices = {''}
        self.expiration_var.set('')
        self.expiration_var.trace('w', self.expiration_var_selection_event)

        self.popup_symbol_menu = tk.OptionMenu(tool_bar, self.symbol_var,
                                               *self.symbol_choices)
        self.popup_symbol_menu.config(width=8)
        self.popup_symbol_menu.pack(side=tk.LEFT, padx=5, pady=5)

        self.popup_expiration_menu = tk.OptionMenu(tool_bar, self.expiration_var,
                                                   *self.expiration_choices)
        self.popup_expiration_menu.config(width=16)
        self.popup_expiration_menu.pack(side=tk.LEFT, padx=5, pady=5)

        self.style = Style()
        self.style.theme_use("default")
        self.style.configure('My.TFrame', background='lightsteelblue')


        date_filter_container = tk.ttk.Frame(tool_bar, style='My.TFrame')
        date_filter_container.pack(fill=tk.X, side=tk.LEFT, expand=False)
        check_box = tk.Checkbutton( date_filter_container,
                                        text="Date Filter",
                                        variable=self.is_date_filter_on,
                                        command=self.toggle_date_filter,
                                        bg='lightsteelblue')
                                        # style='My.TFrame')
        check_box.pack(padx=10,side=tk.LEFT)

        start_date_container = tk.ttk.Frame(date_filter_container, style='My.TFrame')
        start_date_container.pack(fill=tk.X, side=tk.LEFT, expand=True)
        start_date_label = tk.ttk.Label(start_date_container, text="Start Date", background="lightsteelblue")
        start_date_label.pack(side=tk.TOP, padx=5, pady=2)

        self.start_cal = cal.DateEntry(start_date_container, width=12, background='darkblue',
                                       foreground='white', borderwidth=2, year=2020)
        self.start_cal.pack(side=tk.BOTTOM, padx=5, pady=5)
        self.start_cal.bind('<<DateEntrySelected>>', self.start_date_changed)

        end_date_container = tk.ttk.Frame(date_filter_container, style='My.TFrame')
        end_date_container.pack(fill=tk.X, side=tk.LEFT, expand=True)
        end_date_label = tk.ttk.Label(end_date_container, text="End Date", background="lightsteelblue")
        end_date_label.pack(side=tk.TOP, padx=5, pady=2)

        self.end_cal = cal.DateEntry(end_date_container, width=12, background='darkblue',
                                     foreground='white', borderwidth=2, year=2020)
        self.end_cal.pack(side=tk.BOTTOM, padx=5, pady=5)
        self.end_cal.bind('<<DateEntrySelected>>', self.end_date_changed)


def main():
    root = tk.Tk()
    root.geometry("800x600+300+300")
    app = GuiOptions(root)
    root.mainloop()


if __name__ == '__main__':
    main()
