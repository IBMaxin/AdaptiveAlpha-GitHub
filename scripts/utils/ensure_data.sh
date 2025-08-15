#!/usr/bin/env bash
set -euo pipefail
: "${CONFIG:?CONFIG required}"
: "${TIMEFRAME:?TIMEFRAME required}"
: "${DAYS:?DAYS required}"

if [[ -n "${PAIRLIST:-}" ]]; then
	IFS=',' read -ra P <<<"$PAIRLIST"
	for pair in "${P[@]}"; do
		freqtrade download-data -c "$CONFIG" --timeframe "$TIMEFRAME" --days "$DAYS" -p "$pair"
	done
else
	freqtrade download-data -c "$CONFIG" --timeframe "$TIMEFRAME" --days "$DAYS"
fi
