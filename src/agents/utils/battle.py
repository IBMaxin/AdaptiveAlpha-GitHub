"""Module: battle.py — auto-generated docstring for flake8 friendliness."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from agents.backtest_agent import BacktestAgent


def run_battle(strategies: list[str]) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    root = Path("runs") / f"battle-{ts}"
    root.mkdir(parents=True, exist_ok=True)
    leaderboard = []
    for s in strategies:
        out = BacktestAgent(s).run()
        # naive parse of meta for elapsed; results existence is enough
        meta = json.loads((out / "meta.json").read_text())
        leaderboard.append(
            {
                "strategy": s,
                "elapsed_sec": meta.get("elapsed_sec", None),
                "path": str(out),
            }
        )
    lb_path = root / "leaderboard.json"
    lb_path.write_text(json.dumps(leaderboard, indent=2))
    return lb_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--strategies",
        nargs="+",
        required=False,
        default=["SmaRsi_v2", "BreakoutATR_v1"],
    )
    args = ap.parse_args()
    lb = run_battle(args.strategies)
    print(f"# Battle complete. Leaderboard: {lb}")


if __name__ == "__main__":
    main()
