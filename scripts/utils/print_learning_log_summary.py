"""Module: print_learning_log_summary.py — auto-generated docstring for flake8 friendliness."""

import csv
from pathlib import Path


def print_learning_log_summary(
    log_path: str = "user_data/learning_log.csv", n: int = 20
) -> None:
    log_file = Path(log_path)
    if not log_file.exists():
        print(f"No learning log found at {log_path}")
        return
    print("\n=== LEARNING LOG SUMMARY ===")
    with open(log_file, newline="") as f:
        reader = list(csv.reader(f))
        if not reader:
            print("Log is empty.")
            return
        print(
            f"{'Cycle':<6} {'Strategy':<32} {'Timerange':<20} {'Metric':<10} {'Improved':<10}"
        )
        print("-" * 80)
        count = 0
        for row in reversed(reader):
            if len(row) == 5:
                cycle, strat, timerange, metric, improved = row
                print(
                    f"{cycle:<6} {strat:<32} {timerange:<20} {metric:<10} {improved:<10}"
                )
                count += 1
                if count >= n:
                    break
        if count == 0:
            print("No valid summary rows found.")
    print("=" * 80)


if __name__ == "__main__":
    print_learning_log_summary()
