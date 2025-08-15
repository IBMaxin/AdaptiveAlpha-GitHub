"""Module: watchdog_agent.py — auto-generated docstring for flake8 friendliness."""

import logging
import os
import time

from agents.orchestrator_agent import run_agents


class WatchdogAgent:
    """Watches for file changes, errors, or process failures and triggers healing."""

    def __init__(self, watch_dirs=None, interval=10):
        self.logger = logging.getLogger("WatchdogAgent")
        logging.basicConfig(
            level=logging.INFO,
            format="[WatchdogAgent] %(asctime)s %(levelname)s: %(message)s",
        )
        self.watch_dirs = watch_dirs or ["."]
        self.interval = interval
        self.last_mtimes = {}

    def scan_files(self):
        changed = False
        for d in self.watch_dirs:
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith(".py"):
                        path = os.path.join(root, f)
                        mtime = os.path.getmtime(path)
                        if path not in self.last_mtimes:
                            self.last_mtimes[path] = mtime
                        elif self.last_mtimes[path] != mtime:
                            self.logger.warning(f"Detected change in {path}")
                            self.last_mtimes[path] = mtime
                            changed = True
        return changed

    def run(self):
        self.logger.info("Starting WatchdogAgent...")
        while True:
            if self.scan_files():
                self.logger.info("Change detected. Running healing agents...")
                run_agents()
            time.sleep(self.interval)


if __name__ == "__main__":
    agent = WatchdogAgent()
    agent.run()
