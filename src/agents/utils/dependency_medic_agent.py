"""
dependency_medic_agent.py
Agent to check, heal, and update Python dependencies using LLM assistance.
Flake8/black compliant, clean logging, and formatting.
"""

import logging
import subprocess

from services.llm_client import LLMClient, load_cfg


class DependencyMedicAgent:
    """Agent to check, heal, and update Python dependencies."""

    def __init__(self):
        self.cfg = load_cfg()
        self.llm = LLMClient(self.cfg)
        self.logger = logging.getLogger("DependencyMedicAgent")
        logging.basicConfig(
            level=logging.INFO,
            format="[DependencyMedicAgent] %(asctime)s %(levelname)s: %(message)s",
        )

    def check_dependencies(self) -> str:
        """Check for missing or outdated dependencies using pip check."""
        self.logger.info("Checking for missing or outdated dependencies...")
        result = subprocess.run(["pip", "check"], capture_output=True, text=True)
        return result.stdout.strip()

    def list_outdated(self) -> str:
        """List outdated dependencies using pip list --outdated."""
        self.logger.info("Listing outdated dependencies...")
        result = subprocess.run(
            ["pip", "list", "--outdated"], capture_output=True, text=True
        )
        return result.stdout.strip()

    def heal_dependencies(self, dep_log: str) -> str:
        """Send dependency issues to LLM for healing suggestions."""
        self.logger.info("Sending dependency issues to LLM for healing...")
        system = (
            "ROLE: Python Dependency Medic. "
            "You are an expert at fixing and updating Python dependencies for a trading bot project. "
            "OUTPUT: Only valid pip commands or pyproject.toml/requirements.txt patches, no extra text. "
            "If a patch is not possible, explain the root cause and suggest a fix."
        )
        user = f"Dependency issues:\n{dep_log}"
        suggestion = self.llm.chat(system, user)
        self.logger.info("LLM Suggestion: %s", suggestion)
        return suggestion

    def full_heal(self):
        """Run full dependency check and healing process."""
        dep_issues = self.check_dependencies()
        if dep_issues:
            self.logger.warning("Dependency issues found. Sending to LLM...")
            self.heal_dependencies(dep_issues)
        outdated = self.list_outdated()
        if outdated and "Package" in outdated:
            self.logger.warning("Outdated dependencies found. Sending to LLM...")
            self.heal_dependencies(outdated)
        self.logger.info("Dependency healing complete.")


if __name__ == "__main__":
    agent = DependencyMedicAgent()
    agent.full_heal()
