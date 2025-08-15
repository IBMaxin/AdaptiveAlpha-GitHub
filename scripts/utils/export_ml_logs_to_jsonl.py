"""Module: export_ml_logs_to_jsonl.py — auto-generated docstring for flake8 friendliness."""

import argparse
import csv
import json
from typing import Dict, List


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export ML logs and trade book to JSONL for LLM training."
    )
    parser.add_argument("--log", required=True, help="Path to learning_log.csv")
    parser.add_argument("--trades", required=True, help="Path to ml_trades_book.csv")
    parser.add_argument("--out", required=True, help="Output JSONL file")
    return parser.parse_args()


def read_csv_rows(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def main():
    args = parse_args()
    log_rows = read_csv_rows(args.log)
    trade_rows = read_csv_rows(args.trades)
    # Simple join by index for demonstration; customize as needed
    n = min(len(log_rows), len(trade_rows))
    with open(args.out, "w", encoding="utf-8") as out_f:
        for i in range(n):
            prompt = f"Learning log: {log_rows[i]}\nTrade: {trade_rows[i]}"
            response = log_rows[i].get("improvement", "") or trade_rows[i].get(
                "result", ""
            )
            json.dump({"prompt": prompt, "response": response}, out_f)
            out_f.write("\n")
    print(f"Exported {n} samples to {args.out}")


if __name__ == "__main__":
    main()
