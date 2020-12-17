import tkinter as tki
import pandastable as pt
import pandas as pd
import numpy as np

class ListPositions(object):

    root = None

    def __init__(self, dict):
        """
        dict_key = <sequence> (dictionary, key) to associate with position
        (providing a sequence for dict_key creates an entry for user input)
        """
        # tki = tkinter
        self.top = tki.Toplevel(ListPositions.root)
        self.top.geometry('1000x300')
        self.top.grab_set()

        frm = tki.Frame(self.top, borderwidth=4, relief='ridge')
        frm.pack(fill='both', expand=True)

        table_container = tki.ttk.Frame(frm)
        table_container.grid(row=0, column=0, columnspan=2)
        pd_list = pd.DataFrame()
        open_date = []
        close_date = []
        pd_list.insert(0, "Ticker", dict["positions"]["symbol"])
        pd_list.insert(1, "Put/Call", dict["positions"]["put_call"])
        pd_list.insert(2, "Buy/Sell", dict["positions"]["buy_sell"])
        for index, row in dict["positions"].iterrows():
            open_date.append(row["open_date"].strftime('%Y-%m-%d'))
            close_date.append(None if row["close_date"] is None else row["close_date"].strftime('%Y-%m-%d'))

        pd_list.insert(3, "Opened", open_date)
        pd_list.insert(4, "Closed", close_date)
        pd_list.insert(5, "Option Price", dict["positions"]["option_price"])
        pd_list.insert(6, "Strike Price", dict["positions"]["strike_price"])
        pd_list.insert(7, "Stock Price(Open)", dict["positions"]["stock_price_open"])
        pd_list.insert(8, "Stock Price(Close)", dict["positions"]["stock_price_close"])
        pd_list.insert(9, "Expiration", dict["positions"]["expire_date_str"])

        self.table = pt.Table(table_container, dataframe=pd_list, width=930, showtoolbar=False, showstatusbar=False)
        self.table.show()


        # self.list_box = tki.Listbox(frm, selectmode=tki.SINGLE, width=80, font="TkFixedFont")
        # for position in dict_key["positions"]:
        #     # self.list_box.insert(position['id'], "{0}\t{1}\t{2}\tPurchased {3}\t{4}/{:6}.\tExpires {6}".format(
        #     #     position['symbol'], position['buy_sell'], position['put_call'],
        #     #     position['date'], position['strike'], position['option'], position['expiration']
        #
        #     self.list_box.insert(position['id'], "{:8}{:4}({:4}) Opened {:10} {:6}/{:6}. Expires {:10}".format(
        #         position['symbol'], position['buy_sell'], position['put_call'],
        #         position['open_date'], position['strike'], position['option'], position['expiration']
        #     ))
        # self.list_box.grid(row=0, column=0, padx=5, pady=5)
        # self.list_box.select_set(0)
        # self.list_box.event_generate("<<ListboxSelect>>")


        b_ok = tki.Button(frm, text='Delete')
        b_ok['command'] = lambda: self.delete_position(dict_key)
        b_ok.grid(row=1, column= 0)

        b_cancel = tki.Button(frm, text='Close')
        b_cancel['command'] = self.top.destroy
        b_cancel.grid(row=1, column= 1)

    def delete_position(self, dict_key):
        try:
            dict_key["delete"] = True
            dict_key["selected"] = dict_key["positions"][self.list_box.curselection()[0]]
            self.top.destroy()
        except ValueError:
            self.strike_entry.focus_set()
