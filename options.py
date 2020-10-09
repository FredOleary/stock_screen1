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
            options_db.add_option_quote(options[0])
            # quote_map = map(lambda x: x['close'], options)
            # quote_list = list(quote_map)
            # time_series = list(map(lambda x: x['date'], options))
            # mean, volatility_percent = get_variance_and_mean(quote_list)
            # print("volatility for ", company["name"], " (%) = ", math.trunc(volatility_percent))
            #
            # chart = Charts()
            # chart.create_chart(2, 2, company["name"])
            # chart.plot_data_time_series(0, 0, time_series, quote_list, color=(0, 0, 1), label="Raw data")
            #
            # adjust_to_mean = list(map(lambda x: x - mean, quote_list))
            # chart.plot_data_time_series(0, 1, time_series, adjust_to_mean, color=(0, 0, 1), label="Normalized data")
            # max_tab, min_tab = Processing.peak_detect(adjust_to_mean, x_axis=None,
            #                                           lookahead=int(len(adjust_to_mean) / 10))
            #
            # if len(max_tab) > 0:
            #     max_date, max_value = get_scatter_array(max_tab, time_series)
            #     chart.plot_min_max(0, 1, max_date, max_value, "ro", label="Max Peaks")
            # if len(min_tab) > 0:
            #     min_date, min_value = get_scatter_array(min_tab, time_series)
            #     chart.plot_min_max(0, 1, min_date, min_value, "go", label="Min Peaks")
            #


if __name__ == '__main__':
    # dummy()
    process_options()
    input("press enter")
