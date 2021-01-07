import tkinter as tki
import pandastable as pt
import pandas as pd
import datetime


class ListTable(pt.Table):
    def __init__(self, options_db, table_container, position_ids, **kwargs):
        self.options_db = options_db
        self.position_ids = position_ids
        super(ListTable, self).__init__(table_container, **kwargs)
        table_container.pack(fill='x', expand=True)

    def handleCellEntry(self, row, col) -> None:
        super().handleCellEntry(row, col)
        value = self.model.df.iloc[row, col]
        ticker = self.model.df.loc[row, 'Ticker']
        column = self.model.df.columns[col]
        if row < len(self.position_ids):
            position_id = self.position_ids[row]

            if column == 'Closed':
                date = datetime.datetime.strptime(value, '%Y-%m-%d')
                self.options_db.update_positions_field(position_id, "close_date", date)
            elif column == 'Close Price':
                self.options_db.update_positions_field(position_id, "option_price_close", value)
            elif column == 'Open Price':
                self.options_db.update_positions_field(position_id, "option_price_open", value)
            elif column == 'Stock Price(Open)':
                self.options_db.update_positions_field(position_id, "stock_price_open", value)
            elif column == 'Stock Price(Close)':
                self.options_db.update_positions_field(position_id, "stock_price_close", value)
            else:
                print('changed:', row, column, "Unhandled")




class ListPositions(object):
    root = None

    def __init__(self, dict, options_db):

        self.options_db = options_db
        self.top = tki.Toplevel(ListPositions.root)
        self.top.geometry('1300x300')
        self.top.grab_set()

        frm = tki.Frame(self.top, borderwidth=4, relief='ridge')
        frm.pack(fill='both', expand=True)

        table_container = tki.ttk.Frame(frm)
        # table_container.grid(row=0, column=0, columnspan=2)
        pd_list = pd.DataFrame()
        open_date = []
        close_date = []
        pd_list.insert(0, "Ticker", dict["positions"]["symbol"])
        pd_list.insert(1, "Put/Call", dict["positions"]["put_call"])
        pd_list.insert(2, "Buy/Sell", dict["positions"]["buy_sell"])
        for index, row in dict["positions"].iterrows():
            open_date.append(row["open_date"].strftime('%Y-%m-%d'))
            close_date.append(None if row["close_date"] is None or row["close_date"] is pd.NaT else row["close_date"].strftime('%Y-%m-%d'))

        pd_list.insert(3, "Opened", open_date)
        pd_list.insert(4, "Open Price", dict["positions"]["option_price_open"])
        pd_list.insert(5, "Closed", close_date)
        pd_list.insert(6, "Close Price", dict["positions"]["option_price_close"])
        pd_list.insert(7, "Current Price", dict["positions"]["current_option_price"])
        pd_list.insert(8, "Strike Price", dict["positions"]["strike_price"])
        pd_list.insert(9, "Stock Price(Open)", dict["positions"]["stock_price_open"])
        pd_list.insert(10, "Stock Price(Current)", dict["positions"]["current_stock_price"])
        pd_list.insert(11, "Stock Price(Close)", dict["positions"]["stock_price_close"])
        pd_list.insert(12, "Expiration", dict["positions"]["expire_date_str"])

        # super(ListTable, self).__init__(table_container, dataframe=pd_list, width=width,
        #                                     showtoolbar=showtoolbar, showstatusbar=showstatusbar)

        self.table = ListTable(self.options_db, table_container, dict["positions"]["position_id"],
                               dataframe=pd_list,
                               width=1230,
                               showtoolbar=False,
                               showstatusbar= False)
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
        b_ok['command'] = lambda: self.delete_position(dict)
        b_ok.pack(side=tki.LEFT, padx=200)
        # b_ok.grid(row=1, column=0)

        b_cancel = tki.Button(frm, text='Close')
        b_cancel['command'] = self.top.destroy
        b_cancel.pack(side=tki.RIGHT, padx=200)
        # b_cancel.grid(row=1, column=1)

    def delete_position(self, dict):
        try:
            dict["delete"] = True
            selected_row = self.table.getSelectedRow()
            dict["position_id"] = dict["positions"]["position_id"][selected_row]
            self.top.destroy()
        except ValueError:
            self.strike_entry.focus_set()
