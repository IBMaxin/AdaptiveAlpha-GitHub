"""Module: MinimalTestStrategy.py — auto-generated docstring for flake8 friendliness."""

# Minimal working Freqtrade strategy for testing
import pandas as pd
from freqtrade.strategy import IStrategy


class MinimalTestStrategy(IStrategy):
    timeframe = "5m"
    minimal_roi = {"0": 0.01}
    stoploss = -0.05
    startup_candle_count = 20

    def populate_indicators(
        self, dataframe: pd.DataFrame, metadata: dict
    ) -> pd.DataFrame:
        dataframe["rsi"] = dataframe["close"].rolling(window=14).mean()
        return dataframe

    def populate_buy_trend(
        self, dataframe: pd.DataFrame, metadata: dict
    ) -> pd.DataFrame:
        dataframe.loc[(dataframe["rsi"] < 30), "buy"] = 1
        return dataframe

    def populate_sell_trend(
        self, dataframe: pd.DataFrame, metadata: dict
    ) -> pd.DataFrame:
        dataframe.loc[(dataframe["rsi"] > 70), "sell"] = 1
        return dataframe
