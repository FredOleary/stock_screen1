import tkinter as tki
import pandastable as pt
import pandas as pd
import datetime
import math

class ListTable(pt.Table):
    def __init__(self, options_db, table_container, position_ids, **kwargs):
        self.options_db = options_db
        self.position_ids = position_ids
        super(ListTable, self).__init__(table_container, **kwargs)
        table_container.pack(fill='x', expand=True)

    def handleCellEntry(self, row, col) -> None:
        super().handleCellEntry(row, col)
        value = self.model.df.iloc[row, col]
        column = self.model.df.columns[col]
        if row < len(self.position_ids):
            position_id = self.position_ids[row]

            if column == 'Closed':
                if math.isnan(value):
                    self.options_db.update_positions_field(position_id, "close_date", math.nan)
                else:
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
            elif column == 'Opened':
                date = datetime.datetime.strptime(value, '%Y-%m-%d')
                self.options_db.update_positions_field(position_id, "open_date", date)
            elif column == 'Status':
                value = value.upper()
                self.options_db.update_positions_field(position_id, "status", value)
            else:
                print('changed:', row, column, "Unhandled")


class ListPositions(object):
    root = None

    def __init__(self, position_info, options_db):

        self.options_db = options_db
        self.top = tki.Toplevel(ListPositions.root)
        self.top.geometry('1300x300')
        self.top.grab_set()

        frm = tki.Frame(self.top, borderwidth=4, relief='ridge')
        frm.pack(fill='both', expand=True)

        # table_container = tki.ttk.Frame(frm)
        table_container = tki.Frame(frm)
        pd_list = pd.DataFrame()
        open_date = []
        close_date = []
        option_profit =[]
        position = 0
        pd_list.insert(position, "Ticker", position_info["positions"]["symbol"])
        position += 1
        pd_list.insert(position, "Status", position_info["positions"]["status"])
        position += 1
        pd_list.insert(position, "Put/Call", position_info["positions"]["put_call"])
        position += 1
        pd_list.insert(position, "Buy/Sell", position_info["positions"]["buy_sell"])
        position += 1
        for index, row in position_info["positions"].iterrows():
            open_date.append(row["open_date"].strftime('%Y-%m-%d'))
            close_date.append(None if row["close_date"] is None or row["close_date"] is pd.NaT
                              else row["close_date"].strftime('%Y-%m-%d'))

        pd_list.insert(position, "Opened", open_date)
        position += 1
        pd_list.insert(position, "Open Price", position_info["positions"]["option_price_open"])
        position += 1
        pd_list.insert(position, "Closed", close_date)
        position += 1
        pd_list.insert(position, "Close Price", position_info["positions"]["option_price_close"])
        position += 1

        for index, row in position_info["positions"].iterrows():
            if row["status"].upper() == "CLOSED" or row["status"].upper() == "EXPIRED":
                option_profit.append(row["option_price_open"] - row["option_price_close"])
            elif row["status"].upper() == "OPEN":
                option_profit.append(row["option_price_open"] - row["current_option_price"])
            else:
                option_profit.append(None)
        pd_list.insert(position, "Option Profit", option_profit)
        position += 1
        pd_list.insert(position, "Current Price", position_info["positions"]["current_option_price"])
        position += 1
        pd_list.insert(position, "Strike Price", position_info["positions"]["strike_price"])
        position += 1
        pd_list.insert(position, "Stock Price(Open)", position_info["positions"]["stock_price_open"])
        position += 1
        pd_list.insert(position, "Stock Price(Current)", position_info["positions"]["current_stock_price"])
        position += 1
        pd_list.insert(position, "Stock Price(Close)", position_info["positions"]["stock_price_close"])
        position += 1
        pd_list.insert(position, "Expiration", position_info["positions"]["expire_date_str"])

        self.table = ListTable(self.options_db, table_container, position_info["positions"]["position_id"],
                               dataframe=pd_list,
                               width=1230,
                               showtoolbar=False,
                               showstatusbar=False)

        self.table.show()

        b_ok = tki.Button(frm, text='Delete')
        b_ok['command'] = lambda: self.delete_position(position_info)
        b_ok.pack(side=tki.LEFT, padx=200)
        # b_ok.grid(row=1, column=0)

        b_cancel = tki.Button(frm, text='Close')
        b_cancel['command'] = self.top.destroy
        b_cancel.pack(side=tki.RIGHT, padx=200)

    def delete_position(self, position_info):
        try:
            position_info["delete"] = True
            selected_row = self.table.getSelectedRow()
            position_info["position_id"] = position_info["positions"]["position_id"][selected_row]
            self.top.destroy()
        except ValueError:
            pass
