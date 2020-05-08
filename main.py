import numpy as np
import math
import datetime

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
    web.read_from_file = True
    web.save_to_file = False
    for company in companies.get_companies():
        quotes = web.get_quotes_for_stock_series(company["symbol"])
        quotes = filter_dates(FIRST_DATE, quotes)
        if len(quotes) > 0:
            quote_map = map(lambda x: x['close'], quotes)
            quote_list = list(quote_map)
            time_series = list(map(lambda x: x['date'], quotes))
            mean, volatility_percent = get_variance_and_mean(quote_list)
            print("volatility for ", company["name"], " (%) = ", math.trunc(volatility_percent))

            max_tab, min_tab = Processing.peak_detect(quote_list, x_axis=None, lookahead=int(len(quote_list) / 10))

            chart = Charts()
            chart.create_chart(2, 2)
            chart.plot_data_time_series(0, 0, time_series, quote_list, color=(0, 0, 1), label="Raw data")
            if len(max_tab) > 0:
                max_date, max_value = get_scatter_array(max_tab, time_series)
                chart.plot_min_max(0, 0, max_date, max_value, "ro", label="Max Peaks")
            if len(min_tab) > 0:
                min_date, min_value = get_scatter_array(min_tab, time_series)
                chart.plot_min_max(0, 0, min_date, min_value, "go", label="Min Peaks")


if __name__ == '__main__':
    dict_a = [{'name': 'python', 'points': 10}, {'name': 'java', 'points': 8}]
    foo = map(lambda x: x['name'], dict_a)
    screen_stocks()
    input("press enter")
