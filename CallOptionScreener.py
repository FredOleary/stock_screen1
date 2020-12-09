#!/usr/bin/env python3

import tkinter as tk
from tkinter.ttk import Style
from tkinter import messagebox
import sys
import math
import logging
import logging.handlers

from DbFinance import FinanceDB
from OptionsWatch import OptionsWatch
from WebFinance import FinanceWeb
import pandas as pd
from pandastable import Table, TableModel

class CallScreenerOptions(tk.ttk.Frame):

    def __init__(self, root):
        super().__init__()
        self.tk_root = root
        self.close_button = None
        self.status_label = None
        self.call_screener_frame = None

        self.status_var = tk.StringVar(self)

        self.init_ui()
        self.logger = self.create_logger()
        self.web = FinanceWeb(self.logger)

        self.options_db = FinanceDB()
        self.options_db.initialize()
        self.companies = OptionsWatch()
        self.init_table()

        self.update_options()
    # noinspection PyUnusedLocal
    @staticmethod
    def quit_app(event):
        print("Exit command")
        sys.exit()

    def clear_call_screener_frame(self):
        for widget in self.call_screener_frame.winfo_children():
            widget.destroy()

    def create_logger(self):
        # noinspection SpellCheckingInspection
        log_format = "%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s"
        date_fmt = "%m-%d %H:%M"

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(filename="screen_options.log", level=logging.INFO, filemode="w",
                            format=log_format, datefmt=date_fmt)

        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_fmt))

        logger = logging.getLogger("screen_options")
        logger.addHandler(stream_handler)
        logger.setLevel(logging.DEBUG)

        return logger

    def init_ui(self):
        self.master.title("Option Screener")

        # frame2 = Frame(self, relief=RAISED, borderwidth=1, style='My.TFrame')
        tool_bar = tk.ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        tool_bar.pack(fill=tk.X, side=tk.TOP, expand=False)

        self.pack(fill=tk.BOTH, expand=True)

        self.close_button = tk.ttk.Button(tool_bar, text="Close")
        self.close_button.pack(side=tk.RIGHT, padx=5, pady=5)
        self.close_button.bind('<Button-1>', self.quit_app)



        tool_bar_style = Style()
        tool_bar_style.theme_use("default")
        tool_bar_style.configure('My.TFrame', background='lightsteelblue')



        self.call_screener_frame = tk.ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        self.call_screener_frame.pack(fill=tk.BOTH, side=tk.TOP, expand=True)

        self.status_var.set("Status")
        self.status_label = tk.ttk.Label(self, textvariable=self.status_var, background="lightsteelblue")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, expand=False, ipadx=10, ipady=5)

    def init_table(self):
        self.table_dict = {}
        for company in self.companies.get_companies():
            self.table_dict[company["symbol"]] = [company["symbol"], math.nan, math.nan, math.nan, math.nan, math.nan, math.nan]

        self.data_frame = pd.DataFrame.from_dict(self.table_dict, orient='index',
                                         columns=['Ticker', 'Stock Price', 'Strike', '%(OTM)', 'Bid', 'Ask', 'ROI (Bid/Stock Price)'])
        self.table = Table(self.call_screener_frame, dataframe=self.data_frame,
                                showtoolbar=False, showstatusbar=True)
        self.table.show()
        self.update_options()

    def update_options(self):
        print("updating...")
        options = self.web.get_options_for_stock_series_yahoo("TSLA", strike_filter="OTM", put_call="CALL")
        for company in self.companies.get_companies():
            options = self.web.get_options_for_stock_series_yahoo(company["symbol"], strike_filter="OTM", put_call="CALL")
            self.update_company_in_table(company["symbol"], options)
        self.table.redraw()
        self.tk_root.after(10000, self.update_options)

    def update_company_in_table(self, company:str, options: list) -> None:
        chain = options[0] # TODO allow user to choose expiration date
        best_index, otm_percent_actual = self.find_best_index(chain, 15 )
        self.data_frame.loc[company, 'Stock Price'] = chain['current_value']
        self.data_frame.loc[company, 'Strike'] = chain['options_chain']['calls'].iloc[best_index]['strike']
        self.data_frame.loc[company, '%(OTM)'] = otm_percent_actual
        self.data_frame.loc[company, 'Bid'] = chain['options_chain']['calls'].iloc[best_index]['bid']
        self.data_frame.loc[company, 'Ask'] = chain['options_chain']['calls'].iloc[best_index]['ask']
        roi_percnt = round( (chain['options_chain']['calls'].iloc[best_index]['bid']/chain['current_value'] *100),2)
        self.data_frame.loc[company, 'ROI (Bid/Stock Price)'] = roi_percnt

    def find_best_index(self, chain: {}, otm_percent) -> int:
        best_index = 0
        otm_percent_actual = math.nan
        index = 0
        current_delta = 100
        while index <  len(chain['options_chain']['calls']):
            diff = chain['options_chain']['calls'].iloc[index]['strike'] - chain['current_value']
            percent_diff = (diff/chain['current_value'] * 100)
            delta = otm_percent - percent_diff
            if abs(delta) < current_delta:
                current_delta = delta
                best_index = index
                otm_percent_actual = round(percent_diff,2)
            index += 1
        return best_index, otm_percent_actual

def main():
    root = tk.Tk()
    root.geometry("1200x800+300+300")
    CallScreenerOptions(root)
    while True:
        try:
            root.mainloop()
            break
        except UnicodeDecodeError:
            pass



if __name__ == '__main__':
    main()
