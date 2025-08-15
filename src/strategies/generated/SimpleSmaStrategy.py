"""Module: SimpleSmaStrategy.py — auto-generated docstring for flake8 friendliness."""

# --- Do not remove these libs ---

from freqtrade.strategy import IStrategy


class SimpleSmaStrategy(IStrategy):
    # Minimal ROI designed for the strategy
    minimal_roi = {"0": 0.02}

    # Stoploss:
    stoploss = -0.10

    # Optimal timeframe for the strategy
    timeframe = "5m"

    def populate_indicators(self, dataframe, metadata):
        dataframe["sma_fast"] = dataframe["close"].rolling(window=10).mean()
        dataframe["sma_slow"] = dataframe["close"].rolling(window=30).mean()
        return dataframe

    def populate_buy_trend(self, dataframe, metadata):
        dataframe.loc[
            (
                (dataframe["sma_fast"] > dataframe["sma_slow"])
                & (dataframe["close"] > dataframe["sma_fast"])
            ),
            "buy",
        ] = 1
        return dataframe

    def populate_sell_trend(self, dataframe, metadata):
        dataframe.loc[
            (
                (dataframe["sma_fast"] < dataframe["sma_slow"])
                & (dataframe["close"] < dataframe["sma_fast"])
            ),
            "sell",
        ] = 1
        return dataframe
