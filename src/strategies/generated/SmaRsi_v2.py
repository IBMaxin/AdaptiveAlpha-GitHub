"""Module: SmaRsi_v2.py — auto-generated docstring for flake8 friendliness."""

import talib.abstract as ta
from freqtrade.strategy import DecimalParameter, IntParameter
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


# --- helpers ---
def rsi_series(close, period=14):
    return ta.RSI(close, timeperiod=period)


def crossed_above(a, b):
    # True when a crosses from <= b to > b on this bar
    return (a > b) & (a.shift(1) <= b.shift(1))


class SmaRsi_v2(IStrategy):
    timeframe = "5m"
    informative_timeframe = "1h"
    startup_candle_count = 200

    # TSL OFF – it was your biggest loser
    trailing_stop = False

    # Defaults (ROI/SL will be hyperopted later)
    minimal_roi = {"0": 0.187, "31": 0.078, "88": 0.033, "207": 0}
    stoploss = -0.326
    can_short = False

    # --- Hyperoptable parameters ---
    # BUY
    rsi_len = IntParameter(8, 20, default=17, space="buy")
    rsi_max = IntParameter(
        50, 70, default=68, space="buy"
    )  # entry only if RSI below this
    sma_fast_len = IntParameter(10, 30, default=13, space="buy")
    sma_slow_len = IntParameter(40, 80, default=58, space="buy")
    sma_gap_min = DecimalParameter(
        0.0005, 0.02, default=0.0015, decimals=4, space="buy"
    )
    atr_len = IntParameter(7, 21, default=12, space="buy")
    atr_min_pct = DecimalParameter(0.003, 0.015, default=0.008, decimals=4, space="buy")
    atr_max_pct = DecimalParameter(0.02, 0.08, default=0.05, decimals=4, space="buy")
    # SELL
    rsi_exit = IntParameter(60, 85, default=85, space="sell")

    # ===== Informative (1h) =====
    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(p, self.informative_timeframe) for p in pairs]

    def _informative_df(self, pair: str) -> DataFrame:
        inf = self.dp.get_pair_dataframe(
            pair=pair, timeframe=self.informative_timeframe
        )
        inf["ema200"] = ta.EMA(inf["close"], timeperiod=200)
        inf["ema200_slope"] = inf["ema200"].pct_change()
        return inf

    # ===== Indicators =====
    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        # 5m SMAs
        fast = int(self.sma_fast_len.value)
        slow = int(self.sma_slow_len.value)
        df["sma_fast"] = ta.SMA(df["close"], timeperiod=fast)
        df["sma_slow"] = ta.SMA(df["close"], timeperiod=slow)
        df["sma_gap"] = (df["sma_fast"] - df["sma_slow"]) / df["sma_slow"]

        # 5m RSI
        rlen = int(self.rsi_len.value)
        df["rsi"] = rsi_series(df["close"], period=rlen)

        # 5m ATR%
        alen = int(self.atr_len.value)
        df["atr"] = ta.ATR(df["high"], df["low"], df["close"], timeperiod=alen)
        df["atr_pct"] = df["atr"] / df["close"]

        # Merge 1h informative
        inf = self._informative_df(metadata["pair"])
        df = df.merge(inf[["date", "ema200", "ema200_slope"]], on="date", how="left")
        df[["ema200", "ema200_slope"]] = df[["ema200", "ema200_slope"]].ffill()

        return df

    # ===== Entries =====
    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (
                (df["ema200_slope"].isna())
                | ((df["ema200_slope"].isna()) | (df["ema200_slope"] > 0))
            )  # HTF uptrend
            & (df["sma_fast"] > df["sma_slow"])  # local trend
            & (df["sma_gap"] > float(self.sma_gap_min.value))  # avoid flat crosses
            & (df["atr_pct"] > float(self.atr_min_pct.value))  # not dead volatility
            & (df["atr_pct"] < float(self.atr_max_pct.value))  # not crazy vol
            & (df["rsi"] < int(self.rsi_max.value))  # not overheated
            & (
                (crossed_above(df["sma_fast"], df["sma_slow"]))
                | ((df["sma_fast"] > df["sma_slow"]) & (df["sma_gap"] > 0))
            )  # event
        )
        df.loc[cond, "enter_long"] = 1
        return df

    # ===== Exits =====
    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[(df["rsi"] > int(self.rsi_exit.value)), "exit_long"] = 1
        return df
