"""
=============================================
Generate polygons to fill under 3D line graph
=============================================

Demonstrate how to create polygons which fill the space under a line
graph. In this example polygons are semi-transparent, creating a sort
of 'jagged stained glass' effect.
"""

# from mpl_toolkits.mplot3d import Axes3D
# from matplotlib.collections import PolyCollection
# from matplotlib.collections import LineCollection
# from matplotlib.collections import PatchCollection
import matplotlib.pyplot as plt
# noinspection SpellCheckingInspection
# from matplotlib import colors as mcolors
import numpy as np
# from datetime import timedelta
import datetime
# noinspection SpellCheckingInspection
import matplotlib.dates as mdates

from DbFinance import FinanceDB


def chart_options():
    options_db = FinanceDB()
    options_db.initialize()
    df_symbols = options_db.get_all_symbols()
    # for symbol in symbols:
    for i_row, symbol_row in df_symbols.iterrows():
        df_options_expirations = options_db.get_all_options_expirations(symbol_row["symbol"])
        for index, row in df_options_expirations.iterrows():
            if row["expire_date"] > datetime.datetime.now():
                x_dates, y_strikes, z_price = prepare_options(options_db, symbol_row["symbol"],
                                                              row["option_expire_id"], put_call="CALL")
                chart_option(symbol_row["symbol"], "Call", row["expire_date"], x_dates, y_strikes, z_price)

    plt.show()


def prepare_options(options_db: FinanceDB, symbol: str, options_for_expiration_key: int, put_call: str):
    """
    X Coordinate is Time data,
    Y Coordinate is the array of strike prices
    Z Coordinate is the corresponding option price at each time/strike
    """
    df_dates_and_stock_price = options_db.get_date_times_for_expiration_df(symbol, options_for_expiration_key)
    x_dates = df_dates_and_stock_price["datetime"].to_numpy()
    stock_price_ids = df_dates_and_stock_price["stock_price_id"].to_numpy()

    df_strikes = options_db.get_unique_strikes_for_expiration(options_for_expiration_key, put_call)

    y_strikes = df_strikes["strike"].to_numpy()
    options_for_expiration = options_db.get_all_options_for_expiration(options_for_expiration_key, put_call=put_call)

    # Solve the vertices for each strike. (Note there may not always be a solution for a strike/time pair
    # Note that this solution is z*2 (not good). Also indices are fragile

    def solve_for_y(y_strike_nest, stock_price_id_nest, options_for_expiration_nest) -> float:
        result = 0.0
        for option in options_for_expiration_nest:
            if stock_price_id_nest == option[1] and y_strike_nest == option[4]:
                return option[6]  # the bid
        return result

    z_price = np.zeros((x_dates.size, y_strikes.size), dtype=float)
    for i, stock_price_id in enumerate(stock_price_ids):
        for j, y_strike in enumerate(y_strikes):
            z = solve_for_y(y_strike, stock_price_id, options_for_expiration)  # x[0] is the stock_price_id
            z_price[i][j] = z

    return x_dates, y_strikes, z_price


# noinspection SpellCheckingInspection
def chart_option(symbol: str, put_call: str, expiration_date: datetime.datetime,
                 x_dates: np.ndarray, y_strikes: np.ndarray, z_price: np.ndarray) -> None:

    x_dates = mdates.date2num(x_dates)

    x, y = np.meshgrid(x_dates, y_strikes)
    z = z_price.transpose()

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')
    # my_cmap = plt.get_cmap('gist_earth')

    # Plot a 3D surface
    # surf1 = ax.plot_surface(X, Y, Z, cmap=my_cmap)
    ax.plot_surface(x, y, z)
    date_format = mdates.DateFormatter('%D')
    ax.xaxis.set_major_formatter(date_format)

    ax.set_xlabel('Date/Time')
    ax.set_ylabel('Strike Price')
    ax.set_zlabel('Option Price')
    ax.set_zlim3d(0, 50)

    plt.title("{0} chain for {1}, expires {2}".format(put_call, symbol, expiration_date.strftime("%Y-%m-%d")))


if __name__ == '__main__':
    # dummy()
    chart_options()
    input("press enter")
