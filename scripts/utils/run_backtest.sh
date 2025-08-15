#!/usr/bin/env bash
set -euo pipefail
: "${CONFIG:?CONFIG required}"
: "${STRAT:?STRAT required}"
: "${TIMEFRAME:?TIMEFRAME required}"

TIMERANGE="${TIMERANGE:-}"

if [[ -n "$TIMERANGE" ]]; then
	freqtrade backtesting -c "$CONFIG" -s "$STRAT" --timeframe "$TIMEFRAME" --timerange "$TIMERANGE" --export trades
else
	freqtrade backtesting -c "$CONFIG" -s "$STRAT" --timeframe "$TIMEFRAME" --export trades
fi
