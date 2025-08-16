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

# Import MCPMemoryClient with fallback
try:
    from ..utils.mcp_memory_client import MCPMemoryClient
except ImportError:
    print("[WARN] MCP Memory Client not available - using fallback")
    class MCPMemoryClient:
        def get(self, key): return []
        def put(self, key, value): return True

DEFAULT_MODEL = os.getenv("AGENT_MODEL", "meta-llama-3.1-8b-instruct")
OPENAI_BASE = os.getenv("OPENAI_API_BASE", "http://192.168.0.17:1228/v1").rstrip("/")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")

STRATEGY_NAME = "SimpleAlwaysBuySell"
STRATEGY_DIR = Path("strategies")
STRATEGY_FILE = STRATEGY_DIR / f"{STRATEGY_NAME}.py"

BASELINE_STRATEGY = '''from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import pandas as pd
import talib.abstract as ta

class SimpleAlwaysBuySell(IStrategy):
    """
    Guaranteed-to-Trade Strategy
    
    This strategy is designed to ALWAYS generate trades for agent learning,
    regardless of market conditions. It uses multiple entry/exit signals
    to ensure consistent trading activity.
    """
    
    # Conservative but guaranteed parameters
    minimal_roi = {"0": 0.015}  # 1.5% target
    stoploss = -0.08           # -8% stop loss
    timeframe = "1h"
    startup_candle_count = 5   # Minimal startup
    
    # Position management
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Simple indicators for decision making
        dataframe['sma_fast'] = ta.SMA(dataframe, timeperiod=3)
        dataframe['sma_slow'] = ta.SMA(dataframe, timeperiod=10)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=6)
        
        # Volume indicators
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=10)
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Multiple entry conditions to guarantee trades:
        1. Always buy on first few candles
        2. Buy when price moves (any direction)
        3. Buy on volume spikes
        4. Buy on RSI extremes (both high and low)
        """
        conditions = []
        
        # Condition 1: Always buy in first few candles (guaranteed start)
        dataframe.loc[:5, 'enter_long'] = 1
        
        # Condition 2: Price movement triggers (catches trends)
        dataframe.loc[
            (dataframe['close'] > dataframe['close'].shift(1) * 1.001) |  # 0.1% up
            (dataframe['close'] < dataframe['close'].shift(1) * 0.999),   # 0.1% down
            'enter_long'
        ] = 1
        
        # Condition 3: Volume spike (activity indicator)
        dataframe.loc[
            dataframe['volume'] > dataframe['volume_sma'] * 1.2,  # 20% above average
            'enter_long'
        ] = 1
        
        # Condition 4: RSI extreme conditions (catches reversals)
        dataframe.loc[
            (dataframe['rsi'] < 25) |  # Oversold
            (dataframe['rsi'] > 75),   # Overbought
            'enter_long'
        ] = 1
        
        # Condition 5: SMA crossover (trend changes)
        dataframe.loc[
            (dataframe['sma_fast'] > dataframe['sma_slow']) |
            (dataframe['sma_fast'] < dataframe['sma_slow']),
            'enter_long'
        ] = 1
        
        # Condition 6: Regular interval trading (every N candles)
        interval_mask = (dataframe.index % 6 == 0)  # Every 6 hours
        dataframe.loc[interval_mask, 'enter_long'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Multiple exit conditions to ensure position turnover:
        1. Exit after holding for a few candles
        2. Exit on opposite RSI extreme
        3. Exit on volume drop
        4. Regular exit intervals
        """
        
        # Condition 1: Time-based exit (ensure turnover)
        time_exit_mask = (dataframe.index % 4 == 3)  # Every 4th candle
        dataframe.loc[time_exit_mask, 'exit_long'] = 1
        
        # Condition 2: RSI mean reversion
        dataframe.loc[
            (dataframe['rsi'] > 50) & (dataframe['rsi'] < 60),  # Middle RSI
            'exit_long'
        ] = 1
        
        # Condition 3: Volume normalization
        dataframe.loc[
            dataframe['volume'] < dataframe['volume_sma'] * 0.8,  # Below average volume
            'exit_long'
        ] = 1
        
        # Condition 4: Price stagnation
        price_change = abs(dataframe['close'] - dataframe['close'].shift(1)) / dataframe['close'].shift(1)
        dataframe.loc[
            price_change < 0.002,  # Less than 0.2% movement
            'exit_long'
        ] = 1
        
        # Condition 5: Regular exit intervals (guaranteed liquidity)
        regular_exit_mask = (dataframe.index % 8 == 7)  # Every 8th candle
        dataframe.loc[regular_exit_mask, 'exit_long'] = 1
        
        return dataframe
'''

DEFAULT_PROMPT = (
    "You are a JSON API that responds only with valid JSON. Your task is to generate Freqtrade trading parameters.\n\n"
    "STRICT REQUIREMENTS:\n"
    "1. Respond with ONLY a single line of JSON\n"
    '2. Use exactly this format: {"minimal_roi_0": <number>, "stoploss": <number>}\n'
    "3. minimal_roi_0 must be a float between 0.005 and 0.050 (0.5% to 5%)\n"
    "4. stoploss must be a float between -0.20 and -0.03 (-20% to -3%)\n"
    "5. NO explanations, NO markdown, NO extra text\n\n"
    'Example valid response: {"minimal_roi_0": 0.015, "stoploss": -0.08}\n\n'
    "Focus on realistic, conservative parameters for walk-forward validation.\n"
    "Generate trading parameters now:"
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
    system_prompt = "You are a JSON API. Follow instructions exactly and respond only with valid JSON."
    payload: dict[str, object] = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "top_p": 0.95,
        "max_tokens": 128,
    }
    
    os.makedirs("user_data", exist_ok=True)
    with open("user_data/llm_payload.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
        resp.raise_for_status()
        content: str = resp.json()["choices"][0]["message"]["content"]
        
        with open("user_data/llm_raw_response.log", "a", encoding="utf-8") as f:
            f.write(f"Prompt: {prompt}\nResponse: {content}\n\n")
    except requests.RequestException:
        with open("user_data/llm_raw_response.log", "a", encoding="utf-8") as f:
            f.write(f"Prompt: {prompt}\nResponse: <RequestException>\n\n")
        return {"minimal_roi_0": 0.015, "stoploss": -0.08}
    
    match = re.search(r"\{.*?\}", content, re.S)
    if not match:
        return {"minimal_roi_0": 0.015, "stoploss": -0.08}
    
    try:
        data = json.loads(match.group(0))
        m0 = float(data.get("minimal_roi_0", 0.015))
        sl = float(data.get("stoploss", -0.08))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {"minimal_roi_0": 0.015, "stoploss": -0.08}
    
    # Realistic ranges for walk-forward validation
    m0 = max(0.005, min(m0, 0.050))  # 0.5% to 5%
    sl = max(-0.20, min(sl, -0.03))   # -20% to -3%
    return {"minimal_roi_0": m0, "stoploss": sl}

def _ensure_strategy_exists() -> None:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    init_py = STRATEGY_DIR / "__init__.py"
    if not init_py.exists():
        init_py.write_text("", encoding="utf-8")
    
    # Always regenerate the strategy with latest baseline
    print(f"[STRATEGY] Creating guaranteed-to-trade strategy: {STRATEGY_FILE}")
    STRATEGY_FILE.write_text(BASELINE_STRATEGY, encoding="utf-8")

def _mutate_strategy(min_roi_0: float, stoploss: float) -> None:
    txt = STRATEGY_FILE.read_text(encoding="utf-8")
    txt = re.sub(
        r"minimal_roi\s*=\s*\{[^}]*\}",
        f'minimal_roi = {{"0": {min_roi_0:.3f}}}',
        txt, flags=re.S,
    )
    txt = re.sub(r"stoploss\s*=\s*[-]?\d+\.\d+", f"stoploss = {stoploss:.2f}", txt)
    STRATEGY_FILE.write_text(txt, encoding="utf-8")

def _download_data(freqtrade_bin: str, config: str, timeframe: str, verbosity: int = 0) -> None:
    cmd = [freqtrade_bin, "download-data", "-c", config, "-t", timeframe]
    if verbosity >= 1:
        cmd.append("-v")
    subprocess.run(cmd, check=False)

def _backtest(freqtrade_bin: str, config: str, strategy: str, timeframe: str, timerange: str, verbosity: int = 0, export_trades: bool = False) -> bool:
    cmd = [
        freqtrade_bin, "backtesting", "-c", config, "--strategy", strategy,
        "--strategy-path", str(STRATEGY_DIR), "--timeframe", timeframe,
        "--timerange", timerange, "--cache", "none",
    ]
    
    if verbosity >= 1:
        cmd.append("-v")
    if export_trades:
        cmd.extend(["--export", "trades"])
    
    print("[BT]", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
        print(proc.stdout[-1500:])
        
        # Extract summary
        summary_lines: list[str] = []
        in_summary = False
        for line in proc.stdout.splitlines():
            if "STRATEGY SUMMARY" in line:
                in_summary = True
            if in_summary:
                summary_lines.append(line)
                if line.strip().startswith("└"):
                    break
        
        if not summary_lines:
            summary_lines = proc.stdout.splitlines()[-20:]
        
        os.makedirs("user_data", exist_ok=True)
        with open("user_data/backtest_result.log", "w", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")
        
        return True
    except subprocess.CalledProcessError as exc:
        print(exc.stdout[-1200:])
        print(exc.stderr[-800:])
        return False

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="self loop agent")
    parser.add_argument("--config", default="user_data/config.json")
    parser.add_argument("--max-loops", type=int, default=5)
    parser.add_argument("--spec", default=DEFAULT_PROMPT)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--timerange", default=os.getenv("AGENT_TIMERANGE", "20250101-"))
    parser.add_argument("-v", "--verbose", action="count", default=2)
    parser.add_argument("--export-trades", action="store_true", default=True)
    parser.add_argument("--disable-memory", action="store_true", default=False)  # Default to enabled
    
    args = parser.parse_args(argv)
    freqtrade_bin = _detect_freqtrade()
    _ensure_strategy_exists()
    _download_data(freqtrade_bin, args.config, args.timeframe, args.verbose)
    
    if not args.disable_memory:
        mcp = MCPMemoryClient()
        
        # Load existing memories
        stm_raw = mcp.get("short_term_memory")
        ltm_raw = mcp.get("long_term_memory")
        backtest_history = mcp.get("backtest_history") or []
        
        short_term_memory = stm_raw if isinstance(stm_raw, list) else []
        long_term_memory = ltm_raw if isinstance(ltm_raw, list) else []
        
        print(f"[MEMORY] Loaded {len(short_term_memory)} short-term and {len(long_term_memory)} long-term memories")
        print(f"[MEMORY] Loaded {len(backtest_history)} backtest results")
    else:
        print("[INFO] Memory features disabled - using session-only memory")
        mcp = None
        short_term_memory = []
        long_term_memory = []
        backtest_history = []
    
    for i in range(1, args.max_loops + 1):
        print(f"\n=== LOOP {i}/{args.max_loops} ===")
        
        if short_term_memory:
            prompt = (
                f"You are improving a Freqtrade strategy called {STRATEGY_NAME}.\n"
                "Only suggest SMALL numeric tweaks to either or both of:\n"
                '- minimal_roi (dict like {"0": float})\n'
                "- stoploss (negative float between -0.30 and -0.01).\n\n"
                "Return STRICT JSON only with keys: minimal_roi_0 (float), stoploss (float).\n"
                f"Short-term memory:\n" + "\n---\n".join([str(x) for x in short_term_memory[-3:]])
            )
        else:
            prompt = args.spec
        
        rec = _llm_chat_json(prompt)
        m0 = float(rec.get("minimal_roi_0", 0.015))
        sl = float(rec.get("stoploss", -0.08))
        
        print(f"[LLM] Proposed minimal_roi[0]={m0:.3f}, stoploss={sl:.2f}")
        _mutate_strategy(m0, sl)
        
        ok = _backtest(freqtrade_bin, args.config, STRATEGY_NAME, args.timeframe, args.timerange, args.verbose, args.export_trades)
        
        # Update memory with results
        loop_result = {
            "loop": i,
            "parameters": {"minimal_roi_0": m0, "stoploss": sl},
            "backtest_success": ok,
            "timestamp": time.time()
        }
        
        # Add to short-term memory (recent results)
        short_term_memory.append(f"Loop {i}: roi={m0:.3f}, stoploss={sl:.2f}, success={ok}")
        
        # Keep only last 10 short-term memories
        if len(short_term_memory) > 10:
            short_term_memory = short_term_memory[-10:]
        
        # Add to backtest history
        backtest_history.append(loop_result)
        
        # Update persistent memory if enabled
        if mcp:
            mcp.put("short_term_memory", short_term_memory)
            mcp.put("backtest_history", backtest_history)
            
            # Add to long-term memory if successful
            if ok:
                long_term_memory.append(f"Successful config: roi={m0:.3f}, stoploss={sl:.2f}")
                mcp.put("long_term_memory", long_term_memory)
        
        if not ok:
            print("[WARN] Backtest failed; continuing.")
        else:
            print(f"[SUCCESS] Loop {i} completed successfully")
        
        time.sleep(1)
    
    print(f"\n[SUMMARY] Completed {args.max_loops} loops with memory {'enabled' if not args.disable_memory else 'disabled'}")
    if mcp:
        final_memories = len(mcp.get("short_term_memory") or [])
        final_history = len(mcp.get("backtest_history") or [])
        print(f"[MEMORY] Final state: {final_memories} memories, {final_history} backtest records")
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
