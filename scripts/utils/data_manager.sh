#!/bin/bash
# Smart Data Management Utility
# Provides easy data management for trading agents

set -e

echo "=== FREQTRADE DATA MANAGEMENT ==="
echo ""

# Configuration
CONFIG="user_data/config.json"
TIMEFRAME=${TIMEFRAME:-"1h"}  # Default to 1h, but allow override
DATA_DIR="user_data/data"
FREQTRADE_BIN=$(if [ -x ".venv/bin/freqtrade" ]; then echo ".venv/bin/freqtrade"; else echo "freqtrade"; fi)

show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  status              - Show current data status and file sizes"
    echo "  append              - Download and append new data (default)"
    echo "  refresh             - Erase all data and download fresh"
    echo "  check               - Check what data exists without downloading"
    echo "  clean               - Remove all downloaded data"
    echo "  analyze             - Analyze data quality and gaps"
    echo "  download START END  - Download specific date range (YYYYMMDD format)"
    echo ""
    echo "Environment Variables:"
    echo "  TIMEFRAME           - Set timeframe (1m, 5m, 15m, 1h, 4h, 1d) [default: 1h]"
    echo ""
    echo "Examples:"
    echo "  $0 status                    # Check current data (1h default)"
    echo "  TIMEFRAME=5m $0 append       # Download 5-minute data"
    echo "  TIMEFRAME=15m $0 refresh     # Fresh 15-minute data"
    echo "  TIMEFRAME=1h $0 download 20240101 20250101  # 1-hour data for 2024"
    echo "  $0 clean                     # Remove all data"
    echo ""
    echo "Supported Timeframes:"
    echo "  1m   - 1 minute   (High frequency, large files)"
    echo "  5m   - 5 minutes  (Good balance for day trading)"
    echo "  15m  - 15 minutes (Popular for swing trading)"
    echo "  1h   - 1 hour     (Default, good for most strategies)"
    echo "  4h   - 4 hours    (Longer-term analysis)"
    echo "  1d   - 1 day      (Position trading)"
}

show_status() {
    echo "[STATUS] Data directory: $DATA_DIR"
    
    if [[ ! -d "$DATA_DIR" ]]; then
        echo "✗ No data directory found"
        echo "  Run: $0 append    # To download initial data"
        return
    fi
    
    # Count files and sizes
    DATA_FILES=$(find "$DATA_DIR" -name "*.json" 2>/dev/null || echo "")
    if [[ -z "$DATA_FILES" ]]; then
        echo "✗ No data files found in $DATA_DIR"
        echo "  Run: $0 append    # To download data"
        return
    fi
    
    FILE_COUNT=$(echo "$DATA_FILES" | wc -l)
    TOTAL_SIZE=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1 || echo "unknown")
    
    echo "✓ Found $FILE_COUNT data files ($TOTAL_SIZE total)"
    echo ""
    echo "Data files:"
    
    for file in $DATA_FILES; do
        if [[ -f "$file" ]]; then
            SIZE=$(du -sh "$file" | cut -f1)
            BASENAME=$(basename "$file")
            
            # Get date range from file
            FIRST_DATE=$(python3 -c "
import json, sys
try:
    with open('$file', 'r') as f:
        data = json.load(f)
    if data:
        from datetime import datetime
        first_ts = data[0][0] / 1000
        last_ts = data[-1][0] / 1000
        first_date = datetime.fromtimestamp(first_ts).strftime('%Y-%m-%d')
        last_date = datetime.fromtimestamp(last_ts).strftime('%Y-%m-%d')
        print(f'{len(data)} candles, {first_date} to {last_date}')
    else:
        print('empty file')
except:
    print('error reading file')
" 2>/dev/null || echo "unknown")
            
            echo "  - $BASENAME ($SIZE) - $FIRST_DATE"
        fi
    done
}

append_data() {
    echo "[APPEND] Downloading and appending new data..."
    
    $FREQTRADE_BIN download-data \
        -c "$CONFIG" \
        -t "$TIMEFRAME" \
        -v
    
    echo "✓ Data append completed"
}

download_range() {
    local START_DATE="$1"
    local END_DATE="$2"
    
    if [[ -z "$START_DATE" ]] || [[ -z "$END_DATE" ]]; then
        echo "Error: Both start and end dates required"
        echo "Format: YYYYMMDD (e.g., 20240101)"
        echo "Example: $0 download 20240101 20250101"
        return 1
    fi
    
    # Validate date format
    if [[ ! "$START_DATE" =~ ^[0-9]{8}$ ]] || [[ ! "$END_DATE" =~ ^[0-9]{8}$ ]]; then
        echo "Error: Invalid date format. Use YYYYMMDD"
        echo "Example: $0 download 20240101 20250101"
        return 1
    fi
    
    # Convert to readable format for confirmation
    START_READABLE=$(date -d "${START_DATE:0:4}-${START_DATE:4:2}-${START_DATE:6:2}" +"%B %d, %Y" 2>/dev/null || echo "$START_DATE")
    END_READABLE=$(date -d "${END_DATE:0:4}-${END_DATE:4:2}-${END_DATE:6:2}" +"%B %d, %Y" 2>/dev/null || echo "$END_DATE")
    
    echo "[DOWNLOAD] Downloading data for specific range:"
    echo "  From: $START_READABLE ($START_DATE)"
    echo "  To:   $END_READABLE ($END_DATE)"
    echo "  Timeframe: $TIMEFRAME"
    echo ""
    
    # Calculate approximate duration
    if command -v date >/dev/null 2>&1; then
        START_EPOCH=$(date -d "${START_DATE:0:4}-${START_DATE:4:2}-${START_DATE:6:2}" +%s 2>/dev/null || echo 0)
        END_EPOCH=$(date -d "${END_DATE:0:4}-${END_DATE:4:2}-${END_DATE:6:2}" +%s 2>/dev/null || echo 0)
        if [[ $START_EPOCH -gt 0 ]] && [[ $END_EPOCH -gt 0 ]]; then
            DAYS=$(( (END_EPOCH - START_EPOCH) / 86400 ))
            echo "  Duration: $DAYS days"
            
            # Calculate expected candles based on timeframe
            case $TIMEFRAME in
                "1m")   CANDLES_PER_DAY=1440; INTERVAL="minute" ;;
                "5m")   CANDLES_PER_DAY=288;  INTERVAL="5-minute" ;;
                "15m")  CANDLES_PER_DAY=96;   INTERVAL="15-minute" ;;
                "1h")   CANDLES_PER_DAY=24;   INTERVAL="hour" ;;
                "4h")   CANDLES_PER_DAY=6;    INTERVAL="4-hour" ;;
                "1d")   CANDLES_PER_DAY=1;    INTERVAL="day" ;;
                *)      CANDLES_PER_DAY=24;   INTERVAL="hour" ;;  # Default
            esac
            
            EXPECTED_CANDLES=$(( DAYS * CANDLES_PER_DAY ))
            echo "  Expected candles: ~$EXPECTED_CANDLES ($INTERVAL timeframe)"
            
            # Estimate file size
            ESTIMATED_SIZE_MB=$(( EXPECTED_CANDLES * 5 / 1000 ))  # Rough estimate
            if [[ $ESTIMATED_SIZE_MB -gt 1000 ]]; then
                echo "  Estimated size: ~$(( ESTIMATED_SIZE_MB / 1000 )) GB per pair"
            else
                echo "  Estimated size: ~${ESTIMATED_SIZE_MB} MB per pair"
            fi
            echo ""
        fi
    fi
    
    # Create timerange string
    TIMERANGE="${START_DATE}-${END_DATE}"
    
    echo "[DOWNLOAD] Running freqtrade download..."
    $FREQTRADE_BIN download-data \
        -c "$CONFIG" \
        -t "$TIMEFRAME" \
        --timerange "$TIMERANGE" \
        -v
    
    if [[ $? -eq 0 ]]; then
        echo "✓ Range download completed successfully"
        echo ""
        echo "[INFO] Showing updated data status:"
        show_status
    else
        echo "✗ Range download failed"
        echo "[TROUBLESHOOT] Common issues:"
        echo "  - Date range too far in the past (exchange limits)"
        echo "  - Network connectivity issues"
        echo "  - Invalid date range (end before start)"
        echo "  - Exchange API rate limits"
        return 1
    fi
}

refresh_data() {
    echo "[REFRESH] This will DELETE ALL existing data and download fresh"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "[REFRESH] Removing existing data..."
        if [[ -d "$DATA_DIR" ]]; then
            rm -rf "$DATA_DIR"
            echo "✓ Existing data removed"
        fi
        
        echo "[REFRESH] Downloading fresh data..."
        $FREQTRADE_BIN download-data \
            -c "$CONFIG" \
            -t "$TIMEFRAME" \
            -v
        
        echo "✓ Fresh data download completed"
    else
        echo "Refresh cancelled"
    fi
}

check_data() {
    echo "[CHECK] Checking existing data without downloading..."
    show_status
    
    if [[ -d "$DATA_DIR" ]] && [[ -n "$(find "$DATA_DIR" -name "*.json" 2>/dev/null)" ]]; then
        echo ""
        echo "✓ Data exists - no download needed"
        echo "  Use: $0 append    # To add new data"
        echo "  Use: $0 refresh   # To start fresh"
    else
        echo ""
        echo "✗ No data found - download needed"
        echo "  Use: $0 append    # To download initial data"
    fi
}

clean_data() {
    echo "[CLEAN] This will DELETE ALL downloaded data"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ -d "$DATA_DIR" ]]; then
            rm -rf "$DATA_DIR"
            echo "✓ All data removed"
        else
            echo "✓ No data directory found (already clean)"
        fi
    else
        echo "Clean cancelled"
    fi
}

analyze_data() {
    echo "[ANALYZE] Analyzing data quality and coverage..."
    
    if [[ ! -d "$DATA_DIR" ]]; then
        echo "✗ No data directory found"
        return
    fi
    
    DATA_FILES=$(find "$DATA_DIR" -name "*.json" 2>/dev/null || echo "")
    if [[ -z "$DATA_FILES" ]]; then
        echo "✗ No data files found"
        return
    fi
    
    echo "Detailed analysis:"
    
    python3 -c "
import json, os
from datetime import datetime, timedelta
from pathlib import Path

data_dir = Path('$DATA_DIR')
total_candles = 0
earliest_date = None
latest_date = None
pairs_info = {}

for file_path in data_dir.rglob('*.json'):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not data:
            continue
            
        pair_name = file_path.stem.replace('_', '/')
        candle_count = len(data)
        total_candles += candle_count
        
        first_ts = data[0][0] / 1000
        last_ts = data[-1][0] / 1000
        
        first_date = datetime.fromtimestamp(first_ts)
        last_date = datetime.fromtimestamp(last_ts)
        
        if earliest_date is None or first_date < earliest_date:
            earliest_date = first_date
        if latest_date is None or last_date > latest_date:
            latest_date = last_date
            
        duration = last_date - first_date
        expected_candles = int(duration.total_seconds() / 3600)  # 1h timeframe
        coverage = (candle_count / expected_candles * 100) if expected_candles > 0 else 0
        
        pairs_info[pair_name] = {
            'candles': candle_count,
            'start': first_date,
            'end': last_date,
            'duration_days': duration.days,
            'coverage': coverage
        }
        
    except Exception as e:
        print(f'Error reading {file_path}: {e}')

print(f'\\nSummary:')
print(f'  Total candles: {total_candles:,}')
if earliest_date and latest_date:
    print(f'  Date range: {earliest_date.strftime(\"%Y-%m-%d\")} to {latest_date.strftime(\"%Y-%m-%d\")}')
    total_days = (latest_date - earliest_date).days
    print(f'  Total span: {total_days} days')

print(f'\\nPer-pair analysis:')
for pair, info in pairs_info.items():
    print(f'  {pair:12} {info[\"candles\"]:6,} candles, {info[\"duration_days\"]:3} days, {info[\"coverage\"]:5.1f}% coverage')

# Check for gaps
print(f'\\nData quality:')
avg_coverage = sum(info['coverage'] for info in pairs_info.values()) / len(pairs_info) if pairs_info else 0
print(f'  Average coverage: {avg_coverage:.1f}%')

if avg_coverage > 95:
    print('  ✓ Excellent data quality')
elif avg_coverage > 85:
    print('  ✓ Good data quality')
elif avg_coverage > 70:
    print('  ⚠️  Fair data quality - some gaps present')
else:
    print('  ✗ Poor data quality - significant gaps')
"
}

# Main command handling
COMMAND=${1:-status}
START_DATE=$2
END_DATE=$3

case $COMMAND in
    status)
        show_status
        ;;
    append)
        append_data
        ;;
    download)
        download_range "$START_DATE" "$END_DATE"
        ;;
    refresh)
        refresh_data
        ;;
    check)
        check_data
        ;;
    clean)
        clean_data
        ;;
    analyze)
        analyze_data
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
