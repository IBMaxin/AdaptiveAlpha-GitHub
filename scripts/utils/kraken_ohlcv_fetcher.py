"""Module: kraken_ohlcv_fetcher.py — auto-generated docstring for flake8 friendliness."""

import logging
import os
import time
from datetime import datetime

import ccxt
import pandas as pd

try:
    import questionary
except ImportError:
    questionary = None


# Default config
DEFAULT_PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "ADA/USDT",
    "XRP/USDT",
]
DEFAULT_TIMEFRAMES = ["5m", "15m"]
LIMIT = 1000  # Max per call (Kraken's limit)
DEFAULT_HIST_DAYS = 30
OUTPUT_DIR = "user_data/data/kraken"
LOGFILE = "kraken_ohlcv_fetcher.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOGFILE), logging.StreamHandler()],
)


def days_ago_ms(days):
    return int((time.time() - days * 86400) * 1000)


def fetch_ohlcv_all(pairs, timeframes, hist_days):
    kraken = ccxt.kraken()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    since = days_ago_ms(hist_days)
    summary = []
    for pair in pairs:
        for tf in timeframes:
            logging.info(f"Fetching {pair} {tf}...")
            all_ohlcv = []
            next_since = since
            error_count = 0
            while True:
                try:
                    ohlcv = kraken.fetch_ohlcv(pair, tf, since=next_since, limit=LIMIT)
                except Exception as e:
                    logging.error(f"Error fetching {pair} {tf}: {e}")
                    error_count += 1
                    if error_count > 3:
                        logging.error(f"Giving up on {pair} {tf} after 3 errors.")
                        break
                    time.sleep(2)
                    continue
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                if len(ohlcv) < LIMIT:
                    break
                next_since = ohlcv[-1][0] + 1  # move past last candle
                time.sleep(1.2)  # avoid rate limit
            if all_ohlcv:
                df = pd.DataFrame(
                    all_ohlcv,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                fname = f"{pair.replace('/', '_')}-{tf}.feather"
                outpath = os.path.join(OUTPUT_DIR, fname)
                try:
                    df.to_feather(outpath)
                    logging.info(f"Saved {outpath} ({len(df)} rows)")
                    summary.append(
                        {"pair": pair, "tf": tf, "rows": len(df), "file": fname}
                    )
                except Exception as e:
                    logging.error(f"Error saving {outpath}: {e}")
            else:
                logging.warning(f"No data for {pair} {tf}")
                summary.append({"pair": pair, "tf": tf, "rows": 0, "file": None})
    # Print summary
    logging.info("\n==== Download Summary ====")
    for s in summary:
        logging.info(f"{s['pair']} {s['tf']}: {s['rows']} rows -> {s['file']}")
    logging.info("==========================\n")


def tui():
    if questionary is None:
        print(
            "questionary not installed. Please install with 'pip install questionary' for TUI mode."
        )
        return DEFAULT_PAIRS, DEFAULT_TIMEFRAMES, DEFAULT_HIST_DAYS
    print("=== Kraken OHLCV Fetcher TUI ===")
    pairs = questionary.checkbox(
        "Select pairs to download:", choices=DEFAULT_PAIRS
    ).ask()
    if not pairs:
        print("No pairs selected. Exiting.")
        exit(1)
    tfs = questionary.checkbox(
        "Select timeframes:", choices=["1m", "5m", "15m", "1h", "4h", "1d"]
    ).ask()
    if not tfs:
        print("No timeframes selected. Exiting.")
        exit(1)
    hist_days = questionary.text(
        "How many days of history?",
        default=str(DEFAULT_HIST_DAYS),
        validate=lambda val: val.isdigit() and int(val) > 0,
    ).ask()
    return pairs, tfs, int(hist_days)


if __name__ == "__main__":
    logging.info(f"Starting Kraken OHLCV fetcher at {datetime.now()}")
    try:
        pairs, tfs, hist_days = tui()
        fetch_ohlcv_all(pairs, tfs, hist_days)
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
