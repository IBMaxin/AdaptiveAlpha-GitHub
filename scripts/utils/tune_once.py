#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

# --- Config from env (LM Studio on Windows, exported in WSL) ---
BASE = os.getenv("OPENAI_API_BASE", "").rstrip("/")
KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("AGENT_MODEL", "meta-llama-3.1-8b-instruct")


STRATEGY_PATH = Path("strategies/SimpleAlwaysBuySell.py")
CONFIG = "user_data/config.json"
TIMEFRAME = "1h"
TIMERANGE = os.getenv("AGENT_TIMERANGE", "20240101-")  # start-to-now


# Auto-detect freqtrade executable in venv
FREQTRADE_PATH = shutil.which("freqtrade")
if not FREQTRADE_PATH:
    print(
        "[LOG] Could not find 'freqtrade' in PATH. Please ensure your venv is activated."
    )
else:
    print(f"[LOG] Using freqtrade executable: {FREQTRADE_PATH}")


def call_llm(spec: str) -> str:
    """Call local LM Studio /v1/chat/completions and return content string."""
    if not BASE:
        raise RuntimeError("OPENAI_API_BASE missing in env.")
    url = f"{BASE}/chat/completions"
    payload: Dict[str, Any] = {
        "model": MODEL,
        "messages": [{"role": "user", "content": spec}],
        "temperature": 0.2,
        "top_p": 0.95,
        "max_tokens": 256,
    }
    headers = {"Content-Type": "application/json"}
    # Only add Authorization header if KEY is set (for remote APIs)
    if KEY:
        headers["Authorization"] = f"Bearer {KEY}"
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    j = r.json()
    return j["choices"][0]["message"]["content"]


def _scan_json_objects(text: str) -> Optional[dict[str, Any]]:
    """
    Pull the first valid JSON object from:
    - ```json ... ``` fenced blocks
    - raw text containing {...}
    """
    # 1) fenced blocks
    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S | re.I):
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 2) greedy brace scan
    #    take the first top-level {...} that parses
    stack: list[str] = []
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if not stack:
                start = i
            stack.append("{")
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start is not None:
                    chunk = text[start : i + 1]
                    try:
                        return json.loads(chunk)
                    except Exception:
                        start = None
    return None


def normalize_params(obj: dict[str, Any]) -> Tuple[Dict[str, float], float]:
    """
    Accept either:
      {"minimal_roi": {"0": 0.01, "60": 0.0}, "stoploss": -0.1}
    or
      {"minimal_roi_0": 0.012, "stoploss": -0.11}
    """
    roi: Dict[str, float]
    sl: float

    if "minimal_roi" in obj and isinstance(obj["minimal_roi"], dict):
        roi = {str(k): float(v) for k, v in obj["minimal_roi"].items()}  # type: ignore
    elif "minimal_roi_0" in obj:
        roi = {"0": float(obj["minimal_roi_0"])}
    else:
        roi = {"0": 0.012}  # fallback

    sl = float(obj.get("stoploss", -0.11))
    return roi, sl


def patch_strategy(path: Path, roi: Dict[str, float], stoploss: float) -> None:
    """Replace minimal_roi and stoploss assignments inside the strategy file."""
    src = path.read_text(encoding="utf-8")

    # minimal_roi line
    roi_json = json.dumps(roi, separators=(", ", ": "))
    minimal_roi_match = re.search(r"(?m)^\s*minimal_roi\s*=\s*\{.*?\}", src, flags=re.S)
    stoploss_match = re.search(r"(?m)^\s*stoploss\s*=\s*-?\d+(\.\d+)?", src)

    if not minimal_roi_match or not stoploss_match:
        print(
            "[LOG] patch_strategy: minimal_roi or stoploss pattern not found in file."
        )
        raise RuntimeError(
            "Could not find minimal_roi or stoploss assignment in strategy file."
        )

    src_new = re.sub(
        r"(?m)^\s*minimal_roi\s*=\s*\{.*?\}",
        f"    minimal_roi = {roi_json}",
        src,
        count=1,
        flags=re.S,
    )
    src_new = re.sub(
        r"(?m)^\s*stoploss\s*=\s*-?\d+(\.\d+)?",
        f"    stoploss = {stoploss}",
        src_new,
        count=1,
    )

    if src_new != src:
        print("[LOG] patch_strategy: Strategy file patched and updated.")
        path.write_text(src_new, encoding="utf-8")
    else:
        print(
            "[LOG] patch_strategy: Strategy file already up to date, no changes made."
        )


def backtest_once() -> int:
    """Run one backtest and return process returncode."""
    if not FREQTRADE_PATH:
        print("[LOG] backtest_once: freqtrade executable not found, aborting.")
        return 1
    cmd = [
        FREQTRADE_PATH,
        "backtesting",
        "-c",
        CONFIG,
        "--strategy",
        "SimpleAlwaysBuySell",
        "--strategy-path",
        "strategies",
        "--timeframe",
        TIMEFRAME,
        "--timerange",
        TIMERANGE,
        "--cache",
        "none",
    ]
    print("[BT]", " ".join(cmd), flush=True)
    return subprocess.call(cmd)


def main() -> int:
    """
    Main learning loop. Customizable via LOOP_CONFIG at the top of the file or via environment variables.
    Easily set timeframes, timeranges, and number of iterations without code changes.
    """
    import logging
    from datetime import datetime, timedelta
    from typing import Any, Dict, Optional, Tuple

    # --- Customizable loop config (env override) ---
    LOOP_CONFIG: Dict[str, Any] = {
        "timeframes": os.getenv("AGENT_TIMEFRAMES", "5m,1h,4h").split(","),
        "num_iter": int(os.getenv("AGENT_NUM_ITER", "3")),
        "base_start": os.getenv("AGENT_BASE_START", "2024-01-01"),
        "days_per_iter": int(os.getenv("AGENT_DAYS_PER_ITER", "30")),
    }

    # Verify timeframes are valid for Freqtrade
    valid_timeframes = {
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "12h",
        "1d",
        "1w",
    }
    for tf in LOOP_CONFIG["timeframes"]:
        if tf not in valid_timeframes:
            logging.warning(
                f"[VERIFY] Timeframe '{tf}' may not be valid for Freqtrade."
            )

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    best_profit: float = float("-inf")
    best_params: Optional[Tuple[Dict[str, float], float, str, str]] = None
    last_profit: Optional[float] = None
    try:
        for tf in LOOP_CONFIG["timeframes"]:
            logging.info(f"=== Timeframe: {tf} ===")
            base_start = datetime.strptime(LOOP_CONFIG["base_start"], "%Y-%m-%d")
            for i in range(LOOP_CONFIG["num_iter"]):
                logging.info(
                    f"[LOOP] Iteration {i+1}/{LOOP_CONFIG['num_iter']} for {tf}"
                )
                start = base_start + timedelta(days=i * LOOP_CONFIG["days_per_iter"])
                end = start + timedelta(days=LOOP_CONFIG["days_per_iter"])
                timerange = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
                logging.info(f"Using timerange: {timerange}")
                if last_profit is not None:
                    feedback = (
                        f"Last backtest profit: {last_profit:.2f}%. Try to improve it."
                    )
                else:
                    feedback = ""
                spec = (
                    "Return ONLY a single JSON object with either:\n"
                    '{ "minimal_roi": {"0": 0.01, "60": 0.0}, "stoploss": -0.1 }\n'
                    "or\n"
                    '{ "minimal_roi_0": 0.012, "stoploss": -0.11 }\n'
                    "No markdown, no code fences, no commentary.\n"
                    f"{feedback}"
                )
                try:
                    raw = call_llm(spec)
                    obj = _scan_json_objects(raw) or {}
                    roi, sl = normalize_params(obj)
                    logging.info(f"[LLM] Parsed: ROI={roi} stoploss={sl}")
                    patch_strategy(STRATEGY_PATH, roi, sl)
                    # Ensure FREQTRADE_PATH is str, not None
                    if not FREQTRADE_PATH:
                        logging.error("freqtrade executable not found, aborting.")
                        return 1
                    result = subprocess.run(
                        [
                            str(FREQTRADE_PATH),
                            "backtesting",
                            "-c",
                            CONFIG,
                            "--strategy",
                            "SimpleAlwaysBuySell",
                            "--strategy-path",
                            "strategies",
                            "--timeframe",
                            tf,
                            "--timerange",
                            timerange,
                            "--cache",
                            "none",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    logging.info(
                        f"Backtest output for iteration {i+1} (timeframe {tf}):\nSTDOUT:\n{result.stdout}"
                    )
                    logging.info(f"STDERR:\n{result.stderr}")
                    if not result.stdout.strip() and result.stderr.strip():
                        logging.warning(
                            f"[WARN] No stdout from Freqtrade, but stderr present:\n{result.stderr}"
                        )
                    elif not result.stdout.strip():
                        logging.warning("[WARN] No output from Freqtrade backtest.")
                    profit = parse_backtest_profit(result.stdout)
                    logging.info(f"Iteration {i+1} profit: {profit}")
                    if profit > best_profit:
                        best_profit = profit
                        best_params = (roi, sl, tf, timerange)
                    last_profit = profit
                except Exception as e:
                    logging.error(f"Exception in iteration {i+1} (timeframe {tf}): {e}")
    except Exception as loop_e:
        logging.error(f"Learning loop failed: {loop_e}")
    logging.info(f"[RESULT] Best profit: {best_profit}")
    logging.info(f"[RESULT] Best params: {best_params}")
    return 0


def parse_backtest_profit(backtest_output: str) -> float:
    """Extract profit percentage from Freqtrade backtest output. Logs output for debugging if parsing fails."""
    match = re.search(r"Total profit %\s*\|\s*(-?\d+\.\d+)", backtest_output)
    if match:
        return float(match.group(1))
    # fallback: try to find 'Total profit %' in table
    match = re.search(r"Total profit %\s*│\s*(-?\d+\.\d+)", backtest_output)
    if match:
        return float(match.group(1))
    import logging

    # Write the raw output to a debug file for inspection
    with open("backtest_debug_output.txt", "a", encoding="utf-8") as dbg:
        dbg.write("\n--- Could not parse profit ---\n")
        dbg.write(backtest_output)
        dbg.write("\n-----------------------------\n")
    logging.error(
        "[DEBUG] Could not parse profit. See backtest_debug_output.txt for raw output."
    )
    return float("-inf")


if __name__ == "__main__":
    sys.exit(main())
