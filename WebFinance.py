#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 11:15:04 2017

@author: fredoleary
"""

# from yahoo_finance import Share

import urllib.request
import json
import logging
from datetime import datetime
import demjson
from dateutil import parser
from tzlocal import get_localzone
import pytz
import pickle


class FinanceWeb():
    """ Class for retreiving stock quotes and news """
    # Note that alphavantage resstricts API access for free versions to 5 calls/min, max 500 calls per day
    save_to_file = False
    read_from_file = False

    def get_quotes_for_stock_intraday(self, stock_ticker):
        """ Return intraday prices from alphavantage. """
        quotes = []
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
            logging.error("Cannot get quotes for: " + stock_ticker)
        return quotes

    def get_quotes_for_stock_series(self, stock_ticker):
        """ Return day series prices from alphavantage. """
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
                logging.error("Cannot get quotes for: " + stock_ticker)
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
                    news.append({"title": item["t"], "description": item["sp"], \
                                 "source": item["s"], "time": dt_gmt})

        return news

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
            req.add_header("user-agent",
                           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36")
            response = urllib.request.urlopen(req)
            #            response = urllib.request.urlopen(url)
            result = response.read()
            str_result = result.decode("utf-8")

            news_items = json.loads(str_result)
            for news_item in news_items["stories"]:
                dt_gmt = parser.parse(news_item["publishTime"])
                dt_gmt = dt_gmt.replace(tzinfo=None)
                news.append({"title": news_item["title"], "description": news_item["description"], \
                             "source": news_item["source"]["name"], "time": dt_gmt})

            return news
        except urllib.error.HTTPError as err:
            print("Exception ", err.code)
            logging.error(err.code)
            return news
