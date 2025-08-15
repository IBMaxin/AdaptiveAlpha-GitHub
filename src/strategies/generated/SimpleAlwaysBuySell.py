import talib.abstract as ta
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


class SimpleAlwaysBuySell(IStrategy):
    minimal_roi = {"0": 0.012}
    stoploss = -0.11
    timeframe = "1h"
    startup_candle_count = 210

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma_fast"] = ta.SMA(dataframe["close"], timeperiod=50)
        dataframe["sma_slow"] = ta.SMA(dataframe["close"], timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe["close"], timeperiod=14)
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["sma_fast"] > dataframe["sma_slow"])
            & (dataframe["close"] > dataframe["sma_fast"])
            & (dataframe["rsi"].between(50, 70))
        )
        dataframe["buy"] = cond.astype(int)
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (dataframe["rsi"] > 70) | (dataframe["close"] < dataframe["sma_fast"])
        dataframe["sell"] = cond.astype(int)
        return dataframe
