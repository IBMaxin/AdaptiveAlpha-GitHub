"""Module: feature_agent.py — auto-generated docstring for flake8 friendliness."""

import logging
import os
import time
from pathlib import Path

from agents.patch_utils import apply_project_patch, sanitize_patch_string
from services.llm_client import LLMClient, load_cfg


class FeatureAgent:
    """
    Lightweight feature agent that asks the LLM to propose a SMALL unified diff
    to add non-breaking improvements. It sanitizes and applies the diff safely.
    """

    def __init__(self, spec: str, max_changes_hint: int = 3):
        self.spec = spec
        self.max_changes_hint = max_changes_hint
        self.cfg = load_cfg()
        self.llm = LLMClient(self.cfg)
        self.logger = logging.getLogger("FeatureAgent")
        logging.basicConfig(
            level=logging.INFO,
            format="[FeatureAgent] %(asctime)s %(levelname)s: %(message)s",
        )

    def _read(self, rel: str) -> str:
        p = Path(rel)
        if not p.exists():
            return f"[MISSING] {rel}\n"
        try:
            return p.read_text(encoding="utf-8")
        except Exception as e:
            return f"[UNREADABLE] {rel}: {e}\n"

    def propose_and_apply(self) -> str:
        root_files = sorted(os.listdir("."))
        healing_server = self._read("services/healing_server.py")
        readme = self._read("README.md")

        system = (
            "ROLE: Senior Python engineer. Propose a LIGHTWEIGHT improvement as a unified diff. "
            "CONSTRAINTS: Output ONLY a single unified diff (diff --git ...) touching at most 2 files, "
            "<= 60 changed lines total, no new heavy dependencies, tests should still pass."
        )
        user = (
            f"Feature spec (keep it small): {self.spec}\n\n"
            f"Project root files: {', '.join(root_files)}\n\n"
            f"Context: services/healing_server.py:\n{healing_server[:6000]}\n\n"
            f"Context: README.md:\n{readme[:4000]}\n"
        )
        suggestion = self.llm.chat(system, user, temperature=0.2, max_tokens=1200)
        self.logger.info(f"LLM Suggestion (raw)\n{suggestion}")
        cleaned = sanitize_patch_string(suggestion)
        # Persist suggestion
        outdir = Path("user_data/feature_runs")
        outdir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        (outdir / f"feature_{ts}.patch").write_text(cleaned, encoding="utf-8")

        if cleaned.lstrip().startswith("diff --git"):
            ok = apply_project_patch(cleaned)
            if ok:
                self.logger.info("Applied feature diff successfully.")
            else:
                self.logger.error(
                    "Failed to apply feature diff. See .agent_backups logs."
                )
        else:
            self.logger.warning("Suggestion was not a unified diff. Skipping apply.")
        return cleaned


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run FeatureAgent for lightweight changes"
    )
    parser.add_argument(
        "--spec", type=str, required=True, help="Short feature specification"
    )
    parser.add_argument(
        "--max", type=int, default=3, help="Hint for small number of changes"
    )
    args = parser.parse_args()
    agent = FeatureAgent(args.spec, args.max)
    agent.propose_and_apply()
