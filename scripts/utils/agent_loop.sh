#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Activate venv
if [ -f .venv/bin/activate ]; then
	source .venv/bin/activate
fi

# Config
SPEC=${SPEC:-"Robust 15m EMA/RSI baseline with volatility filter."}
CFG=${CFG:-"config.json"}
LOG_DIR=${LOG_DIR:-"logs"}
STRAT_DIR=${FT_STRATEGY_DIR:-"$ROOT_DIR/user_data/strategies"}
mkdir -p "$LOG_DIR" "$STRAT_DIR"

# Use LM Studio by default (unset offline)
unset LLM_OFFLINE || true

echo "[agent_loop] starting with SPEC='$SPEC' CFG='$CFG' STRAT_DIR='$STRAT_DIR'" | tee -a "$LOG_DIR/self_loop.log"

# Restart loop on failure with backoff
backoff=2
while true; do
	FT_STRATEGY_DIR="$STRAT_DIR" \
		python -m agents.self_loop_agent --spec "$SPEC" --config "$CFG" >>"$LOG_DIR/self_loop.log" 2>&1 || true
	echo "[agent_loop] process exited; restarting in ${backoff}s..." | tee -a "$LOG_DIR/self_loop.log"
	sleep "$backoff"
	backoff=$((backoff < 60 ? backoff * 2 : 60))
done
