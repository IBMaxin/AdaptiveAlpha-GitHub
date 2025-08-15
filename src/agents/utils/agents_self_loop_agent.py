from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict, cast

import requests

# Environment knobs read by the agent.
# Defaults align with a local LM Studio server.
DEFAULT_MODEL: str = os.getenv("AGENT_MODEL", "meta-llama-3.1-8b-instruct")
OPENAI_BASE: str = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:1234/v1").rstrip("/")
OPENAI_KEY: str = os.getenv("OPENAI_API_KEY", "lm-studio")

# Filenames/paths used across the loop to avoid duplicating literals.
STRATEGY_NAME: str = "SimpleAlwaysBuySell"
STRATEGY_DIR: Path = Path("strategies")
STRATEGY_FILE: Path = STRATEGY_DIR / f"{STRATEGY_NAME}.py"
RESULTS_DIR: Path = Path("user_data/backtest_results")
LOG_FILE: Path = Path("user_data/learning_log.csv")
MEM_FILE: Path = Path("user_data/agent_memory.json")

# A minimal, valid Freqtrade strategy we can mutate.
# Guarantees buy/sell so backtests run.
BASELINE_STRATEGY: str = (
    "from freqtrade.strategy.interface import IStrategy\n"
    "from pandas import DataFrame\n\n"
    f"class {STRATEGY_NAME}(IStrategy):\n"
    '    minimal_roi = {"0": 0.01}\n'
    "    stoploss = -0.10\n"
    '    timeframe = "1h"\n'
    "    startup_candle_count = 10\n\n"
    "    def populate_indicators(self, dataframe: DataFrame,"
    " metadata: dict) -> DataFrame:\n"
    "        return dataframe\n\n"
    "    def populate_buy_trend(self, dataframe: DataFrame,"
    " metadata: dict) -> DataFrame:\n"
    '        dataframe["buy"] = 1\n'
    "        return dataframe\n\n"
    "    def populate_sell_trend(self, dataframe: DataFrame,"
    " metadata: dict) -> DataFrame:\n"
    '        dataframe["sell"] = 1\n'
    "        return dataframe\n"
)

# Prompt guiding the model to propose tiny numeric tweaks we can
# safely apply.
BASE_PROMPT: str = (
    "You are improving a trivial Freqtrade strategy in Python called "
    "SimpleAlwaysBuySell.\n"
    "Only suggest SMALL numeric tweaks to either or both of:\n"
    '- minimal_roi (dict like {"0": float})\n'
    "- stoploss (negative float between -0.30 and -0.01).\n\n"
    "Return STRICT JSON only with keys: minimal_roi_0 (float), stoploss "
    "(float).\n"
    "Do not include text outside the JSON.\n"
)


# Typed dicts for the OpenAI-compatible chat API payload/response.
class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionPayload(TypedDict):
    model: str
    messages: List[ChatMessage]
    temperature: float
    top_p: float
    max_tokens: int


class ChoiceMessage(TypedDict):
    role: Literal["assistant", "user", "system"]
    content: str


class Choice(TypedDict):
    index: int
    message: ChoiceMessage


class ChatCompletionResponse(TypedDict):
    choices: List[Choice]


def detect_freqtrade() -> str:
    """Return freqtrade executable, preferring the project's venv.

    We probe .venv first so users don't accidentally call a global
    binary with older deps.
    """
    venv_ft = Path(".venv/bin/freqtrade")
    if venv_ft.exists():
        return str(venv_ft)
    return "freqtrade"


def load_memory() -> Dict[str, float]:
    """Load the agent's memory (best params/score so far).

    A missing or corrupt file yields an empty dict, treated as
    "no prior".
    """
    if MEM_FILE.exists():
        try:
            text = MEM_FILE.read_text(encoding="utf-8")
            data = json.loads(text)
            # Coerce to Dict[str, float] where possible.
            out: Dict[str, float] = {}
            for k, v in cast(Dict[str, Any], data).items():
                try:
                    # best_* fields are numeric
                    out[k] = float(v)
                except (TypeError, ValueError):
                    # ignore non-numeric noise if present
                    continue
            return out
        except json.JSONDecodeError:
            return {}
    return {}


def save_memory(mem: Dict[str, float]) -> None:
    """Persist memory so the next loop can nudge changes toward what worked."""
    MEM_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEM_FILE.write_text(json.dumps(mem, indent=2), encoding="utf-8")


def prompt_with_memory() -> str:
    """Compose the LLM prompt, appending best-known parameters if any."""
    mem = load_memory()
    if not mem:
        return BASE_PROMPT
    tail = (
        f"\nPrevious best minimal_roi_0={mem.get('best_min_roi_0')}, "
        f"stoploss={mem.get('best_stoploss')}, "
        f"profit_total={mem.get('best_profit_total')}.\n"
        "Make a small change from this baseline."
    )
    return BASE_PROMPT + tail


def llm_tweak() -> Dict[str, float]:
    """Ask the model for small numeric tweaks and sanitize the response.

    We call /v1/chat/completions, extract the first JSON blob, and
    clamp values to sensible/safe ranges so accidental wild outputs
    won't break backtests.
    """
    url: str = f"{OPENAI_BASE}/chat/completions"
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json",
    }
    payload: ChatCompletionPayload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt_with_memory(),
            }
        ],
        "temperature": 0.6,
        "top_p": 0.95,
        "max_tokens": 128,
    }
    try:
        resp = requests.post(
            url, headers=headers, data=json.dumps(payload), timeout=120
        )
        resp.raise_for_status()
        resp_json: ChatCompletionResponse = cast(ChatCompletionResponse, resp.json())
        content: str = resp_json["choices"][0]["message"]["content"]
    except requests.RequestException:
        return {"minimal_roi_0": 0.012, "stoploss": -0.11}
    except (KeyError, IndexError, TypeError):
        return {"minimal_roi_0": 0.012, "stoploss": -0.11}

    # Grab the first JSON-looking block in the output.
    match = re.search(r"\{.*?\}", content, re.S)
    if not match:
        return {"minimal_roi_0": 0.012, "stoploss": -0.11}

    try:
        data = json.loads(match.group(0))
        m0 = float(cast(Dict[str, Any], data).get("minimal_roi_0", 0.012))
        sl = float(cast(Dict[str, Any], data).get("stoploss", -0.11))
    except (json.JSONDecodeError, TypeError, ValueError):
        return {"minimal_roi_0": 0.012, "stoploss": -0.11}

    # Clamp to guardrails so we only try small, plausible changes.
    m0 = max(0.001, min(m0, 0.10))
    sl = max(-0.30, min(sl, -0.01))
    return {"minimal_roi_0": m0, "stoploss": sl}


def ensure_strategy() -> None:
    """Create a baseline strategy (and package init) if missing.

    This guarantees a valid import path and a file we can patch with
    regex.
    """
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    init_py = STRATEGY_DIR / "__init__.py"
    if not init_py.exists():
        init_py.write_text("", encoding="utf-8")
    if not STRATEGY_FILE.exists():
        STRATEGY_FILE.write_text(BASELINE_STRATEGY, encoding="utf-8")


def mutate_strategy(min_roi_0: float, stoploss: float) -> None:
    """Patch minimal_roi and stoploss in-place using narrow regexes.

    The patterns are intentionally strict to avoid touching unrelated
    code.
    """
    txt = STRATEGY_FILE.read_text(encoding="utf-8")
    txt = re.sub(
        r"minimal_roi\s*=\s*\{[^}]*\}",
        f'minimal_roi = {{"0": {min_roi_0:.3f}}}',
        txt,
        flags=re.S,
    )
    txt = re.sub(
        r"stoploss\s*=\s*[-]?\d+\.\d+",
        f"stoploss = {stoploss:.2f}",
        txt,
    )
    STRATEGY_FILE.write_text(txt, encoding="utf-8")


def ensure_data(freqtrade_bin: str, config: str, timeframe: str) -> None:
    """Fetch candles for the timeframe if missing (best-effort, non-fatal)."""
    cmd: List[str] = [freqtrade_bin, "download-data", "-c", config, "-t", timeframe]
    subprocess.run(cmd, check=False)


def backtest(
    freqtrade_bin: str,
    config: str,
    timeframe: str,
    timerange: str,
    loop_id: int,
) -> Path:
    """Run a short backtest and export per-loop trades to CSV.

    We pass --strategy-path so Freqtrade picks up our local strategy
    folder reliably.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    export_path: Path = RESULTS_DIR / f"trades_loop_{loop_id}.csv"
    cmd: List[str] = [
        freqtrade_bin,
        "backtesting",
        "-c",
        config,
        "--strategy",
        STRATEGY_NAME,
        "--strategy-path",
        str(STRATEGY_DIR),
        "--timeframe",
        timeframe,
        "--timerange",
        timerange,
        "--export",
        "trades",
        "--export-filename",
        str(export_path),
        "--cache",
        "none",
    ]
    print("[BT]", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        # Print end of report for quick feedback without scrolling.
        print(proc.stdout[-1500:])
    except subprocess.CalledProcessError as exc:
        # On failure, show tails to aid debugging, then continue.
        print(exc.stdout[-1200:])
        print(exc.stderr[-800:])
    return export_path


def summarize_trades(csv_path: Path) -> Dict[str, float]:
    """Aggregate the trades CSV into a compact score dict.

    We avoid heavy parsing and just compute totals and a simple win rate.
    """
    if not csv_path.exists():
        return {
            "trades": 0.0,
            "profit_abs_sum": 0.0,
            "profit_ratio_sum": 0.0,
            "win_rate": 0.0,
        }

    wins = 0
    total = 0
    profit_abs_sum = 0.0
    profit_ratio_sum = 0.0

    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            try:
                pr = float(row.get("profit_ratio", 0.0))
                pa = float(row.get("profit_abs", 0.0))
            except (TypeError, ValueError):
                pr, pa = 0.0, 0.0
            profit_ratio_sum += pr
            profit_abs_sum += pa
            if pr > 0:
                wins += 1

    win_rate = (wins / total) * 100.0 if total else 0.0
    return {
        "trades": float(total),
        "profit_abs_sum": profit_abs_sum,
        "profit_ratio_sum": profit_ratio_sum,
        "win_rate": win_rate,
    }


def append_log(
    loop_id: int,
    min_roi_0: float,
    stoploss: float,
    metrics: Dict[str, float],
) -> None:
    """Append a single row to the learning log CSV.

    Creates header on first write.
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_file = not LOG_FILE.exists()

    with LOG_FILE.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(
                [
                    "loop",
                    "minimal_roi_0",
                    "stoploss",
                    "trades",
                    "profit_abs_sum",
                    "profit_ratio_sum",
                    "win_rate",
                    "ts",
                ]
            )
        writer.writerow(
            [
                loop_id,
                round(min_roi_0, 6),
                round(stoploss, 6),
                int(metrics.get("trades", 0)),
                round(metrics.get("profit_abs_sum", 0.0), 8),
                round(metrics.get("profit_ratio_sum", 0.0), 8),
                round(metrics.get("win_rate", 0.0), 4),
                int(time.time()),
            ]
        )


def maybe_update_memory(
    min_roi_0: float,
    stoploss: float,
    metrics: Dict[str, float],
) -> None:
    """If this loop improved total absolute profit, record it as best so far."""
    mem = load_memory()
    curr = metrics.get("profit_abs_sum", 0.0)
    prev = float(mem.get("best_profit_total", float("-inf")))
    if curr > prev:
        mem.update(
            {
                "best_min_roi_0": float(min_roi_0),
                "best_stoploss": float(stoploss),
                "best_profit_total": float(curr),
                "best_updated_ts": int(time.time()),
            }
        )
        save_memory(mem)


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the self-improvement loop.

    It ensures data/strategy exist, queries the model for tweaks,
    backtests, logs results, and saves a memory to bias the next
    iteration.
    """
    parser = argparse.ArgumentParser(description="self loop agent")
    parser.add_argument("--config", default="user_data/config.json")
    parser.add_argument("--max-loops", type=int, default=1)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--timerange", default="20240601-20240901")
    args = parser.parse_args(argv)

    freqtrade_bin = detect_freqtrade()
    ensure_strategy()
    ensure_data(freqtrade_bin, args.config, args.timeframe)

    for i in range(1, args.max_loops + 1):
        print(f"\n=== LOOP {i}/{args.max_loops} ===")

        # Model proposes small parameter changes
        tweak = llm_tweak()
        m0 = float(tweak.get("minimal_roi_0", 0.012))
        sl = float(tweak.get("stoploss", -0.11))
        print(f"[LLM] Proposed minimal_roi[0]={m0:.3f}, stoploss={sl:.2f}")

        # Apply changes to the strategy source file
        mutate_strategy(m0, sl)

        csv_path = backtest(
            freqtrade_bin,
            args.config,
            args.timeframe,
            args.timerange,
            i,
        )
        # Quick numeric summary of the backtest
        metrics = summarize_trades(csv_path)
        # Persistent per-loop log
        append_log(i, m0, sl, metrics)
        # Keep best params so far
        maybe_update_memory(m0, sl, metrics)
        # Small pause so logs/files feel ordered
        time.sleep(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
