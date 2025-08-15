"""Module: backtest_agent.py

Auto-generated docstring for flake8 friendliness.
"""

import logging
import os
import subprocess
from typing import Optional


class BacktestAgent:
    """Agent to run backtests on strategies and collect results.

    This agent is responsible for executing Freqtrade backtests for a given strategy.
    It handles the configuration of the backtest environment, runs the backtest command,
    and ensures that the trade logs are properly collected for further analysis,
    including machine learning logging.
    """

    def __init__(self, strategy_path: Optional[str] = None):
        """
        Initializes the BacktestAgent.

        Args:
            strategy_path (Optional[str]): The path to the strategy file to be backtested.
                If None, it's expected that the strategy will be set via environment variables
                or other means before `run_backtest`.
        """
        self.strategy_path = strategy_path
        self.logger = logging.getLogger("BacktestAgent")
        logging.basicConfig(
            level=logging.INFO,
            format="[BacktestAgent] %(asctime)s %(levelname)s: %(message)s",
        )

    def run_backtest(self, config_path: Optional[str] = None) -> str:
        """
        Executes a Freqtrade backtest for the specified strategy.

        This method sets up the necessary environment variables for the backtest,
        runs the `run_backtest.sh` script, and captures its output. It also ensures
        that the generated `trades.csv` file is copied to a standardized location
        for ML logging purposes.

        Args:
            config_path (str, optional): Path to the Freqtrade configuration file.
                If None, it defaults to `config.json` or the value of the
                `FT_CONFIG_PATH` environment variable.

        Returns:
            str: The complete standard output from the backtest process.

        Raises:
            Exception: If there are issues during the backtest execution or file operations.
        """
        self.logger.info(f"Running backtest for {self.strategy_path}...")
        # Determine config, strategy, and timeframe
        config = config_path or os.environ.get(
            "FT_CONFIG_PATH", "user_data/config.json"
        )
        if self.strategy_path is None:
            raise ValueError("strategy_path must be set before running backtest.")
        strat = os.path.splitext(os.path.basename(self.strategy_path))[0]
        # Try to extract timeframe from config file
        import json

        try:
            with open(config, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            timeframe = cfg.get("timeframe", "15m")
        except Exception:
            timeframe = "15m"
        env = os.environ.copy()
        env["CONFIG"] = config
        env["STRAT"] = strat
        env["TIMEFRAME"] = timeframe
        self.logger.info(
            f"Backtest env: CONFIG={config}, STRAT={strat}, " f"TIMEFRAME={timeframe}"
        )
        cmd = ["bash", "scripts/run_backtest.sh"]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        self.logger.info(f"Backtest output:\n{result.stdout}")

        # --- Ensure trades export is always copied for ML logging ---
        import glob
        import shutil

        trades_files = glob.glob("user_data/backtest_results/*trades.csv")
        # Find the most recent trades file
        if trades_files:
            latest_trades = max(trades_files, key=os.path.getmtime)
            dest = f"user_data/backtest_results/{strat}_trades.csv"
            try:
                shutil.copy2(latest_trades, dest)
                self.logger.info(f"Copied {latest_trades} to {dest} for ML logging.")
            except Exception as e:
                self.logger.warning(f"Could not copy trades file for ML logging: {e}")
        else:
            self.logger.warning("No trades.csv file found after backtest.")

        return result.stdout


if __name__ == "__main__":
    import sys

    strategy = sys.argv[1] if len(sys.argv) > 1 else None
    agent = BacktestAgent(strategy)
    agent.run_backtest()
