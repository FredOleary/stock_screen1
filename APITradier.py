import requests
import Utilities
import datetime
import pandas as pd
from APIOptions import APIOptions
import math

class APITradier(APIOptions):
    def __init__(self, logger=None):
        self.logger = logger
        self.authorization = 'Bearer FH98drEqHDafbIJDkGW71Ati3hRY'
        self.base_url = 'https://sandbox.tradier.com/v1/markets/'
        self.greeks = 'true'
        self.utilizationPct = 0

    def get_stock_price_for_symbol(self, symbol: str) -> {}:
        if self.logger is not None:
            self.logger.info("Get stock price for {0}".format( symbol))
        quote_dict = self.__get_quote(symbol)
        if bool(quote_dict):
            return {'ticker': symbol, 'value': quote_dict['quotes']['quote']['last']}
        else:
            return {}

    def __get_quote(self, symbol: str) -> dict:
        url = self.base_url + 'quotes'
        response = requests.get(url,
                                params={'symbols': symbol, 'greeks': 'false'},
                                headers={'Authorization': self.authorization,
                                         'Accept': 'application/json'})
        if response.status_code == 200:
            json_response = response.json()
            return json_response
        else:
            if self.logger is not None:
                self.logger.error(response.status_code, response.reason)
            return {}

    def __get_expirations(self, symbol: str) -> dict:
        url = self.base_url + 'options/expirations'
        response = requests.get(url,
                                params={'symbol': symbol, 'includeAllRoots': 'false', 'strikes':'false'},
                                headers={'Authorization': self.authorization,
                                         'Accept': 'application/json'})
        if response.status_code == 200:
            json_response = response.json()
            return json_response
        else:
            if self.logger is not None:
                self.logger.error(response.status_code, response.reason)
            return {}

    def __get_option_chain(self, symbol: str, expiration: str) -> dict:
        url = self.base_url + 'options/chains'
        response = requests.get(url,
                                params={'symbol': symbol, 'expiration': expiration, 'greeks':self.greeks},
                                headers={'Authorization': self.authorization,
                                         'Accept': 'application/json'})
        if response.status_code == 200:
            json_response = response.json()
            utility = float(response.headers['X-Ratelimit-Used'])/float(response.headers['X-Ratelimit-Allowed']) * 100
            self.utilizationPct = utility
            return json_response
        else:
            if self.logger is not None:
                self.logger.error(response.status_code, response.reason)
            return {}

    def get_options_for_symbol(self, symbol: str, put_call="BOTH", look_a_heads=2) -> list:
        option_chains = []
        if self.logger is not None:
            self.logger.info("Get option prices for {0}, put_call: {1}, look_a_heads: {2}".format(
                symbol, put_call, look_a_heads))

        quote_dict = self.__get_quote(symbol)
        if bool(quote_dict):
            expirations_dict = self.__get_expirations(symbol)
            if bool(expirations_dict):
                for expiration in expirations_dict['expirations']['date']:
                    is_third_friday, date_time = Utilities.is_third_friday(expiration)
                    if is_third_friday and look_a_heads > 0:
                        option_chain = self.__get_option_chain(symbol, expiration)
                        if bool(option_chain):
                            opt_chain = self.__quote_header(symbol, expiration, quote_dict)
                            if put_call == "BOTH" or put_call == "CALL":
                                df = self.__filter_options( option_chain, "CALL", opt_chain['current_value'])
                                opt_chain['options_chain']["calls"] = df
                            if put_call == "BOTH" or put_call == "PUT":
                                df = self.__filter_options( option_chain, "PUT", opt_chain['current_value'])
                                opt_chain['options_chain']["puts"] = df
                            option_chains.append(opt_chain)
                        else:
                            if self.logger is not None:
                                self.logger.warning(
                                    "No option chain for {0} at expiration: {1}".format(symbol, expiration))
                        look_a_heads -= 1
        return option_chains

    def get_options_for_symbol_and_expiration(self, symbol: str, expiration: str, put_call="BOTH") -> {}:
        opt_chain = {}
        if self.logger is not None:
            self.logger.info("Get option prices for {0}, put_call: {1}, expiration: {2}".format(
                symbol, put_call, expiration))

        quote_dict = self.__get_quote(symbol)
        if bool(quote_dict):
            option_chain = self.__get_option_chain(symbol, expiration)
            if bool(option_chain):
                opt_chain = self.__quote_header( symbol, expiration, quote_dict)
                if put_call == "BOTH" or put_call == "CALL":
                    df = self.__filter_options( option_chain, "CALL", opt_chain['current_value'])
                    opt_chain['options_chain']["calls"] = df
                if put_call == "BOTH" or put_call == "PUT":
                    df = self.__filter_options( option_chain, "PUT", opt_chain['current_value'])
                    opt_chain['options_chain']["puts"] = df
            else:
                if self.logger is not None:
                    self.logger.warning(
                        "No option chain for {0} at expiration: {1}".format(symbol, expiration))
        return opt_chain

    def __quote_header(self, symbol: str, expiration: str, quote_dict: dict) ->dict:
        current_time = datetime.datetime.utcfromtimestamp( quote_dict['quotes']['quote']['trade_date']/1000)
        header = {'ticker': symbol, 'current_value': quote_dict['quotes']['quote']['last'],
                  'current_time': current_time,
                  'expire_date': datetime.datetime.strptime(expiration, '%Y-%m-%d'),
                  'options_chain': {'calls':{}, 'puts':{}}}
        return header

    def __filter_options( self, option_chain, put_call, current_value ) -> pd.DataFrame:
        dict = {'contractsSymbol': [], 'lastTradeDate': [], 'strike': [], 'lastPrice': [],
                'bid': [], 'ask': [], 'change': [], 'volume': [], 'openInterest': [],
                'impliedVolatility': [], 'inTheMoney': []}
        #TDODO Fix case where option_chain['options] = None
        for option in option_chain['options']['option']:
            if option['option_type'].lower() == put_call.lower():
                if option['trade_date'] > 0:
                    dict['contractsSymbol'].append(option['symbol'])
                    last_trade_date = datetime.datetime.utcfromtimestamp(option['trade_date']/1000)
                    dict['lastTradeDate'].append(last_trade_date)
                    dict['strike'].append(option['strike'])
                    dict['lastPrice'].append(option['last'])
                    dict['bid'].append(option['bid'])
                    dict['ask'].append(option['ask'])
                    if option['change'] is None:
                        dict['change'].append(0.0)
                    else:
                        dict['change'].append(option['change'])
                    dict['volume'].append(option['volume'])
                    dict['openInterest'].append(option['open_interest'])
                    if 'greeks' in option:
                        dict['impliedVolatility'].append(option['greeks']['mid_iv'])
                    else:
                        dict['impliedVolatility'].append(None)
                    in_the_money = True
                    if put_call == 'CALL':
                        if option['strike'] > current_value:
                            in_the_money = False
                    else:
                        if option['strike'] < current_value:
                            in_the_money = False
                    dict['inTheMoney'].append(in_the_money)

        df = pd.DataFrame.from_dict(dict)
        return df
