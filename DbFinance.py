#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue October  8 19:35:54 2020

@author: fred OLeary
"""
import sqlite3
import numpy as np
import pandas as pd


# noinspection PyMethodMayBeStatic
class FinanceDB:
    """ Storage for news/prices etc """

    def __init__(self, stock_data=None):
        self.connection = None
        self.db_name = "stock_options"
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
                    cursor.execute("SELECT * FROM stock_price WHERE symbol = ? AND time = ? AND option_expire_id = ?",
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
                # print("value added for time: ", quote["time"])
            except Exception as err:
                print("Exception ", err.args[0])
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
                               "change, volume, openInterest, impliedVolatility, inTheMoney, "
                               "option_expire_id, current_value) "
                               "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
                    print(err.args[0])

    def get_all_symbols(self) -> pd.DataFrame:
        """ all symbols for """
        query = "SELECT symbol FROM stocks"
        cursor = self.connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        np_rows = np.array(rows)
        df_symbols = np_rows[:, 0]  # symbols
        df = pd.DataFrame(data=df_symbols, columns=["symbol"])
        return df

    def get_all_options_expirations(self, symbol: str) -> pd.DataFrame:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM option_expire where symbol = ?", [symbol])
        rows = cursor.fetchall()
        np_rows = np.array(rows)
        df_expirations = np_rows[:, [0, 2]]  # expire date
        df_column_values = ["option_expire_id", "expire_date"]
        df = pd.DataFrame(data=df_expirations, columns=df_column_values)
        return df

    def get_all_options_for_expiration(self, option_expire_id, put_call=None):
        cursor = self.connection.cursor()
        if type is None:
            cursor.execute("SELECT * FROM put_call_options where option_expire_id = ?",
                           [option_expire_id])
        else:
            cursor.execute("SELECT * FROM put_call_options where option_expire_id = ? AND put_call = ?",
                           [option_expire_id, put_call])

        rows = cursor.fetchall()
        return rows

    def get_date_times_for_expiration_df(self, symbol, option_expire_id) -> pd.DataFrame:
        cursor = self.connection.cursor()

        cursor.execute("SELECT * FROM stock_price where symbol = ? AND option_expire_id = ?",
                       [symbol, option_expire_id])
        rows = cursor.fetchall()
        np_rows = np.array(rows)
        df_data = np_rows[:, [0, 2, 3]]  # stock_price_id, DateTime and stock price
        df_column_values = ["stock_price_id", "datetime", "price"]
        df = pd.DataFrame(data=df_data, columns=df_column_values)
        return df

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
        return df

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

    def _create_verify_stock_data(self):
        for stock in self.stock_data:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM stocks WHERE symbol = ?", [stock["symbol"]])
            rows = cursor.fetchall()
            if not rows:  # empty - record does not exist
                cursor.execute("INSERT INTO stocks(symbol, name) VALUES (?,?)",
                               [stock["symbol"], stock["name"]])
                self.connection.commit()
        return
