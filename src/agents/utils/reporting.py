"""Module: reporting.py — auto-generated docstring for flake8 friendliness."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def latest_run_dir(root: Path = Path("runs")) -> Path | None:
    if not root.exists():
        return None
    dirs = sorted([p for p in root.glob("*") if p.is_dir()], reverse=True)
    return dirs[0] if dirs else None


def summarize(results_path: Path) -> dict:
    data = json.loads(results_path.read_text())
    # Attempt common keys in freqtrade export; fallback gracefully
    trades = data.get("trades", [])
    metrics = data.get("results", data)
    summary = {
        "trades": len(trades) if isinstance(trades, list) else trades or 0,
        "profit_total": metrics.get("profit_total", metrics.get("total_profit", None)),
        "max_drawdown": metrics.get("max_drawdown", None),
        "calmar": metrics.get("calmar", None),
        "sharpe": metrics.get("sharpe", None),
        "winrate": metrics.get("winrate", None),
    }
    return summary


def main():
    run_root = latest_run_dir()
    if not run_root:
        print("# No runs/ directory found")
        sys.exit(1)
    # Pick first strategy folder
    strat_dirs = [p for p in run_root.glob("*") if p.is_dir()]
    if not strat_dirs:
        print("# No strategy subdir in latest run")
        sys.exit(1)
    strat_dir = strat_dirs[0]
    res = strat_dir / "results.json"
    if not res.exists():
        print(f"# No results.json in {strat_dir}")
        sys.exit(1)
    summary = summarize(res)
    print("# Run report")
    print(f"- Run dir: {run_root.name}/{strat_dir.name}")
    for k, v in summary.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()
