#!/bin/bash
# Smart Realistic Validation Setup
# Automatically detects available data range and creates appropriate validation periods

set -e

echo "=== SMART REALISTIC VALIDATION SETUP ==="
echo "Detecting available data and creating appropriate validation periods"
echo ""

# Configuration
PAIRS="BTC/USDT,ETH/USDT,ADA/USDT,SOL/USDT,MATIC/USDT"
TIMEFRAME="1h"
CONFIG="user_data/config.json"

echo "[STEP 1] Detecting available data range..."

# First, download recent data to check what's available
FREQTRADE_BIN=$(if [ -x ".venv/bin/freqtrade" ]; then echo ".venv/bin/freqtrade"; else echo "freqtrade"; fi)

echo "[DATA] Downloading recent data to check availability..."
$FREQTRADE_BIN download-data \
  --config $CONFIG \
  --timeframe $TIMEFRAME \
  --pairs BTC/USDT \
  --exchange binanceus \
  -v || echo "[WARN] Data download had issues"

# Check what data we actually have
echo "[STEP 2] Analyzing available data..."

if [[ -f "user_data/data/binanceus/BTC_USDT-1h.json" ]]; then
    # Use Python to analyze the data range
    python3 -c "
import json
from datetime import datetime

# Load the data
with open('user_data/data/binanceus/BTC_USDT-1h.json', 'r') as f:
    data = json.load(f)

if len(data) > 0:
    first_ts = data[0][0]
    last_ts = data[-1][0]
    
    first_date = datetime.fromtimestamp(first_ts / 1000)
    last_date = datetime.fromtimestamp(last_ts / 1000)
    
    print(f'Available data range:')
    print(f'  Start: {first_date.strftime(\"%Y-%m-%d %H:%M\")}')
    print(f'  End: {last_date.strftime(\"%Y-%m-%d %H:%M\")}')
    print(f'  Total candles: {len(data)}')
    print(f'  Days: {(last_ts - first_ts) / (1000 * 60 * 60 * 24):.1f}')
    
    # Determine appropriate validation range
    days_available = (last_ts - first_ts) / (1000 * 60 * 60 * 24)
    
    if days_available >= 120:  # At least 4 months
        # Use shorter periods for available data
        start_date = first_date.strftime('%Y%m%d')
        end_date = last_date.strftime('%Y%m%d')
        
        print(f'\\nRecommended validation setup:')
        print(f'  Period length: 2 weeks train, 1 week test')
        print(f'  Date range: {start_date} to {end_date}')
        
        # Save the detected range
        with open('user_data/detected_data_range.txt', 'w') as f:
            f.write(f'{start_date}\\n{end_date}\\n{days_available:.1f}\\n')
    else:
        print(f'\\n[WARNING] Only {days_available:.1f} days available')
        print(f'Minimum 120 days needed for proper validation')
        print(f'Available data is too limited for walk-forward validation')
        
        with open('user_data/detected_data_range.txt', 'w') as f:
            f.write('INSUFFICIENT\\n0\\n0\\n')
else:
    print('No data found in file')
    with open('user_data/detected_data_range.txt', 'w') as f:
        f.write('NO_DATA\\n0\\n0\\n')
"
else
    echo "[ERROR] No data file found. Data download may have failed."
    exit 1
fi

# Read the detected range
if [[ -f "user_data/detected_data_range.txt" ]]; then
    START_DATE=$(sed -n '1p' user_data/detected_data_range.txt)
    END_DATE=$(sed -n '2p' user_data/detected_data_range.txt)
    DAYS=$(sed -n '3p' user_data/detected_data_range.txt)
    
    if [[ "$START_DATE" == "INSUFFICIENT" ]]; then
        echo ""
        echo "[LIMITATION] Available data is too limited for proper walk-forward validation"
        echo "Available: $DAYS days"
        echo "Required: 120+ days minimum"
        echo ""
        echo "Options:"
        echo "1. Use shorter validation periods (weekly instead of monthly)"
        echo "2. Use single backtest validation instead of walk-forward"
        echo "3. Wait for more historical data to accumulate"
        echo ""
        exit 1
    elif [[ "$START_DATE" == "NO_DATA" ]]; then
        echo "[ERROR] No data available. Check exchange connectivity."
        exit 1
    fi
else
    echo "[ERROR] Could not detect data range"
    exit 1
fi

echo ""
echo "[STEP 3] Creating validation periods for available data..."

# Generate appropriate validation periods
python scripts/utils/walk_forward_validation.py \
  --start $START_DATE \
  --end $END_DATE \
  --train-months 1 \
  --test-months 1 \
  --step-months 1 \
  --format bash > user_data/walk_forward_periods.sh

PERIOD_COUNT=$(grep -c "TRAIN_RANGE_" user_data/walk_forward_periods.sh || echo 0)

echo ""
echo "=== SMART VALIDATION SETUP COMPLETE ==="
echo "✓ Data range detected: $START_DATE to $END_DATE ($DAYS days)"
echo "✓ Generated $PERIOD_COUNT validation periods"
echo "✓ Using 1 month train / 1 month test periods"
echo ""

if [[ $PERIOD_COUNT -ge 2 ]]; then
    echo "🎯 System ready for validation!"
    echo ""
    echo "Next steps:"
    echo "  bash scripts/utils/run_walk_forward_validation.sh 1 2  # Test first 2 periods"
    echo "  bash scripts/utils/run_walk_forward_validation.sh      # Run all periods"
else
    echo "⚠️  Limited validation capability"
    echo "Only $PERIOD_COUNT periods available"
    echo "Consider single-period backtesting instead"
fi
