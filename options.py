import numpy as np
import logging
import logging.handlers
import sys
import time

from WebFinance import FinanceWeb
from DbFinance import FinanceDB
from OptionsWatch import OptionsWatch

UPDATE_RATE = 900  # 15 minutes/update


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


# noinspection SpellCheckingInspection
def create_logger():
    # noinspection SpellCheckingInspection
    log_format = "%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s"
    date_fmt = "%m-%d %H:%M"

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(filename="options.log", level=logging.INFO, filemode="w",
                        format=log_format, datefmt=date_fmt)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_fmt))

    logger = logging.getLogger("options")
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)

    return logger


def process_options():
    logger = create_logger()
    web = FinanceWeb(logger)
    logger.info("Application started")
    companies = OptionsWatch()
    options_db = FinanceDB(companies.options_list, logger)
    options_db.initialize()

    repeat_get_quotes = True
    while repeat_get_quotes:
        for company in companies.get_companies():
            options = web.get_options_for_stock_series_yahoo(company["symbol"])
            if len(options) > 0:
                options_db.add_option_quote(options)

        if len(sys.argv) > 1:
            if sys.argv[1] == "repeat":
                logger.info("Sleeping for {delay} minutes".format(delay=UPDATE_RATE / 60))
                time.sleep(UPDATE_RATE)
            else:
                repeat_get_quotes = False
        else:
            repeat_get_quotes = False


if __name__ == '__main__':
    logging.info("Application started")
    process_options()
    input("press enter")
