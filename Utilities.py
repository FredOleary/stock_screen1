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

def is_third_friday(time_str: str) -> (bool, datetime.datetime):
    d = datetime.datetime.strptime(time_str, '%Y-%m-%d')  # Eg "2020-10-08"

    if d.weekday() == 4 and 15 <= d.day <= 21:
        return True, d
    return False, d

