#!/usr/bin/env python3

import tkinter as tk
from tkinter.ttk import Style
from tkinter import messagebox
import sys

import matplotlib.pyplot as plt
# noinspection SpellCheckingInspection
import datetime
# noinspection SpellCheckingInspection
import tkcalendar as cal
from DbFinance import FinanceDB
from WebFinance import FinanceWeb
from AddPosition import AddPosition as addPos
from ListPositions import ListPositions as listPos

from ChartOptions import ChartOptions
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
from dateutil import parser


class GuiOptions(tk.ttk.Frame):

    def __init__(self, root):
        super().__init__()
        self.tk_root = root
        self.close_button = None
        # self.surface_chart_button = None
        # self.line_chart_button = None
        # self.strike_chart_button = None
        self.delete_option_button = None
        self.status_label = None
        self.plot_frame = None
        self.symbol_var = tk.StringVar(self)
        self.expiration_var = tk.StringVar(self)
        self.strike_var = tk.StringVar(self)
        self.is_date_filter_on = tk.IntVar(value=0)
        self.start_date = None
        self.end_date = None
        self.shadow_expiration = dict()
        self.popup_symbol_menu = None
        self.popup_expiration_menu = None
        self.popup_strike_menu = None
        self.start_cal = None
        self.end_cal = None
        self.status_var = tk.StringVar(self)
        self.bid_extrinsic_value = tk.IntVar(self)

        self.init_ui()
        self.clear_symbol_menu()
        self.clear_expiration_menu()
        self.clear_strike_menu()
        self.toggle_date_filter()
        self.update_chart_button_enable()
        self.options_db = FinanceDB()
        self.options_db.initialize()
        self.get_symbols()
        self.extrinsic_value_radio = None
        self.bid_value_radio = None

    def get_symbols(self):
        df_symbols = self.options_db.get_all_symbols()
        symbol_set = set()
        for i_row, symbol_row in df_symbols.iterrows():
            symbol_set.add(symbol_row["symbol"])

        self.update_symbols(symbol_set)

    # noinspection PyUnusedLocal
    @staticmethod
    def quit_app(event):
        print("Exit command")
        sys.exit()

    def clear_plot_frame(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

    def delete_option(self, event):
        if not self.expiration_var.get():
            message = "Do you want to delete all options for symbol {0}?".format(self.symbol_var.get())
        else:
            message = "Do you want to delete all options for symbol {0} with expiration date {1}?". \
                format(self.symbol_var.get(), self.expiration_var.get())
        answer = tk.messagebox.askquestion("Delete Option", message, icon='warning')
        if answer == 'yes':
            option_expire_id = -1
            if self.expiration_var.get():
                row = self.shadow_expiration[self.expiration_var.get()]
                option_expire_id = row['option_expire_id']
            symbol = self.symbol_var.get()
            self.options_db.delete_options(symbol, option_expire_id)
            self.clear_symbol_menu()
            self.clear_expiration_menu()
            self.clear_strike_menu()
            self.get_symbols()
        else:
            print("not deleted....")

    # noinspection PyUnusedLocal
    def create_line_chart(self, event=None):
        self.close_button.focus_force()
        self.status_var.set("Creating chart...")
        self.update()
        self.update_idletasks()

        if bool(self.shadow_expiration):
            self.clear_plot_frame()
            fig = Figure(figsize=(10, 6))
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)

            chart = ChartOptions()
            row = self.shadow_expiration[self.expiration_var.get()]

            success = chart.prepare_options(self.options_db,
                                            self.symbol_var.get(),
                                            row["option_expire_id"], put_call="CALL",
                                            start_date=self.start_date,
                                            end_date=self.end_date,
                                            option_type='extrinsic' if self.bid_extrinsic_value.get() == 1 else 'bid')
            if success:
                chart.line_chart_option(fig, self.symbol_var.get(), "Call", row["expire_date"])
                self.show_figure(canvas)
                self.status_var.set("Done")
            else:
                self.status_var.set("No data available")

    # noinspection PyUnusedLocal
    def create_surface_chart(self):
        self.close_button.focus_force()
        self.status_var.set("Creating chart...")
        self.update()
        self.update_idletasks()

        if bool(self.shadow_expiration):
            self.clear_plot_frame()
            fig = Figure(figsize=(10, 6))
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)

            chart = ChartOptions()
            row = self.shadow_expiration[self.expiration_var.get()]

            success = chart.prepare_options(self.options_db,
                                            self.symbol_var.get(),
                                            row["option_expire_id"], put_call="CALL",
                                            start_date=self.start_date,
                                            end_date=self.end_date,
                                            option_type='extrinsic' if self.bid_extrinsic_value.get() == 1 else 'bid')
            if success:
                chart.surface_chart_option(fig, self.symbol_var.get(), "Call", row["expire_date"])
                self.show_figure(canvas)
                self.status_var.set("Done")
            else:
                self.status_var.set("No data available")

    def create_strike_profit_chart(self, event=None):
        self.close_button.focus_force()
        self.status_var.set("Creating strike chart...")
        self.update()
        self.update_idletasks()

        if bool(self.shadow_expiration) and self.strike_var.get() != "":
            self.clear_plot_frame()
            fig = Figure(figsize=(10, 6))
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            chart = ChartOptions()
            row = self.shadow_expiration[self.expiration_var.get()]
            strike = self.strike_var.get()
            success = chart.create_strike_profit_chart(self.options_db,
                                                       fig,
                                                       self.symbol_var.get(),
                                                       row["option_expire_id"],
                                                       strike,
                                                       row["expire_date"],
                                                       put_call="CALL",
                                                       start_date=self.start_date,
                                                       end_date=self.end_date,
                                                       option_type='extrinsic' if self.bid_extrinsic_value.get() == 1 else 'bid')
            if success:
                self.show_figure(canvas)
                self.status_var.set("Done")
            else:
                self.status_var.set("No data available")

    def create_strike_metrics_chart(self, event=None):
        self.close_button.focus_force()
        self.status_var.set("Creating strike chart...")
        self.update()
        self.update_idletasks()

        if bool(self.shadow_expiration) and self.strike_var.get() != "":
            self.clear_plot_frame()
            fig = Figure(figsize=(10, 6))
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            chart = ChartOptions()
            row = self.shadow_expiration[self.expiration_var.get()]
            strike = self.strike_var.get()
            success = chart.create_strike_metrics_chart(self.options_db,
                                                        fig,
                                                        self.symbol_var.get(),
                                                        row["option_expire_id"],
                                                        strike,
                                                        row["expire_date"],
                                                        put_call="CALL",
                                                        start_date=self.start_date,
                                                        end_date=self.end_date)

            if success:
                self.show_figure(canvas)
                self.status_var.set("Done")
            else:
                self.status_var.set("No data available")

    def show_figure(self, canvas):
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def clear_symbol_menu(self):
        self.symbol_var.set('')
        self.popup_symbol_menu['menu'].delete(0, 'end')

    def update_symbols(self, choices):
        for choice in choices:
            self.popup_symbol_menu['menu'].add_command(label=choice,
                                                       command=lambda value=choice: self.symbol_var.set(value))

    # noinspection PyUnusedLocal
    def symbol_selection_event(self, *args):
        print("symbol_selection_event", self.symbol_var.get())
        self.update_chart_button_enable()
        if not self.symbol_var.get():
            pass
        else:
            self.clear_expiration_menu()
            df_options_expirations = self.options_db.get_all_options_expirations(self.symbol_var.get())
            expiration_set = []
            self.shadow_expiration = dict()
            for index, row in df_options_expirations.iterrows():
                expiration_key = row["expire_date"].strftime('%Y-%m-%d')
                expiration_set.append(expiration_key)
                self.shadow_expiration[expiration_key] = row
            self.update_expiration(expiration_set)

    def clear_expiration_menu(self):
        self.expiration_var.set('')
        self.popup_expiration_menu['menu'].delete(0, 'end')

    def update_expiration(self, choices):
        for choice in choices:
            self.popup_expiration_menu['menu'].add_command(label=choice,
                                                           command=lambda value=choice: self.expiration_var.set(value))

    def clear_strike_menu(self):
        self.strike_var.set('')
        self.popup_strike_menu['menu'].delete(0, 'end')

    def update_strike(self, choices):
        for choice in choices:
            self.popup_strike_menu['menu'].add_command(label=choice,
                                                       command=lambda value=choice: self.strike_var.set(value))

    # noinspection PyUnusedLocal
    def expiration_var_selection_event(self, *args):
        self.update_chart_button_enable()
        if not self.expiration_var.get():
            pass
        else:
            self.clear_strike_menu()
            row = self.shadow_expiration[self.expiration_var.get()]

            df_strikes = self.options_db.get_unique_strikes_for_expiration(row["option_expire_id"], put_call="CALL")
            strike_list = []
            for index, row in df_strikes.iterrows():
                strike_list.append(row["strike"])
            self.update_strike(strike_list)

    def strike_var_selection_event(self, *args):
        self.update_chart_button_enable()

    # noinspection PyUnusedLocal
    def start_date_changed(self, args):
        self.start_date = datetime.datetime.strptime(self.start_cal.get(), "%m/%d/%y")
        print(self.start_cal.get())

    # noinspection PyUnusedLocal
    def end_date_changed(self, args):
        self.end_date = datetime.datetime.strptime(self.end_cal.get(), "%m/%d/%y")
        self.adjust_end_date()
        print(self.end_cal.get())

    def adjust_end_date(self):
        if self.end_date is not None:
            self.end_date += datetime.timedelta(days=1)
            self.end_date -= datetime.timedelta(seconds=1)

    def toggle_date_filter(self):
        if self.is_date_filter_on.get():
            self.start_cal.config(state='normal')
            self.end_cal.config(state='normal')
            self.end_date = datetime.datetime.strptime(self.end_cal.get(), "%m/%d/%y")
            self.start_date = datetime.datetime.strptime(self.start_cal.get(), "%m/%d/%y")
            self.adjust_end_date()
        else:
            self.start_cal.config(state='disabled')
            self.end_cal.config(state='disabled')
            self.end_date = None
            self.start_date = None

    def update_chart_button_enable(self):
        if not self.symbol_var.get() or not self.expiration_var.get():
            # self.surface_chart_button.config(state='disabled')
            # self.line_chart_button.config(state='disabled')
            # self.strike_chart_button.config(state='disabled')

            self.positions_menu.entryconfig("Add", state="disabled")
            self.chart_menu.entryconfig("Surface", state="disabled")
            self.chart_menu.entryconfig("Line", state="disabled")
            self.chart_menu.entryconfig("Strike/Profit", state="disabled")
            self.chart_menu.entryconfig("Strike/Metrics", state="disabled")

        else:
            # self.surface_chart_button.config(state='normal')
            # self.line_chart_button.config(state='normal')
            self.positions_menu.entryconfig("Add", state="normal")
            self.chart_menu.entryconfig("Surface", state="normal")
            self.chart_menu.entryconfig("Line", state="normal")

            if not self.strike_var.get():
                # self.strike_chart_button.config(state='disabled')
                self.chart_menu.entryconfig("Strike/Profit", state="disabled")
                self.chart_menu.entryconfig("Strike/Metrics", state="disabled")
            else:
                # self.strike_chart_button.config(state='normal')
                self.chart_menu.entryconfig("Strike/Profit", state="normal")
                self.chart_menu.entryconfig("Strike/Metrics", state="normal")
        if not self.symbol_var.get():
            self.delete_option_button.config(state='disabled')
        else:
            self.delete_option_button.config(state='normal')

    def init_ui(self):
        self.master.title("Options")
        self.init_menus()

        # frame2 = Frame(self, relief=RAISED, borderwidth=1, style='My.TFrame')
        tool_bar = tk.ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        tool_bar.pack(fill=tk.X, side=tk.TOP, expand=False)

        self.pack(fill=tk.BOTH, expand=True)

        self.close_button = tk.ttk.Button(tool_bar, text="Close")
        self.close_button.pack(side=tk.RIGHT, padx=5, pady=5)
        self.close_button.bind('<Button-1>', self.quit_app)

        # self.line_chart_button = tk.ttk.Button(tool_bar, text="Line Chart")
        # self.line_chart_button.pack(side=tk.LEFT, padx=5, pady=5)
        # self.line_chart_button.bind('<Button-1>', self.create_line_chart)

        # self.surface_chart_button = tk.ttk.Button(tool_bar, text="Surface Chart")
        # self.surface_chart_button.pack(side=tk.LEFT, padx=5, pady=5)
        # self.surface_chart_button.bind('<Button-1>', self.create_surface_chart)

        # self.strike_chart_button = tk.ttk.Button(tool_bar, text="Strike Chart")
        # self.strike_chart_button.pack(side=tk.LEFT, padx=5, pady=5)
        # self.strike_chart_button.bind('<Button-1>', self.create_strike_chart)

        self.delete_option_button = tk.ttk.Button(tool_bar, text="Delete option")
        self.delete_option_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.delete_option_button.bind('<Button-1>', self.delete_option)

        self.symbol_var.set('')
        self.symbol_var.trace('w', self.symbol_selection_event)

        self.expiration_var.set('')
        self.expiration_var.trace('w', self.expiration_var_selection_event)

        self.popup_symbol_menu = tk.OptionMenu(tool_bar, self.symbol_var,
                                               *{''})
        self.popup_symbol_menu.config(width=8)
        self.popup_symbol_menu.pack(side=tk.LEFT, padx=5, pady=5)

        self.popup_expiration_menu = tk.OptionMenu(tool_bar, self.expiration_var,
                                                   *{''})
        self.popup_expiration_menu.config(width=16)
        self.popup_expiration_menu.pack(side=tk.LEFT, padx=5, pady=5)

        self.strike_var.set('')
        self.strike_var.trace('w', self.strike_var_selection_event)

        self.popup_strike_menu = tk.OptionMenu(tool_bar, self.strike_var,
                                               *{''})
        self.popup_strike_menu.config(width=7)
        self.popup_strike_menu.pack(side=tk.LEFT, padx=5, pady=5)

        tool_bar_style = Style()
        tool_bar_style.theme_use("default")
        tool_bar_style.configure('My.TFrame', background='lightsteelblue')

        date_filter_container = tk.ttk.Frame(tool_bar, style='My.TFrame')
        date_filter_container.pack(fill=tk.X, side=tk.LEFT, expand=False)
        check_box = tk.Checkbutton(date_filter_container,
                                   text="Date Filter",
                                   variable=self.is_date_filter_on,
                                   command=self.toggle_date_filter,
                                   bg='lightsteelblue')
        # style='My.TFrame')
        check_box.pack(padx=10, side=tk.LEFT)

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

        bid_extrinsic_container = tk.ttk.Frame(tool_bar, style='My.TFrame')
        bid_extrinsic_container.pack(fill=tk.BOTH, side=tk.LEFT, expand=False)

        self.bid_extrinsic_value.set(1)

        self.extrinsic_value_radio = tk.Radiobutton(bid_extrinsic_container,
                                                    text="Extrinsic value",
                                                    padx=20,
                                                    variable=self.bid_extrinsic_value,
                                                    value=1,
                                                    background="lightsteelblue")
        self.extrinsic_value_radio.pack(anchor=tk.W)
        self.bid_value_radio = tk.Radiobutton(bid_extrinsic_container,
                                              text="Bid Value",
                                              padx=20,
                                              variable=self.bid_extrinsic_value,
                                              value=2,
                                              background="lightsteelblue")
        self.bid_value_radio.pack(anchor=tk.W)
        self.bid_extrinsic_value.set(1)
        # import time
        # time.sleep(1)

        self.plot_frame = tk.ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        self.plot_frame.pack(fill=tk.BOTH, side=tk.TOP, expand=True)

        self.status_var.set("Status")
        self.status_label = tk.ttk.Label(self, textvariable=self.status_var, background="lightsteelblue")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, expand=False, ipadx=10, ipady=5)

    def show_positions(self):
        df_positions = self.options_db.get_positions()
        dialog_position = []
        if len(df_positions.index) > 0:
            web = FinanceWeb()
            # for index, row in df_positions.iterrows():
            #     open_date = row["open_date"].strftime('%Y-%m-%d')
            #     expire_date = self.options_db.get_expire_date_from_id(row["option_expire_id"]).strftime('%Y-%m-%d')
            #     position = {'id': row["position_id"], 'symbol': row["symbol"], 'put_call': row["put_call"],
            #                 'buy_sell': row["buy_sell"], 'open_date': open_date, 'option': row["option_price"],
            #                 'strike': row["strike_price"], 'expiration': expire_date}
            #     dialog_position.append(position)

            expire_date_list = []
            for index, row in df_positions.iterrows():
                expire_date = self.options_db.get_expire_date_from_id(row["option_expire_id"]).strftime('%Y-%m-%d')
                expire_date_list.append((expire_date))
            df_positions.insert( len(df_positions.columns), "expire_date_str", expire_date_list)

            current_stock_price = web.get_quotes_for_stock_series_yahoo(row["symbol"])

            dict = {'positions': df_positions, 'delete': False, 'current_stock_price': current_stock_price}

            dialog = listPos(dict)
            self.tk_root.wait_window(dialog.top)
            if dict["delete"]:
                self.options_db.delete_position(dict["selected"]["id"])
        else:
            tk.messagebox.showinfo("No Positions", "There are no positions")

    def add_position(self):
        if self.expiration_var.get():
            row = self.shadow_expiration[self.expiration_var.get()]
            option_expire_id = row['option_expire_id']

            dict = {'symbol': self.symbol_var.get(),
                    'expiration_str': self.expiration_var.get(),
                    'option_expire_id': option_expire_id,
                    'added': False}

            dialog = addPos(dict)
            self.tk_root.wait_window(dialog.top)
            if dict["added"]:
                open_date = parser.parse(dict["open_date"])
                self.options_db.add_position(dict["symbol"],
                                             dict["put_call"],
                                             dict["buy_sell"],
                                             open_date,
                                             dict["option_price"],
                                             dict["strike_price"],
                                             dict["option_expire_id"])

    def init_menus(self):
        self.menu_bar = tk.Menu(self.tk_root)
        self.positions_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.positions_menu.add_command(label="Show", command=self.show_positions)
        self.positions_menu.add_command(label="Add", command=self.add_position)
        self.menu_bar.add_cascade(label="Positions", menu=self.positions_menu)

        self.chart_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.chart_menu.add_command(label="Surface", command=self.create_surface_chart)
        self.chart_menu.add_command(label="Line", command=self.create_line_chart)
        self.chart_menu.add_command(label="Strike/Profit", command=self.create_strike_profit_chart)
        self.chart_menu.add_command(label="Strike/Metrics", command=self.create_strike_metrics_chart)
        # self.chart_menu.add_command(label="Strike/Profit", command=self.add_position)
        self.menu_bar.add_cascade(label="Charts", menu=self.chart_menu)

        self.tk_root.config(menu=self.menu_bar)


def main():
    root = tk.Tk()
    root.geometry("1200x800+300+300")
    GuiOptions(root)
    while True:
        try:
            root.mainloop()
            break
        except UnicodeDecodeError:
            pass


if __name__ == '__main__':
    main()
