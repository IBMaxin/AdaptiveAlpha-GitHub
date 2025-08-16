#!/bin/bash
# Simple Single-Period Validation
# For when historical data is limited - validates on available data range

set -e

echo "=== SIMPLE SINGLE-PERIOD VALIDATION ==="
echo "Using available data for focused validation"
echo ""

# Configuration
CONFIG="user_data/config.json"
STRATEGY="SimpleAlwaysBuySell"

# Check what data we have
if [[ -f "user_data/data/binanceus/BTC_USDT-1h.json" ]]; then
    echo "[INFO] Analyzing available data range..."
    
    # Get data range
    python3 -c "
import json
import sys
from datetime import datetime, timedelta

with open('user_data/data/binanceus/BTC_USDT-1h.json', 'r') as f:
    data = json.load(f)

if len(data) > 24:  # Need at least 24 hours
    first_ts = data[0][0]
    last_ts = data[-1][0]
    
    first_date = datetime.fromtimestamp(first_ts / 1000)
    last_date = datetime.fromtimestamp(last_ts / 1000)
    
    total_hours = len(data)
    
    print(f'Available: {total_hours} hours ({total_hours/24:.1f} days)')
    print(f'Range: {first_date.strftime(\"%Y-%m-%d\")} to {last_date.strftime(\"%Y-%m-%d\")}')
    
    # Use most recent data for validation
    if total_hours >= 168:  # At least 1 week
        # Split: 80% train, 20% test
        train_hours = int(total_hours * 0.8)
        train_end_ts = data[train_hours][0]
        train_end = datetime.fromtimestamp(train_end_ts / 1000)
        
        train_range = f'{first_date.strftime(\"%Y%m%d\")}-{train_end.strftime(\"%Y%m%d\")}'
        test_range = f'{train_end.strftime(\"%Y%m%d\")}-{last_date.strftime(\"%Y%m%d\")}'
        
        print(f'Train period: {train_range} ({train_hours} hours)')
        print(f'Test period: {test_range} ({total_hours - train_hours} hours)')
        
        with open('user_data/simple_validation_ranges.txt', 'w') as f:
            f.write(f'{train_range}\\n{test_range}\\n')
    else:
        print(f'[WARNING] Only {total_hours} hours available - too limited')
        sys.exit(1)
else:
    print('[ERROR] Insufficient data for validation')
    sys.exit(1)
"

    if [[ $? -ne 0 ]]; then
        echo "[ERROR] Data analysis failed"
        exit 1
    fi
else
    echo "[ERROR] No data file found. Run data download first:"
    echo "  freqtrade download-data -c user_data/config.json --timeframe 1h --pairs BTC/USDT"
    exit 1
fi

# Read the ranges
if [[ ! -f "user_data/simple_validation_ranges.txt" ]]; then
    echo "[ERROR] Could not determine validation ranges"
    exit 1
fi

TRAIN_RANGE=$(sed -n '1p' user_data/simple_validation_ranges.txt)
TEST_RANGE=$(sed -n '2p' user_data/simple_validation_ranges.txt)

echo ""
echo "[VALIDATION] Running training optimization..."

# Run training with agent
RESULTS_DIR="user_data/simple_validation_results"
mkdir -p "$RESULTS_DIR"

echo "[TRAIN] Optimizing guaranteed-to-trade strategy on training period: $TRAIN_RANGE"
AGENT_TIMERANGE="$TRAIN_RANGE" \
PYTHONPATH=src python src/agents/trading/self_loop_agent_fixed.py \
    --config "$CONFIG" \
    --timerange "$TRAIN_RANGE" \
    --max-loops 3 \
    --export-trades \
    --spec "Optimize guaranteed-to-trade strategy for available data period $TRAIN_RANGE. This strategy ALWAYS generates trades through multiple entry/exit conditions. Focus on parameter tuning for consistent profitability." \
    > "$RESULTS_DIR/training_log.txt" 2>&1

if [[ $? -eq 0 ]]; then
    echo "[TRAIN] ✓ Training completed successfully"
    cp "user_data/backtest_result.log" "$RESULTS_DIR/training_backtest.log" 2>/dev/null || true
else
    echo "[TRAIN] ✗ Training failed - check $RESULTS_DIR/training_log.txt"
fi

echo ""
echo "[TEST] Validating on test period: $TEST_RANGE"

# Run validation on test period
FREQTRADE_BIN=$(if [ -x ".venv/bin/freqtrade" ]; then echo ".venv/bin/freqtrade"; else echo "freqtrade"; fi)

$FREQTRADE_BIN backtesting \
    --config "$CONFIG" \
    --strategy "$STRATEGY" \
    --strategy-path "strategies" \
    --timeframe "1h" \
    --timerange "$TEST_RANGE" \
    --export trades \
    --cache none \
    > "$RESULTS_DIR/validation_log.txt" 2>&1

if [[ $? -eq 0 ]]; then
    echo "[TEST] ✓ Validation completed successfully"
    cp "user_data/backtest_result.log" "$RESULTS_DIR/validation_backtest.log" 2>/dev/null || true
    
    # Extract key metrics
    echo ""
    echo "=== VALIDATION RESULTS ==="
    echo "Training Period: $TRAIN_RANGE"
    echo "Test Period: $TEST_RANGE"
    echo ""
    
    if [[ -f "$RESULTS_DIR/validation_backtest.log" ]]; then
        echo "Performance Summary:"
        grep -E "(Tot Profit|Trades|Win|Drawdown)" "$RESULTS_DIR/validation_backtest.log" | head -5 || echo "Could not extract metrics"
    fi
    
    echo ""
    echo "Results saved to: $RESULTS_DIR/"
    echo "- training_log.txt (agent optimization)"
    echo "- validation_backtest.log (test results)"
    
else
    echo "[TEST] ✗ Validation failed - check $RESULTS_DIR/validation_log.txt"
fi

echo ""
echo "=== SIMPLE VALIDATION COMPLETE ==="
echo "This approach works with limited data by using train/test split"
echo "For more robust validation, accumulate more historical data over time"
