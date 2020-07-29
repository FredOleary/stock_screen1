import numpy as np
import math
import datetime
import yfinance as yf

from WebFinance import FinanceWeb
from CompanyWatch import CompanyWatch
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


def screen_stocks():
    web = FinanceWeb()
    companies = CompanyWatch()
    update = True
    if update is False:
        web.read_from_file = True
        web.save_to_file = False
    else:
        web.read_from_file = False
        web.save_to_file = True

    for company in companies.get_companies():
        quotes = web.get_quotes_for_stock_series_yahoo(company["symbol"])
        quotes = filter_dates(FIRST_DATE, quotes)
        if len(quotes) > 0:
            quote_map = map(lambda x: x['close'], quotes)
            quote_list = list(quote_map)
            time_series = list(map(lambda x: x['date'], quotes))
            mean, volatility_percent = get_variance_and_mean(quote_list)
            print("volatility for ", company["name"], " (%) = ", math.trunc(volatility_percent))

            chart = Charts()
            chart.create_chart(2, 2, company["name"])
            chart.plot_data_time_series(0, 0, time_series, quote_list, color=(0, 0, 1), label="Raw data")

            adjust_to_mean = list(map(lambda x: x - mean, quote_list))
            chart.plot_data_time_series(0, 1, time_series, adjust_to_mean, color=(0, 0, 1), label="Normalized data")
            max_tab, min_tab = Processing.peak_detect(adjust_to_mean, x_axis=None,
                                                      lookahead=int(len(adjust_to_mean) / 10))

            if len(max_tab) > 0:
                max_date, max_value = get_scatter_array(max_tab, time_series)
                chart.plot_min_max(0, 1, max_date, max_value, "ro", label="Max Peaks")
            if len(min_tab) > 0:
                min_date, min_value = get_scatter_array(min_tab, time_series)
                chart.plot_min_max(0, 1, min_date, min_value, "go", label="Min Peaks")


def dummy():
    mar = yf.Ticker("MAR")
    hist = mar.history(period="ytd")
    # print(hist.values[10][0])
    value = hist.Close[0]
    date = hist.Close.axes[0].date[0]
    dt = datetime.datetime.combine(date, datetime.datetime.min.time())
    for i in range(len( hist.Close)):
        print(hist.Close[i])
        print(datetime.datetime.combine(hist.Close.axes[0].date[i], datetime.datetime.min.time()))
        print("foo")
    pass

if __name__ == '__main__':
    # dummy()
    screen_stocks()
    input("press enter")
