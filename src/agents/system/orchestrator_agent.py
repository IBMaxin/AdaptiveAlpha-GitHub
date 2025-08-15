"""Module: orchestrator_agent.py — auto-generated docstring for flake8 friendliness."""

import logging
import subprocess
import sys
import time

AGENTS = [
    ("Error Medic", [sys.executable, "-m", "agents.error_medic_agent"]),
    ("Dependency Medic", [sys.executable, "-m", "agents.dependency_medic_agent"]),
]


def run_agents():
    logging.basicConfig(
        level=logging.INFO,
        format="[Orchestrator] %(asctime)s %(levelname)s: %(message)s",
    )
    logger = logging.getLogger("Orchestrator")
    for name, cmd in AGENTS:
        logger.info(f"Running {name} agent...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        logger.info(f"{name} agent finished.")
        time.sleep(1)


def main():
    run_agents()


if __name__ == "__main__":
    main()
