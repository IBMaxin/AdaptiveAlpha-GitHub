-include .env
export

.DEFAULT_GOAL := help
SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-builtin-rules

# ========= Globals you can override on the CLI =========
PY            ?= python3.11
VENV          ?= .venv
PYBIN         ?= $(VENV)/bin/python
PIP           ?= $(VENV)/bin/pip

CONFIG        ?= user_data/config.json
STRAT         ?= SmaRsiStrategy
TIMEFRAME     ?= 5m
DAYS          ?= 120
TIMERANGE     ?=
PAIRS         ?= BTC/USDT,ETH/USDT
TAG           ?= manual

FREQTRADE_BIN ?= $(VENV)/bin/freqtrade

SAFE          ?= ./scripts/safe_run.sh
GUARD         ?= ./scripts/guard.sh

# Resolve freqtrade at runtime (venv > PATH)
define FREQTRADE_CMD
bash -c 'if [ -x "$(FREQTRADE_BIN)" ]; then echo "$(FREQTRADE_BIN)"; elif command -v freqtrade >/dev/null 2>&1; then command -v freqtrade; else echo "MISSING"; fi'
endef

.PHONY: help guard tools data list bt bt-range paper fix-config agent-error agent-error-apply clean-data show
.PHONY: agent-loop-5 agent-loop-1 llm-orchestrate update-data clean-results local-learn-loop
.PHONY: agent-help agent-prompt-sample llm-prompt-sample venv install dev-install lint fix type test
.PHONY: start stop status package report battle agent-full realistic-test walk-forward-validation simple-validation
.PHONY: data-status data-append data-refresh data-check data-clean data-analyze data-2024 data-range
.PHONY: data-2024-1m data-2024-5m data-2024-15m data-2024-1h data-2024-4h data-2024-1d

help:
	@echo "Targets:"
	@echo "  venv              Create .venv with $(PY)"
	@echo "  install           Base deps (requirements.txt)"
	@echo "  dev-install       Dev deps (dev-requirements.txt)"
	@echo "  lint / fix        Lint check / autofix (ruff+black)"
	@echo "  flake8            Run flake8 lint checks"
	@echo "  type              Type-check (mypy)"
	@echo "  test              Run tests (pytest)"
	@echo "  start/stop/status Start Freqtrade webserver (or healing server fallback)"
	@echo "  tools             Install CLI helpers (jq, yq)"
	@echo "  guard             Run safety checks (scripts/guard.sh if present)"
	@echo "  data              Download data (TIMEFRAME=$(TIMEFRAME), DAYS=$(DAYS))"
	@echo "  bt                Backtest $(STRAT) using downloaded data"
	@echo "  bt-range          Backtest with TIMERANGE=$(TIMERANGE)"
	@echo "  list              List strategies Freqtrade sees"
	@echo "  fix-config        Quick JSON fixes for common schema issues"
	@echo "  agent-error       ErrorMedic (dry-run): analyze an error log"
	@echo "  agent-error-apply ErrorMedic: apply patches"
	@echo "  clean-data        Remove downloaded OHLCV"
	@echo "  agent-loop-5/1    Self-improving agent loop (all features enabled)"
	@echo "  agent-full        Run agent with all features enabled (default)"
	@echo "  realistic-test    Setup and run realistic walk-forward validation"
	@echo "  simple-validation Run simple train/test validation (limited data)"
	@echo "  walk-forward-validation  Run full walk-forward validation"
	@echo "  data-status       Show current data status and coverage"
	@echo "  data-append       Download and append new data (default)"
	@echo "  data-refresh      Erase and download fresh data"
	@echo "  data-check        Check existing data without downloading"
	@echo "  data-clean        Remove all downloaded data"
	@echo "  data-analyze      Analyze data quality and gaps"
	@echo "  data-2024         Download full year 2024 data (1h timeframe)"
	@echo "  data-2024-5m      Download 2024 data with 5-minute candles"
	@echo "  data-2024-15m     Download 2024 data with 15-minute candles"
	@echo "  data-2024-1h      Download 2024 data with 1-hour candles"
	@echo "  data-range        Download custom date range (START=YYYYMMDD END=YYYYMMDD)"
	@echo "  llm-orchestrate   Run LLM orchestrator script"
	@echo "  update-data       Fetch and update data from Kraken"
	@echo "  clean-results     Remove ML/backtest results"
	@echo "  package           Zip a reproducible bundle"
	@echo "  report / battle   Reporting & battle helpers"
	@echo "  start-memory-mcp  Start the Memory MCP server (local dev)"
	@echo "Vars you can override: CONFIG, STRAT, TIMEFRAME, DAYS, TIMERANGE, PAIRS, TAG"

# ===== Dev workflow =====

.PHONY: flake8
flake8:
	. $(VENV)/bin/activate && flake8 .

.PHONY: start-memory-mcp
start-memory-mcp:
	bash scripts/start_memory_mcp.sh

venv:
	$(PY) -m venv $(VENV)

install:
	. $(VENV)/bin/activate && $(PIP) install -U pip && \
	if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi

dev-install:
	. $(VENV)/bin/activate && \
	if [ -f dev-requirements.txt ]; then $(PIP) install -r dev-requirements.txt; fi

lint:
	. $(VENV)/bin/activate && black --check . && ruff check .

fix:
	. $(VENV)/bin/activate && ruff check --fix . && black .

type:
	. $(VENV)/bin/activate && mypy .

test:
	. $(VENV)/bin/activate && pytest -q

start:
	@FTBIN="$$( $(FREQTRADE_CMD) )"; \
	if [ "$$FTBIN" = "MISSING" ]; then \
	  echo "[WARN] freqtrade not found. Starting healing server fallback on :8000"; \
	  . $(VENV)/bin/activate && uvicorn services.healing_server:app --host 0.0.0.0 --port 8000; \
	else \
	  echo "[INFO] Using $$FTBIN"; \
	  . $(VENV)/bin/activate && $$FTBIN webserver --config $(CONFIG); \
	fi

stop:
	pkill -f "freqtrade webserver" || true
	pkill -f "uvicorn services.healing_server:app" || true

status:
	pgrep -af "freqtrade|uvicorn" || true

# ===== Ops helpers =====

guard:
	@if [ -x "$(GUARD)" ]; then \
	  "$(GUARD)" "$(CONFIG)" "$(STRAT)"; \
	else \
	  echo "[WARN] $(GUARD) not found. Skipping guard checks."; \
	fi

tools:
	@command -v jq >/dev/null || { sudo apt-get update -y && sudo apt-get install -y jq; }
	@command -v yq >/dev/null || { sudo apt-get install -y yq || true; }

list: guard
	@FTBIN="$$( $(FREQTRADE_CMD) )"; \
	if [ "$$FTBIN" = "MISSING" ]; then echo "[ERROR] freqtrade not found"; exit 1; fi; \
	"$$FTBIN" list-strategies -c $(CONFIG)

data: guard
	@if [ -x "$(SAFE)" ]; then \
	  PAIRLIST="$(PAIRS)" TIMEFRAME="$(TIMEFRAME)" DAYS="$(DAYS)" CONFIG="$(CONFIG)" "$(SAFE)" bash scripts/ensure_data.sh; \
	else \
	  echo "[WARN] $(SAFE) not found. Running without wrapper."; \
	  PAIRLIST="$(PAIRS)" TIMEFRAME="$(TIMEFRAME)" DAYS="$(DAYS)" CONFIG="$(CONFIG)" bash scripts/ensure_data.sh; \
	fi

bt: guard
	@if [ -x "$(SAFE)" ]; then \
	  CONFIG="$(CONFIG)" STRAT="$(STRAT)" TIMERANGE="" TIMEFRAME="$(TIMEFRAME)" "$(SAFE)" bash scripts/run_backtest.sh; \
	else \
	  echo "[WARN] $(SAFE) not found. Running without wrapper."; \
	  CONFIG="$(CONFIG)" STRAT="$(STRAT)" TIMERANGE="" TIMEFRAME="$(TIMEFRAME)" bash scripts/run_backtest.sh; \
	fi

bt-range: guard
	@if [ -x "$(SAFE)" ]; then \
	  CONFIG="$(CONFIG)" STRAT="$(STRAT)" TIMERANGE="$(TIMERANGE)" TIMEFRAME="$(TIMEFRAME)" "$(SAFE)" bash scripts/run_backtest.sh; \
	else \
	  echo "[WARN] $(SAFE) not found. Running without wrapper."; \
	  CONFIG="$(CONFIG)" STRAT="$(STRAT)" TIMERANGE="$(TIMERANGE)" TIMEFRAME="$(TIMEFRAME)" bash scripts/run_backtest.sh; \
	fi

paper: guard
	@CONFIRM_LIVE=$${CONFIRM_LIVE:-NO}; \
	if [ -x "$(SAFE)" ]; then \
	  CONFIRM_LIVE="$$CONFIRM_LIVE" "$(SAFE)" bash scripts/start_paper.sh "$(CONFIG)" "$(STRAT)"; \
	else \
	  echo "[WARN] $(SAFE) not found. Running without wrapper."; \
	  CONFIRM_LIVE="$$CONFIRM_LIVE" bash scripts/start_paper.sh "$(CONFIG)" "$(STRAT)"; \
	fi

fix-config:
	@jq '(.fee |= (if type=="number" then . else 0.001 end))
	   | .telegram = (.telegram // {"enabled":false,"token":"","chat_id":""})
	   | .telegram.enabled = false
	   | .telegram.token   = (.telegram.token   // "")
	   | .telegram.chat_id = (.telegram.chat_id // "")
	   | .exit_pricing = (.exit_pricing // {"price_side":"same","use_order_book":false,"order_book_top":1})
	   | .stake_currency = (.stake_currency // "USDT")
	   | .stoploss = (.stoploss // -0.10)
	   ' $(CONFIG) > $(CONFIG).tmp && mv $(CONFIG).tmp $(CONFIG)
	@echo "Applied config fixes to $(CONFIG)"

agent-error:
	@echo "Usage: make agent-error FILE=err.txt  (or pipe stdin)"
	@[ -z "$${FILE:-}" ] && node -e "process.stdout.write(require('fs').readFileSync(0,'utf8'))" | npx tsx scripts/agents/error_medic.ts - || npx tsx scripts/agents/error_medic.ts "$$FILE"

agent-error-apply:
	@echo "Applying suggested fixes..."
	@[ -z "$${FILE:-}" ] && node -e "process.stdout.write(require('fs').readFileSync(0,'utf8'))" | npx tsx scripts/agents/error_medic.ts - --apply || npx tsx scripts/agents/error_medic.ts "$$FILE" --apply

clean-data:
	rm -rf user_data/data

show:
	@echo "CONFIG=$(CONFIG) STRAT=$(STRAT) TIMEFRAME=$(TIMEFRAME) DAYS=$(DAYS) TIMERANGE=$(TIMERANGE)"

# ===== Agent loops & LLM helpers =====

agent-loop-5:
	bash scripts/utils/auto_start_all.sh \
	  --spec "Start with a simple guaranteed-trade strategy (SimpleAlwaysBuySell) for BTC/USDT, 1h timeframe. Each loop, mutate or improve the strategy logic to increase trade quality, diversity, and profit. Log all trades and results for ML. Use clear comments and robust logic."

agent-loop-1:
	bash scripts/utils/auto_start_all.sh \
	  --spec "Minimal robust Freqtrade strategy for BTC/USDT, 1h timeframe, with clear logic and comments" \
	  --max-loops 1

llm-orchestrate:
	$(PYBIN) scripts/llm_orchestrator.py

update-data:
	$(PYBIN) scripts/kraken_ohlcv_fetcher.py --pair BTC/USDT --timeframe 1h --since 2023-08-08 --to 2025-08-08

clean-results:
	rm -f user_data/ml_trades_book.csv user_data/learning_log.csv user_data/backtest_results/*.log

local-learn-loop:
	bash scripts/utils/auto_start_all.sh \
	  --spec "Fully local, self-updating Freqtrade agent loop. Use SimpleAlwaysBuySell as baseline for BTC/USDT, 1h. Each loop, mutate or improve the strategy logic, log all trades and results for ML, and update the learning log and strategy files as needed. No cloud, no remote calls. All logic and logs are local and persistent."
	@echo "[INFO] Local learning loop complete. Logs and strategies updated."

# === AGENT HELPER TARGETS ===

agent-full:
	bash scripts/utils/auto_start_all.sh

realistic-test:
	bash scripts/utils/realistic_test_runner.sh

simple-validation:
	bash scripts/utils/simple_validation.sh

walk-forward-validation:
	bash scripts/utils/run_walk_forward_validation.sh

# Data management targets
data-status:
	bash scripts/utils/data_manager.sh status

data-append:
	bash scripts/utils/data_manager.sh append

data-refresh:
	bash scripts/utils/data_manager.sh refresh

data-check:
	bash scripts/utils/data_manager.sh check

data-clean:
	bash scripts/utils/data_manager.sh clean

data-analyze:
	bash scripts/utils/data_manager.sh analyze

# Special data ranges
data-2024:
	bash scripts/utils/download_2024_data.sh

# Timeframe-specific downloads
data-2024-1m:
	bash scripts/utils/download_2024_timeframe.sh 1m

data-2024-5m:
	bash scripts/utils/download_2024_timeframe.sh 5m

data-2024-15m:
	bash scripts/utils/download_2024_timeframe.sh 15m

data-2024-1h:
	bash scripts/utils/download_2024_timeframe.sh 1h

data-2024-4h:
	bash scripts/utils/download_2024_timeframe.sh 4h

data-2024-1d:
	bash scripts/utils/download_2024_timeframe.sh 1d

data-range:
	@echo "Usage: make data-range START=YYYYMMDD END=YYYYMMDD"
	@echo "Example: make data-range START=20240101 END=20250101"
	@if [ -n "$(START)" ] && [ -n "$(END)" ]; then \
		bash scripts/utils/data_manager.sh download $(START) $(END); \
	else \
		echo "Error: Both START and END dates required"; \
	fi

agent-help:
	@echo "Agent Automation Targets:"
	@echo "  make agent-full           # Run agent with all features enabled (max-loops=5, verbose=2, memory=on, export-trades=on)"
	@echo "  make realistic-test       # Setup comprehensive validation (auto-detects data range)"
	@echo "  make simple-validation    # Simple train/test split (works with limited data)"
	@echo "  make walk-forward-validation # Run full walk-forward validation on all periods"
	@echo ""
	@echo "Data Management:"
	@echo "  make data-status          # Show current data status and file sizes"
	@echo "  make data-append          # Download new data (default, safe)"
	@echo "  make data-refresh         # Erase all data and download fresh"
	@echo "  make data-check           # Check existing data, skip download if good"
	@echo "  make data-analyze         # Detailed data quality analysis"
	@echo "  make data-clean           # Remove all downloaded data"
	@echo ""
	@echo "Timeframe Downloads (2024 full year):"
	@echo "  make data-2024-1m         # 1-minute data (~525k candles, ~2.5GB per pair)"
	@echo "  make data-2024-5m         # 5-minute data (~105k candles, ~500MB per pair)"
	@echo "  make data-2024-15m        # 15-minute data (~35k candles, ~175MB per pair)"
	@echo "  make data-2024-1h         # 1-hour data (~8.7k candles, ~45MB per pair)"
	@echo "  make data-2024-4h         # 4-hour data (~2.2k candles, ~11MB per pair)"
	@echo "  make data-2024-1d         # Daily data (~365 candles, ~2MB per pair)"
	@echo "  make data-range START=YYYYMMDD END=YYYYMMDD  # Custom date range"
	@echo ""
	@echo "  make agent-loop-5         # Run 5-cycle agent loop with SimpleAlwaysBuySell"
	@echo "  make agent-loop-1         # Run single agent loop for quick test"
	@echo "  make local-learn-loop     # Fully local, self-updating, learning agent loop"
	@echo "  make llm-orchestrate      # Orchestrate via LM Studio LLM (see scripts/llm_orchestrator.py)"
	@echo "  make update-data          # Update BTC/USDT 1h data for full range"
	@echo "  make clean-results        # Clean all logs and results"
	@echo ""
	@echo "Tips:"
	@echo "- Edit scripts/llm_orchestrator.py to customize LLM prompts or workflow."
	@echo "- Use --spec in agent-loop targets to set your own strategy prompt."
	@echo "- Logs and ML trade books live in user_data/."

agent-prompt-sample:
	@echo "Sample agent prompt:"
	@echo '"Start with a simple guaranteed-trade strategy (SimpleAlwaysBuySell) for BTC/USDT, 1h timeframe. Each loop, mutate or improve the strategy logic to increase trade quality, diversity, and profit. Log all trades and results for ML. Use clear comments and robust logic."'

llm-prompt-sample:
	@echo "Sample LLM orchestration prompt:"
	@echo '"You are an expert Freqtrade research orchestrator. Run the Freqtrade agent loop for 5 cycles using the SimpleAlwaysBuySell strategy for BTC/USDT, 1h timeframe. Each loop, mutate or improve the strategy logic to increase trade quality, diversity, and profit. Log all trades and results for ML. After completion, summarize the results in a clear, human-readable format."'

# Packaging & misc

package:
	$(PYBIN) scripts/package_for_ai_review.py --reproducible -o hf_battle_ai_review_package.zip

report:
	$(PYBIN) agents/reporting.py --latest || python agents/reporting.py --latest || python agents/reporting.py

battle:
	$(PYBIN) agents/battle.py || python agents/battle.py
