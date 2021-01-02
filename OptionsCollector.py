import logging
import logging.handlers
import sys
import time

# from WebFinance import FinanceWeb
from APITradier import APITradier
from DbFinance import FinanceDB
from OptionsWatch import OptionsWatch
from OptionsConfiguration import OptionsConfiguration
from datetime import timedelta
import Utilities

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
    web = APITradier(logger)
    logger.info("Application started")
    companies = OptionsWatch()
    options_db = FinanceDB(companies.options_list, logger)
    options_db.initialize()
    configuration = OptionsConfiguration()
    # foo = configuration.get_configuration()
    # foo['collector_update_rate_in_seconds']
    update_rate = (configuration.get_configuration())["collector_update_rate_in_seconds"]
    look_a_heads = (configuration.get_configuration())["collector_look_ahead_expirations"]
    repeat_get_quotes = True
    while repeat_get_quotes:
        for company in companies.get_companies():
            options = web.get_options_for_symbol(company["symbol"], look_a_heads=look_a_heads)
            if len(options) > 0:
                for option in options:
                    logger.info("{0}(Before filter). Expires {1}. {2} Calls, {3} Puts".format(
                          option["ticker"],
                          option['expire_date'].strftime("%Y-%m-%d"),
                          len(option["options_chain"]["calls"]),
                          len(option["options_chain"]["puts"])))
                    Utilities.filter_by_date(option, 10)
                    Utilities.filter_by_at_the_money(option, 30, 50)
                    Utilities.decimate_options(option, 50)

                    logger.info("{0}(After filter). Expires {1}. {2} Calls, {3} Puts".format(
                          option["ticker"],
                          option['expire_date'].strftime("%Y-%m-%d"),
                          len(option["options_chain"]["calls"]),
                          len(option["options_chain"]["puts"])))

                options_db.add_option_quote(options)

        if len(sys.argv) > 1:
            if sys.argv[1] == "repeat":
                logger.info("Sleeping for {delay} minutes".format(delay=update_rate / 60))
                time.sleep(update_rate)
            else:
                repeat_get_quotes = False
        else:
            repeat_get_quotes = False



if __name__ == '__main__':
    logging.info("Application started")
    process_options()
    input("press enter")
