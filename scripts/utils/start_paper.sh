#!/usr/bin/env bash
set -euo pipefail
CONFIG="${1:-user_data/config.json}"
STRAT="${2:-SmaRsiStrategy}"

if [[ "${CONFIRM_LIVE:-NO}" != "YES" ]]; then
	echo "❌ Set CONFIRM_LIVE=YES to run paper mode."
	exit 2
fi

echo "⚠️  Starting paper mode with $STRAT (dry_run must be true in config)"
freqtrade trade -c "$CONFIG" --strategy "$STRAT"
