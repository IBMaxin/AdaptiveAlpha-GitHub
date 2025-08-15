"""Module: improve_agent.py — auto-generated docstring for flake8 friendliness."""

import logging
import os

from services.llm_client import LLMClient, load_cfg


class ImproveAgent:
    """Agent to analyze backtest results and suggest improvements to strategies.

    This agent interacts with an LLM (Large Language Model) to get suggestions
    for improving a trading strategy based on its backtest performance. It feeds
    the backtest log and the strategy's code to the LLM and returns the LLM's
    suggested improvements, typically in the form of a patch.
    """

    def __init__(self, strategy_path: str, backtest_log: str):
        """
        Initializes the ImproveAgent.

        Args:
            strategy_path (str): The path to the strategy file that was backtested.
            backtest_log (str): The full log output from the backtest of the strategy.
        """
        self.strategy_path = strategy_path
        self.backtest_log = backtest_log
        self.cfg = load_cfg()
        self.llm = LLMClient(self.cfg)
        self.offline_mode = os.getenv("LLM_OFFLINE", "0") == "1"
        self.logger = logging.getLogger("ImproveAgent")
        logging.basicConfig(
            level=logging.INFO,
            format="[ImproveAgent] %(asctime)s %(levelname)s: %(message)s",
        )

    def suggest_improvement(self) -> str:
        """
        Suggests improvements to the trading strategy based on the backtest log.

        This method reads the strategy's code, constructs a prompt with the backtest
        log and the code, and sends it to the LLM. The LLM is instructed to provide
        a unified diff/patch or a direct code fix as its output.

        Returns:
            str: The LLM's suggested improvement, typically a patch string.
        """
        self.logger.info(f"Analyzing backtest results for {self.strategy_path}...")
        with open(self.strategy_path, "r", encoding="utf-8") as f:
            code = f.read()
        # Respect offline mode to avoid noisy non-diff outputs
        if self.offline_mode:
            self.logger.info("LLM is in offline mode; skipping suggestion.")
            return ""
        system = (
            "ROLE: Trading Strategy Optimizer. "
            "You improve a single Freqtrade IStrategy file based on a backtest log. "
            "OUTPUT: Return only one unified diff in diff --git format that modifies exactly the target file. "
            "Do not include prose. Do not add new files. Keep imports minimal."
        )
        # Provide explicit path and constraints to increase patch success rate
        self.logger.info("Analyzing backtest results for %s", self.strategy_path)
        user = (
            f"# TARGET_FILE: {self.strategy_path}\n"
            "## CONSTRAINTS:\n"
            "- Only modify TARGET_FILE.\n"
            "- Provide a single diff starting with "
            f"'diff --git a/{self.strategy_path} b/{self.strategy_path}'\n"
            "- Keep code PEP8 and Freqtrade-compatible.\n"
            "\n## Backtest log (excerpt):\n"
            f"{self.backtest_log[:4000]}\n"
            "\n## Current code of TARGET_FILE:\n"
            f"{code}"
        )
        suggestion = self.llm.chat(system, user, temperature=0.2)
        self.logger.info(f"LLM Suggestion:\n{suggestion}")
        return suggestion


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m agents.improve_agent <strategy_path> <backtest_log>")
        exit(1)
    agent = ImproveAgent(sys.argv[1], sys.argv[2])
    agent.suggest_improvement()
