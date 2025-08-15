#!/usr/bin/env python3
"""Module: parse_report.py — auto-generated docstring for flake8 friendliness."""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def get(d: Dict[str, Any], keys: List[str], default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            return d[k]
    return default


def first_dict(obj) -> Optional[Dict[str, Any]]:
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        return obj[0]
    return None


def pick_file(arg: Optional[str]) -> Optional[Path]:
    # 1) explicit path
    if arg:
        p = Path(arg).expanduser()
        if p.exists():
            return p
    # 2) latest exported report under user_data/reports
    reports_dir = Path("user_data/reports")
    if reports_dir.exists():
        cands = sorted(
            reports_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True
        )
        if cands:
            return cands[0]
    # 3) freqtrade dumps a last-result file sometimes
    p = Path(".last_result.json")
    if p.exists():
        return p
    return None


def num(x) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    p = pick_file(arg)
    if not p or not p.exists():
        print("Usage: scripts/parse_report.py /path/to/report.json")
        print("Hint: run `make parse-report` to auto-pick the latest file.")
        sys.exit(0)  # don't hard-fail Make

    data = load_json(p)

    # Defaults shown when missing
    strategy_name = "-"
    trades = "-"
    avg_profit = "-"
    total_profit_abs = "-"
    total_profit_pct = "-"
    pf = "-"
    winrate = "-"
    dd_abs = "-"
    dd_pct = "-"

    # 1) strategy_comparison (common for multi-run)
    sc = data.get("strategy_comparison")
    if isinstance(sc, list) and sc:
        row = sc[0]
        strategy_name = row.get("Strategy", row.get("strategy", strategy_name))
        trades = row.get("Trades", trades)
        avg_profit = row.get("Avg Profit %", avg_profit)
        total_profit_abs = row.get(
            "Tot Profit USDT", row.get("Total Profit USDT", total_profit_abs)
        )
        total_profit_pct = row.get(
            "Tot Profit %", row.get("Total Profit %", total_profit_pct)
        )

    # 2) single-strategy shapes
    # try top-level "strategy" and "results"
    if strategy_name == "-":
        strategy_name = get(data, ["strategy", "Strategy"], strategy_name)

    # metrics may live in various places
    metrics_paths = [
        data.get("metrics"),
        data.get("strategy_metrics"),
        get(data, ["results"], {}),
        get(data, ["strategy"], {}),
    ]
    for mp in metrics_paths:
        if not isinstance(mp, (dict, list)):
            continue
        m = first_dict(mp)
        if not isinstance(m, dict):
            continue

        pf = m.get("profit_factor", pf) or m.get("pf", pf)
        winrate = (
            m.get("winrate", winrate)
            or m.get("wins_ratio", winrate)
            or m.get("winrate_ratio", winrate)
        )
        total_profit_pct = m.get("profit_total", total_profit_pct) or m.get(
            "total_profit_percent", total_profit_pct
        )
        total_profit_abs = m.get("profit_abs", total_profit_abs) or m.get(
            "total_profit_abs", total_profit_abs
        )
        dd_abs = m.get("max_drawdown_abs", dd_abs) or m.get(
            "max_drawdown_abs_usdt", dd_abs
        )
        dd_pct = m.get("max_drawdown", dd_pct) or m.get("max_drawdown_pct", dd_pct)
        trades = m.get("total_trades", trades) or m.get("trades", trades)
        avg_profit = m.get("avg_profit", avg_profit) or m.get(
            "Avg Profit %", avg_profit
        )

    # Some versions put totals under "results"->"strategy" or similar
    results = data.get("results")
    if isinstance(results, dict):
        rfirst = first_dict(results)
        if rfirst:
            total_profit_abs = rfirst.get("profit_abs", total_profit_abs)
            total_profit_pct = rfirst.get("profit_total", total_profit_pct)
            trades = rfirst.get("total_trades", trades)

    print("=== Quick Report ===")
    print(f"File: {p.name}")
    print(f"Strategy: {strategy_name} | Trades: {trades}")
    print(f"Win%: {winrate}")
    print(f"PF: {pf}")
    print(f"Total Profit %: {total_profit_pct}")
    print(f"Absolute Profit: {total_profit_abs}")
    print(f"Avg Profit %: {avg_profit}")
    print(f"DD Abs/%: {dd_abs}/{dd_pct}")


if __name__ == "__main__":
    main()
