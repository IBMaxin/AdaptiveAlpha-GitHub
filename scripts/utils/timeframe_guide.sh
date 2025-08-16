#!/bin/bash
# Show timeframe comparison for 2024 data download

echo "=== TIMEFRAME COMPARISON FOR 2024 DATA ==="
echo ""
echo "Choose the best timeframe for your trading strategy:"
echo ""

printf "%-10s %-12s %-15s %-12s %-25s\n" "Timeframe" "Candles" "File Size" "Download" "Best For"
printf "%-10s %-12s %-15s %-12s %-25s\n" "----------" "--------" "---------" "--------" "-------------------------"
printf "%-10s %-12s %-15s %-12s %-25s\n" "1m" "~525,600" "~2.5GB/pair" "~30min" "Scalping, HFT"
printf "%-10s %-12s %-15s %-12s %-25s\n" "5m" "~105,120" "~500MB/pair" "~10min" "Day trading"
printf "%-10s %-12s %-15s %-12s %-25s\n" "15m" "~35,040" "~175MB/pair" "~5min" "Swing trading"
printf "%-10s %-12s %-15s %-12s %-25s\n" "1h" "~8,760" "~45MB/pair" "~2min" "Most strategies (default)"
printf "%-10s %-12s %-15s %-12s %-25s\n" "4h" "~2,190" "~11MB/pair" "~1min" "Position trading"
printf "%-10s %-12s %-15s %-12s %-25s\n" "1d" "~365" "~2MB/pair" "<1min" "Long-term analysis"

echo ""
echo "💡 Recommendations:"
echo ""
echo "🚀 For most users:      make data-2024-1h    # Good balance, fast download"
echo "📈 For day trading:     make data-2024-5m    # Higher resolution, reasonable size"
echo "⚡ For scalping:       make data-2024-1m    # Maximum detail, large files"
echo "📊 For swing trading:   make data-2024-15m   # Medium resolution, quick download"
echo "🎯 For backtesting:     make data-2024-1h    # Standard for strategy development"
echo ""
echo "🔄 You can download multiple timeframes - they're stored separately!"
echo ""

read -p "Would you like to see detailed download commands? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "=== DOWNLOAD COMMANDS ==="
    echo ""
    echo "# Quick downloads for 2024:"
    echo "make data-2024-1m      # 1-minute data"
    echo "make data-2024-5m      # 5-minute data"  
    echo "make data-2024-15m     # 15-minute data"
    echo "make data-2024-1h      # 1-hour data (default)"
    echo "make data-2024-4h      # 4-hour data"
    echo "make data-2024-1d      # Daily data"
    echo ""
    echo "# Manual timeframe control:"
    echo "TIMEFRAME=5m bash scripts/utils/data_manager.sh download 20240101 20250101"
    echo "TIMEFRAME=15m bash scripts/utils/data_manager.sh download 20240601 20250101"
    echo ""
    echo "# Check what you have:"
    echo "make data-status       # Show current data"
    echo "make data-analyze      # Detailed analysis"
fi
