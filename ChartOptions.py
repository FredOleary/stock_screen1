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
import matplotlib.ticker as ticker
# noinspection SpellCheckingInspection
import numpy as np
import datetime
# noinspection SpellCheckingInspection
import matplotlib.cm as cm
import pandas as pd
from DbFinance import FinanceDB


class ChartOptions:
    @staticmethod
    def prepare_options(options_db: FinanceDB, symbol: str, options_for_expiration_key: int, put_call: str,
                        start_date: datetime.datetime = None, end_date: datetime.datetime = None) -> \
            (np.ndarray, np.ndarray, np.ndarray):
        """
        X Coordinate is Time data,
        Y Coordinate is the array of strike prices
        Z Coordinate is the corresponding option price at each time/strike
        """

        def get_option_value(option_row) -> float:
            result = math.nan
            extrinsic_value = option_row["bid"]
            if extrinsic_value is not None:
                if put_call == "CALL":
                    # Calculate extrinsic value for call
                    if option_row['bid'] == 0 and option_row['ask' == 0]:
                        # Looks like some kind of hiccup...
                        result = math.nan
                    else:
                        if option_row["current_value"] > option_row["strike"]:
                            intrinsic_value = option_row["current_value"] - option_row["strike"]
                            result = extrinsic_value - intrinsic_value
                        else:
                            result = extrinsic_value
            else:
                pass
            return result

        def create_index_map(series):
            index_map = {}
            idx = 0
            for element in series:
                if element not in index_map.keys():
                    index_map[element] = idx
                    idx += 1
            return index_map

        df_dates_and_stock_price = options_db.get_date_times_for_expiration_df(
            symbol, options_for_expiration_key, start_date, end_date)
        if df_dates_and_stock_price is not None:
            x_dates = df_dates_and_stock_price["datetime"].to_numpy()
            stock_price_ids = df_dates_and_stock_price["stock_price_id"].to_numpy()

            df_strikes = options_db.get_unique_strikes_for_expiration(options_for_expiration_key, put_call)

            y_strikes = df_strikes["strike"].to_numpy()
            options_for_expiration = options_db.get_all_options_for_expiration(options_for_expiration_key,
                                                                               put_call=put_call)

            z_price = np.full((x_dates.size, y_strikes.size), math.nan, dtype=float)
            stock_price_id_map = create_index_map(stock_price_ids)
            y_strike_map = create_index_map(y_strikes)

            for index, row in options_for_expiration.iterrows():
                if row["stock_price_id"] in stock_price_id_map:
                    value = get_option_value(row)
                    z_price[stock_price_id_map[row["stock_price_id"]]][
                        y_strike_map[row["strike"]]] = value

            return x_dates, y_strikes, z_price
        else:
            return None, None, None

    # noinspection SpellCheckingInspection
    @staticmethod
    def surface_chart_option(symbol: str, put_call: str, expiration_date: datetime.datetime,
                             x_dates_in: np.ndarray, y_strikes: np.ndarray, z_price: np.ndarray) -> None:

        # noinspection PyUnusedLocal
        # def format_date(x_in, pos=None):
        #     index = np.clip(int(x_in + 0.5), 0, len(x_dates_in) - 1)
        #     return pd.to_datetime(x_dates_in[index]).strftime('%Y-%m-%d')

        # x_dates = mdates.date2num(x_dates_in)
        indicies = np.arange(len(x_dates_in))

        x, y = np.meshgrid(indicies, y_strikes)
        z = z_price.transpose()

        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111, projection='3d')
        cmap = plt.get_cmap("coolwarm")
        ax.plot_surface(x, y, z, linewidth=0, facecolors=cmap(z), shade=True, alpha=0.5)

        mappable = cm.ScalarMappable(cmap=cmap)
        mappable.set_array(z)
        min_value = np.amin(z, where=~np.isnan(z), initial=500)
        max_value = np.amax(z, where=~np.isnan(z), initial=-1)
        mappable.set_clim(math.floor(min_value), math.ceil(max_value))
        fig.colorbar(mappable, shrink=0.9, aspect=5)

        ChartOptions.add_x_axis_and_title(ax, x_dates_in, expiration_date, put_call, symbol, True)
        # ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        #
        # ax.set_xlabel('Date/Time')
        # ax.set_ylabel('Strike Price')
        # ax.set_zlabel('Option Price')
        #
        # days_to_expire = expiration_date - datetime.datetime.now()
        # delta_days = days_to_expire.days
        # if delta_days > 0:
        #     days_to_expiration = "{0} days to expiration".format(delta_days)
        # else:
        #     days_to_expiration = "Expired"
        #
        # plt.title("{0} chain for {1}, expires {2}. ({3})".
        #           format(put_call, symbol, expiration_date.strftime("%Y-%m-%d"), days_to_expiration))

    @staticmethod
    def line_chart_option(symbol: str, put_call: str, expiration_date: datetime.datetime,
                          x_dates_in: np.ndarray, y_strikes: np.ndarray, z_price: np.ndarray) -> None:
        # # noinspection PyUnusedLocal
        # def format_date(x_in, pos=None):
        #     index = np.clip(int(x_in + 0.5), 0, len(x_dates_in) - 1)
        #     return pd.to_datetime(x_dates_in[index]).strftime('%Y-%m-%d')

        indicies = np.arange(len(x_dates_in))
        fig = plt.figure(figsize=(10, 6))
        strike_lines = []
        strike_dictionary = dict()

        ax = fig.add_subplot(111)
        # count number of strikes that have prices
        non_zero_strike_count = 0
        for i in range(len(y_strikes)):
            column = z_price[:, i]
            non_zeros = column[~np.isnan(column)]
            if len(non_zeros) > 0:
                non_zero_strike_count +=1

        decimation_factor = 1
        if non_zero_strike_count > 0:
            # TODO - Make these constants variables....
            decimation_factor = int( math.ceil(non_zero_strike_count/10))

        for i in range(len(y_strikes)):
            column = z_price[:, i]
            non_zeros = column[~np.isnan(column)]
            if len(non_zeros) > 0:
                if i % decimation_factor == 0:
                    strike_line, = ax.plot(indicies, z_price[:, i], label="{0}".format(y_strikes[i]))
                    strike_lines.append(strike_line)

        legend = ax.legend(loc='upper left')
        legend.get_frame().set_alpha(0.4)

        for legend_line, orig_line in zip(legend.get_lines(), strike_lines):
            legend_line.set_picker(5)  # 5 pts tolerance
            strike_dictionary[legend_line] = orig_line

        ChartOptions.add_x_axis_and_title(ax, x_dates_in, expiration_date, put_call, symbol, False)

        def onpick(event):
            # on the pick event, find the orig line corresponding to the
            # legend proxy line, and toggle the visibility
            legend_line = event.artist
            orig_line = strike_dictionary[legend_line]
            vis = not orig_line.get_visible()
            orig_line.set_visible(vis)
            # Change the alpha on the line in the legend so we can see what lines
            # have been toggled
            if vis:
                legend_line.set_alpha(1.0)
            else:
                legend_line.set_alpha(0.2)
            fig.canvas.draw()

        fig.canvas.mpl_connect('pick_event', onpick)

        # plt.legend()
        # plt.plot(indicies, z_price[:,1], label="Strike 2")
        # plt.plot(indicies, z_price[:,2], label="Strike 3")
        # plt.plot(indicies, z_price[:,int(len(y_strikes)/2)], label="Strike xxx")

    @staticmethod
    def add_x_axis_and_title(ax, x_dates, expiration_date, put_call, symbol, has_zLabel):
        def format_date(x_in, pos=None):
            index = np.clip(int(x_in + 0.5), 0, len(x_dates) - 1)
            return pd.to_datetime(x_dates[index]).strftime('%Y-%m-%d')

        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))

        ax.set_xlabel('Date/Time')

        if has_zLabel:
            ax.set_zlabel('Extrinsic value')
            ax.set_ylabel('Strike Price')
        else:
            ax.set_ylabel('Extrinsic value')


        days_to_expire = expiration_date - datetime.datetime.now()
        delta_days = days_to_expire.days
        if delta_days > 0:
            days_to_expiration = "{0} days to expiration".format(delta_days)
        else:
            days_to_expiration = "Expired"

        plt.title("{0} chain for {1}, expires {2}. ({3})".
                  format(put_call, symbol, expiration_date.strftime("%Y-%m-%d"), days_to_expiration))
