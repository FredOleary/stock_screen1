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
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
# noinspection SpellCheckingInspection
import numpy as np
import datetime
# noinspection SpellCheckingInspection
import matplotlib.cm as cm
import matplotlib.widgets as widgets
import pandas as pd
from DbFinance import FinanceDB
import pytz
from pytz import timezone
import matplotlib.lines as mlines

import Utilities as util

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

class ChartOptions:
    def __init__(self):
        self.line_min_readings_for_strike = 5  # Minimum no of readings for a strike for line to be drawn
        self.max_no_strike_lines_in_line_chart = 10  # Approx maximum no of strike lines
        self.show_all_strikes = True
        self.on_off_button = None
        self.stock_price = None
        self.x_dates = None
        self.y_strikes = None
        self.z_price = None
        self.option_type = "extrinsic"

    def get_option_value(self, option_row, put_call, option_type) -> float:
        result = math.nan
        extrinsic_value = option_row["bid"]
        if extrinsic_value is not None:
            if put_call == "CALL":
                # Calculate extrinsic value for call
                if option_row['bid'] == 0 and option_row['ask' == 0]:
                    # Looks like some kind of hiccup...
                    result = math.nan
                else:
                    if option_row["current_value"] > option_row["strike"] and option_type == "extrinsic":
                        intrinsic_value = option_row["current_value"] - option_row["strike"]
                        result = extrinsic_value - intrinsic_value
                    else:
                        result = extrinsic_value
            else:
                pass
        return result

    def get_option_implied_volatility(self, option_row ) -> float:
        result = math.nan
        implied_volatility = option_row["impliedVolatility"]
        if implied_volatility is not None:
            if option_row['bid'] != 0 or option_row['ask'] != 0:
                # Seems to get garbage when both put/ask are 0
                result = implied_volatility
        return result


    def get_option_ask(self, option_row) -> float:
        ask_value = math.nan
        ask_value = option_row["ask"]
        if ask_value is not None:
            if option_row['bid'] == 0 and option_row['ask' == 0]:
                # Looks like some kind of hiccup...
                ask_value = math.nan
        return ask_value

    def prepare_options(self, options_db: FinanceDB, symbol: str, options_for_expiration_key: int, put_call: str,
                        start_date: datetime.datetime = None, end_date: datetime.datetime = None,
                        option_type: str = 'extrinsic') -> bool:
        """
        X Coordinate is Time data,
        Y Coordinate is the array of strike prices
        Z Coordinate is the corresponding option price at each time/strike
        """

        def create_index_map(series):
            index_map = {}
            idx = 0
            for element in series:
                if element not in index_map.keys():
                    index_map[element] = idx
                    idx += 1
            return index_map

        self.option_type = option_type
        df_dates_and_stock_price = options_db.get_date_times_for_expiration_df(
            symbol, options_for_expiration_key, start_date, end_date)
        if df_dates_and_stock_price is not None:
            self.x_dates = df_dates_and_stock_price["datetime"].to_numpy()
            stock_price_ids = df_dates_and_stock_price["stock_price_id"].to_numpy()
            self.stock_price = df_dates_and_stock_price["price"].to_numpy()
            df_strikes = options_db.get_unique_strikes_for_expiration(options_for_expiration_key, put_call)

            self.y_strikes = df_strikes["strike"].to_numpy()
            options_for_expiration = options_db.get_all_options_for_expiration(options_for_expiration_key,
                                                                               put_call=put_call)
            self.z_price = np.full((self.x_dates.size, self.y_strikes.size), math.nan, dtype=float)
            stock_price_id_map = create_index_map(stock_price_ids)
            self.y_strike_map = create_index_map(self.y_strikes)

            for index, row in options_for_expiration.iterrows():
                if row["stock_price_id"] in stock_price_id_map:
                    value = self.get_option_value(row, put_call, option_type)
                    self.z_price[stock_price_id_map[row["stock_price_id"]]][
                        self.y_strike_map[row["strike"]]] = value
            return True
        else:
            return False

    # noinspection SpellCheckingInspection
    def surface_chart_option(self, fig: Figure, symbol: str, put_call: str, expiration_date: datetime.datetime) -> None:

        indicies = np.arange(len(self.x_dates))

        x, y = np.meshgrid(indicies, self.y_strikes)
        z = self.z_price.transpose()

        ax = fig.add_subplot(111, projection='3d')
        cmap = plt.get_cmap("coolwarm")
        ax.plot_surface(x, y, z, linewidth=0, facecolors=cmap(z), shade=True, alpha=0.5)

        mappable = cm.ScalarMappable(cmap=cmap)
        mappable.set_array(z)
        min_value = np.amin(z, where=~np.isnan(z), initial=500)
        max_value = np.amax(z, where=~np.isnan(z), initial=-1)
        mappable.set_clim(math.floor(min_value), math.ceil(max_value))
        fig.colorbar(mappable, shrink=0.9, aspect=5)

        self.add_x_axis_and_title_2(fig, ax, self.x_dates, expiration_date, put_call, symbol, True)

    def line_chart_option(self, fig: Figure, symbol: str, put_call: str, expiration_date: datetime.datetime) -> None:
        indicies = np.arange(len(self.x_dates))
        strike_lines = []
        strike_dictionary = dict()

        ax = fig.add_subplot(111, picker=True)

        # count number of strikes that have prices
        non_zero_strike_count = 0
        for i in range(len(self.y_strikes)):
            column = self.z_price[:, i]
            non_zeros = column[~np.isnan(column)]
            if len(non_zeros) > 0:
                non_zero_strike_count += 1

        decimation_factor = 1
        if non_zero_strike_count >= self.line_min_readings_for_strike:
            decimation_factor = int(math.ceil(non_zero_strike_count / self.max_no_strike_lines_in_line_chart))

        for i in range(len(self.y_strikes)):
            column = self.z_price[:, i]
            non_zeros = column[~np.isnan(column)]
            if len(non_zeros) >= self.line_min_readings_for_strike:
                if i % decimation_factor == 0 or self.y_strikes[i] % 10 == 0:
                    strike_line, = ax.plot(indicies, self.z_price[:, i], label="{0}".format(self.y_strikes[i]), picker=True)
                    strike_lines.append(strike_line)

        legend = ax.legend(loc='upper left')
        legend.get_frame().set_alpha(0.4)

        for legend_line, orig_line in zip(legend.get_lines(), strike_lines):
            legend_line.set_picker(5)  # 5 pts tolerance
            strike_dictionary[legend_line] = orig_line

        self.add_x_axis_and_title_2(fig, ax, self.x_dates, expiration_date, put_call, symbol, False)

        def on_pick(event):
            # on the pick event, find the orig line corresponding to the
            # legend proxy line, and toggle the visibility
            legend_line = event.artist
            if isinstance(legend_line, mlines.Line2D):
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

        def toggle_strikes(event):
            if self.show_all_strikes:
                self.show_all_strikes = False
                self.on_off_button.label.set_text("Show All Strikes")
                for legend_key, strike_value in strike_dictionary.items():
                    legend_key.set_alpha(0.2)
                    strike_value.set_visible(False)

            else:
                self.show_all_strikes = True
                self.on_off_button.label.set_text("Hide All Strikes")
                for legend_key, strike_value in strike_dictionary.items():
                    legend_key.set_alpha(1.0)
                    strike_value.set_visible(True)
            fig.canvas.draw()

        fig.canvas.mpl_connect('pick_event', on_pick)

        ax_toggle = fig.add_axes([0.01, 0.9, 0.15, 0.075])
        self.on_off_button = widgets.Button(ax_toggle, "Hide All Strikes")
        self.on_off_button.on_clicked(toggle_strikes)

    def create_strike_profit_chart(self, options_db: FinanceDB, fig: Figure, symbol: str, options_for_expiration_key: int,
                                   strike: float, expiration_date: datetime.datetime, put_call: str,
                                   start_date: datetime.datetime = None, end_date: datetime.datetime = None,
                                   option_type: str = 'extrinsic') -> bool:

        def create_index_map(series):
            index_map = {}
            idx = 0
            for element in series:
                if element not in index_map.keys():
                    index_map[element] = idx
                    idx += 1
            return index_map

        self.option_type = option_type
        df_dates_and_stock_price = options_db.get_date_times_for_expiration_df(
            symbol, options_for_expiration_key, start_date, end_date)
        if df_dates_and_stock_price is not None:
            # Check if there is a position for this option
            open_date, option_price_open, close_date, option_price_close, position_strike_price = \
                options_db.search_positions(options_for_expiration_key, strike)
            x_dates = df_dates_and_stock_price["datetime"].to_numpy()
            stock_price_ids = df_dates_and_stock_price["stock_price_id"].to_numpy()
            self.stock_price = df_dates_and_stock_price["price"].to_numpy()
            strikes_for_expiration = options_db.get_strikes_for_expiration(options_for_expiration_key,
                                                                           strike,
                                                                           put_call=put_call)
            y_strikes_bid = np.empty(x_dates.size)
            y_strikes_extrinsic = np.empty(x_dates.size)
            if open_date is not None:
                y_strikes_profit = np.empty(x_dates.size)
                y_strikes_profit.fill(math.nan)

            y_strikes_bid.fill(math.nan)
            y_strikes_extrinsic.fill(math.nan)
            stock_price_id_map = create_index_map(stock_price_ids)

            for index, row in strikes_for_expiration.iterrows():
                if row["stock_price_id"] in stock_price_id_map:
                    # Bid value
                    value = self.get_option_value(row, put_call, 'bid')
                    y_strikes_bid[stock_price_id_map[row["stock_price_id"]]] = value
                    # extrinsic value
                    value = self.get_option_value(row, put_call, 'extrinsic')
                    y_strikes_extrinsic[stock_price_id_map[row["stock_price_id"]]] = value
                    # calculate profit if we have a position
                    # (Note... only implemented for selling calls)
                    if open_date is not None:
                        date = pd.to_datetime(x_dates[stock_price_id_map[row["stock_price_id"]]])
                        if date > open_date:
                            ask_value = self.get_option_ask(row)
                            y_strikes_profit[stock_price_id_map[row["stock_price_id"]]] = \
                                option_price_open - ask_value

            indicies = np.arange(len(x_dates))

            ax = fig.add_subplot(111)
            ax.plot(indicies, y_strikes_bid, label="{0} (bid)".format(strike))
            ax.plot(indicies, y_strikes_extrinsic, label="{0} (extrinsic)".format(strike))
            if open_date is not None:
                ax.plot(indicies, y_strikes_profit, label="{0} (profit)".format(strike))

            legend = ax.legend(loc='upper left')
            legend.get_frame().set_alpha(0.4)

            self.add_x_axis_and_title_2(fig, ax, x_dates, expiration_date, put_call, symbol, False)

            ax2 = ax.twinx()
            ax2.set_ylabel("Stock price", color="red")
            ax2.plot(indicies, self.stock_price, color="red")

            return True
        else:
            return False

    def create_strike_metrics_chart(self, options_db: FinanceDB, fig: Figure, symbol: str, options_for_expiration_key: int,
                                   strike: float, expiration_date: datetime.datetime, put_call: str,
                                   start_date: datetime.datetime = None, end_date: datetime.datetime = None) -> bool:

        def create_index_map(series):
            index_map = {}
            idx = 0
            for element in series:
                if element not in index_map.keys():
                    index_map[element] = idx
                    idx += 1
            return index_map

        # def normalize_series(series):
        #     no_nans = np.asarray(series[~np.isnan(series)])
        #     norm = np.linalg.norm(no_nans)
        #     return no_nans / norm

        df_dates_and_stock_price = options_db.get_date_times_for_expiration_df(
            symbol, options_for_expiration_key, start_date, end_date)
        if df_dates_and_stock_price is not None:
            x_dates = df_dates_and_stock_price["datetime"].to_numpy()
            stock_price_ids = df_dates_and_stock_price["stock_price_id"].to_numpy()
            self.stock_price = df_dates_and_stock_price["price"].to_numpy()
            strikes_for_expiration = options_db.get_strikes_for_expiration(options_for_expiration_key,
                                                                           strike,
                                                                           put_call=put_call)
            y_strikes_bid = np.empty(x_dates.size)
            y_strikes_extrinsic = np.empty(x_dates.size)
            y_strikes_IV = np.empty(x_dates.size)

            y_strikes_bid.fill(math.nan)
            y_strikes_extrinsic.fill(math.nan)
            y_strikes_IV.fill(math.nan)
            stock_price_id_map = create_index_map(stock_price_ids)

            for index, row in strikes_for_expiration.iterrows():
                if row["stock_price_id"] in stock_price_id_map:
                    # Bid value
                    value = self.get_option_value(row, put_call, 'bid')
                    y_strikes_bid[stock_price_id_map[row["stock_price_id"]]] = value
                    # extrinsic value
                    value = self.get_option_value(row, put_call, 'extrinsic')
                    y_strikes_extrinsic[stock_price_id_map[row["stock_price_id"]]] = value
                    y_strikes_IV[stock_price_id_map[row["stock_price_id"]]] = self.get_option_implied_volatility(row)

            indicies = np.arange(len(x_dates))

            ax = fig.add_subplot(111)
            ax.plot(indicies, util.normalize_series(y_strikes_bid), label="{0} (bid)".format(strike))
            ax.plot(indicies, util.normalize_series(y_strikes_extrinsic), label="{0} (extrinsic)".format(strike))
            ax.plot(indicies, util.normalize_series(self.stock_price), label="{0} (stock price)".format(strike))
            ax.plot(indicies, util.normalize_series(y_strikes_IV), label="{0} (Implied Volatility)".format(strike))

            legend = ax.legend(loc='upper left')
            legend.get_frame().set_alpha(0.4)

            self.add_x_axis_and_title_2(fig, ax, x_dates, expiration_date, put_call, symbol, False)

            return True
        else:
            return False


    def add_x_axis_and_title(self, ax, x_dates, expiration_date, put_call, symbol, has_zlabel):
        def format_date(x_in, pos=None):
            date_time_format = '%y-%m-%d'
            if num_days < 4:
                date_time_format = '%y-%m-%d:%H:%M'

            index = np.clip(int(x_in + 0.5), 0, len(x_dates) - 1)
            date_time = pd.to_datetime(x_dates[index])
            date_time_with_tz = date_time.replace(tzinfo=pytz.UTC)
            date_time_with_tz = date_time_with_tz.astimezone(timezone('US/Pacific'))
            return date_time_with_tz.strftime(date_time_format)

        num_days = ((x_dates[len(x_dates) - 1] - x_dates[0]).astype('timedelta64[D]')).astype(int)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))

        ax.set_xlabel('Date/Time (PST)')

        if has_zlabel:
            ax.set_zlabel('Extrinsic value' if self.option_type == 'extrinsic' else 'Bid value')
            ax.set_ylabel('Strike Price')
        else:
            ax.set_ylabel('Extrinsic value' if self.option_type == 'extrinsic' else 'Bid value')

        days_to_expire = expiration_date - datetime.datetime.now()
        delta_days = days_to_expire.days
        if delta_days > 0:
            days_to_expiration = "{0} days to expiration".format(delta_days)
        else:
            days_to_expiration = "Expired"

        current_price = "Current Price: N/A"
        if self.stock_price is not None and len(self.stock_price) > 0:
            current_price = "Current Price: {0}".format(self.stock_price[len(self.stock_price) - 1])
        plt.title("{0} chain for {1}, expires {2}. ({3}), {4}".
                  format(put_call, symbol, expiration_date.strftime("%Y-%m-%d"),
                         days_to_expiration, current_price))

    def add_x_axis_and_title_2(self, fig, ax, x_dates, expiration_date, put_call, symbol, has_zlabel):
        def format_date(x_in, pos=None):
            date_time_format = '%y-%m-%d'
            if num_days < 4:
                date_time_format = '%y-%m-%d:%H:%M'

            index = np.clip(int(x_in + 0.5), 0, len(x_dates) - 1)
            date_time = pd.to_datetime(x_dates[index])
            date_time_with_tz = date_time.replace(tzinfo=pytz.UTC)
            date_time_with_tz = date_time_with_tz.astimezone(timezone('US/Pacific'))
            return date_time_with_tz.strftime(date_time_format)

        num_days = ((x_dates[len(x_dates) - 1] - x_dates[0]).astype('timedelta64[D]')).astype(int)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))

        ax.set_xlabel('Date/Time (PST)')

        if has_zlabel:
            ax.set_zlabel('Extrinsic value' if self.option_type == 'extrinsic' else 'Bid value')
            ax.set_ylabel('Strike Price')
        else:
            ax.set_ylabel('Extrinsic value' if self.option_type == 'extrinsic' else 'Bid value')

        days_to_expire = expiration_date - datetime.datetime.now()
        delta_days = days_to_expire.days
        if delta_days > 0:
            days_to_expiration = "{0} days to expiration".format(delta_days)
        else:
            days_to_expiration = "Expired"

        current_price = "Current Price: N/A"
        if self.stock_price is not None and len(self.stock_price) > 0:
            current_price = "Current Price: {0}".format(self.stock_price[len(self.stock_price) - 1])
        fig.suptitle("{0} chain for {1}, expires {2}. ({3}), {4}".
                  format(put_call, symbol, expiration_date.strftime("%Y-%m-%d"),
                         days_to_expiration, current_price))
