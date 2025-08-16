#!/bin/bash
# Walk-Forward Validation Runner
# Runs agent optimization on each validation period

set -e

echo "=== Walk-Forward Validation Runner ==="

# Configuration
CONFIG="user_data/config.json"
STRATEGY="SimpleAlwaysBuySell"
RESULTS_DIR="user_data/walk_forward_results"
PERIODS_FILE="user_data/walk_forward_periods.sh"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Check if periods file exists
if [[ ! -f "$PERIODS_FILE" ]]; then
    echo "[ERROR] Walk-forward periods not found. Run setup first:"
    echo "  bash scripts/utils/setup_realistic_validation.sh"
    exit 1
fi

# Source the periods
source "$PERIODS_FILE"

# Count periods
PERIOD_COUNT=$(grep -c "TRAIN_RANGE_" "$PERIODS_FILE" || echo 0)
echo "[INFO] Found $PERIOD_COUNT validation periods"

if [[ $PERIOD_COUNT -eq 0 ]]; then
    echo "[ERROR] No validation periods found"
    exit 1
fi

# Function to run single period validation
run_period_validation() {
    local period=$1
    local train_range_var="TRAIN_RANGE_$period"
    local test_range_var="TEST_RANGE_$period"
    
    local train_range=${!train_range_var}
    local test_range=${!test_range_var}
    
    if [[ -z "$train_range" || -z "$test_range" ]]; then
        echo "[SKIP] Period $period: Missing range definition"
        return 1
    fi
    
    echo ""
    echo "=== PERIOD $period ==="
    echo "Train: $train_range"
    echo "Test:  $test_range"
    
    local period_dir="$RESULTS_DIR/period_$period"
    mkdir -p "$period_dir"
    
    # Run training optimization
    echo "[TRAIN] Optimizing on training period..."
    AGENT_TIMERANGE="$train_range" \
    PYTHONPATH=src python src/agents/trading/self_loop_agent_fixed.py \
        --config "$CONFIG" \
        --timerange "$train_range" \
        --max-loops 5 \
        --export-trades \
        --spec "Optimize strategy for training period $train_range. Focus on robust parameters that generalize well. Use conservative risk management." \
        > "$period_dir/training_log.txt" 2>&1
    
    if [[ $? -eq 0 ]]; then
        echo "[TRAIN] ✓ Training completed successfully"
        cp "user_data/backtest_result.log" "$period_dir/training_backtest.log"
        
        # Extract optimized parameters
        if [[ -f "strategies/SimpleAlwaysBuySell.py" ]]; then
            cp "strategies/SimpleAlwaysBuySell.py" "$period_dir/optimized_strategy.py"
        fi
    else
        echo "[TRAIN] ✗ Training failed"
        return 1
    fi
    
    # Run validation on test period
    echo "[TEST] Validating on test period..."
    FREQTRADE_BIN=$(if [ -x ".venv/bin/freqtrade" ]; then echo ".venv/bin/freqtrade"; else echo "freqtrade"; fi)
    
    $FREQTRADE_BIN backtesting \
        --config "$CONFIG" \
        --strategy "$STRATEGY" \
        --strategy-path "strategies" \
        --timeframe "1h" \
        --timerange "$test_range" \
        --export trades \
        --cache none \
        > "$period_dir/validation_log.txt" 2>&1
    
    if [[ $? -eq 0 ]]; then
        echo "[TEST] ✓ Validation completed successfully"
        cp "user_data/backtest_result.log" "$period_dir/validation_backtest.log"
        
        # Extract key metrics
        extract_metrics "$period_dir/validation_backtest.log" > "$period_dir/metrics.txt"
    else
        echo "[TEST] ✗ Validation failed"
        return 1
    fi
    
    echo "[PERIOD $period] ✓ Completed"
    return 0
}

# Function to extract key metrics from backtest results
extract_metrics() {
    local log_file=$1
    
    if [[ ! -f "$log_file" ]]; then
        echo "No metrics available"
        return
    fi
    
    echo "=== VALIDATION METRICS ==="
    
    # Extract key metrics using awk/grep
    local total_profit=$(grep "Tot Profit" "$log_file" | awk '{print $5}' | head -1)
    local profit_pct=$(grep "Tot Profit" "$log_file" | awk '{print $7}' | head -1)
    local trades=$(grep "Trades" "$log_file" | awk '{print $3}' | head -1)
    local win_rate=$(grep "Win" "$log_file" | awk '{print $8}' | head -1)
    local drawdown=$(grep "Drawdown" "$log_file" | awk '{print $3}' | head -1)
    
    echo "Total Profit: ${total_profit:-N/A}"
    echo "Profit %: ${profit_pct:-N/A}"
    echo "Trades: ${trades:-N/A}"
    echo "Win Rate: ${win_rate:-N/A}"
    echo "Max Drawdown: ${drawdown:-N/A}"
}

# Main execution
echo "[INFO] Starting walk-forward validation..."
echo "[INFO] Results will be saved to: $RESULTS_DIR"

# Initialize summary
SUMMARY_FILE="$RESULTS_DIR/validation_summary.txt"
echo "=== WALK-FORWARD VALIDATION SUMMARY ===" > "$SUMMARY_FILE"
echo "Generated: $(date)" >> "$SUMMARY_FILE"
echo "Periods: $PERIOD_COUNT" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

# Run validation for specified periods (or all if no argument)
START_PERIOD=${1:-1}
END_PERIOD=${2:-$PERIOD_COUNT}

echo "[INFO] Running periods $START_PERIOD to $END_PERIOD"

successful_periods=0
failed_periods=0

for period in $(seq $START_PERIOD $END_PERIOD); do
    if run_period_validation $period; then
        ((successful_periods++))
        echo "Period $period: SUCCESS" >> "$SUMMARY_FILE"
    else
        ((failed_periods++))
        echo "Period $period: FAILED" >> "$SUMMARY_FILE"
    fi
done

# Final summary
echo "" >> "$SUMMARY_FILE"
echo "Successful: $successful_periods" >> "$SUMMARY_FILE"
echo "Failed: $failed_periods" >> "$SUMMARY_FILE"
echo "Success Rate: $(( successful_periods * 100 / (successful_periods + failed_periods) ))%" >> "$SUMMARY_FILE"

echo ""
echo "=== VALIDATION COMPLETE ==="
echo "✓ Processed $((successful_periods + failed_periods)) periods"
echo "✓ Success rate: $(( successful_periods * 100 / (successful_periods + failed_periods) ))%"
echo "✓ Results saved to: $RESULTS_DIR"
echo "✓ Summary: $SUMMARY_FILE"

# Show summary
echo ""
echo "=== SUMMARY ==="
cat "$SUMMARY_FILE"
