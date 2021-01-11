import logging
import logging.handlers
import sys
import time
import argparse

from DbFinance import FinanceDB
from OptionsWatch import OptionsWatch
from OptionsConfiguration import OptionsConfiguration
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
    database = "stock_options"
    configuration = OptionsConfiguration()
    update_rate = (configuration.get_configuration())["collector_update_rate_in_seconds"]
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-r", "--repeat", help="Continuous collection - Set by update rate", action="store_true")
        parser.add_argument('-u', '--update', action='store', type=int, help= "Update rate in seconds")
        parser.add_argument('-d', '--db', action='store', type=str, help= "Database to use")
        parser.add_argument('-e', '--expire', action='store', type=str, help= "expiration (YYYY-MM-DD)")

        args = parser.parse_args()
        repeat = args.repeat
        if args.update is not None:
            update_rate = args.update
        if args.db is not None:
            database = args.db
        expiration = args.expire

    except Exception as err:
        print(err)
        sys.exit(2)

    print("Repeat: {0}, database: {1}, update rate: {2}".format(repeat, database, update_rate))

    web = Utilities.get_options_API(logger)
    logger.info("Application started")
    companies = OptionsWatch()
    options_db = FinanceDB(companies.options_list, logger, database)
    options_db.initialize()

    look_a_heads = (configuration.get_configuration())["collector_look_ahead_expirations"]
    repeat_get_quotes = True
    while repeat_get_quotes:
        for company in companies.get_companies():
            if expiration is not None:
                options = [web.get_options_for_symbol_and_expiration(company["symbol"], expiration)]

            else:
                options = web.get_options_for_symbol(company["symbol"], look_a_heads=look_a_heads)
            if len(options) > 0:
                for option in options:
                    logger.info("{0}(Before filter). Expires {1}. {2} Calls, {3} Puts".format(
                          option["ticker"],
                          option['expire_date'].strftime("%Y-%m-%d"),
                          len(option["options_chain"]["calls"]),
                          len(option["options_chain"]["puts"])))
                    if len(option["options_chain"]["puts"]) > 0 and len(option["options_chain"]["calls"]) > 0:
                        Utilities.filter_by_date(option, 10)
                        Utilities.filter_by_at_the_money(option, 30, 50)
                        Utilities.decimate_options(option, 50)

                        logger.info("{0}(After filter). Expires {1}. {2} Calls, {3} Puts".format(
                              option["ticker"],
                              option['expire_date'].strftime("%Y-%m-%d"),
                              len(option["options_chain"]["calls"]),
                              len(option["options_chain"]["puts"])))

                options_db.add_option_quote(options)

        if repeat:
            logger.info("Sleeping for {delay} seconds".format(delay=update_rate))
            time.sleep(update_rate)
        else:
            repeat_get_quotes = False



if __name__ == '__main__':
    logging.info("Application started")
    process_options()
    input("press enter")
