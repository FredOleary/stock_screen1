import numpy as np

from WebFinance import FinanceWeb
from CompanyWatch import CompanyWatch
from charts import Charts


def get_variance_and_mean( quote_list):
    volatility = np.sqrt(np.var(quote_list))
    mean = np.mean(quote_list)
    return mean, volatility

def screen_stocks():
    web = FinanceWeb()
    companies = CompanyWatch()
    web.read_from_file = True
    web.save_to_file = False
    for company in companies.get_companies():
        quotes = web.get_quotes_for_stock_series(company["symbol"])
        quote_map = map(lambda x : x['close'], quotes)
        quote_list = list(quote_map)
        time_series = list(map(lambda x : x['date'], quotes))
        mean, volatility = get_variance_and_mean(quote_list)
        print("volatility for ", company["name"], " = ", volatility)
        chart = Charts()
        chart.create_chart(2, 2)
        chart.plot_data_time_series(0, 0, time_series, quote_list, color=(0, 0, 1), label="Raw data")


if __name__ == '__main__':
    dict_a = [{'name': 'python', 'points': 10}, {'name': 'java', 'points': 8}]
    foo = map(lambda x : x['name'], dict_a)
    screen_stocks()
    input("press enter")