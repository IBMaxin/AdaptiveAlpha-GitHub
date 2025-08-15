"""Module: strategy_lab.py — auto-generated docstring for flake8 friendliness."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    # flake8: noqa: E402, F401 -- allow unresolved import for local dev, rollbackable
    from services.llm_client import LLMClient, load_cfg
except ImportError as e:
    # Optionally log or handle the error, but keep the file importable for flake8/mypy
    from typing import Any, Callable

    LLMClient: Optional[type] = None  # type: ignore
    load_cfg: Optional[Callable[[], dict[str, Any]]] = None  # type: ignore
    # Optionally: print(f"[WARN] Could not import services.llm_client: {e}")

ROOT = Path(__file__).resolve().parents[1]
CODE_BLOCK_RE = re.compile(r"```python\s*(.*?)```", re.S)


def extract_code(text: str) -> str | None:
    """
    Extracts a Python code block from a given text.

    This function searches for a code block enclosed in triple backticks
    (```python ... ```) and returns its content. This is useful for parsing
    LLM outputs that often include code snippets within markdown.

    Args:
        text (str): The input text, potentially containing a Python code block.

    Returns:
        str | None: The extracted Python code as a string, or None if no
                    code block is found.
    """
    m = CODE_BLOCK_RE.search(text)
    return m.group(1).strip() if m else None


def filename_from_class(code: str) -> str:
    """
    Generates a filename for a strategy based on its class name and a timestamp.

    This function parses the provided Python code to find the class name that
    inherits from `IStrategy`. If found, it uses that name as the base for the
    filename; otherwise, it defaults to 'GeneratedStrategy'. A Unix timestamp
    is appended to ensure uniqueness.

    Args:
        code (str): The Python code of the strategy.

    Returns:
        str: The generated filename (e.g., `MyStrategy_1678889900.py`).
    """
    import re
    import time

    m = re.search(r"class\s+([A-Za-z0-9_]+)\s*\(\s*IStrategy\s*\)\s*:", code)
    base = m.group(1) if m else "GeneratedStrategy"
    suffix = str(int(time.time()))
    return f"{base}_{suffix}.py"


import datetime

import yaml

PROMPT_LOG = Path("user_data/llm_prompt_response.log")


def load_prompt_config() -> dict[str, str]:
    """
    Loads prompt templates and system instructions from config/agents.yaml.
    Returns a dict with keys: 'system_prompt', 'user_prompt'.
    """
    config_path = Path("config/agents.yaml")
    if not config_path.exists():
        raise FileNotFoundError("Missing config/agents.yaml for prompt system.")
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # Example structure: agents: { StrategyLab: { system_prompt: ..., user_prompt: ... } }
    agents = config.get("agents", {})
    stratlab = agents.get("StrategyLab", {})
    # Fallback to top-level keys if not nested
    system_prompt = stratlab.get("system_prompt") or config.get("system_prompt")
    user_prompt = stratlab.get("user_prompt") or config.get("user_prompt")
    if not system_prompt or not user_prompt:
        raise ValueError("Prompt config must define system_prompt and user_prompt.")
    return {"system_prompt": system_prompt, "user_prompt": user_prompt}


def log_prompt_response(prompt: str, response: str) -> None:
    """
    Appends a timestamped prompt/response pair to PROMPT_LOG for traceability.
    """
    PROMPT_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().isoformat()
    with PROMPT_LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n---\nTIMESTAMP: {ts}\nPROMPT:\n{prompt}\nRESPONSE:\n{response}\n")


def main(spec: Optional[str] = None) -> Path:
    """
    Generates a new trading strategy using an LLM and saves it to a file.
    Loads prompt templates from config/agents.yaml for real-world flexibility.
    Logs all prompts and LLM responses for auditability.

    Args:
        spec (str): Optional. The user prompt for the trading strategy. If not provided, uses the template from config.

    Returns:
        Path: The path to the newly created strategy file.

    Raises:
        SystemExit: If the LLM does not return a valid Python code block.
    """
    if LLMClient is None or load_cfg is None:
        raise ImportError(
            "[ERROR] Could not import LLMClient or load_cfg from services.llm_client. "
            "Ensure services/llm_client.py exists and is error-free."
        )
    cfg = load_cfg()
    llm = LLMClient(cfg)
    prompt_cfg: dict[str, str] = load_prompt_config()
    system: str = prompt_cfg["system_prompt"]
    user: str = spec if spec else prompt_cfg["user_prompt"]
    out: str = llm.chat(system, user)
    log_prompt_response(user, out)
    code: Optional[str] = extract_code(out)
    if not code:
        raise SystemExit("LLM did not return a ```python ...``` block.")

    # Resolve strategy directory, default to user_data/strategies/ if env var is not set
    raw_dir: str = cfg["freqtrade"].get("strategy_dir", "user_data/strategies/")
    resolved_dir: str = os.path.expandvars(raw_dir)
    if resolved_dir == raw_dir or not resolved_dir.strip():
        resolved_dir = str((ROOT / "user_data" / "strategies").resolve())
    strat_dir: Path = Path(resolved_dir)
    strat_dir.mkdir(parents=True, exist_ok=True)
    path: Path = strat_dir / filename_from_class(code)
    path.write_text(code, encoding="utf-8")
    print(f"[OK] Wrote strategy: {path}")
    return path


if __name__ == "__main__":
    spec = None
    if len(sys.argv) > 1:
        spec = " ".join(sys.argv[1:])
    main(spec)
