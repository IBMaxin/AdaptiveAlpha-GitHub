# strategies/MicroSwingATRRSI_v1.py
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy
from pandas import DataFrame


class MicroSwingATRRSI_v1(IStrategy):
    """
    Mid-horizon (hours, not seconds) micro-swing strategy:
      - Trend filter: SMA fast > SMA slow
      - Buys pullbacks toward fast SMA with ATR cushion and RSI relief
      - Exits on RSI pop or ATR channel touch
    Hyperoptable + FreqAI-ready (feature + target methods below).
    """

    # --- Core run settings (config will override) ---
    timeframe = "5m"
    startup_candle_count = 200
    process_only_new_candles = True

    # Small-cap defaults (config can override these)
    stake_currency = "USDT"
    stake_amount = 25
    max_open_trades = 3

    # Order handling
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "limit",
        "stoploss_on_exchange": False,
        "stoploss_on_exchange_interval": 60,
    }
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # Default ROI/SL — hyperopt will override if you optimize ROI/SL spaces
    minimal_roi = {
        "0": 0.12,
        "30": 0.05,
        "120": 0.02,
        "240": 0,
    }
    stoploss = -0.12
    trailing_stop = False

    plot_config = {
        "main_plot": {
            "sma_fast": {"color": "blue"},
            "sma_slow": {"color": "orange"},
            "atr_low_band": {"color": "gray"},
            "atr_high_band": {"color": "gray"},
        },
        "subplots": {
            "RSI": {"rsi": {}},
            "ATR%": {"atr_pct": {}},
        },
    }

    # -------------------- Hyperopt params --------------------
    # Trend & pullback structure
    sma_fast_len = IntParameter(10, 30, default=20, space="buy")
    sma_slow_len = IntParameter(40, 100, default=60, space="buy")
    sma_gap_min = DecimalParameter(0.002, 0.03, decimals=4, default=0.008, space="buy")

    # Volatility cushion
    atr_len = IntParameter(10, 30, default=14, space="buy")
    atr_buy_mult = DecimalParameter(0.4, 1.6, decimals=3, default=0.8, space="buy")
    atr_exit_mult = DecimalParameter(0.3, 1.2, decimals=3, default=0.6, space="sell")

    # Momentum filter/exit
    rsi_len = IntParameter(7, 21, default=14, space="buy")
    rsi_buy_max = IntParameter(45, 60, default=55, space="buy")
    rsi_exit = IntParameter(60, 90, default=75, space="sell")

    # -------------------- Indicator helpers --------------------
    @staticmethod
    def _rsi(series: pd.Series, length: int) -> pd.Series:
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
        roll_down = down.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
        rs = roll_up / (roll_down + 1e-12)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _atr(df: DataFrame, length: int) -> pd.Series:
        prev_close = df["close"].shift(1)
        tr1 = (df["high"] - df["low"]).abs()
        tr2 = (df["high"] - prev_close).abs()
        tr3 = (df["low"] - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()

    # -------------------- Indicators --------------------
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        sf = int(self.sma_fast_len.value)
        ss = int(self.sma_slow_len.value)
        rl = int(self.rsi_len.value)
        al = int(self.atr_len.value)

        dataframe["sma_fast"] = dataframe["close"].rolling(sf).mean()
        dataframe["sma_slow"] = dataframe["close"].rolling(ss).mean()

        dataframe["atr"] = self._atr(dataframe, al)
        dataframe["atr_pct"] = (dataframe["atr"] / dataframe["close"]).fillna(0)

        dataframe["rsi"] = self._rsi(dataframe["close"], rl)

        # ATR bands around fast SMA (visual + exits)
        dataframe["atr_low_band"] = (
            dataframe["sma_fast"] - self.atr_buy_mult.value * dataframe["atr"]
        )
        dataframe["atr_high_band"] = (
            dataframe["sma_fast"] + self.atr_exit_mult.value * dataframe["atr"]
        )

        # Gap of fast/slow to ensure trend strength
        dataframe["sma_gap"] = (
            dataframe["sma_fast"] - dataframe["sma_slow"]
        ) / dataframe["sma_slow"]

        dataframe.replace([np.inf, -np.inf], np.nan, inplace=True)
        return dataframe

    # -------------------- Entries --------------------
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions: List[pd.Series] = []

        # Trend: fast > slow & enough separation
        conditions += [
            (dataframe["sma_fast"] > dataframe["sma_slow"]),
            (dataframe["sma_gap"] > float(self.sma_gap_min.value)),
        ]

        # Pullback near/below fast SMA with ATR cushion
        conditions += [
            (dataframe["close"] <= dataframe["atr_low_band"]),
            (dataframe["rsi"] <= int(self.rsi_buy_max.value)),
        ]

        if conditions:
            dataframe.loc[
                np.logical_and.reduce(conditions),
                ["enter_long", "enter_tag"],
            ] = (1, "pullback_atr_rsi")

        return dataframe

    # -------------------- Exits --------------------
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_conditions: List[pd.Series] = []

        # Momentum pop or ATR channel top
        exit_conditions += [
            (dataframe["rsi"] >= int(self.rsi_exit.value))
            | (dataframe["close"] >= dataframe["atr_high_band"])
        ]

        if exit_conditions:
            dataframe.loc[
                np.logical_and.reduce(exit_conditions),
                ["exit_long", "exit_tag"],
            ] = (1, "rsi_or_atr_band")

        return dataframe

    # -------------------- FreqAI hooks (optional) --------------------
    # These are used only when FreqAI is enabled in config.
    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict
    ) -> DataFrame:
        df = dataframe.copy()
        # Lightweight, model-friendly features
        df["ret_1"] = df["close"].pct_change().fillna(0)
        df["ret_3"] = df["close"].pct_change(3).fillna(0)
        df["rsi_fe"] = self._rsi(df["close"], int(self.rsi_len.value)).fillna(50)
        df["atr_pct_fe"] = (
            self._atr(df, int(self.atr_len.value)) / df["close"]
        ).fillna(0)
        df["sma_gap_fe"] = (
            df["close"].rolling(int(self.sma_fast_len.value)).mean()
            - df["close"].rolling(int(self.sma_slow_len.value)).mean()
        ) / df["close"].rolling(int(self.sma_slow_len.value)).mean()
        df["sma_gap_fe"] = df["sma_gap_fe"].fillna(0)
        df.replace([np.inf, -np.inf], 0, inplace=True)
        return df

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Create a simple future-return target over ~2 hours (24x5m candles).
        Matches your config's label_period_candles=24.
        """
        df = dataframe.copy()
        horizon = 24
        df["fai_target_return"] = (
            df["close"].shift(-horizon) / df["close"] - 1.0
        ).fillna(0)
        return df
