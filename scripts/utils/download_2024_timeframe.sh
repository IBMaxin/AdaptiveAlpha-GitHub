#!/bin/bash
# Download 2024 data with different timeframes

set -e

TIMEFRAME=${1:-"1h"}

echo "=== DOWNLOADING 2024 DATA - $TIMEFRAME TIMEFRAME ==="
echo ""

case $TIMEFRAME in
    "1m")
        echo "📊 1-MINUTE DATA (High Frequency)"
        echo "   • Duration: 365 days"
        echo "   • Expected: ~525,600 candles per pair"
        echo "   • File size: ~2.5 GB per pair"
        echo "   • Use case: Scalping, high-frequency strategies"
        ;;
    "5m")
        echo "📊 5-MINUTE DATA (Day Trading)"
        echo "   • Duration: 365 days" 
        echo "   • Expected: ~105,120 candles per pair"
        echo "   • File size: ~500 MB per pair"
        echo "   • Use case: Day trading, short-term strategies"
        ;;
    "15m")
        echo "📊 15-MINUTE DATA (Swing Trading)"
        echo "   • Duration: 365 days"
        echo "   • Expected: ~35,040 candles per pair"
        echo "   • File size: ~175 MB per pair"
        echo "   • Use case: Swing trading, medium-term strategies"
        ;;
    "1h")
        echo "📊 1-HOUR DATA (Default)"
        echo "   • Duration: 365 days"
        echo "   • Expected: ~8,760 candles per pair"
        echo "   • File size: ~45 MB per pair"
        echo "   • Use case: Most trading strategies, backtesting"
        ;;
    "4h")
        echo "📊 4-HOUR DATA (Long-term)"
        echo "   • Duration: 365 days"
        echo "   • Expected: ~2,190 candles per pair"
        echo "   • File size: ~11 MB per pair"
        echo "   • Use case: Position trading, long-term analysis"
        ;;
    "1d")
        echo "📊 DAILY DATA (Position Trading)"
        echo "   • Duration: 365 days"
        echo "   • Expected: ~365 candles per pair"
        echo "   • File size: ~2 MB per pair"
        echo "   • Use case: Position trading, fundamental analysis"
        ;;
    *)
        echo "❌ Invalid timeframe: $TIMEFRAME"
        echo "Supported: 1m, 5m, 15m, 1h, 4h, 1d"
        exit 1
        ;;
esac

echo ""
echo "Pairs: BTC/USDT, ETH/USDT, ADA/USDT, SOL/USDT, MATIC/USDT"
echo ""

read -p "Continue with $TIMEFRAME timeframe? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Download cancelled"
    exit 0
fi

echo ""
echo "[DOWNLOAD] Starting $TIMEFRAME data download..."

# Use the data manager with specific timeframe
TIMEFRAME=$TIMEFRAME bash scripts/utils/data_manager.sh download 20240101 20250101

echo ""
echo "=== 2024 $TIMEFRAME DATA DOWNLOAD COMPLETE ==="
echo ""
echo "Next steps:"
echo "  make data-status         # Check what was downloaded"
echo "  make data-analyze        # Analyze data quality"  
echo "  TIMEFRAME=$TIMEFRAME make simple-validation   # Run validation"
echo "  TIMEFRAME=$TIMEFRAME make realistic-test      # Run comprehensive testing"
