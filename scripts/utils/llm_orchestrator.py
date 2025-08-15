"""Module: llm_orchestrator.py — auto-generated docstring for flake8 friendliness."""

import subprocess
import time

import requests

# LM Studio API endpoint (adjust if needed)
LLM_API = (
    "http://192.168.0.27:1234/v1/chat/completions"  # Use your actual LM Studio endpoint
)

PROMPT = (
    "You are an expert Freqtrade research orchestrator. "
    "Run the Freqtrade agent loop for 5 cycles using a guaranteed-trade baseline (AlwaysBuyStrategy or AlwaysSellStrategy) for BTC/USDT, 1h timeframe. "
    "Each loop, generate or mutate the strategy logic to increase trade quality, diversity, and profit. "
    "Incorporate at least one new indicator, risk management, or volatility adaptation per cycle. "
    "For each patch, explain the reasoning and expected effect. "
    "Use recent trade logs and results (provided below) to inform improvements. "
    "Log all trades and results for ML. After completion, summarize the results in a clear, human-readable format, and suggest next steps."
)

HEADERS = {"Content-Type": "application/json"}


def run_orchestrator_loop(max_retries=3):
    summary = None
    for attempt in range(max_retries):
        try:
            print("[LLM] Sending orchestration prompt to LM Studio...")
            payload = {
                "model": "qwen2.5-coder-7b-instruct",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI agent."},
                    {"role": "user", "content": PROMPT},
                ],
                "temperature": 0.2,
            }
            resp = requests.post(LLM_API, json=payload, headers=HEADERS, timeout=60)
            if resp.status_code != 200:
                print(f"[LLM] LLM API returned status {resp.status_code}: {resp.text}")
                # Try minimal payload if error is 400
                if resp.status_code == 400:
                    print("[LLM] Retrying with minimal payload...")
                    payload_min = {
                        "model": "qwen2.5-coder-7b-instruct",
                        "messages": [{"role": "user", "content": PROMPT}],
                    }
                    resp2 = requests.post(
                        LLM_API, json=payload_min, headers=HEADERS, timeout=60
                    )
                    resp2.raise_for_status()
                    llm_response = resp2.json()
                else:
                    resp.raise_for_status()
                    llm_response = resp.json()
            else:
                llm_response = resp.json()
            generated = (
                llm_response.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            print("[LLM] LLM response:")
            print(generated)
        except Exception as e:
            print(f"[LLM] Error communicating with LM Studio: {e}")
            if attempt < max_retries - 1:
                print(
                    f"[AGENT] Retrying LLM orchestration (attempt {attempt + 2}/{max_retries})..."
                )
                time.sleep(5)
                continue
            else:
                print("[AGENT] Max retries reached. Exiting.")
                return

        # Step 2: Execute agent loop (if LLM suggests, or always)
        print("[AGENT] Running agent loop for 5 cycles...")
        cmd = [
            "python",
            "-m",
            "agents.self_loop_agent",
            "--spec",
            "Start with a simple guaranteed-trade strategy (SimpleAlwaysBuySell) for BTC/USDT, 1h timeframe. Each loop, mutate or improve the strategy logic to increase trade quality, diversity, and profit. Log all trades and results for ML. Use clear comments and robust logic.",
            "--config",
            "config.json",
            "--max-loops",
            "5",
        ]
        agent_log = []
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in proc.stdout:
            print(line, end="")
            agent_log.append(line)
        proc.wait()

        # Step 3: Summarize results (send logs back to LLM for summary)
        summary_prompt = (
            "Here are the logs/results from the Freqtrade agent loop. "
            "Please summarize the results, highlight any improvements, and suggest next steps.\n\n"
            + "".join(agent_log[-200:])  # last 200 lines
        )
        summary_payload = {
            "model": "qwen2.5-coder-7b-instruct",
            "messages": [
                {"role": "system", "content": "You are a helpful AI agent."},
                {"role": "user", "content": summary_prompt},
            ],
            "temperature": 0.2,
        }
        try:
            print("[LLM] Sending agent logs/results to LM Studio for summary...")
            resp = requests.post(
                LLM_API, json=summary_payload, headers=HEADERS, timeout=120
            )
            resp.raise_for_status()
            summary_response = resp.json()
            summary = (
                summary_response.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            print("[LLM] LLM summary:")
            print(summary)
            break  # Success, exit loop
        except Exception as e:
            print(f"[LLM] Error getting summary from LM Studio: {e}")
            if attempt < max_retries - 1:
                print(
                    f"[AGENT] Retrying summary step (attempt {attempt + 2}/{max_retries})..."
                )
                time.sleep(5)
                continue
            else:
                print("[AGENT] Max retries reached. Exiting.")
                return


if __name__ == "__main__":
    run_orchestrator_loop(max_retries=3)
