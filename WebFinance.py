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

import demjson
import pandas
import pytz
import yfinance as yf
from dateutil import parser
from tzlocal import get_localzone


# noinspection SpellCheckingInspection,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,
# PyMethodMayBeStatic,PyMethodMayBeStatic
# noinspection PyMethodMayBeStatic
class FinanceWeb:
    """ Class for retrieving stock quotes and news """
    # Note that AlphaVantage restricts API access for free versions to 5 calls/min, max 500 calls per day
    save_to_file = False
    read_from_file = False

    def __init__(self, log=None):
        self.logger = log

    # noinspection SpellCheckingInspection
    def get_quotes_for_stock_intra_day(self, stock_ticker):
        """ Return intra-day prices from AlphaVantage. """
        quotes = []
        # noinspection SpellCheckingInspection
        url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY" + \
              "&symbol=" + stock_ticker + "&interval=1min&outputsize=full" + \
              "&apikey=M8KGCPCGZQSJJO3V"
        response = urllib.request.urlopen(url)
        result = response.read()
        str_result = result.decode("utf-8")
        python_obj = json.loads(str_result)
        if "Time Series (1min)" in python_obj:
            for key, value in python_obj["Time Series (1min)"].items():
                # The date/times are EST, convert to GMT and remove Tz info.
                # (sqlite doesn't like tz info)
                dt_est = parser.parse(key)  # Date time with no TZ info
                dt_est = pytz.timezone('US/Eastern').localize(dt_est)  # Date time with EST info
                dt_gmt = dt_est.astimezone(pytz.utc)  # Date time with as GMT
                dt_gmt = dt_gmt.replace(tzinfo=None)  # GM time with tz info stripped
                quotes.append({"time": dt_gmt, "price": value["4. close"]})
        else:
            if self.logger is not None:
                self.logger.error("Cannot get quotes for: " + stock_ticker)
        return quotes

    # noinspection SpellCheckingInspection
    def get_quotes_for_stock_series(self, stock_ticker):
        """ Return day series prices from AlphaVantage. """
        quotes = []
        if self.read_from_file is False:
            url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY" + \
                  "&symbol=" + stock_ticker + "&outputsize=compact" + \
                  "&apikey=M8KGCPCGZQSJJO3V"
            response = urllib.request.urlopen(url)
            result = response.read()
            str_result = result.decode("utf-8")
            python_obj = json.loads(str_result)
            if "Time Series (Daily)" in python_obj:
                for key, value in python_obj["Time Series (Daily)"].items():
                    date = parser.parse(key)
                    quotes.append({"date": date,
                                   "open": float(value["1. open"]),
                                   "high": float(value["2. high"]),
                                   "low": float(value["3. low"]),
                                   "close": float(value["4. close"])})

                    if self.save_to_file is True:
                        self.save_in_file(stock_ticker, quotes)

            else:
                if self.logger is not None:
                    self.logger.error("Cannot get quotes for: " + stock_ticker)
        else:
            quotes = self.read_file(stock_ticker)
        return quotes

    def get_quotes_for_stock_series_yahoo(self, stock_ticker):
        """ Return day series prices from yahoo finance. """
        quotes = []
        if self.read_from_file is False:
            ticker = yf.Ticker(stock_ticker)
            hist = ticker.history(period="ytd")

            if "Close" in hist:
                for i in range(len(hist.Close)):
                    close_date = datetime.combine(hist.Close.axes[0].date[i], datetime.min.time())

                    quotes.append({"date": close_date,
                                   "open": hist.Open[i],
                                   "high": hist.High[i],
                                   "low": hist.Low[i],
                                   "close": hist.Close[i]})

                    if self.save_to_file is True:
                        self.save_in_file(stock_ticker, quotes)

            else:
                if self.logger is not None:
                    self.logger.error("Cannot get quotes for: " + stock_ticker)
        else:
            quotes = self.read_file(stock_ticker)
        return quotes

    def read_file(self, stock_ticker):
        with open(stock_ticker + "_file.pkl", 'rb') as f:
            quotes = pickle.load(f)
        return quotes

    def save_in_file(self, stock_ticker, quotes):
        f = open(stock_ticker + "_file.pkl", "wb")
        pickle.dump(quotes, f)
        f.close()

    @classmethod
    def get_news_for_stock(cls, stock_ticker):
        """ Return the list of news items for stock_ticker using Googles Finance """
        news = []
        url = "https://www.google.com/finance/company_news?q=" + stock_ticker + "&output=json"
        response = urllib.request.urlopen(url)
        result = response.read()
        str_result = result.decode("utf-8")

        news_items = demjson.decode(str_result)
        for news_item in news_items["clusters"]:
            if news_item.get('a'):
                item_array = news_item["a"]
                for item in item_array:
                    dt_local = datetime.fromtimestamp(int(item["tt"]))
                    # this will be in local time, convert to GMT
                    dt_local = dt_local.astimezone(get_localzone())  # Adds local tz info
                    dt_gmt = dt_local.astimezone(pytz.utc)  # Converts to gmt
                    dt_gmt = dt_gmt.replace(tzinfo=None)  # finally removes the tz info
                    # print( "date/time: ", dt_gmt)
                    news.append({"title": item["t"], "description": item["sp"],
                                 "source": item["s"], "time": dt_gmt})

        return news

    # noinspection PyUnresolvedReferences
    @classmethod
    def get_news_for_stock_cf(cls, stock_ticker):
        """ Return the list of news items for stock_ticker using City falcon """
        news = []
        url = "https://api.cityfalcon.com/v0.2/stories.json?identifier_type=tickers" + \
              "&identifiers=" + stock_ticker + "&categories=mp%2Cop&order_by=top" + \
              "&time_filter=d1&languages=en&all_languages=false" + \
              "&access_token=8e02bc06e7d6c129f55d45253eb2240b275e66de8d8c959ad7b60bea9bad22f2"
        try:
            req = urllib.request.Request(url)
            # noinspection SpellCheckingInspection
            req.add_header("user-agent",
                           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36")
            response = urllib.request.urlopen(req)
            #            response = urllib.request.urlopen(url)
            result = response.read()
            str_result = result.decode("utf-8")

            news_items = json.loads(str_result)
            for news_item in news_items["stories"]:
                dt_gmt = parser.parse(news_item["publishTime"])
                dt_gmt = dt_gmt.replace(tzinfo=None)
                news.append({"title": news_item["title"], "description": news_item["description"],
                             "source": news_item["source"]["name"], "time": dt_gmt})

            return news
        except urllib.error.HTTPError as err:
            if self.logger is not None:
                self.logger.error(err.code)
            return news

    def get_options_for_stock_series_yahoo(self, stock_ticker,
                                           strike_filter="ATM",
                                           put_call="BOTH",
                                           look_a_heads=2) -> list:
        """ Return options chain prices from yahoo finance.
        This method returns monthly options chains for option strike prices 'around' the money
        """
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
            for expire_date in ticker.options:
                (is_third_friday, date, date_time) = self.is_third_friday(expire_date)
                if is_third_friday and look_a_heads > 0:
                    options_obj = ticker.option_chain(expire_date)
                    self.filter_garbage_options(options_obj)
                    if strike_filter == "ATM":
                        filtered_options = self._filter_to_at_the_money(options_obj)
                    elif strike_filter == "OTM":
                        filtered_options = self._filter_to_out_of_the_money(options_obj, put_call)
                    else:
                        filtered_options = {}
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

    def filter_garbage_options(self, options_obj) -> None:
        """
        The Yahoo api seems to yield stale strikes , esp for Tesla. E.g. with lastTradeDates > 1 month
        Additionally these strikes have garbage values. E.g. a call strike of $810 with a current price of $600 has
        a legit bid of $11. However a 'stale' strike of $815 has a garage bid of $1322.
        This method 'purges' options with stale lastTradeDates
        """

        def _filter_garbage(options_df: pandas.DataFrame):
            now = datetime.now()
            delete_rows = []
            for index, row in options_df.iterrows():
                last_trade_date = pandas.to_datetime(row["lastTradeDate"])
                days_diff = (now.date() - last_trade_date.date()).days
                if days_diff > 10:
                    delete_rows.append(index)

            if delete_rows:
                options_df.drop(delete_rows, inplace=True)

        _filter_garbage(options_obj.calls)
        _filter_garbage(options_obj.puts)

    def is_third_friday(self, time_str: str) -> (bool, str, datetime):
        d = datetime.strptime(time_str, '%Y-%m-%d')  # Eg "2020-10-08"
        # Note - day is actually d-1 (no idea why)
        d = d + timedelta(days=1)

        if d.weekday() == 4 and 15 <= d.day <= 21:
            # # Also check that expiration date isn't more than 60 days out
            # days_diff = d - datetime.now()
            # if days_diff.days < 60:
            return True, time_str, d
        return False, time_str, d

    def _filter_to_at_the_money(self, options_obj: any) -> {}:
        calls = self._filter_to_the_money_puts_and_calls(options_obj.calls, True)
        puts = self._filter_to_the_money_puts_and_calls(options_obj.puts, False)
        return {'calls': calls, 'puts': puts}

    def _filter_to_the_money_puts_and_calls(self, df: pandas.DataFrame, is_call: bool) -> pandas.DataFrame:
        start_index = 0
        end_index = len(df)
        current_index = 0
        found_transition = False
        transition = True
        if is_call:
            transition = False
        for index, row in df.iterrows():
            if found_transition:
                if current_index - 10 > 0:
                    start_index = current_index - 10
                if current_index + 10 < end_index:
                    end_index = current_index + 10
                return df.iloc[start_index:end_index]

            else:
                if row["inTheMoney"] == transition:
                    found_transition = True
                else:
                    current_index += 1
        return df

    def _filter_to_out_of_the_money(self, options_obj: any, put_call: str) -> {}:
        result = {}
        if put_call == "BOTH" or put_call == "CALL":
            result["calls"] = self._filter_out_the_money_puts_and_calls(options_obj.calls, True)
        if put_call == "BOTH" or put_call == "PUT":
            result["puts"] = self._filter_out_the_money_puts_and_calls(options_obj.puts, False)
        return result

    def _filter_out_the_money_puts_and_calls(self, df: pandas.DataFrame, is_call: bool) -> pandas.DataFrame:
        current_index = 0
        found_transition = False
        transition = True
        if is_call:
            transition = False
        for index, row in df.iterrows():
            if found_transition:
                if is_call:
                    return df.iloc[current_index:len(df)]
                else:
                    return df.iloc[0:current_index]
            else:
                if row["inTheMoney"] == transition:
                    found_transition = True
                else:
                    current_index += 1
        return df
