"""Module: BreakoutATR_v1.py — auto-generated docstring for flake8 friendliness."""

import pandas as pd
import talib.abstract as ta
from freqtrade.strategy import DecimalParameter, IntParameter
from freqtrade.strategy.interface import IStrategy


class BreakoutATR_v1(IStrategy):
    timeframe = "5m"
    startup_candle_count = 60

    atr_period = IntParameter(7, 28, default=14, space="buy")
    atr_mult = DecimalParameter(1.0, 5.0, decimals=1, default=2.0, space="buy")

    def populate_indicators(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df["atr"] = ta.ATR(df, timeperiod=int(self.atr_period.value))
        df["high_ma"] = ta.SMA(df["high"], timeperiod=20)
        df["low_ma"] = ta.SMA(df["low"], timeperiod=20)
        if "enter_long" not in df.columns:
            df["enter_long"] = 0
        if "exit_long" not in df.columns:
            df["exit_long"] = 0
        return df

    def populate_entry_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        thr = df["high_ma"] + (float(self.atr_mult.value) * df["atr"])
        buy_mask = df["close"] > thr
        df.loc[buy_mask, "enter_long"] = 1
        return df

    def populate_exit_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        thr = df["low_ma"] - (float(self.atr_mult.value) * df["atr"])
        sell_mask = df["close"] < thr
        df.loc[sell_mask, "exit_long"] = 1
        return df
