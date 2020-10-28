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
import math
import matplotlib.pyplot as plt
# noinspection SpellCheckingInspection
# from matplotlib import colors as mcolors
import numpy as np
# from datetime import timedelta
import datetime
# noinspection SpellCheckingInspection
import matplotlib.dates as mdates
from matplotlib.colors import Normalize
import matplotlib.cm as cm
from DbFinance import FinanceDB
from ChartOptions import ChartOptions

def chart_options():
    options_db = FinanceDB()
    options_db.initialize()
    df_symbols = options_db.get_all_symbols()
    # for symbol in symbols:
    for i_row, symbol_row in df_symbols.iterrows():
        df_options_expirations = options_db.get_all_options_expirations(symbol_row["symbol"])
        for index, row in df_options_expirations.iterrows():
            if row["expire_date"] > datetime.datetime.now():
                chart = ChartOptions()

                x_dates, y_strikes, z_price = chart.prepare_options(options_db, symbol_row["symbol"],
                                                              row["option_expire_id"], put_call="CALL")
                chart.chart_option(symbol_row["symbol"], "Call", row["expire_date"], x_dates, y_strikes, z_price)

    plt.show()


# def prepare_options(options_db: FinanceDB, symbol: str, options_for_expiration_key: int, put_call: str):
#     """
#     X Coordinate is Time data,
#     Y Coordinate is the array of strike prices
#     Z Coordinate is the corresponding option price at each time/strike
#     """
#     def get_option_value(option_row) -> float:
#         result = math.nan
#         value = option_row["bid"]
#         # if value is None:
#         #     value = option_row["lastPrice"]
#         if value is not None:
#             if put_call == "CALL":
#                 # Calculate extrinsic value for call
#                 if option_row['bid'] == 0 and option_row['ask' == 0]:
#                     # Looks like some kind of hiccup...
#                     result = math.nan
#                 else:
#                     if option_row["current_value"] > option_row["strike"]:
#                         intrinsic_value = option_row["current_value"] - option_row["strike"]
#                         result = value - intrinsic_value
#                     else:
#                         result = value
#         return result
#
#     def create_index_map(series):
#         index_map = {}
#         index = 0
#         for element in series:
#             if not element in index_map.keys():
#                 index_map[element] = index
#                 index += 1
#         return index_map
#
#
#     df_dates_and_stock_price = options_db.get_date_times_for_expiration_df(symbol, options_for_expiration_key)
#     x_dates = df_dates_and_stock_price["datetime"].to_numpy()
#     stock_price_ids = df_dates_and_stock_price["stock_price_id"].to_numpy()
#
#     df_strikes = options_db.get_unique_strikes_for_expiration(options_for_expiration_key, put_call)
#
#     y_strikes = df_strikes["strike"].to_numpy()
#     options_for_expiration = options_db.get_all_options_for_expiration(options_for_expiration_key, put_call=put_call)
#
#     z_price = np.full((x_dates.size, y_strikes.size), math.nan, dtype=float)
#     stock_price_id_map = create_index_map(stock_price_ids)
#     y_strike_map = create_index_map(y_strikes)
#
#     for index, option_row in options_for_expiration.iterrows():
#         value = get_option_value( option_row)
#         z_price[stock_price_id_map[option_row["stock_price_id"]]][y_strike_map[option_row["strike"]]]= value
#
#     return x_dates, y_strikes, z_price


# noinspection SpellCheckingInspection
# def chart_option(symbol: str, put_call: str, expiration_date: datetime.datetime,
#                  x_dates: np.ndarray, y_strikes: np.ndarray, z_price: np.ndarray) -> None:
#
#     x_dates = mdates.date2num(x_dates)
#
#     x, y = np.meshgrid(x_dates, y_strikes)
#     z = z_price.transpose()
#
#     fig = plt.figure(figsize=(10, 6))
#     ax = fig.add_subplot(111, projection='3d')
#     # my_cmap = plt.get_cmap('gist_earth')
#     my_cmap = plt.get_cmap("gist_earth")
#     # Plot a 3D surface
#     #surf1 = ax.plot_surface(x, y, z, cmap=my_cmap)
#     #ax.plot_surface(x, y, z, cmap=None)
#     cmap = plt.get_cmap("coolwarm")
#     ax.plot_surface(x, y, z, linewidth=0, facecolors=cmap(z), shade=True, alpha=0.5)
#     # ax.plot_surface(x, y, z, cmap=cmap, shade=True, alpha=0.75)
#
#     mappable = cm.ScalarMappable(cmap=cmap)
#     mappable.set_array(z)
#     min = np.amin(z, where=~np.isnan(z),initial=500)
#     max = np.amax(z, where=~np.isnan(z),initial=-1)
#     mappable.set_clim(math.floor(min), math.ceil(max))
#     fig.colorbar(mappable, shrink=0.9, aspect=5)
#
#     date_format = mdates.DateFormatter('%D %H:%M')
#     ax.xaxis.set_major_formatter(date_format)
#
#     ax.set_xlabel('Date/Time')
#     ax.set_ylabel('Strike Price')
#     ax.set_zlabel('Option Price')
#     # ax.set_zlim3d(0, 50)
#
#     plt.title("{0} chain for {1}, expires {2}".format(put_call, symbol, expiration_date.strftime("%Y-%m-%d")))


if __name__ == '__main__':
    # dummy()
    chart_options()
    input("press enter")
