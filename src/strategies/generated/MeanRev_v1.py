"""Module: MeanRev_v1.py — auto-generated docstring for flake8 friendliness."""

from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


class MeanRev_v1(IStrategy):
    timeframe = "5m"
    minimal_roi = {"0": 0.02}
    stoploss = -0.015

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        df["ma"] = df["close"].rolling(50).mean()
        df["z"] = (df["close"] - df["ma"]) / (df["close"].rolling(50).std() + 1e-9)
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[(df["z"] < -1.0), "enter_long"] = 1
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[(df["z"] >= 0.0), "exit_long"] = 1
        return df
