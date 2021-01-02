import numpy as np
import pandas as pd
import math
import datetime

def normalize_series(series: np.ndarray) -> np.ndarray:
    norm = []
    series_no_nans = series[~pd.isnull(series)]
    min = np.min(series_no_nans)
    max = np.max(series_no_nans)
    try:
        norm = [(val-min)/(max-min) if val is not math.nan else math.nan for val in series]
    except:
        print("oh dear")
    return norm


# def is_third_friday(time_str: str) -> (bool, datetime.datetime):
#     d = datetime.datetime.strptime(time_str, '%Y-%m-%d')  # Eg "2020-10-08"
#
#     if d.weekday() == 4 and 15 <= d.day <= 21:
#         return True, d
#     return False, d


def is_third_friday(time_str: str, allow_yahoo_glitch=False) -> (bool, datetime):
    d = datetime.datetime.strptime(time_str, '%Y-%m-%d')  # Eg "2020-10-08"
    if(allow_yahoo_glitch):
        # Note - empirically we see that sometimes a thursday is returned, (rather than a Friday)
        # No idea why however options expirations are Friday...
        if d.weekday() == 3:
            d = d + datetime.timedelta(days=1)

    if d.weekday() == 4 and 15 <= d.day <= 21:
        return True, d
    return False, d

def filter_by_date(option: {}, time_delta_in_days: int) -> {}:
    option['options_chain']['calls'] = __filter_put_call_by_date(option['options_chain']['calls'], time_delta_in_days)
    option['options_chain']['puts'] = __filter_put_call_by_date(option['options_chain']['puts'], time_delta_in_days)
    return option


def __filter_put_call_by_date(df_option: pd.DataFrame, time_delta_in_days) -> pd.DataFrame:
    delete_rows = []
    for index, row in df_option.iterrows():
        lastTrade = row["lastTradeDate"].to_pydatetime()
        delta = datetime.datetime.now() - lastTrade
        if delta.days >= time_delta_in_days:
            delete_rows.append(index)
    df_out = df_option.drop(delete_rows)
    return df_out


def filter_by_at_the_money(option: {}, atm_percent: int, max_options) -> {}:
    stock_price = option["current_value"]
    low_value = stock_price - atm_percent * stock_price/100
    high_value = stock_price + atm_percent * stock_price/100

    option['options_chain']['calls'] = __filter_put_call_by_atm(option['options_chain']['calls'],
                                                                low_value, high_value, max_options)
    option['options_chain']['puts'] = __filter_put_call_by_atm(option['options_chain']['puts'],
                                                               low_value, high_value, max_options)
    return option


def __filter_put_call_by_atm(df_option: pd.DataFrame, low_value, high_value, max_options) -> pd.DataFrame:
    if len(df_option.index) <= max_options:
        return df_option
    delete_rows = []
    for index, row in df_option.iterrows():
        if row["strike"] <= low_value or row["strike"] >= high_value:
            delete_rows.append(index)
    df_out = df_option.drop(delete_rows)
    return df_out


def decimate_options(option: {}, max_puts_calls: int):
    option['options_chain']['calls'] = __decimate_option(option['options_chain']['calls'], max_puts_calls)
    option['options_chain']['puts'] = __decimate_option(option['options_chain']['puts'], max_puts_calls)
    return option


def __decimate_option(df_option: pd.DataFrame, max_puts_calls: int):
    if len(df_option.index) <= max_puts_calls:
        return df_option
    decimation = int(len(df_option.index)/max_puts_calls)
    if decimation <= 1:
        return df_option
    low_strike_value = df_option.iloc[0]["strike"]
    high_strike_value = df_option.iloc[len(df_option.index)-1]["strike"]
    decimate_factor = math.ceil((high_strike_value - low_strike_value)/max_puts_calls)
    delete_rows = []
    for index, row in df_option.iterrows():
        if row["strike"] % 10 != 0 and row["strike"] % 5 != 0 and row["strike"] % decimate_factor != 0:
            delete_rows.append(index)
    df_out = df_option.drop(delete_rows)
    return df_out

