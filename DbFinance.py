#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 19:35:54 2017

@author: fredoleary
"""
import sqlite3
import hashlib
import logging

class FinanceDB():
    """ Storage for news/prices etc """
    def __init__(self, stock_data):
        self.connection = None
        self.db_name = "stock_options"
        self.stock_data = stock_data
        self.tables = [{"name":"stocks",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS stocks (
                                        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        symbol TEXT,
                                        name TEXT NOT NULL
                                    ); """},
                       {"name" :"stock_price",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS stock_price (
                                        stock_price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        symbol TEXT,
                                        time DATETIME NOT NULL,
                                        price REAL NOT NULL,
                                        expire_date DATETIME NOT NULL,
                                        UNIQUE( symbol, time)
                                    ); """},
                       {"name": "call_options",
                        "create_sql": """ CREATE TABLE IF NOT EXISTS call_options (
                            call_option_price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            stock_price_id INTEGER, 
                            lastTradeDate DATETIME NOT NULL,
                            strike REAL NOT NULL,
                            lastPrice REAL,
                            bid REAL,
                            ask REAL,
                            CONSTRAINT fk_stock_price
                                FOREIGN KEY (stock_price_id)
                                REFERENCES stock_price(stock_price_id)

                            UNIQUE( call_option_price_id, strike)
                     ); """},

                       ]
    def initialize(self):
        """ Initialize database connection and tables """
        self.connection = sqlite3.connect(self.db_name, \
                            detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self._create_verify_tables()
        self._create_verify_stock_data()

    def close(self):
        """ Close db if necessary """
        if self.connection is not None:
            self.connection.close()

    def get_stock_data(self):
        """ Stock_data accessor """
        return self.stock_data


    def add_option_quote(self, quote: object) -> int:
        if quote:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT rowid, * FROM stock_price WHERE symbol = ? AND time = ?", [quote["ticker"], quote["current_time"]])
                rows = cursor.fetchall()
                if not rows:  # empty - record does not exist
                    cursor.execute ("INSERT INTO stock_price(symbol, time, price, expire_date) VALUES (?,?,?,?)",
                                   (quote["ticker"],
                                    quote["current_time"],
                                    quote["current_value"],
                                    quote["expire_date"]))
                    self.connection.commit()
                    return cursor.lastrowid
                else:
                    return rows[0][0] # Existing rowid
                #print("value added for time: ", quote["time"])
            except Exception as err:
                print("Exception ", err.args[0])
                return 0
                #print("value already added for time: ", quote["time"])



    def get_prices_before(self, symbol, time):
        """ get prices up to time """
        query = "SELECT * FROM prices WHERE symbol = ? AND time <= ? ORDER BY TIME DESC LIMIT 5"
        cursor = self.connection.cursor()
        cursor.execute(query, [symbol, time])
        rows = cursor.fetchall()
        return rows

    def get_prices_after(self, symbol, time):
        """ get prices onwards from time """
        query = "SELECT * FROM prices WHERE symbol = ? AND time >= ? ORDER BY TIME ASC LIMIT 5"
        cursor = self.connection.cursor()
        cursor.execute(query, [symbol, time])
        rows = cursor.fetchall()
        return rows

    def get_quotes(self, symbol):
        """ Fetch prices for symbol """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM prices WHERE symbol = ?", [symbol])
        return cursor.fetchall()

    def _create_verify_tables(self):
        #Get a list of all tables
        cursor = self.connection.cursor()
        cmd = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor.execute(cmd)
        names = [row[0] for row in cursor.fetchall()]
        for table in self.tables:
            if not table['name'] in names:
                cursor.execute(table['create_sql'])
                #table doesn't exist, create it

    def _create_verify_stock_data(self):
        for stock in self.stock_data:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM stocks WHERE symbol = ?", [stock["symbol"]])
            rows = cursor.fetchall()
            if not rows: #empty - record does not exist
                cursor.execute("INSERT INTO stocks(symbol, name) VALUES (?,?)",
                               [stock["symbol"], stock["name"]])
                self.connection.commit()
        return
