#!/bin/bash
# Auto-start MCP memory server and self-healing agent
# Usage: bash scripts/auto_mcp_self_heal.sh

# Ensure script runs from project root
cd "$(dirname "$0")/.."

# Activate Python environment
echo "Activating Python environment..."
source .venv-ft2025/bin/activate

# Start MCP memory server in background if not already running
if ! lsof -i :8080 | grep LISTEN >/dev/null; then
  echo "Starting MCP memory server on port 8080..."
  nohup python scripts/minimal_mcp_server.py > user_data/mcp_server.log 2>&1 &
  sleep 2
else
  echo "MCP memory server already running."
fi

# Retry loop for self-healing agent
while true; do
  echo "Running self-healing agent..."
  # Start a background logger for live task updates
  (
    while true; do
      ts=$(date '+%Y-%m-%d %H:%M:%S')
      last_status=$(tail -n 1 user_data/self_heal_status.txt 2>/dev/null)
      last_patch=$(grep -m1 'Patch Applied:' user_data/self_heal_status.txt 2>/dev/null | tail -n1)
      gpu_info=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | head -n1 2>/dev/null)
      # Try to get token count from last LLM response if available
      token_count=""
      if [ -f user_data/self_heal_status.txt ]; then
        token_count=$(grep -o 'tokens_used:[0-9]*' user_data/self_heal_status.txt | tail -n1 | cut -d: -f2)
      fi
      echo "$ts | Copilot: Working on self-healing loop. Status: $last_status | $last_patch | GPU: $gpu_info | Tokens: $token_count" >> user_data/copilot_live.log
      sleep 10
    done
  ) &
  logger_pid=$!
  PYTHONPATH=. python agents/self_heal_mcp_agent.py
  status=$?
  kill $logger_pid 2>/dev/null
  if [ $status -eq 0 ]; then
    echo "Self-healing agent completed successfully."
    break
  else
    echo "Self-healing agent exited with code $status. Retrying in 30 seconds..." | tee -a user_data/self_heal_agent_error.log
    sleep 30
  fi
done
