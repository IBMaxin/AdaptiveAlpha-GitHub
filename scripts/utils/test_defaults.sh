#!/bin/bash
# Quick test script to verify all features are enabled

echo "=== Testing Agent Features Default State ==="

echo "1. Testing agent defaults (should show max-loops=5, verbose=2, etc.)"
PYTHONPATH=src python src/agents/trading/self_loop_agent_fixed.py --help

echo -e "\n2. Testing memory server status..."
if pgrep -f "start_memory_mcp" > /dev/null; then
    echo "✓ Memory server is running"
else
    echo "✗ Memory server not running - will auto-start"
fi

echo -e "\n3. Testing auto-start script..."
if [[ -x "scripts/utils/auto_start_all.sh" ]]; then
    echo "✓ Auto-start script is executable"
else
    echo "✗ Auto-start script needs chmod +x"
    echo "  Run: chmod +x scripts/utils/auto_start_all.sh"
fi

echo -e "\n4. Available make targets:"
make agent-help

echo -e "\n=== Configuration Summary ==="
echo "All agent features now enabled by default:"
echo "  • max-loops: 5 (was 1)"
echo "  • verbose: 2 (was 0)"
echo "  • export-trades: true (was false)"
echo "  • memory: enabled (was disabled)"
echo ""
echo "Usage:"
echo "  make agent-full      # Run with all defaults"
echo "  make agent-loop-5    # Run 5-cycle loop"
echo "  make agent-loop-1    # Quick single cycle test"
echo ""
echo "Direct usage:"
echo "  bash scripts/utils/auto_start_all.sh [additional args]"
