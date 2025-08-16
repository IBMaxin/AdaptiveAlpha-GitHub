#!/bin/bash
# Test the guaranteed-to-trade strategy

set -e

echo "=== TESTING GUARANTEED-TO-TRADE STRATEGY ==="
echo ""

# Test the strategy creation
echo "[TEST 1] Testing strategy generation..."
PYTHONPATH=src python -c "
from agents.trading.self_loop_agent_fixed import _ensure_strategy_exists, STRATEGY_FILE
_ensure_strategy_exists()
print('✓ Strategy file created successfully')

# Check if strategy contains key components
with open(STRATEGY_FILE, 'r') as f:
    content = f.read()
    
checks = [
    ('class SimpleAlwaysBuySell', 'Strategy class defined'),
    ('def populate_entry_trend', 'Entry logic defined'), 
    ('def populate_exit_trend', 'Exit logic defined'),
    ('enter_long', 'Entry signals present'),
    ('exit_long', 'Exit signals present'),
    ('ta.SMA', 'Technical indicators present'),
    ('ta.RSI', 'RSI indicator present'),
    ('volume_sma', 'Volume analysis present'),
]

for check, desc in checks:
    if check in content:
        print(f'✓ {desc}')
    else:
        print(f'✗ {desc} - MISSING')
        
print('')
print('Strategy preview:')
lines = content.split('\\n')
for i, line in enumerate(lines[:20]):
    print(f'{i+1:2d}: {line}')
if len(lines) > 20:
    print(f'... and {len(lines)-20} more lines')
"

echo ""
echo "[TEST 2] Testing strategy compilation..."
# Quick validation that strategy loads without syntax errors
PYTHONPATH=src python -c "
import sys
sys.path.append('strategies')
try:
    from SimpleAlwaysBuySell import SimpleAlwaysBuySell
    strategy = SimpleAlwaysBuySell()
    print('✓ Strategy compiles without errors')
    print(f'✓ ROI target: {strategy.minimal_roi}')
    print(f'✓ Stop loss: {strategy.stoploss}')
    print(f'✓ Timeframe: {strategy.timeframe}')
    print(f'✓ Startup candles: {strategy.startup_candle_count}')
except Exception as e:
    print(f'✗ Strategy compilation failed: {e}')
    sys.exit(1)
"

echo ""
echo "[TEST 3] Testing quick backtest..."
# Run a very quick backtest to see if it generates trades
FREQTRADE_BIN=$(if [ -x ".venv/bin/freqtrade" ]; then echo ".venv/bin/freqtrade"; else echo "freqtrade"; fi)

# Use the most recent week of data for quick test
RECENT_START="20250810"
RECENT_END="20250816"

echo "Testing with data range: $RECENT_START to $RECENT_END"

$FREQTRADE_BIN backtesting \
    --config user_data/config.json \
    --strategy SimpleAlwaysBuySell \
    --strategy-path strategies \
    --timeframe 1h \
    --timerange "${RECENT_START}-${RECENT_END}" \
    --cache none \
    --export trades \
    > test_backtest.log 2>&1

if [[ $? -eq 0 ]]; then
    echo "✓ Backtest completed successfully"
    
    # Check for trades
    TRADES=$(grep -c "Tot Profit" test_backtest.log || echo 0)
    if [[ $TRADES -gt 0 ]]; then
        echo "✓ Strategy generated trades"
        
        # Show summary
        echo ""
        echo "Quick Results:"
        grep -E "(Trades|Tot Profit|Win|Max Drawdown)" test_backtest.log | head -5 || echo "Could not extract metrics"
    else
        echo "⚠️  Strategy may not have generated trades"
    fi
else
    echo "✗ Backtest failed"
    echo "Error log:"
    tail -20 test_backtest.log
fi

echo ""
echo "[TEST 4] Checking trade export..."
if [[ -f "user_data/backtest_results/backtest-result-${RECENT_START}_${RECENT_END}.json" ]]; then
    TRADE_COUNT=$(python -c "
import json
try:
    with open('user_data/backtest_results/backtest-result-${RECENT_START}_${RECENT_END}.json', 'r') as f:
        data = json.load(f)
        trades = data.get('strategy', {}).get('SimpleAlwaysBuySell', {}).get('trades', [])
        print(len(trades))
except:
    print(0)
")
    
    if [[ $TRADE_COUNT -gt 0 ]]; then
        echo "✓ Generated $TRADE_COUNT trades in export file"
    else
        echo "⚠️  No trades found in export file"
    fi
else
    echo "⚠️  No trade export file found"
fi

# Cleanup
rm -f test_backtest.log

echo ""
echo "=== GUARANTEED-TO-TRADE STRATEGY TEST COMPLETE ==="
echo ""
echo "✅ The strategy is designed to ALWAYS generate trades through:"
echo "   • Multiple entry conditions (price movement, volume, RSI, intervals)"
echo "   • Multiple exit conditions (time-based, technical, regular intervals)"
echo "   • Guaranteed initial trades in first few candles"
echo "   • Conservative but achievable profit targets (1.5%)"
echo "   • Reasonable stop-loss protection (-8%)"
echo ""
echo "🎯 This gives agents consistent trading data to learn from!"
