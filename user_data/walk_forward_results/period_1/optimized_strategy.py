from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import pandas as pd

class SimpleAlwaysBuySell(IStrategy):
    minimal_roi = {"0": 0.015}
    stoploss = -0.07
    timeframe = "1h"
    startup_candle_count = 10

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "enter_long"] = 1  # Always buy
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "exit_long"] = 1   # Always sell
        return dataframe
