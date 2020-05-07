import numpy as np

from WebFinance import FinanceWeb
from CompanyWatch import CompanyWatch

def get_variance_and_mean( quote_list):
    variance = np.var(quote_list)
    mean = np.mean(quote_list)
    return mean, variance

def screen_stocks():
    web = FinanceWeb()
    companies = CompanyWatch()
    for company in companies.get_companies():
        quotes = web.get_quotes_for_stock_series(company["symbol"])
        quote_list = map(lambda x : float(x['close']), quotes)
        mean, variance = get_variance_and_mean(list(quote_list))
        print("Variance for ", company["name"], " (%) = ", variance/mean * 100)


if __name__ == '__main__':
    dict_a = [{'name': 'python', 'points': 10}, {'name': 'java', 'points': 8}]
    foo = map(lambda x : x['name'], dict_a)
    screen_stocks()
