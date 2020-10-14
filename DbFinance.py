#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 19:35:54 2017

@author: fredoleary
"""
import sqlite3


class FinanceDB():
    """ Storage for news/prices etc """

    def __init__(self, stock_data):
        self.connection = None
        self.db_name = "stock_options"
        self.stock_data = stock_data
        self.tables = [{"name": "stocks",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS stocks (
                                        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        symbol TEXT,
                                        name TEXT NOT NULL
                                    ); """},
                       {"name": "stock_price",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS stock_price (
                                        stock_price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        symbol TEXT,
                                        time DATETIME NOT NULL,
                                        price REAL NOT NULL,
                                        expire_date DATETIME NOT NULL,
                                        UNIQUE( symbol, time)
                                    ); """},
                       {"name": "put_call_options",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS put_call_options (
                            call_option_price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            stock_price_id INTEGER, 
                            put_call TEXT NOT NULL,
                            lastTradeDate DATETIME NOT NULL,
                            strike REAL NOT NULL,
                            lastPrice REAL,
                            bid REAL,
                            ask REAL,
                            change REAL NOT NULL,
                            volume REAL,
                            openInterest INTEGER,
                            impliedVolatility REAL NOT NULL,
                            inTheMoney TEXT NOT NULL,
                            UNIQUE( stock_price_id, put_call, strike),
                            CONSTRAINT fk_stock_price
                                FOREIGN KEY (stock_price_id)
                                REFERENCES stock_price(stock_price_id)

                      ); """},

                       ]

    def initialize(self):
        """ Initialize database connection and tables """
        self.connection = sqlite3.connect(self.db_name, \
                                          detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self._create_verify_tables()
        self._create_verify_stock_data()

    def close(self):
        """ Close db if necessary """
        if self.connection is not None:
            self.connection.close()

    def add_option_quote(self, quotes: object) -> int:
        if len(quotes) > 0:
            try:
                for quote in quotes:
                    rowid = -1
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT rowid, * FROM stock_price WHERE symbol = ? AND time = ?",
                                   [quote["ticker"], quote["current_time"]])
                    rows = cursor.fetchall()
                    if not rows:  # empty - record does not exist
                        cursor.execute("INSERT INTO stock_price(symbol, time, price, expire_date) VALUES (?,?,?,?)",
                                       (quote["ticker"],
                                        quote["current_time"],
                                        quote["current_value"],
                                        quote["expire_date"]))

                        rowid = cursor.lastrowid
                    else:
                        rowid = rows[0][0]  # Existing rowid
                    if rowid != -1:

                        self.insert_put_call(cursor, True, rowid, quote['options_chain']['calls'])
                        self.insert_put_call(cursor, False, rowid, quote['options_chain']['puts'])

                self.connection.commit()
                # print("value added for time: ", quote["time"])
            except Exception as err:
                print("Exception ", err.args[0])
                return 0
                # print("value already added for time: ", quote["time"])

    def insert_put_call(self, cursor: object, is_call: str, rowid: int, put_call_options_chain: object):
        for index, option in put_call_options_chain.iterrows():
            put_call = "PUT"
            if is_call: put_call = "CALL"
            try:
                cursor.execute("INSERT INTO put_call_options("
                               "stock_price_id, put_call, lastTradeDate, strike, lastPrice, bid, ask, "
                               "change, volume, openInterest, impliedVolatility, inTheMoney) "
                               "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
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
                                   ("FALSE", "TRUE")[option["inTheMoney"]]
                               ))
            except sqlite3.IntegrityError as err:
                if err.args[0] == 'UNIQUE constraint failed: put_call_options.stock_price_id, put_call_options.put_call, put_call_options.strike':
                    # This can happen if we attempt to insert the same data twice
                    pass
                else:
                    print(err.args[0])

    # def get_prices_before(self, symbol, time):
    #     """ get prices up to time """
    #     query = "SELECT * FROM prices WHERE symbol = ? AND time <= ? ORDER BY TIME DESC LIMIT 5"
    #     cursor = self.connection.cursor()
    #     cursor.execute(query, [symbol, time])
    #     rows = cursor.fetchall()
    #     return rows


    # def get_quotes(self, symbol):
    #     """ Fetch prices for symbol """
    #     cursor = self.connection.cursor()
    #     cursor.execute("SELECT * FROM prices WHERE symbol = ?", [symbol])
    #     return cursor.fetchall()

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
