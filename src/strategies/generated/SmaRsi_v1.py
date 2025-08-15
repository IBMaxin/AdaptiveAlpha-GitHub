"""Module: SmaRsi_v1.py — auto-generated docstring for flake8 friendliness."""

import numpy as np
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


def rsi(series, period=14):
    delta = series.diff()
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    roll_up = DataFrame(up).ewm(alpha=1 / period, adjust=False).mean()
    roll_down = DataFrame(down).ewm(alpha=1 / period, adjust=False).mean()
    rs = roll_up / (roll_down + 1e-9)
    return 100 - (100 / (1 + rs))


class SmaRsi_v1(IStrategy):
    timeframe = "5m"
    minimal_roi = {"0": 0.04}
    stoploss = -0.02
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        df["sma_fast"] = df["close"].rolling(20).mean()
        df["sma_slow"] = df["close"].rolling(50).mean()
        df["rsi"] = rsi(df["close"], 14)
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[(df["sma_fast"] > df["sma_slow"]) & (df["rsi"] < 60), "enter_long"] = 1
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[(df["rsi"] > 70), "exit_long"] = 1
        return df
