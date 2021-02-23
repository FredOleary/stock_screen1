#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue October  8 19:35:54 2020

@author: fred OLeary
"""
import sqlite3
import numpy as np
import pandas as pd
import datetime


# noinspection PyMethodMayBeStatic
class FinanceDB:
    """ Storage for news/prices etc """

    def __init__(self, stock_data=None, logger=None, db_name_schema="stock_options"):
        self.connection = None
        self.logger = logger
        self.db_name = db_name_schema
        self.stock_data = stock_data
        self.tables = [{"name": "stocks",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS stocks (
                                        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        symbol TEXT,
                                        name TEXT NOT NULL
                                    ); """},
                       {"name": "option_expire",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS option_expire (
                                        option_expire_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        symbol TEXT,
                                        expire_date TIMESTAMP NOT NULL,
                                        UNIQUE( symbol, expire_date)
                                    ); """},
                       {"name": "stock_price",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS stock_price (
                                        stock_price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        symbol TEXT,
                                        time TIMESTAMP NOT NULL,
                                        price REAL NOT NULL,
                                        option_expire_id INTEGER,
                                        UNIQUE( symbol, time, option_expire_id),
                                        CONSTRAINT fk_option_expire
                                            FOREIGN KEY (option_expire_id)
                                            REFERENCES option_expire(option_expire_id)

                                    ); """},

                       {"name": "put_call_options",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS put_call_options (
                            call_option_price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            stock_price_id INTEGER, 
                            put_call TEXT NOT NULL,
                            lastTradeDate TIMESTAMP NOT NULL,
                            strike REAL NOT NULL,
                            lastPrice REAL,
                            bid REAL,
                            ask REAL,
                            change REAL NOT NULL,
                            volume REAL,
                            openInterest INTEGER,
                            impliedVolatility REAL NOT NULL,
                            delta REAL,
                            gamma REAL,
                            theta REAL,
                            vega REAL,
                            inTheMoney TEXT NOT NULL,
                            option_expire_id INTEGER,
                            current_value REAL NOT NULL,
                            UNIQUE( stock_price_id, put_call, strike),
                            CONSTRAINT fk_stock_price
                                FOREIGN KEY (stock_price_id)
                                REFERENCES stock_price(stock_price_id)
                            CONSTRAINT fk_option_expire
                                FOREIGN KEY (option_expire_id)
                                REFERENCES option_expire(option_expire_id)

                      ); """},
                       {"name": "positions",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS positions (
                         position_id INTEGER PRIMARY KEY AUTOINCREMENT,
                         symbol TEXT,
                         put_call TEXT NOT NULL,
                         buy_sell TEXT NOT NULL,
                         open_date TIMESTAMP NOT NULL,
                         option_price_open REAL NOT NULL,
                         close_date TIMESTAMP,
                         option_price_close REAL,
                         strike_price REAL NOT NULL,
                         stock_price_open REAL,
                         stock_price_close REAL,
                         option_expire_id INTEGER,
                         status TEXT,
                         contracts INTEGER,
                         option_profit REAL,
                         stock_profit REAL,
                         UNIQUE( symbol, open_date, option_expire_id),
                         CONSTRAINT fk_option_expire
                            FOREIGN KEY (option_expire_id)
                            REFERENCES option_expire(option_expire_id)


                     ); """}

                       ]

    def initialize(self):
        """ Initialize database connection and tables """
        self.connection = sqlite3.connect(self.db_name,
                                          detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        if self.stock_data:
            self._create_verify_tables()
            self._create_verify_stock_data()

    def close(self):
        """ Close db if necessary """
        if self.connection is not None:
            self.connection.close()

    def add_option_quote(self, quotes: list) -> int:
        if len(quotes) > 0:
            try:
                for quote in quotes:
                    if len(quote['options_chain']['calls']) > 0 or len(quote['options_chain']['puts']) > 0:
                        cursor = self.connection.cursor()
                        cursor.execute("SELECT * FROM option_expire WHERE symbol = ? AND expire_date = ?",
                                       [quote["ticker"], quote["expire_date"]])
                        rows = cursor.fetchall()
                        if not rows:
                            cursor.execute("INSERT INTO option_expire(symbol, expire_date) VALUES (?,?)",
                                           (quote["ticker"],
                                            quote["expire_date"]))
                            option_expire_id = cursor.lastrowid
                        else:
                            option_expire_id = rows[0][0]
                        cursor.execute(
                            "SELECT * FROM stock_price WHERE symbol = ? AND time = ? AND option_expire_id = ?",
                            [quote["ticker"], quote["current_time"], option_expire_id])
                        rows = cursor.fetchall()
                        if not rows:  # empty - record does not exist
                            cursor.execute(
                                "INSERT INTO stock_price(symbol, time, price, option_expire_id) VALUES (?,?,?,?)",
                                (quote["ticker"],
                                 quote["current_time"],
                                 quote["current_value"],
                                 option_expire_id))

                            rowid = cursor.lastrowid
                        else:
                            rowid = rows[0][0]  # Existing rowid
                        if rowid != -1:
                            self.insert_put_call(cursor, True, rowid, quote['options_chain']['calls'], option_expire_id,
                                                 quote["current_value"])
                            self.insert_put_call(cursor, False, rowid, quote['options_chain']['puts'], option_expire_id,
                                                 quote["current_value"])

                        self.connection.commit()
                        cursor.close()
                    else:
                        if self.logger is not None:
                            self.logger.info(
                                "No options for {0}, expiration {1}".format(quote["ticker"], quote["expire_date"]))
                # print("value added for time: ", quote["time"])
            except Exception as err:
                if self.logger is not None:
                    self.logger.error("Exception ", err.args[0])
                return 0
                # print("value already added for time: ", quote["time"])

    def insert_put_call(self, cursor: sqlite3.Cursor, is_call: bool, rowid: int,
                        put_call_options_chain: pd.DataFrame, option_expire_id: int, current_value: float):
        for index, option in put_call_options_chain.iterrows():
            put_call = "PUT"
            if is_call:
                put_call = "CALL"
            try:
                cursor.execute("INSERT INTO put_call_options("
                               "stock_price_id, put_call, lastTradeDate, strike, lastPrice, bid, ask, "
                               "change, volume, openInterest, impliedVolatility, delta, gamma, theta, vega, inTheMoney, "
                               "option_expire_id, current_value) "
                               "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                               (
                                   rowid,
                                   put_call,
                                   option["lastTradeDate"].to_pydatetime(),
                                   option["strike"],
                                   option["lastPrice"],
                                   option["bid"],
                                   option["ask"],
                                   option["change"],
                                   option["volume"],
                                   option["openInterest"],
                                   option["impliedVolatility"],
                                   option["delta"],
                                   option["gamma"],
                                   option["theta"],
                                   option["vega"],
                                   ("FALSE", "TRUE")[option["inTheMoney"]],
                                   option_expire_id,
                                   current_value
                               ))
            except sqlite3.IntegrityError as err:
                if err.args[0] == 'UNIQUE constraint failed: put_call_options.stock_price_id, ' \
                                  'put_call_options.put_call, put_call_options.strike':
                    # This can happen if we attempt to insert the same data twice
                    pass
                else:
                    if self.logger is not None:
                        self.logger.error(err.args[0])

    def get_all_symbols(self) -> pd.DataFrame:
        """ all symbols for """
        query = "SELECT symbol FROM stocks"
        cursor = self.connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        np_rows = np.array(rows)
        df_symbols = np_rows[:, 0]  # symbols
        df = pd.DataFrame(data=df_symbols, columns=["symbol"])
        cursor.close()
        return df

    def get_all_options_expirations(self, symbol: str) -> pd.DataFrame:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM option_expire where symbol = ?", [symbol])
        rows = cursor.fetchall()
        np_rows = np.array(rows)
        cursor.close()
        if len(np_rows) > 0:
            df_expirations = np_rows[:, [0, 2]]  # expire date
            df_column_values = ["option_expire_id", "expire_date"]
            df = pd.DataFrame(data=df_expirations, columns=df_column_values)
            return df
        else:
            return pd.DataFrame()

    def get_all_options_for_expiration(self, option_expire_id: int, put_call: str = None) -> pd.DataFrame:
        cursor = self.connection.cursor()
        query = "SELECT * FROM put_call_options where option_expire_id = ?"
        args = [option_expire_id]
        if type is not None:
            query = query + " AND put_call = ?"
            args.append(put_call)
        cursor.execute(query, args)

        rows = cursor.fetchall()
        np_rows = np.array(rows)
        df_data = np_rows[:, [1, 4, 5, 6, 7, 18]]  # stock_price_id, strike and bid
        df = pd.DataFrame(data=df_data, columns=["stock_price_id", "strike", "lastPrice",
                                                 "bid", "ask", "current_value"])
        cursor.close()
        return df

    def get_strikes_for_expiration(self, option_expire_id: int, strike: float, put_call: str = None) -> pd.DataFrame:
        cursor = self.connection.cursor()
        query = "SELECT * FROM put_call_options where option_expire_id = ? and strike = ?"
        args = [option_expire_id, strike]
        if type is not None:
            query = query + " AND put_call = ?"
            args.append(put_call)
        cursor.execute(query, args)

        rows = cursor.fetchall()
        np_rows = np.array(rows)
        df_data = np_rows[:, [1, 4, 5, 6, 7, 11, 12, 14, 18]]
        df = pd.DataFrame(data=df_data, columns=["stock_price_id", "strike", "lastPrice",
                                                 "bid", "ask", "impliedVolatility",
                                                 "delta", "theta", "current_value"])
        cursor.close()
        return df

    def get_date_times_for_expiration_df(self, symbol: str, option_expire_id: int,
                                         start_date: datetime.datetime = None,
                                         end_date: datetime.datetime = None, ) -> pd.DataFrame:
        cursor = self.connection.cursor()

        query = "SELECT * FROM stock_price where symbol = ? AND option_expire_id = ?"
        args = [symbol, option_expire_id]
        if start_date is not None:
            query = query + " AND time >= ?"
            args.append(start_date)
        if end_date is not None:
            query = query + " AND time <= ?"
            args.append(end_date)

        cursor.execute(query, args)
        rows = cursor.fetchall()
        np_rows = np.array(rows)
        cursor.close()
        if len(np_rows) > 0:
            df_data = np_rows[:, [0, 2, 3]]  # stock_price_id, DateTime and stock price
            df_column_values = ["stock_price_id", "datetime", "price"]
            df = pd.DataFrame(data=df_data, columns=df_column_values)
            return df
        else:
            return pd.DataFrame()

    def get_unique_strikes_for_expiration(self, option_expire_id, put_call=None) -> pd.DataFrame:
        cursor = self.connection.cursor()
        if put_call is None:
            cursor.execute("SELECT distinct strike FROM put_call_options where option_expire_id = ? ORDER BY strike",
                           [option_expire_id])
        else:
            cursor.execute("SELECT distinct strike FROM put_call_options where option_expire_id = ? AND put_call = ?"
                           "ORDER BY strike",
                           [option_expire_id, put_call])
        rows = cursor.fetchall()
        np_rows = np.array(rows)
        df_data = np_rows[:, 0]  # strike
        df_column_values = ["strike"]
        df = pd.DataFrame(data=df_data, columns=df_column_values)
        cursor.close()
        return df

    def delete_options(self, symbol: str, option_expire_id: int) -> None:
        if option_expire_id != -1:
            self._delete_option(option_expire_id)
        else:
            cursor = self.connection.cursor()
            cursor.execute("SELECT option_expire_id FROM option_expire where symbol = ? ",[symbol])
            rows = cursor.fetchall()
            for row in rows:
                self._delete_option(row[0])
            cursor.execute("DELETE FROM stocks where symbol = ?", (symbol,))
            cursor.close()

    def _delete_option(self, expire_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM put_call_options where option_expire_id = ? ", (expire_id,))
        cursor.execute("DELETE FROM option_expire where option_expire_id = ? ", (expire_id,))
        cursor.execute("DELETE FROM stock_price where option_expire_id = ? ", (expire_id,))
        self.connection.commit()
        cursor.close()

    def get_positions(self) -> pd.DataFrame:
        cursor = self.connection.cursor()
        cmd = "SELECT * FROM positions"
        cursor.execute(cmd)
        rows = np.array(cursor.fetchall())
        cursor.close()
        if len(rows) > 0:
            df_data = rows[:, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]]  # stock_price_id, strike and bid
            df = pd.DataFrame(data=df_data, columns=["position_id", "symbol", "put_call", "buy_sell",
                                                     "open_date", "option_price_open",
                                                     "close_date", "option_price_close",
                                                     "strike_price", "stock_price_open", "stock_price_close",
                                                     "option_expire_id", "status", "contracts"])
            return df
        return pd.DataFrame()

    def delete_position(self, position_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM positions where position_id = ? ", (position_id,))
        self.connection.commit()
        cursor.close()

    def update_positions_field(self, position_id, column_name, value) -> None:
        cursor = self.connection.cursor()
        sql_query = "UPDATE positions SET {0} = ? WHERE position_id = ?".format(column_name)
        cursor.execute(sql_query, (value, position_id))
        self.connection.commit()
        cursor.close()

    def get_expire_date_from_id(self, option_expire_id: int) -> datetime.datetime:
        cursor = self.connection.cursor()
        cursor.execute("SELECT expire_date FROM option_expire where option_expire_id = ?", (option_expire_id,))
        rows = cursor.fetchall()
        cursor.close()
        return rows[0][0]

    def add_position(self, symbol: str, put_call: str, buy_sell: str, open_date: datetime.datetime,
                     option_price_open: float, strike_price: float, option_expire_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO positions(symbol, put_call, buy_sell, open_date,"
                       "option_price_open, strike_price, option_expire_id, status) VALUES (?,?,?,?,?,?,?,?)",
                       [symbol, put_call, buy_sell, open_date, option_price_open,
                        strike_price, option_expire_id, "OPEN"])
        self.connection.commit()
        cursor.close()

    def search_positions(self, option_expire_id: int, strike_price: float) -> \
            (datetime.datetime, float, datetime.datetime, float, float):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM positions where option_expire_id = ? and strike_price = ?",
                       (option_expire_id, strike_price))
        rows = cursor.fetchall()
        cursor.close()
        if len(rows) > 0:
            return rows[0][4], rows[0][5], rows[0][6], rows[0][7], rows[0][8]
        else:
            return None, None, None, None, None

    def get_name_for_symbol(self, symbol: str) -> str:
        result = ""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM stocks where symbol = ? ", (symbol,))
        rows = cursor.fetchall()
        if len(rows) > 0:
            result = rows[0][0]
        cursor.close()
        return result

    def get_strike_data_for_expiration(self, expire_id: int, strike: float, put_call: str) -> pd.DataFrame:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM put_call_options LEFT JOIN stock_price "
                       "ON put_call_options.stock_price_id = stock_price.stock_price_id "
                       "where put_call_options.option_expire_id = ? "
                       "and put_call_options.strike = ?"
                       "and put_call_options.put_call = ?",
                       (expire_id, strike, put_call))
        rows = np.array(cursor.fetchall())
        cursor.close()
        if len(rows) > 0:
            df_data = rows[:, [21, 2, 5, 6, 7, 18]]
            df = pd.DataFrame(data=df_data, columns=["time", "put_call", "lastPrice",
                                                     "bid", "ask", "impliedVolatility"])
            return df

        return pd.DataFrame()

    def _create_verify_tables(self):
        # Get a list of all tables
        cursor = self.connection.cursor()
        cmd = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor.execute(cmd)
        names = [row[0] for row in cursor.fetchall()]
        for table in self.tables:
            if not table['name'] in names:
                cursor.execute(table['create_sql'])
                # table doesn't exist, create it
        cursor.close()

    def _create_verify_stock_data(self):
        for stock in self.stock_data:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM stocks WHERE symbol = ?", [stock["symbol"]])
            rows = cursor.fetchall()
            if not rows:  # empty - record does not exist
                cursor.execute("INSERT INTO stocks(symbol, name) VALUES (?,?)",
                               [stock["symbol"], stock["name"]])
                self.connection.commit()
            cursor.close()
        return
