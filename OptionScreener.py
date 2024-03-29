#!/usr/bin/env python3

import tkinter as tk
from tkinter.ttk import Style
from queue import Queue
from threading import Thread

import sys
import math
import logging
import logging.handlers
import datetime

# import APITradier
import Utilities
from DbFinance import FinanceDB
from OptionsScreenerWatch import OptionsScreenerWatch
import pandas as pd
from pandastable import Table
from OptionsConfiguration import OptionsConfiguration


class OptionsFetch(Thread):
    def __init__(self, request_queue: Queue, response_queue: Queue, logger=None) -> None:
        Thread.__init__(self)
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.logger = logger
        # self.web = FinanceWeb()
        self.web = Utilities.get_options_API(self.logger)
        self.running = True

    def run(self):
        config = OptionsConfiguration()
        look_a_heads = (config.get_configuration())["screener_look_ahead_expirations"]
        print("Starting OptionsFetch thread, look_a_heads = {0}".format(look_a_heads))
        while self.running:
            company = self.request_queue.get()
            if type(company) == str and company == "QUIT":
                self.running = False
            else:
                if self.logger:
                    self.logger.info("Request received. {0} ({1}), expiration: {2}".format(
                        company["symbol"], company["name"], company["expiration"]
                    ))
                try:
                    options = self.web.get_options_for_symbol_and_expiration(company["symbol"],
                                                                             company["expiration"],
                                                                             put_call="CALL")

                    self.response_queue.put({'company': company, 'options': options})
                except Exception as err:
                    if self.logger:
                        self.logger.error("OptionsFetch thread: Exception ", err.args[0])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyAttributeOutsideInit
class CallScreenerOptions(tk.ttk.Frame):

    def __init__(self, root):
        super().__init__()
        self.tk_root = root
        self.close_button = None
        self.status_label = None
        self.call_screener_frame = None
        self.popup_expiration_menu = None
        self.expiration_var = tk.StringVar(self)
        self.otm_strike_var = tk.StringVar(self)
        self.otm_list = ["15%", "5%", "ATM", "10%", "20%"]

        self.request_queue = Queue()
        self.response_queue = Queue()

        self.status_var = tk.StringVar(self)

        self.init_ui()
        self.logger = self.create_logger()
        # self.web = FinanceWeb(self.logger)

        self.options_db = FinanceDB()
        self.options_db.initialize()
        self.companies = OptionsScreenerWatch()
        self.init_table()
        self.clear_expiration_menu()
        self.clear_otm_strike_menu()
        config = OptionsConfiguration()
        look_a_heads = (config.get_configuration())["screener_look_ahead_expirations"]
        expiration_list = self.get_expirations(look_a_heads)
        self.update_expiration(expiration_list)
        self.expiration_var.set(expiration_list[0])
        self.update_otm_strike(self.otm_list)
        self.otm_strike_var.set(self.otm_list[0])
        self.temp()
        self.options_fetch = OptionsFetch(self.request_queue, self.response_queue, self.logger)
        self.options_fetch.start()
        self.update_options()

        self.tk_root.protocol("WM_DELETE_WINDOW", self.quit_app)

    @staticmethod
    def get_expirations(count):
        expiration_date = datetime.datetime.now()
        result = []
        while count > 0:
            date_str = expiration_date.strftime('%Y-%m-%d')
            (is_third_friday, date_time) = Utilities.is_third_friday(date_str)
            if is_third_friday:
                result.append(date_time.strftime('%Y-%m-%d'))
                count -= 1
            expiration_date += datetime.timedelta(days=1)
        return result

    # noinspection PyUnusedLocal
    def quit_app(self, event=None):
        print("Exit command")
        with self.request_queue.mutex:
            self.request_queue.queue.clear()

        self.request_queue.put("QUIT")
        self.options_fetch.join()
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

        start_date_label = tk.ttk.Label(tool_bar, text="Expiration")
        start_date_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.popup_expiration_menu = tk.OptionMenu(tool_bar, self.expiration_var, *{''})
        self.popup_expiration_menu.config(width=16)
        self.popup_expiration_menu.pack(side=tk.LEFT, padx=5, pady=5)
        self.expiration_var.trace('w', self.expiration_var_selection_event)

        otm_label = tk.ttk.Label(tool_bar, text="OTM Strike delta (%)")
        otm_label.pack(side=tk.LEFT, padx=10, pady=5)

        self.otm_strike_menu = tk.OptionMenu(tool_bar, self.otm_strike_var, *{''})
        self.otm_strike_menu.config(width=10)
        self.otm_strike_menu.pack(side=tk.LEFT, padx=5, pady=5)
        self.otm_strike_var.trace('w', self.otm_strike_var_selection_event)

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

    # noinspection PyAttributeOutsideInit
    def init_table(self):
        table_dict = {}
        for company in self.companies.get_companies():
            table_dict[company["symbol"]] = [company["symbol"], math.nan, math.nan,
                                             math.nan, math.nan, math.nan, math.nan,
                                             math.nan, math.nan, math.nan, math.nan]

        self.data_frame = pd.DataFrame.from_dict(table_dict, orient='index',
                                                 columns=['Ticker', 'Stock Price', 'Strike', '%(OTM)',
                                                          'Bid', 'Ask', 'ROI(%) (Bid/Stock Price)',
                                                          'Annual ROI(%)', 'Implied Volatility',
                                                          'Delta', 'Theta'])
        self.table = Table(self.call_screener_frame, dataframe=self.data_frame,
                           showtoolbar=False, showstatusbar=True)
        self.table.show()
        self.check_response()

    def clear_expiration_menu(self):
        self.expiration_var.set('')
        self.popup_expiration_menu['menu'].delete(0, 'end')

    def clear_otm_strike_menu(self):
        self.otm_strike_var.set('')
        self.otm_strike_menu['menu'].delete(0, 'end')

    def update_expiration(self, choices):
        for choice in choices:
            self.popup_expiration_menu['menu'].add_command(label=choice,
                                                           command=lambda value=choice: self.expiration_var.set(value))

    def update_otm_strike(self, choices):
        for choice in choices:
            self.otm_strike_menu['menu'].add_command(label=choice,
                                                           command=lambda value=choice: self.otm_strike_var.set(value))

    # noinspection PyUnusedLocal
    def expiration_var_selection_event(self, *args):
        if self.expiration_var.get():
            self.__clear_table()
            self.table.redraw()

    def otm_strike_var_selection_event(self, *args):
        if self.otm_strike_var.get():
            numbers = [i for i in self.otm_strike_var.get() if i.isdigit()]
            strings =  [str(integer) for integer in numbers]
            a_string = "".join(strings)
            self.otm_percent = 0 if len(a_string) == 0 else int(a_string)
            self.__clear_table()
            self.table.redraw()

    def __clear_table(self):
        with self.request_queue.mutex:
            self.request_queue.queue.clear()

        for index, row in self.data_frame.iterrows():
            self.data_frame.loc[row['Ticker'], 'Stock Price'] = math.nan
            self.data_frame.loc[row['Ticker'], 'Strike'] = math.nan
            self.data_frame.loc[row['Ticker'], '%(OTM)'] = math.nan
            self.data_frame.loc[row['Ticker'], 'Bid'] = math.nan
            self.data_frame.loc[row['Ticker'], 'Ask'] = math.nan
            self.data_frame.loc[row['Ticker'], 'ROI(%) (Bid/Stock Price)'] = math.nan
            self.data_frame.loc[row['Ticker'], 'Annual ROI(%)'] = math.nan
            self.data_frame.loc[row['Ticker'], 'Implied Volatility'] = math.nan
            self.data_frame.loc[row['Ticker'], 'Delta'] = math.nan
            self.data_frame.loc[row['Ticker'], 'Theta'] = math.nan

    def update_options(self):
        if self.request_queue.empty():
            self.status_var.set("Updating...")
            for company in self.companies.get_companies():
                company["expiration"] = self.expiration_var.get()
                self.request_queue.put(company)
            self.status_var.set("")
        else:
            if self.logger:
                self.logger.info("Request Queue not empty yet")

        self.tk_root.after(15000, self.update_options)

    def check_response(self):
        if not self.response_queue.empty():
            response = self.response_queue.get()
            if self.logger:
                if bool(response['options']):
                    self.logger.info("Options received for {0}".format(response['company']['symbol']))
                else:
                    self.logger.warning("No Options received for {0}".format(response['company']['symbol']))
            self.update_company_in_table(response)

        self.tk_root.after(500, self.check_response)

    def update_company_in_table(self, response) -> None:
        try:
            display_chain = response['options']
            if bool(display_chain):
                company = display_chain["ticker"]
                best_index, otm_percent_actual = self.find_best_index(display_chain, self.otm_percent)
                if best_index != -1:
                    self.data_frame.loc[company, 'Stock Price'] = display_chain['current_value']
                    self.data_frame.loc[company, 'Strike'] = display_chain['options_chain']['calls'].iloc[best_index][
                        'strike']
                    self.data_frame.loc[company, '%(OTM)'] = otm_percent_actual
                    self.data_frame.loc[company, 'Bid'] = display_chain['options_chain']['calls'].iloc[best_index][
                        'bid']
                    self.data_frame.loc[company, 'Ask'] = display_chain['options_chain']['calls'].iloc[best_index][
                        'ask']
                    roi_percent = round(
                        (display_chain['options_chain']['calls'].iloc[best_index]['bid'] / display_chain[
                            'current_value'] * 100), 2)
                    self.data_frame.loc[company, 'ROI(%) (Bid/Stock Price)'] = roi_percent
                    self.data_frame.loc[company, 'Implied Volatility'] = \
                        round(display_chain['options_chain']['calls'].iloc[best_index]['impliedVolatility'] * 100, 2)
                    now = datetime.datetime.now()
                    expiration = datetime.datetime.strptime(self.expiration_var.get(), '%Y-%m-%d')
                    delta = (expiration - now).days +1
                    annual_roi = 365 / delta * roi_percent
                    self.data_frame.loc[company, 'Annual ROI(%)'] = round(annual_roi, 2)
                    if 'delta' in display_chain['options_chain']['calls'].columns:
                        self.data_frame.loc[company, 'Delta'] = \
                            display_chain['options_chain']['calls'].iloc[best_index]['delta']
                    if 'theta' in display_chain['options_chain']['calls'].columns:
                        self.data_frame.loc[company, 'Theta'] = \
                            display_chain['options_chain']['calls'].iloc[best_index]['theta']
                else:
                    if self.logger:
                        self.logger.error("No option available for {0}".format(company))
            else:
                if self.logger:
                    self.logger.error("No option available")
        except Exception as err:
            if self.logger:
                self.logger.error(err)

        self.table.redraw()

    def find_best_index(self, chain: {}, otm_percent) -> (int, float):
        best_index = 0
        otm_percent_actual = math.nan
        index = 0
        current_delta = 100
        if len(chain['options_chain']['calls']) > 0:
            while index < len(chain['options_chain']['calls']):
                diff = chain['options_chain']['calls'].iloc[index]['strike'] - chain['current_value']
                percent_diff = (diff / chain['current_value'] * 100)
                delta = otm_percent - percent_diff
                if abs(delta) < current_delta:
                    current_delta = delta
                    best_index = index
                    otm_percent_actual = round(percent_diff, 2)
                index += 1
            return best_index, otm_percent_actual
        else:
            return -1, 0

    def temp(self):
        web = Utilities.get_options_API(self.logger)
        # response_dict = web.get_quote("MAR")
        # if response_dict != {}:
        #     print("pass")
        # else:
        #     print("fail")
        #
        # expirations_dict = web.get_expirations("MAR")
        # if expirations_dict != {}:
        #     print("pass")
        # else:
        #     print("fail")

        options_dict = web.get_options_for_symbol_and_expiration("MAR", "2021-02-19")
        if options_dict != {}:
            print("pass")
        else:
            print("fail")


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
