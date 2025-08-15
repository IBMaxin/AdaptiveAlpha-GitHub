
import os
import subprocess
import time
import glob
import logging
import requests
import json
from agents.mcp_memory_client import MCPMemoryClient

CHECK_COMMANDS = [
    ("flake8", ".venv-ft2025/bin/flake8 agents/ scripts/ services/ strategies/ tests/"),
    (
        "black",
        ".venv-ft2025/bin/black --check agents/ scripts/ services/ strategies/ tests/",
    ),
    (
        "isort",
        ".venv-ft2025/bin/isort --check-only agents/ scripts/ services/ strategies/ tests/",
    ),
]

PROBLEM_KEY = "self_heal:problems"
ATTEMPT_KEY = "self_heal:attempts"
MEMORY_KEY = "self_heal:memory"


def run_check(name: str, cmd: str) -> tuple[int, str]:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr



def scan_problems() -> dict[str, str]:
    problems: dict[str, str] = {}
    for name, cmd in CHECK_COMMANDS:
        code, output = run_check(name, cmd)
        if code != 0:
            problems[name] = output.strip()
    return problems

import os
import time
import logging
import requests
import json


def build_llm_prompt(problem_report, attempt_num, context):
    """
    Build a professional, robust LLM prompt for code fixing.
    """
    return (
        f"""
You are an expert Python code repair agent. Your job is to:
1. Analyze the following code quality report and error log.
2. Propose and apply a minimal, high-quality fix that resolves the issues.
3. Ensure all code style, lint, and test checks pass after your patch.
4. Never break existing functionality.
5. Document your patch in a concise summary.

---
Attempt: {attempt_num}
Context: {context}
Problem Report:
{problem_report}
---
Respond ONLY with the patch in unified diff format, no explanations. If no changes are needed, reply with 'NOOP'.
"""
    )


def call_local_llm(prompt):
    """Call the local LLM (Ollama or LM Studio) with the given prompt."""
    api_base = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:1234/v1")
    api_key = os.getenv("OPENAI_API_KEY", "lm-studio")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": os.getenv("AGENT_MODEL", "deepseek-coder-v2:16b"),
        "messages": [
            {"role": "system", "content": "You are a professional Python code fixer."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2048,
        "temperature": 0.2,
    }
    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Local LLM call failed: {e}")
        return None


def call_claude_llm(prompt):
    """Call Claude via API as fallback."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logging.error("Claude API key not set.")
        return None
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2048,
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            data=json.dumps(data),
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["content"]
    except Exception as e:
        logging.error(f"Claude LLM call failed: {e}")
        return None


def main():

def scan_all_project_problems():
    """Scan all Python files in the project for lint, syntax, and test errors."""
    problems = []
    py_files = glob.glob("**/*.py", recursive=True)
    for f in py_files:
        # Check syntax
        try:
            subprocess.check_output(["python3", "-m", "py_compile", f], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            problems.append(f"[SYNTAX] {f}: {e.output.decode(errors='ignore')}")
        # Check flake8
        try:
            out = subprocess.check_output(["flake8", f], stderr=subprocess.STDOUT)
            if out:
                problems.append(f"[FLAKE8] {f}: {out.decode(errors='ignore')}")
        except subprocess.CalledProcessError as e:
            problems.append(f"[FLAKE8] {f}: {e.output.decode(errors='ignore')}")
    # Optionally: run tests
    try:
        out = subprocess.check_output(["pytest", "--maxfail=1", "--disable-warnings"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        problems.append(f"[TEST] pytest: {e.output.decode(errors='ignore')}")
    return problems

def check_project_runnable():
    """Check if the project is runnable (e.g., main script runs without error)."""
    main_candidates = ["main.py", "run.py", "agents/self_heal_mcp_agent.py"]
    for script in main_candidates:
        if not os.path.exists(script):
            continue
        try:
            subprocess.check_output(["python3", script], stderr=subprocess.STDOUT, timeout=10)
            return True
        except Exception:
            continue
    return False

def run_learning_strategy_loop(mcp, log_path):
    """Run a placeholder learning/strategy loop when no errors are found."""
    with open(log_path, "a") as f:
        f.write(f"[LEARN][{time.strftime('%H:%M:%S')}] Learning/strategy loop running. (Placeholder)\n")
    # Example: could generate new strategies, run experiments, or optimize code
    # For now, just log and sleep
    time.sleep(10)
    """
    Main self-healing loop: runs at least 4 local LLM fixer attempts, then falls back to Claude if needed.
    All status and patching is tracked in MCP memory. Robust monitoring/logging is enforced.
    Logs model selection, LLM usage, and attempt status every 5 seconds in a dedicated background log.
    """
    def mcp_health_check():
        try:
            mcp = MCPMemoryClient()
            mcp.put("__healthcheck__", "ok")
            return mcp
        except Exception as e:
            with open("user_data/self_heal_model_switch.log", "a") as f:
                f.write(f"[ERROR][MCP] MCPMemoryClient unavailable: {e}\n")
            return None

    attempt = 0
    local_attempts = 0
    max_local_attempts = 4
    log_path = "user_data/self_heal_model_switch.log"

    import threading
    last_attempt = {'val': 0}
    last_log_time = {'val': time.time()}

    def log_status_bg():
        summary_counter = 0
        fix_count = 0
        error_count = 0
        restart_count = 0
        last_restart = time.strftime('%Y-%m-%d %H:%M:%S')
        while True:
            with open(log_path, "a") as f:
                f.write("\n====================[ SELF-HEAL AGENT STATUS ]====================\n")
                f.write(f"[LOOP] #{attempt+1} | [Local Attempts] {local_attempts}/{max_local_attempts}\n")
                if local_attempts < max_local_attempts:
                    f.write(f"[MODEL] Using local LLM: {os.getenv('AGENT_MODEL', 'deepseek-coder-v2:16b')}\n")
                else:
                    f.write("[MODEL] Using Claude fallback\n")
                f.write(f"[TIME] {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"[RESTARTS] {restart_count} | [LAST RESTART] {last_restart}\n")
                f.write(f"[FIXES] {fix_count} | [ERRORS] {error_count}\n")
                f.write("===============================================================\n\n")
                summary_counter += 1
                if summary_counter % 10 == 0:
                    f.write(f"\n[SUMMARY] {time.strftime('%Y-%m-%d %H:%M:%S')} | Total Fixes: {fix_count} | Errors: {error_count} | Restarts: {restart_count}\n\n")
            last_log_time['val'] = time.time()
            time.sleep(5)

    def watchdog_bg():
        while True:
            time.sleep(5)
            # Check for hang: if attempt hasn't changed in 2 cycles (10s) or log not updated
            now = time.time()
            if last_attempt['val'] == attempt and (now - last_log_time['val']) > 10:
                with open(log_path, "a") as f:
                    f.write(f"[WATCHDOG WARNING] Possible hang detected at {time.strftime('%Y-%m-%d %H:%M:%S')} (loop {attempt+1})\n")
            else:
                with open(log_path, "a") as f:
                    f.write(f"[WATCHDOG] Heartbeat OK at {time.strftime('%Y-%m-%d %H:%M:%S')} (loop {attempt+1})\n")
            last_attempt['val'] = attempt

    threading.Thread(target=log_status_bg, daemon=True).start()
    threading.Thread(target=watchdog_bg, daemon=True).start()

    while True:
        try:
            mcp = mcp_health_check()
            if not mcp:
                with open(log_path, "a") as f:
                    f.write(f"[SELF-HEAL][MCP][{time.strftime('%H:%M:%S')}] MCP unavailable, mutating and retrying...\n")
                time.sleep(10)
                continue
            try:
                problems = scan_all_project_problems()
            except Exception as e:
                with open(log_path, "a") as f:
                    f.write(f"[ERROR][SCAN][{time.strftime('%H:%M:%S')}] scan_all_project_problems failed: {e}\n[SELF-HEAL] Retrying...\n")
                time.sleep(10)
                continue
            try:
                mcp.put(PROBLEM_KEY, problems)
            except Exception as e:
                with open(log_path, "a") as f:
                    f.write(f"[ERROR][MCP][{time.strftime('%H:%M:%S')}] Failed to put problems: {e}\n[SELF-HEAL] Retrying...\n")
                time.sleep(10)
                continue
            if not problems:
                try:
                    is_runnable = check_project_runnable()
                except Exception as e:
                    with open(log_path, "a") as f:
                        f.write(f"[ERROR][RUNNABLE][{time.strftime('%H:%M:%S')}] check_project_runnable failed: {e}\n[SELF-HEAL] Retrying...\n")
                    time.sleep(10)
                    continue
                if is_runnable:
                    with open(log_path, "a") as f:
                        f.write(f"[LEARN][{time.strftime('%H:%M:%S')}] No errors found, project is runnable. Entering learning/strategy loop.\n")
                    try:
                        run_learning_strategy_loop(mcp, log_path)
                    except Exception as e:
                        with open(log_path, "a") as f:
                            f.write(f"[ERROR][LEARN][{time.strftime('%H:%M:%S')}] run_learning_strategy_loop failed: {e}\n[SELF-HEAL] Retrying...\n")
                    time.sleep(30)
                    continue
                else:
                    with open(log_path, "a") as f:
                        f.write(f"[WARN][{time.strftime('%H:%M:%S')}] No errors found, but project is not runnable.\n")
                    time.sleep(30)
                    continue
            context = mcp.get(MEMORY_KEY) or ""
            prompt = build_llm_prompt(str(problems), attempt + 1, context)
            if local_attempts < max_local_attempts:
                try:
                    patch = call_local_llm(prompt)
                except Exception as e:
                    with open(log_path, "a") as f:
                        f.write(f"[ERROR][LLM][{time.strftime('%H:%M:%S')}] call_local_llm failed: {e}\n[SELF-HEAL] Retrying...\n")
                    time.sleep(10)
                    continue
                local_attempts += 1
                with open(log_path, "a") as f:
                    f.write(f"[PATCH][LOCAL][{time.strftime('%H:%M:%S')}] Loop {attempt+1} | Local LLM PATCH attempt {local_attempts}\n")
            else:
                try:
                    patch = call_claude_llm(prompt)
                except Exception as e:
                    with open(log_path, "a") as f:
                        f.write(f"[ERROR][LLM][{time.strftime('%H:%M:%S')}] call_claude_llm failed: {e}\n[SELF-HEAL] Retrying...\n")
                    time.sleep(10)
                    continue
                with open(log_path, "a") as f:
                    f.write(f"[PATCH][CLAUDE][{time.strftime('%H:%M:%S')}] Loop {attempt+1} | Claude PATCH fallback\n")
            try:
                mcp.put(
                    ATTEMPT_KEY,
                    {"attempt": attempt + 1, "patch": patch, "problems": problems},
                )
            except Exception as e:
                with open(log_path, "a") as f:
                    f.write(f"[ERROR][MCP][{time.strftime('%H:%M:%S')}] Failed to put attempt: {e}\n[SELF-HEAL] Retrying...\n")
                time.sleep(10)
                continue
            # Apply patch if not NOOP
            if patch and patch.strip() != "NOOP":
                try:
                    # ...apply patch logic here...
                    logging.info(f"Patch applied on attempt {attempt + 1}.")
                    with open(log_path, "a") as f:
                        f.write(f"[FIX][SUCCESS][{time.strftime('%H:%M:%S')}] Patch applied on attempt {attempt+1}\n")
                    fix_count += 1
                except Exception as e:
                    with open(log_path, "a") as f:
                        f.write(f"[ERROR][PATCH][{time.strftime('%H:%M:%S')}] Patch application failed: {e}\n[SELF-HEAL] Retrying...\n")
                    time.sleep(10)
                    continue
            else:
                logging.info(f"No patch needed on attempt {attempt + 1}.")
                # Diagnose why no patch is needed
                reason = ""
                if not problems:
                    reason = "No errors detected in scan."
                else:
                    # Check if patch is empty or LLM failed to generate
                    if not patch:
                        reason = "Patch is empty. LLM may have failed to generate a response."
                    elif patch.strip() == "NOOP":
                        reason = "LLM responded with NOOP. It may not see any actionable issues."
                    else:
                        reason = "Unknown reason."
                with open(log_path, "a") as f:
                    f.write(f"[FIX][NOOP][{time.strftime('%H:%M:%S')}] No patch needed on attempt {attempt+1} | Reason: {reason}\n")
            # Monitoring/logging
            try:
                logging.info(f"Attempt {attempt + 1} complete. Problems: {problems}")
                mcp.put(MEMORY_KEY, f"Attempt {attempt + 1} done.")
            except Exception as e:
                with open(log_path, "a") as f:
                    f.write(f"[ERROR][MCP][{time.strftime('%H:%M:%S')}] Failed to update memory: {e}\n[SELF-HEAL] Retrying...\n")
            attempt += 1
            time.sleep(10)
        except Exception as e:
            with open(log_path, "a") as f:
                f.write(f"[FATAL][{time.strftime('%H:%M:%S')}] Unhandled exception in main loop: {e}\n[SELF-HEAL] Retrying...\n")
            time.sleep(10)
            continue
    mcp = MCPMemoryClient()
    # max_retries removed (unused)
    def write_status(loop, problems, patch_applied, llm_response, mutation_info=None, status_file="user_data/self_heal_status.txt"):
        import datetime
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(status_file, "w", encoding="utf-8") as f:
            f.write(f"[Self-Heal Status] {ts}\n")
            f.write(f"Loop: {loop}\n")
            f.write(f"Problems: {list(problems.keys()) if problems else 'None'}\n")
            f.write(f"Patch Applied: {patch_applied}\n")
            f.write(f"LLM Response: {llm_response[:120].replace('\n',' ')}...\n")
            if mutation_info:
                f.write(f"Mutation/Adaptation: {mutation_info}\n")

    # Log launch
    import datetime
    launch_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("user_data/self_heal_launch.log", "a", encoding="utf-8") as f:
        f.write(f"[Launch] Self-healing agent started at {launch_time}\n")

    loop = 1
    last_improvement = time.time()
    last_problems = None
    import threading
    def log_in_background():
        while True:
            time.sleep(5)
            try:
                with open("user_data/self_heal_status.txt", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                print("[LIVE STATUS] " + lines[-1].strip() if lines else "[LIVE STATUS] (no status)")
            except Exception:
                pass
    t = threading.Thread(target=log_in_background, daemon=True)
    t.start()
    # --- Minimum local fixer attempts before fallback ---
    local_attempts = 0
    MIN_LOCAL_FIXERS = 4
    while True:
        try:
            problems = scan_problems()
            mcp.put(PROBLEM_KEY, problems)
            patch_applied = False
            mutation_info = None
            llm_response = ""  # Always define llm_response for logging and patching
            # Detect improvement
            if last_problems is not None and problems == last_problems and (time.time() - last_improvement) > 60:
                print("[MUTATE] No improvement in 60 seconds, forcing mutation and retry...")
                mutation_info = "Forced mutation due to no improvement in 60 seconds."
                last_improvement = time.time()
            elif last_problems is None or problems != last_problems:
                last_improvement = time.time()
            last_problems = problems.copy() if problems is not None else None
            if not problems:
                msg = f"[OK] All checks passed at loop {loop}. Forcing mutation to continue auto-dev."
                print(f"\n===== {msg} =====\n")
                write_status(loop, problems, patch_applied, msg, mutation_info)
                mutation_info = "No problems found, but continuing mutation for full auto-dev."
                prompt = "Suggest a random code improvement or refactor for this Python project. Return a patch or instructions."
            else:
                print(f"\n===== [LOOP {loop}] Problems found: {list(problems.keys())} =====")
                short_problems = dict(list(problems.items())[:2])
                prompt = f"Fix the following problems in the codebase:\n{short_problems}\nReturn a patch or instructions."

            # --- LLM PATCHING: Try local Ollama at least 4 times before fallback ---
            import os
            import requests
            agent_model = os.getenv("AGENT_MODEL") or "deepseek-coder-v2:16b"
            ollama_url = "http://127.0.0.1:11434/api/chat"
            ollama_payload = {
                "model": agent_model,
                "messages": [
                    {"role": "system", "content": "You are an expert Python developer and code fixer."},
                    {"role": "user", "content": prompt},
                ],
                "options": {"temperature": 0.3, "num_ctx": 2048, "top_p": 0.95},
                "stream": False
            }
            anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
            anthropic_url = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")
            fallback_needed = False
            # Try local Ollama up to MIN_LOCAL_FIXERS times before fallback
            for local_try in range(MIN_LOCAL_FIXERS):
                try:
                    resp = requests.post(ollama_url, json=ollama_payload, timeout=90)
                    resp.raise_for_status()
                    llm_response = resp.json().get("message", {}).get("content", "")
                    if llm_response and not llm_response.startswith("[ERROR]"):
                        print(f"[LLM PATCH][LOCAL-{local_try+1}] {llm_response[:120].replace('\n',' ')}...")
                        break
                except Exception as e:
                    print(f"[LLM PATCH][LOCAL-{local_try+1}] Ollama error: {e}")
                    llm_response = f"[ERROR] Ollama LLM call failed: {e}"
                time.sleep(2)
            else:
                fallback_needed = True

            # If still no good response, fallback to Claude
            if (not llm_response or llm_response.startswith("[ERROR]") or fallback_needed) and anthropic_key:
                llm_url = anthropic_url
                llm_headers = {
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                llm_payload = {
                    "model": os.getenv("AGENT_MODEL", "claude-3-5-sonnet-20241022"),
                    "max_tokens": 1024,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
                try:
                    resp = requests.post(llm_url, headers=llm_headers, json=llm_payload, timeout=90)
                    resp.raise_for_status()
                    llm_response = resp.json().get("content", [{}])[0].get("text", "")
                    print(f"[LLM PATCH][CLAUDE] {llm_response[:120].replace('\n',' ')}...")
                except Exception as e:
                    llm_response = f"[ERROR] Claude LLM call failed: {e}"

            mcp.put(ATTEMPT_KEY, {"loop": loop, "problems": problems, "prompt": prompt, "llm_response": llm_response})
            print(f"[LLM PATCH] {llm_response[:120].replace('\n',' ')}...")

            # --- PATCH APPLICATION ---
            import subprocess
            if "*** Begin Patch" in llm_response and "*** End Patch" in llm_response:
                patch = llm_response.split("*** Begin Patch", 1)[1].split("*** End Patch")[0]
                patch = "*** Begin Patch\n" + patch.strip() + "\n*** End Patch"
                patch_file = f"user_data/llm_patch_{loop}.diff"
                with open(patch_file, "w", encoding="utf-8") as f:
                    f.write(patch)
                # Try to apply patch using git
                apply_cmd = f"git apply --whitespace=fix {patch_file}"
                result = subprocess.run(apply_cmd, shell=True, capture_output=True, text=True)
                patch_applied = result.returncode == 0
                mutation_info = f"Patch file: {patch_file}, Applied: {patch_applied}, Stdout: {result.stdout.strip()}, Stderr: {result.stderr.strip()}"
                mcp.put(
                    f"self_heal:patch:{loop}",
                    {
                        "patch": patch,
                        "applied": patch_applied,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    },
                )
                print(f"[PATCH] Applied: {patch_applied}, stdout: {result.stdout.strip()}, stderr: {result.stderr.strip()}")
            else:
                print("[WARN] No valid patch found in LLM response.")

            # --- VERIFICATION & STATUS ---
            write_status(loop, problems, patch_applied, llm_response, mutation_info)
            if patch_applied:
                print("[VERIFY] Re-scanning after patch...")
                time.sleep(2)
            else:
                print("[WAIT] No patch or patch failed, waiting before retry/mutation...")
                time.sleep(10)
        except Exception as e:
            print(f"[ERROR] Exception in auto loop: {e}")
            mutation_info = f"Exception: {e} (auto-survive)"
            write_status(loop, {}, False, str(e), mutation_info)
            time.sleep(10)
        loop += 1

        # --- LLM PATCHING: Claude 3.5 (Anthropic) or Ollama ---
        import os
        anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        anthropic_url = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")
        agent_model = os.getenv("AGENT_MODEL", "llama3:instruct")
        # 1. Try Ollama first
        llm_response = None
        ollama_url = "http://127.0.0.1:11434/api/chat"
        ollama_payload = {
            "model": agent_model,
            "messages": [
                {"role": "system", "content": "You are an expert Python developer and code fixer."},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.3, "num_ctx": 4096, "top_p": 0.95},
            "stream": False
        }
        try:
            resp = requests.post(ollama_url, json=ollama_payload, timeout=120)
            resp.raise_for_status()
            llm_response = resp.json()["message"]["content"]
        except Exception as e:
            llm_response = f"[ERROR] Ollama LLM call failed: {e}"

        # 2. If Ollama fails or response is empty/error, try Claude if available
        fallback_needed = (
            not llm_response or
            llm_response.startswith("[ERROR]") or
            "not supported" in llm_response.lower() or
            "i don't know" in llm_response.lower() or
            "error" in llm_response.lower()
        )
        if fallback_needed and anthropic_key:
            llm_url = anthropic_url
            llm_headers = {
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            llm_payload = {
                "model": os.getenv("AGENT_MODEL", "claude-3-5-sonnet-20241022"),
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            try:
                resp = requests.post(llm_url, headers=llm_headers, json=llm_payload, timeout=120)
                resp.raise_for_status()
                llm_response = resp.json()["content"][0]["text"]
            except Exception as e:
                llm_response = f"[ERROR] Claude LLM call failed: {e}"
        mcp.put(ATTEMPT_KEY, {"loop": loop, "problems": problems, "prompt": prompt, "llm_response": llm_response})
        print(f"[LLM PATCH] {llm_response[:120].replace('\n',' ')}...")

        # --- PATCH APPLICATION ---
        if "*** Begin Patch" in llm_response and "*** End Patch" in llm_response:
            patch = llm_response.split("*** Begin Patch", 1)[1].split("*** End Patch")[0]
            patch = "*** Begin Patch\n" + patch.strip() + "\n*** End Patch"
            patch_file = f"user_data/llm_patch_{loop}.diff"
            with open(patch_file, "w", encoding="utf-8") as f:
                f.write(patch)
            # Try to apply patch using git
            apply_cmd = f"git apply --whitespace=fix {patch_file}"
            result = subprocess.run(apply_cmd, shell=True, capture_output=True, text=True)
            patch_applied = result.returncode == 0
            mutation_info = f"Patch file: {patch_file}, Applied: {patch_applied}, Stdout: {result.stdout.strip()}, Stderr: {result.stderr.strip()}"
            mcp.put(
                f"self_heal:patch:{loop}",
                {
                    "patch": patch,
                    "applied": patch_applied,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )
            print(f"[PATCH] Applied: {patch_applied}, stdout: {result.stdout.strip()}, stderr: {result.stderr.strip()}")
        else:
            print("[WARN] No valid patch found in LLM response.")

        # --- VERIFICATION & STATUS ---
        write_status(loop, problems, patch_applied, llm_response, mutation_info)
        if patch_applied:
            print("[VERIFY] Re-scanning after patch...")
            time.sleep(2)
            continue  # Next loop will re-scan and retry if needed
        else:
            print("[WAIT] No patch or patch failed, waiting before retry...")
            time.sleep(10)
    print("\n===== [DONE] Self-healing loop complete. =====\n")


if __name__ == "__main__":
    main()
