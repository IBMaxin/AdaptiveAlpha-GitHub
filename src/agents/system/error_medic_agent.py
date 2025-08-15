"""Module: error_medic_agent.py — auto-generated docstring for flake8 friendliness."""

import logging
import os
import subprocess
import sys
from typing import List, Optional

from agents.patch_utils import apply_patch, apply_project_patch, rollback_file
from services.llm_client import LLMClient, load_cfg


class BaseAgent:
    """Base class for all agents, providing logging and config."""

    def __init__(self, name: str):
        self.name = name
        self.cfg = load_cfg()
        self.logger = logging.getLogger(name)
        logging.basicConfig(
            level=logging.INFO,
            format=f"[{name}] %(asctime)s %(levelname)s: %(message)s",
        )


class ErrorMedicAgent(BaseAgent):
    """Production-grade error healing agent using LLM and classic tools."""

    def __init__(self):
        super().__init__("ErrorMedicAgent")
        self.llm = LLMClient(self.cfg)

    def run_linter(self) -> str:
        self.logger.info("Running ruff linter...")
        result = subprocess.run(["ruff", "check", "."], capture_output=True, text=True)
        return result.stdout.strip()

    def run_formatter(self):
        self.logger.info("Running ruff format...")
        subprocess.run(["ruff", "format", "."])

    def run_type_checker(self) -> str:
        self.logger.info("Running mypy type checker...")
        result = subprocess.run(["mypy", "."], capture_output=True, text=True)
        return result.stdout.strip()

    def run_tests(self) -> str:
        self.logger.info("Running pytest...")
        result = subprocess.run(["pytest"], capture_output=True, text=True)
        return result.stdout.strip()

    def heal_errors(
        self, error_log: str, context_files: Optional[List[str]] = None
    ) -> str:
        self.logger.info("Sending errors to LLM for healing...")
        context = ""
        if context_files:
            for fname in context_files:
                try:
                    with open(fname, "r", encoding="utf-8") as f:
                        code = f.read()
                    context += f"\n\n# File: {fname}\n" + code
                except Exception as e:
                    context += f"\n\n# File: {fname} (unreadable: {e})\n"
        system = (
            "ROLE: Senior Python Project Healer. "
            "Fix code, tests, and configuration. "
            "OUTPUT: Only a valid unified diff for the project root (diff --git ...) or a direct file replacement. "
            "No prose. Coordinate multi-file changes in one diff."
        )
        user = (
            f"Error log(s):\n{error_log}\n"
            f"Project context (snippets):{context}\n"
            "Project root files: " + ", ".join(os.listdir("."))
        )
        suggestion = self.llm.chat(system, user)
        self.logger.info(f"LLM Suggestion:\n{suggestion}")
        # Auto-apply patch if config allows and patch detected
        if self.cfg.get("agents", {}).get("ErrorMedic", {}).get("auto_patch", True):
            from agents.patch_utils import sanitize_patch_string

            cleaned = sanitize_patch_string(suggestion)
            if cleaned.lstrip().startswith("diff --git"):
                self.logger.info("Applying project-wide diff...")
                success = apply_project_patch(cleaned)
                if success and self.cfg.get("agents", {}).get("ErrorMedic", {}).get(
                    "auto_restart", True
                ):
                    self.logger.info("Restarting agent after patch...")
                    os.execv(sys.executable, [sys.executable] + sys.argv)
            elif context_files:
                for fname in context_files:
                    if fname in cleaned:
                        success = apply_patch(fname, cleaned)
                        if not success:
                            self.logger.error(
                                f"Patch failed for {fname}, rolling back."
                            )
                            rollback_file(fname)
                        elif (
                            self.cfg.get("agents", {})
                            .get("ErrorMedic", {})
                            .get("auto_restart", True)
                        ):
                            self.logger.info("Restarting agent after patch...")
                            os.execv(sys.executable, [sys.executable] + sys.argv)
        return suggestion

    def full_heal(self):
        self.logger.info("Starting full healing process...")
        self.run_formatter()
        lint_errors = self.run_linter()
        if lint_errors:
            self.logger.warning("Lint errors found. Sending to LLM...")
            files = [
                f
                for f in lint_errors.split("\n")
                if f and ":" in f and os.path.exists(f.split(":")[0])
            ]
            self.heal_errors(lint_errors, context_files=files)
        type_errors = self.run_type_checker()
        if type_errors:
            self.logger.warning("Type errors found. Sending to LLM...")
            self.heal_errors(type_errors)
        test_output = self.run_tests()
        if "FAILED" in test_output:
            self.logger.warning("Test failures found. Sending to LLM...")
            self.heal_errors(test_output)
        self.logger.info("Healing complete.")


if __name__ == "__main__":
    agent = ErrorMedicAgent()
    agent.full_heal()
