import numpy as np
import pandas as pd
import math

def normalize_series(series: np.ndarray) -> np.ndarray:
    norm = []
    series_no_nans = series[~pd.isnull(series)]
    min = np.min(series_no_nans)
    max = np.max(series_no_nans)
    try:
        norm = [(val-min)/(max-min) if val is not math.nan else math.nan for val in series]
    except:
        print("poo")
    return norm

