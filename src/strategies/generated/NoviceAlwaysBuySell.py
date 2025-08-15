"""Module: NoviceAlwaysBuySell.py — auto-generated docstring for flake8 friendliness."""

from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


class AlwaysBuyStrategy(IStrategy):
    timeframe = "1h"
    minimal_roi = {"0": 0.01}
    stoploss = -0.05
    trailing_stop = False
    position_adjustment_enable = False

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "buy"] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "sell"] = 1
        return dataframe


# ---


class AlwaysSellStrategy(IStrategy):
    timeframe = "1h"
    minimal_roi = {"0": 0.01}
    stoploss = -0.05
    trailing_stop = False
    position_adjustment_enable = False

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "buy"] = 0
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "sell"] = 1
        return dataframe
