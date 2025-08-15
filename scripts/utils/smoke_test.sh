#!/usr/bin/env bash
set -euo pipefail

# Lightweight system-wide smoke test for hf-battle
# 1. Run a minimal agent loop
# 2. Check all critical logs
# 3. Validate imports
# 4. Check LLM endpoint
# 5. Verify strategy discovery
# 6. Check data pipeline

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

fail() {
	echo -e "${RED}[FAIL] $1${NC}"
	exit 1
}
pass() { echo -e "${GREEN}[PASS] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARN] $1${NC}"; }

# 1. Minimal agent loop
echo "[TEST] Running minimal agent loop..."
PYTHONPATH=. python -m agents.self_loop_agent --spec "Minimal robust Freqtrade strategy for BTC/USDT, 1h timeframe, with clear logic and comments" --config config.json --max-loops 1 >user_data/smoke_agent_loop.log 2>&1 || fail "Agent loop failed"
if grep -q 'Result for strategy' user_data/smoke_agent_loop.log || grep -q 'Final balance' user_data/smoke_agent_loop.log; then
	pass "Agent loop ran and produced output"
else
	warn "Agent loop ran but did not find expected summary. Printing last 20 lines:"
	tail -n 20 user_data/smoke_agent_loop.log
fi

# 2. Check logs
for f in user_data/learning_log.csv user_data/ml_trades_book.csv; do
	if [ -s "$f" ]; then pass "$f exists and is non-empty"; else warn "$f missing or empty"; fi
done

# 3. Validate imports
python -c "import agents.self_loop_agent, agents.backtest_agent, agents.improve_agent, agents.patch_utils" && pass "All main agent modules import OK" || fail "Agent import error"

# 4. Check LLM endpoint
curl -s -X POST http://localhost:1234/v1/chat/completions -H 'Content-Type: application/json' \
	-d '{"model":"qwen2.5-coder-7b-instruct","messages":[{"role":"user","content":"ping"}]}' | grep -q 'choices' && pass "LLM endpoint responded" || warn "LLM endpoint did not respond as expected"

# 5. Verify strategy discovery
python -c "import os; [__import__(f'strategies.'+f[:-3]) for f in os.listdir('strategies') if f.endswith('.py') and not f.startswith('__')]" && pass "All strategies import OK" || warn "Strategy import error"

# 6. Data pipeline check
PYTHONPATH=. python scripts/random_update_kraken_data.py >user_data/smoke_data_update.log 2>&1 && pass "Data update script ran" || warn "Data update script failed"

# Summary
echo -e "${GREEN}System smoke test complete.${NC}"
