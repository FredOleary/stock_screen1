import numpy as np
import math
import datetime
import yfinance as yf

from WebFinance import FinanceWeb
from DbFinance import FinanceDB
from OptionsWatch import OptionsWatch
from charts import Charts
from processing import Processing

# potential market bottom, March 23, 2020
FIRST_DATE = datetime.datetime(2020, 3, 23)


def get_variance_and_mean(quote_list):
    volatility = np.sqrt(np.var(quote_list))
    mean = np.mean(quote_list)
    return mean, volatility / mean * 100


def get_scatter_array(min_max: [], date_array: []) -> object:
    dates = []
    amplitudes = []
    for value in min_max:
        dates.append(date_array[value[0]])
        amplitudes.append(value[1])
    return dates, amplitudes


def filter_dates(first_date: object, data: []) -> []:
    return_dates = []
    for value in data:
        if value['date'] > first_date:
            return_dates.append(value)
    return return_dates


def process_options():
    web = FinanceWeb()
    companies = OptionsWatch()
    options_db = FinanceDB(companies.options_list)
    options_db.initialize()

    for company in companies.get_companies():
        options = web.get_options_for_stock_series_yahoo(company["symbol"])
        if len(options) > 0:
            options_db.add_option_quote(options)



if __name__ == '__main__':
    # dummy()
    process_options()
    input("press enter")
