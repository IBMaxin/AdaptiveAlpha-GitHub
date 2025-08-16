#!/bin/bash
# Quick command to download data from January 1, 2024 to January 1, 2025

set -e

echo "=== DOWNLOADING 2024 FULL YEAR DATA ==="
echo "From: January 1, 2024 to January 1, 2025"
echo "Duration: 365 days (~8,760 hours of 1h candles)"
echo ""

# Use the data manager with specific date range
bash scripts/utils/data_manager.sh download 20240101 20250101

echo ""
echo "=== 2024 DATA DOWNLOAD COMPLETE ==="
echo ""
echo "Next steps:"
echo "  make data-status         # Check what was downloaded"
echo "  make data-analyze        # Analyze data quality"  
echo "  make simple-validation   # Run validation with new data"
echo "  make realistic-test      # Run comprehensive testing"
