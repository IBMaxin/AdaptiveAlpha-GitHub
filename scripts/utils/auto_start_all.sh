#!/bin/bash
# Auto-start all agent features

set -e

echo "[INFO] Starting all agent features with defaults enabled..."

# Function to check if memory server is needed
check_memory_needed() {
    # Check if --disable-memory is in the arguments
    for arg in "$@"; do
        if [[ "$arg" == "--disable-memory" ]]; then
            return 1  # Memory not needed
        fi
    done
    return 0  # Memory needed
}

# Start memory server if needed and not running
if check_memory_needed "$@"; then
    echo "[INFO] Memory features enabled - checking memory server..."
    
    # Check if already running
    if pgrep -f "@modelcontextprotocol/server-memory" > /dev/null; then
        echo "[INFO] Memory server already running"
    else
        echo "[INFO] Starting memory server..."
        # Start in background and give it time to initialize
        nohup bash scripts/utils/start_memory_mcp.sh > user_data/memory_server.log 2>&1 &
        
        # Wait a bit for startup
        sleep 3
        
        # Check if it started successfully
        if pgrep -f "@modelcontextprotocol/server-memory" > /dev/null; then
            echo "[INFO] Memory server started successfully"
        else
            echo "[WARN] Memory server may not have started properly. Check user_data/memory_server.log"
            echo "[INFO] Agent will use file-based memory fallback"
        fi
    fi
else
    echo "[INFO] Memory features disabled via --disable-memory flag"
fi

echo "[INFO] Running agent with all features enabled..."
echo "[INFO] Default settings: max-loops=5, verbose=2, export-trades=true, memory=enabled"

# Run agent with all features enabled by default
PYTHONPATH=src python src/agents/trading/self_loop_agent_fixed.py \
  --config user_data/config.json \
  "$@"

echo "[INFO] Agent execution completed"
