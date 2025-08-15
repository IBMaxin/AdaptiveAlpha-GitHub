"""Module: verify_kraken_data.py — auto-generated docstring for flake8 friendliness."""

import os
from pathlib import Path

import pandas as pd


def verify_kraken_data(data_dir="user_data/data/kraken"):
    print(f"Verifying Kraken OHLCV data in: {data_dir}\n")
    if not os.path.exists(data_dir):
        print("[ERROR] Data directory does not exist.")
        return
    files = list(Path(data_dir).glob("*.feather"))
    if not files:
        print("[ERROR] No .feather files found.")
        return
    for f in files:
        try:
            df = pd.read_feather(f)
            print(f"{f.name}: {len(df)} rows, columns: {list(df.columns)}")
        except Exception as e:
            print(f"[ERROR] Could not read {f.name}: {e}")


if __name__ == "__main__":
    verify_kraken_data()
