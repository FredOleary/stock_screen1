#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 11:15:04 2017

@author: Fred OLeary
"""

# from yahoo_finance import Share

import json
import pickle
import urllib.request
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import Utilities
import pandas
import yfinance as yf
from APIOptions import APIOptions


# noinspection SpellCheckingInspection,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,
# PyMethodMayBeStatic,PyMethodMayBeStatic
# noinspection PyMethodMayBeStatic
class APIYahoo(APIOptions):
    """ Class for retrieving stock quotes and news """
    # Note that AlphaVantage restricts API access for free versions to 5 calls/min, max 500 calls per day
    save_to_file = False
    read_from_file = False

    def __init__(self, logger=None):
        self.logger = logger

    def get_stock_price_for_symbol(self, symbol: str) -> {}:
        if self.logger is not None:
            self.logger.info("Get stock price for {0}".format( symbol))
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d", interval="1m")
        current_value = history.Close[len(history.Close) - 1]
        return {'ticker': symbol, 'value': current_value}

    def get_options_for_symbol_and_expiration(self, symbol: str, expiration: str, put_call="BOTH") -> {}:
        if self.logger is not None:
            self.logger.info("Get option prices for {0}, put_call: {1}, expiration: {2}".format(
                symbol, put_call, expiration))
        options = {}
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period="1d", interval="1m")
            current_value = history.Close[len(history.Close) - 1]
            current_pd_time = history.axes[0][len(history.axes[0]) - 1]
            current_time = current_pd_time.to_pydatetime()
            current_time = current_time.astimezone(timezone.utc)
            current_time = current_time.replace(tzinfo=None)  # Want UTC with NO timezone info
            expire_dates = ticker.options
            ex_required = datetime.strptime(expiration, '%Y-%m-%d')
            for expire_date in expire_dates:
                # Note expiration dates seem to be malformed; correct via "is_third_friday"
                is_third, ex_date = Utilities.is_third_friday(expire_date, allow_yahoo_glitch=True)
                if ex_date == ex_required:
                    options_obj = ticker.option_chain(expire_date)
                    # self.__filter_garbage_options(options_obj)
                    filtered_options = self.__filter_options(options_obj)
                    options = {'ticker': symbol,
                               'current_value': current_value,
                               'current_time': current_time,
                               'expire_date':  ex_required,
                               'options_chain': filtered_options}
                    break
        except Exception as err:
            if self.logger is not None:
                self.logger.error(err.args[0])

        return options

    def get_options_for_symbol(self, stock_ticker, put_call="BOTH", look_a_heads=2) -> list:
        if self.logger is not None:
            self.logger.info("Get option prices for {symbol}".format(symbol=stock_ticker))
        options = []
        try:
            ticker = yf.Ticker(stock_ticker)
            history = ticker.history(period="1d", interval="1m")
            current_value = history.Close[len(history.Close) - 1]
            current_pd_time = history.axes[0][len(history.axes[0]) - 1]
            current_time = current_pd_time.to_pydatetime()
            current_time = current_time.astimezone(timezone.utc)
            current_time = current_time.replace(tzinfo=None)  # Want UTC with NO timezone info
            expire_dates = ticker.options
            for expire_date in expire_dates:
                (is_third_friday, date_time) = Utilities.is_third_friday(expire_date, allow_yahoo_glitch=True)
                if is_third_friday and look_a_heads > 0:
                    options_obj = ticker.option_chain(expire_date)
                    # self.__filter_garbage_options(options_obj)
                    filtered_options = self.__filter_options(options_obj)
                    return_options = {'ticker': stock_ticker,
                                      'current_value': current_value,
                                      'current_time': current_time,
                                      'expire_date': date_time,
                                      'options_chain': filtered_options}
                    options.append(return_options)
                    look_a_heads -= 1
        except Exception as err:
            if self.logger is not None:
                self.logger.error(err.args[0])

        return options

    # def __filter_garbage_options(self, options_obj) -> None:
    #     """
    #     The Yahoo api seems to yield stale strikes , esp for Tesla. E.g. with lastTradeDates > 1 month
    #     Additionally these strikes have garbage values. E.g. a call strike of $810 with a current price of $600 has
    #     a legit bid of $11. However a 'stale' strike of $815 has a garage bid of $1322.
    #     This method 'purges' options with stale lastTradeDates
    #     """
    #
    #     def _filter_garbage(options_df: pandas.DataFrame):
    #         now = datetime.now()
    #         delete_rows = []
    #         for index, row in options_df.iterrows():
    #             last_trade_date = pandas.to_datetime(row["lastTradeDate"])
    #             days_diff = (now.date() - last_trade_date.date()).days
    #             if days_diff > 10:
    #                 delete_rows.append(index)
    #
    #         if delete_rows:
    #             options_df.drop(delete_rows, inplace=True)
    #
    #     _filter_garbage(options_obj.calls)
    #     _filter_garbage(options_obj.puts)

    def __filter_options(self, options_obj: any) -> {}:
        calls = options_obj.calls
        puts = options_obj.puts
        return {'calls': calls, 'puts': puts}
