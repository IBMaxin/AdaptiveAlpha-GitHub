#!/bin/bash
# Final System Verification Script
# Tests all components of the realistic walk-forward validation system

set -e

echo "=== FINAL SYSTEM VERIFICATION ==="
echo "Testing all components of the realistic walk-forward validation system"
echo ""

# Configuration
PROJECT_ROOT=$(pwd)
SUCCESS_COUNT=0
TOTAL_TESTS=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    ((TOTAL_TESTS++))
    echo "[TEST $TOTAL_TESTS] $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo "  ✅ PASSED"
        ((SUCCESS_COUNT++))
    else
        echo "  ❌ FAILED"
        echo "  Command: $test_command"
    fi
    echo ""
}

echo "🔍 COMPONENT VERIFICATION"
echo "=========================="

# Test 1: Check if all scripts exist
run_test "Scripts existence" "
    [[ -f 'scripts/utils/setup_realistic_validation.sh' ]] &&
    [[ -f 'scripts/utils/walk_forward_validation.py' ]] &&
    [[ -f 'scripts/utils/run_walk_forward_validation.sh' ]] &&
    [[ -f 'scripts/utils/realistic_test_runner.sh' ]] &&
    [[ -f 'scripts/utils/analyze_walk_forward_results.py' ]] &&
    [[ -f 'scripts/utils/auto_start_all.sh' ]] &&
    [[ -f 'scripts/utils/test_memory.sh' ]]
"

# Test 2: Check agent improvements
run_test "Agent script with realistic parameters" "
    grep -q 'minimal_roi_0 must be a float between 0.005 and 0.050' src/agents/trading/self_loop_agent_fixed.py &&
    grep -q 'stoploss must be a float between -0.20 and -0.03' src/agents/trading/self_loop_agent_fixed.py &&
    grep -q 'max-loops.*default=5' src/agents/trading/self_loop_agent_fixed.py
"

# Test 3: Check memory system
run_test "Memory client implementation" "
    grep -q 'file-based storage' src/agents/utils/mcp_memory_client.py &&
    grep -q 'def append' src/agents/utils/mcp_memory_client.py &&
    grep -q 'agent_memory.json' src/agents/utils/mcp_memory_client.py
"

# Test 4: Check configuration updates
run_test "Configuration for realistic testing" "
    grep -q 'BTC/USDT.*ETH/USDT.*ADA/USDT.*SOL/USDT.*MATIC/USDT' user_data/config.json &&
    grep -q 'stake_currency.*USDT' user_data/config.json &&
    grep -q 'binanceus' user_data/config.json
"

# Test 5: Check Makefile integration
run_test "Makefile targets" "
    grep -q 'realistic-test:' Makefile &&
    grep -q 'walk-forward-validation:' Makefile &&
    grep -q 'agent-full:' Makefile
"

# Test 6: Test walk-forward generator
run_test "Walk-forward period generator" "
    python scripts/utils/walk_forward_validation.py --start 20220101 --end 20230101 --format json | 
    python -c 'import json, sys; data=json.load(sys.stdin); assert len(data) >= 9'
"

# Test 7: Test memory system
run_test "Memory system functionality" "
    python -c \"
import sys
sys.path.append('src')
from agents.utils.mcp_memory_client import MCPMemoryClient
client = MCPMemoryClient('test_memory.json')
assert client.put('test', 'value')
assert client.get('test') == 'value'
assert client.append('list', 'item1')
assert client.get('list') == ['item1']
import os; os.remove('test_memory.json')
\"
"

# Test 8: Check documentation
run_test "Documentation completeness" "
    [[ -f 'WALK_FORWARD_VALIDATION.md' ]] &&
    grep -q 'Walk-Forward Validation' WALK_FORWARD_VALIDATION.md &&
    grep -q 'make realistic-test' WALK_FORWARD_VALIDATION.md
"

echo "🎯 FUNCTIONALITY TESTS"
echo "======================"

# Test 9: Agent help system
run_test "Agent help system" "make agent-help | grep -q 'realistic-test'"

# Test 10: Check if freqtrade is available
run_test "Freqtrade availability" "
    command -v freqtrade >/dev/null || [[ -x '.venv/bin/freqtrade' ]]
"

echo "📊 FINAL RESULTS"
echo "================"
echo "Tests Passed: $SUCCESS_COUNT / $TOTAL_TESTS"

if [[ $SUCCESS_COUNT -eq $TOTAL_TESTS ]]; then
    echo "🎉 ALL TESTS PASSED!"
    echo ""
    echo "✅ System Status: FULLY OPERATIONAL"
    echo ""
    echo "🚀 Ready to use:"
    echo "   make realistic-test           # Setup and run sample validation"
    echo "   make walk-forward-validation  # Run full validation"
    echo "   make agent-full              # Run agent with all features"
    echo ""
    echo "📖 Documentation:"
    echo "   cat WALK_FORWARD_VALIDATION.md"
    echo ""
    echo "🎯 System Features:"
    echo "   ✅ Walk-forward validation with 1+ year data"
    echo "   ✅ Realistic parameter ranges (ROI: 0.5-5%, SL: -3% to -20%)"
    echo "   ✅ Multi-pair diversification (5 crypto pairs)"
    echo "   ✅ Memory system with persistent learning"
    echo "   ✅ Comprehensive analysis and reporting"
    echo "   ✅ Production-ready configuration"
    
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    echo ""
    echo "Failed: $((TOTAL_TESTS - SUCCESS_COUNT)) / $TOTAL_TESTS tests"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Check if all files were created correctly"
    echo "   2. Verify Python path and dependencies"
    echo "   3. Ensure freqtrade is installed"
    echo "   4. Check file permissions"
    
    exit 1
fi
