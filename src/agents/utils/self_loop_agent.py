from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

import requests

# Import MCPMemoryClient for persistent memory
from agents.mcp_memory_client import MCPMemoryClient

DEFAULT_MODEL = os.getenv("AGENT_MODEL", "meta-llama-3.1-8b-instruct")
OPENAI_BASE = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:1234/v1").rstrip("/")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")

STRATEGY_NAME = "SimpleAlwaysBuySell"
STRATEGY_DIR = Path("strategies")
STRATEGY_FILE = STRATEGY_DIR / f"{STRATEGY_NAME}.py"

BASELINE_STRATEGY = (
    "from freqtrade.strategy.interface import IStrategy\n"
    "from pandas import DataFrame\n\n"
    f"class {STRATEGY_NAME}(IStrategy):\n"
    '    minimal_roi = {"0": 0.01}\n'
    "    stoploss = -0.10\n"
    '    timeframe = "1h"\n'
    "    startup_candle_count = 10\n\n"
    "    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:\n"
    "        return dataframe\n\n"
    "    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:\n"
    '        dataframe["buy"] = 1\n'
    "        return dataframe\n\n"
    "    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:\n"
    '        dataframe["sell"] = 1\n'
    "        return dataframe\n"
)

DEFAULT_PROMPT = (
    "You are a JSON API that responds only with valid JSON. Your task is to generate Freqtrade trading parameters.\n\n"
    "STRICT REQUIREMENTS:\n"
    "1. Respond with ONLY a single line of JSON\n"
    '2. Use exactly this format: {"minimal_roi_0": <number>, "stoploss": <number>}\n'
    "3. minimal_roi_0 must be a float between 0.001 and 0.10\n"
    "4. stoploss must be a float between -0.30 and -0.01\n"
    "5. NO explanations, NO markdown, NO extra text\n\n"
    'Example valid response: {"minimal_roi_0": 0.025, "stoploss": -0.12}\n\n'
    "Generate random trading parameters now:"
)


def _detect_freqtrade() -> str:
    venv_ft = Path(".venv/bin/freqtrade")
    if venv_ft.exists():
        return str(venv_ft)
    return "freqtrade"


def _llm_chat_json(prompt: str) -> Dict[str, float]:
    url = f"{OPENAI_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json",
    }
    # Use system/user message structure for better results
    system_prompt = "You are a JSON API. Follow instructions exactly and respond only with valid JSON."
    payload: dict[str, object] = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,  # Lower temperature for more consistent JSON output
        "top_p": 0.95,
        "max_tokens": 128,
    }
    # Log the payload for debugging and reproducibility
    os.makedirs("user_data", exist_ok=True)
    with open("user_data/llm_payload.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    try:
        resp = requests.post(
            url, headers=headers, data=json.dumps(payload), timeout=120
        )
        resp.raise_for_status()
        content: str = resp.json()["choices"][0]["message"]["content"]
        # Log the raw LLM response for debugging
        with open("user_data/llm_raw_response.log", "a", encoding="utf-8") as f:
            f.write(f"Prompt: {prompt}\nResponse: {content}\n\n")
    except requests.RequestException:
        with open("user_data/llm_raw_response.log", "a", encoding="utf-8") as f:
            f.write(f"Prompt: {prompt}\nResponse: <RequestException>\n\n")
        return {"minimal_roi_0": 0.012, "stoploss": -0.11}
    match = re.search(r"\{.*?\}", content, re.S)
    if not match:
        with open("user_data/llm_raw_response.log", "a", encoding="utf-8") as f:
            f.write(f"Prompt: {prompt}\nResponse: {content} (no JSON found)\n\n")
        return {"minimal_roi_0": 0.012, "stoploss": -0.11}
    try:
        data = json.loads(match.group(0))
        m0 = float(data.get("minimal_roi_0", 0.012))
        sl = float(data.get("stoploss", -0.11))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        with open("user_data/llm_raw_response.log", "a", encoding="utf-8") as f:
            f.write(f"Prompt: {prompt}\nResponse: {content} (JSON decode error)\n\n")
        return {"minimal_roi_0": 0.012, "stoploss": -0.11}
    m0 = max(0.001, min(m0, 0.10))
    sl = max(-0.30, min(sl, -0.01))
    return {"minimal_roi_0": m0, "stoploss": sl}


def _ensure_strategy_exists() -> None:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    init_py = STRATEGY_DIR / "__init__.py"
    if not init_py.exists():
        init_py.write_text("", encoding="utf-8")
    if not STRATEGY_FILE.exists():
        STRATEGY_FILE.write_text(BASELINE_STRATEGY, encoding="utf-8")


def _mutate_strategy(min_roi_0: float, stoploss: float) -> None:
    txt = STRATEGY_FILE.read_text(encoding="utf-8")
    txt = re.sub(
        r"minimal_roi\s*=\s*\{[^}]*\}",
        f'minimal_roi = {{"0": {min_roi_0:.3f}}}',
        txt,
        flags=re.S,
    )
    txt = re.sub(r"stoploss\s*=\s*[-]?\d+\.\d+", f"stoploss = {stoploss:.2f}", txt)
    STRATEGY_FILE.write_text(txt, encoding="utf-8")


def _download_data(freqtrade_bin: str, config: str, timeframe: str, verbosity: int = 0) -> None:
    cmd = [freqtrade_bin, "download-data", "-c", config, "-t", timeframe]
    
    # Add verbosity flags based on the verbosity level
    if verbosity >= 1:
        cmd.append("-v")
    if verbosity >= 2:
        cmd.append("-v")  # -vv
    if verbosity >= 3:
        cmd.append("-v")  # -vvv
    
    subprocess.run(cmd, check=False)


def _backtest(
    freqtrade_bin: str,
    config: str,
    strategy: str,
    timeframe: str,
    timerange: str,
    verbosity: int = 0,
    export_trades: bool = False,
) -> bool:
    cmd = [
        freqtrade_bin,
        "backtesting",
        "-c",
        config,
        "--strategy",
        strategy,
        "--strategy-path",
        str(STRATEGY_DIR),
        "--timeframe",
        timeframe,
        "--timerange",
        timerange,
        "--cache",
        "none",
    ]
    
    # Add verbosity flags based on the verbosity level  
    if verbosity >= 1:
        cmd.append("-v")
    if verbosity >= 2:
        cmd.append("-v")  # -vv
    if verbosity >= 3:
        cmd.append("-v")  # -vvv
        
    # Add export trades if requested
    if export_trades:
        cmd.extend(["--export", "trades"])
    print("[BT]", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        tail = proc.stdout[-1500:]
        print(tail)
        # Extract and write summary to user_data/backtest_result.log
        summary_lines: list[str] = []
        in_summary = False
        for line in proc.stdout.splitlines():
            if "STRATEGY SUMMARY" in line:
                in_summary = True
            if in_summary:
                summary_lines.append(line)
                if line.strip().startswith("└"):
                    break
        # Fallback: if no summary, write last 20 lines
        if not summary_lines:
            summary_lines = proc.stdout.splitlines()[-20:]
        os.makedirs("user_data", exist_ok=True)
        with open("user_data/backtest_result.log", "w", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")
        # Log the summary action
        with open("user_data/learning_loop.log", "a", encoding="utf-8") as flog:
            flog.write("[BACKTEST] Summary written to backtest_result.log\n")
        return True
    except subprocess.CalledProcessError as exc:
        print(exc.stdout[-1200:])
        print(exc.stderr[-800:])
        # Log failure
        with open("user_data/learning_loop.log", "a", encoding="utf-8") as flog:
            flog.write("[BACKTEST] Backtest failed, no summary written.\n")
        return False


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="self loop agent")
    parser.add_argument("--config", default="user_data/config.json")
    parser.add_argument("--max-loops", type=int, default=1)
    parser.add_argument("--spec", default=DEFAULT_PROMPT)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument(
        "--timerange", default=os.getenv("AGENT_TIMERANGE", "20250101-")
    )
    # Add verbosity support for better debugging and monitoring
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="Increase verbosity level (-v, -vv, -vvv). More v's = more detailed output."
    )
    # Add export trades support for detailed trade analysis
    parser.add_argument(
        "--export-trades", action="store_true", default=False,
        help="Export detailed trade information to CSV files for analysis."
    )
    # Add option to disable MCP memory features for simpler operation
    parser.add_argument(
        "--disable-memory", action="store_true", default=False,
        help="Disable MCP memory features to avoid connection errors when memory server isn't running."
    )
    args = parser.parse_args(argv)
    freqtrade_bin = _detect_freqtrade()
    _ensure_strategy_exists()
    _download_data(freqtrade_bin, args.config, args.timeframe, args.verbose)
    MEMORY_WINDOW = 5
    # --- MCP Memory Integration ---
    if not args.disable_memory:
        mcp = MCPMemoryClient()
        stm_raw = mcp.get("short_term_memory")
        ltm_raw = mcp.get("long_term_memory")
        short_term_memory: list[str] = [str(x) for x in stm_raw] if isinstance(stm_raw, list) else []  # type: ignore
        long_term_memory: list[str] = [str(x) for x in ltm_raw] if isinstance(ltm_raw, list) else []  # type: ignore
    else:
        print("[INFO] Memory features disabled - using session-only memory")
        short_term_memory: list[str] = []
        long_term_memory: list[str] = []
    for i in range(1, args.max_loops + 1):
        print(f"\n=== LOOP {i}/{args.max_loops} ===")
        # Read the latest summary for feedback
        last_backtest_summary = None
        try:
            with open("user_data/backtest_result.log", "r", encoding="utf-8") as fbt:
                last_backtest_summary = fbt.read().strip()
        except Exception as e:
            last_backtest_summary = f"(summary unavailable: {e})"
        # Update memory
        if last_backtest_summary:
            short_term_memory.append(last_backtest_summary)
            long_term_memory.append(last_backtest_summary)
            if len(short_term_memory) > MEMORY_WINDOW:
                short_term_memory.pop(0)
            # Save updated memory to MCP only if memory is enabled
            if not args.disable_memory:
                mcp.put("short_term_memory", short_term_memory)
                mcp.put("long_term_memory", long_term_memory)
        # Build prompt with both short- and long-term memory
        if short_term_memory:
            prompt = (
                f"You are improving a Freqtrade strategy in Python called {STRATEGY_NAME}.\n"
                "Only suggest SMALL numeric tweaks to either or both of:\n"
                '- minimal_roi (dict like {"0": float})\n'
                "- stoploss (negative float between -0.30 and -0.01).\n\n"
                "Return STRICT JSON only with keys: minimal_roi_0 (float), stoploss (float).\n"
                "Do not include text outside the JSON.\n\n"
                f"Short-term memory (last {MEMORY_WINDOW} summaries):\n"
                + "\n---\n".join(short_term_memory)
                + "\n\n"
                "Long-term memory (all summaries so far):\n"
                + "\n---\n".join(long_term_memory)
                + "\n"
            )
        else:
            prompt = args.spec
        # Log the prompt and memory
        with open("user_data/learning_loop.log", "a", encoding="utf-8") as flog:
            flog.write(f"LOOP {i} PROMPT:\n{prompt}\n")
            flog.write(f"LOOP {i} SHORT_TERM_MEMORY: {short_term_memory}\n")
            flog.write(f"LOOP {i} LONG_TERM_MEMORY: {long_term_memory}\n")
        # Retry logic for LLM failures
        max_retries = 3
        rec: dict[str, float] = {"minimal_roi_0": 0.012, "stoploss": -0.11}
        for attempt in range(max_retries):
            rec_raw = _llm_chat_json(prompt)
            try:
                m0_val = float(rec_raw.get("minimal_roi_0", 0.012))
                sl_val = float(rec_raw.get("stoploss", -0.11))
                rec = {"minimal_roi_0": m0_val, "stoploss": sl_val}
                break
            except Exception:
                with open("user_data/learning_loop.log", "a", encoding="utf-8") as flog:
                    flog.write(f"LOOP {i} LLM RETRY {attempt+1}: {rec_raw}\n")
                time.sleep(2)
        else:
            # If all retries fail, log and use fallback values
            with open("user_data/learning_loop.log", "a", encoding="utf-8") as flog:
                flog.write(f"LOOP {i} LLM ALL RETRIES FAILED, using fallback values.\n")
            # rec is already set to fallback values
        m0 = float(rec.get("minimal_roi_0", 0.012))
        sl = float(rec.get("stoploss", -0.11))
        print(f"[LLM] Proposed minimal_roi[0]={m0:.3f}, stoploss={sl:.2f}")
        _mutate_strategy(m0, sl)
        ok = _backtest(
            freqtrade_bin,
            args.config,
            STRATEGY_NAME,
            args.timeframe,
            args.timerange,
            args.verbose,
            args.export_trades,
        )
        # Log the result
        with open("user_data/learning_loop.log", "a", encoding="utf-8") as flog:
            flog.write(f"LOOP {i} LLM RESPONSE: {rec}\n")
            flog.write(f"LOOP {i} STRATEGY: minimal_roi_0={m0}, stoploss={sl}\n")
        if not ok:
            print("[WARN] Backtest failed; continuing.")
            with open("user_data/learning_loop.log", "a", encoding="utf-8") as flog:
                flog.write(f"LOOP {i} WARNING: Backtest failed.\n")
        time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
