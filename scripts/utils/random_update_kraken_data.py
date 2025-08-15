"""Module: random_update_kraken_data.py — auto-generated docstring for flake8 friendliness."""

import logging
import random
import sys

from scripts.kraken_ohlcv_fetcher import DEFAULT_PAIRS, fetch_ohlcv_all


def random_update_kraken_data():
    timeframes = ["5m", "15m", "1h", "4h", "1d"]
    hist_days_options = [7, 14, 30, 60, 90, 180, 365]
    # Randomly select pairs, timeframes, and history window
    pairs = random.sample(DEFAULT_PAIRS, k=random.randint(1, len(DEFAULT_PAIRS)))
    tfs = random.sample(timeframes, k=random.randint(1, len(timeframes)))
    hist_days = random.choice(hist_days_options)
    logging.info(
        f"Random update: pairs={pairs}, timeframes={tfs}, hist_days={hist_days}"
    )
    fetch_ohlcv_all(pairs, tfs, hist_days)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    random_update_kraken_data()
