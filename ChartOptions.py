"""
=============================================
Generate polygons to fill under 3D line graph
=============================================

Demonstrate how to create polygons which fill the space under a line
graph. In this example polygons are semi-transparent, creating a sort
of 'jagged stained glass' effect.
"""

from mpl_toolkits.mplot3d import Axes3D
from matplotlib.collections import PolyCollection
from matplotlib.collections import LineCollection
from matplotlib.collections import PatchCollection
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import numpy as np
from datetime import timedelta
import datetime
import matplotlib.dates as mdates

from DbFinance import FinanceDB


def chart_options():
    options_db = FinanceDB()
    options_db.initialize()
    symbols = options_db.get_all_symbols()
    for symbol in symbols:
        options_expirations = options_db.get_all_options_expirations(symbol[0])
        for options_expiration in options_expirations:
            if options_expiration[2] > datetime.datetime.now():
                x_dates, y_strikes, z_price = prepare_options( options_db, symbol[0], options_expiration[0], put_call="CALL")
                chart_option(x_dates, y_strikes, z_price)
                print("foo")
    pass

def prepare_options( options_db: FinanceDB, symbol: str, options_for_expiration_key: int, put_call: str ):
    """
    X Coordinate is Time data,
    Y Coordiante is the array of strike prices
    Z Coordinate is the corresponding option price at each time/strike

    # x = np.asarray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    # y = np.asarray([100, 110, 120, 130, 140, 150, 160, 180])
    # X, Y = np.meshgrid(x, y)
    #
    # Z = np.random.rand(8, 10)
    # Z = Z / 10
    The X dimension will contain the datetimes for the option (converted to numbers)

    """
    data_frame = options_db.get_date_times_for_expiration_df(symbol, options_for_expiration_key)
    x_dates = data_frame["datetime"].to_numpy()
    stock_price_ids = data_frame["stock_price_id"].to_numpy()

    strikes = options_db.get_unique_strikes_for_expiration(options_for_expiration_key, put_call)

    y_strikes = np.array(strikes)[:,0]  # FRAGILE
    options_for_expiration = options_db.get_all_options_for_expiration(options_for_expiration_key, put_call=put_call)

     # Solve the vertices for each strike. (Note there may not always be a solution for a strike/time pair
    # Note that this solution is z*2 (not good). Also indices are fragile

    def solve_for_y(y_strike, stock_price_id, options_for_expiration) -> float:
        result = 0.0
        for option in options_for_expiration:
            if stock_price_id == option[1] and y_strike == option[4]:
                return option[6] # the bid
        return result

    z_price = np.zeros((x_dates.size, y_strikes.size), dtype=float)
    for i, stock_price_id in enumerate(stock_price_ids):
        for j, y_strike in enumerate(y_strikes):
            z = solve_for_y(y_strike, stock_price_id, options_for_expiration ) # x[0] is the stock_price_id
            z_price[i][j] = z

    return x_dates, y_strikes, z_price

def chart_option(x_dates, y_strikes, z_price):
    x_dates = mdates.date2num(x_dates)

    X, Y = np.meshgrid(x_dates, y_strikes)
    Z = z_price.transpose()

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')
    mycmap = plt.get_cmap('gist_earth')

    # Plot a 3D surface
    surf1 = ax.plot_surface(X, Y, Z, cmap=mycmap)
    date_format = mdates.DateFormatter('%D')
    ax.xaxis.set_major_formatter(date_format)

    ax.set_xlabel('Date/Time')
    ax.set_ylabel('Strike Price')
    ax.set_zlabel('Option Price')
    ax.set_zlim3d(0, 50)
    plt.show()
    plt.show()

if __name__ == '__main__':
    # dummy()
    chart_options()
    input("press enter")
