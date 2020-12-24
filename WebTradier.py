import requests
import Utilities
import datetime
import pandas as pd


class WebTradier:
    def __init__(self, logger=None):
        self.logger = logger
        self.authorization = 'Bearer FH98drEqHDafbIJDkGW71Ati3hRY'
        self.base_url = 'https://sandbox.tradier.com/v1/markets/'
        self.greeks = 'true'

    def get_quote(self, symbol: str) -> dict:
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

    def get_expirations(self, symbol: str) -> dict:
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

    def get_option_chain(self, symbol: str, expiration: str) -> dict:
        url = self.base_url + 'options/chains'
        response = requests.get(url,
                                params={'symbol': symbol, 'expiration': expiration, 'greeks':self.greeks},
                                headers={'Authorization': self.authorization,
                                         'Accept': 'application/json'})
        if response.status_code == 200:
            json_response = response.json()
            return json_response
        else:
            if self.logger is not None:
                self.logger.error(response.status_code, response.reason)
            return {}

    def get_options_for_symbol(self, symbol: str, strike_filter="ATM", put_call="BOTH", look_a_heads=2) -> list:
        option_chains = []
        if self.logger is not None:
            self.logger.info("Get option prices for {symbol}".format(symbol=symbol))

        quote_dict = self.get_quote(symbol)
        if bool(quote_dict):
            expirations_dict = self.get_expirations(symbol)
            if bool(expirations_dict):
                for expiration in expirations_dict['expirations']['date']:
                    is_third_friday, date_time = Utilities.is_third_friday(expiration)
                    if is_third_friday and look_a_heads > 0:
                        option_chain = self.get_option_chain( symbol, expiration)
                        if bool(option_chain):
                            current_time = datetime.datetime.utcfromtimestamp(
                                quote_dict['quotes']['quote']['trade_date']/1000)
                            opt_chain = {'ticker': symbol,
                                         'current_value': quote_dict['quotes']['quote']['last'],
                                         'current_time': current_time,
                                         'expire_date': datetime.datetime.strptime(expiration, '%Y-%m-%d')}
                            if put_call == "BOTH" or put_call == "CALL":
                                self._filter_options( option_chain, "CALL", strike_filter )
                            if put_call == "BOTH" or put_call == "PUT":
                                self._filter_options( option_chain, "PUT", strike_filter )
                            option_chains.append(opt_chain)
                        else:
                            if self.logger is not None:
                                self.logger.warning(
                                    "No option chain for {0} at expiration: {1}".format(symbol, expiration))
        return option_chains

    def _filter_options( self, option_chain, put_call, strike_filter ) -> pd.DataFrame:
        dict = {'contractsSymbol': [], 'lastTradeDate': [], 'strike': [], 'lastPrice': [],
                'bid': [], 'ask': [], 'change': [], 'volume': [], 'openInterest': []}
        for option in option_chain['options']['option']:
            if option['option_type'].lower() == put_call.lower():
                dict['contractsSymbol'].append(option['symbol'])
                last_trade_date = datetime.datetime.utcfromtimestamp(option['trade_date']/1000)
                dict['lastTradeDate'].append(last_trade_date)
                dict['strike'].append(option['strike'])
                dict['lastPrice'].append(option['last'])
                dict['bid'].append(option['bid'])
                dict['ask'].append(option['ask'])
                dict['change'].append(option['change'])
                dict['volume'].append(option['volume'])
                dict['openInterest'].append(option['open_interest'])

        df = pd.DataFrame.from_dict(dict)
        return df
