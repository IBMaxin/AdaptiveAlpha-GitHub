"""Module: loop_orchestrator.py — auto-generated docstring for flake8 friendliness."""

import logging
import sys

from agents.backtest_agent import BacktestAgent
from agents.improve_agent import ImproveAgent


class LoopOrchestrator:
    """Coordinates the full research/trading loop: generate/modify strategy -> backtest -> improve -> repeat."""

    def __init__(self, strategy_path: str, config_path: str = None, max_loops: int = 5):
        self.strategy_path = strategy_path
        self.config_path = config_path
        self.max_loops = max_loops
        self.logger = logging.getLogger("LoopOrchestrator")
        logging.basicConfig(
            level=logging.INFO,
            format="[LoopOrchestrator] %(asctime)s %(levelname)s: %(message)s",
        )

    def run(self):
        for i in range(self.max_loops):
            self.logger.info(f"=== Loop {i + 1}/{self.max_loops} ===")
            # 1. Backtest
            backtest_agent = BacktestAgent(self.strategy_path)
            backtest_log = backtest_agent.run_backtest(self.config_path)
            # 2. Improve
            improve_agent = ImproveAgent(self.strategy_path, backtest_log)
            patch = improve_agent.suggest_improvement()
            # 3. (Optional) Apply patch automatically if desired
            # ...existing code for patch application could go here...
            self.logger.info(f"Loop {i + 1} complete.\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python -m agents.loop_orchestrator <strategy_path> [config_path] [max_loops]"
        )
        exit(1)
    strategy = sys.argv[1]
    config = sys.argv[2] if len(sys.argv) > 2 else None
    max_loops = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    orchestrator = LoopOrchestrator(strategy, config, max_loops)
    orchestrator.run()
