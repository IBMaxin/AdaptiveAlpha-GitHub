#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

CONFIG="${CONFIG:-user_data/config.json}"
STRAT="${STRAT:-SmaRsiStrategy}"

"$SCRIPT_DIR/guard.sh" "$CONFIG" "$STRAT"

cmd=("$@")

if [[ "${CONFIRM_LIVE:-NO}" != "YES" ]]; then
	if [[ "${cmd[0]##*/}" == "start_paper.sh" ]]; then
		echo "❌ Live/paper-like command blocked. Set CONFIRM_LIVE=YES to proceed."
		exit 1
	fi
	if [[ "${cmd[0]##*/}" == "freqtrade" && "${cmd[1]:-}" == "trade" ]]; then
		echo "❌ Live/paper-like command blocked. Set CONFIRM_LIVE=YES to proceed."
		exit 1
	fi
fi

echo "▶ ${cmd[*]}"
start_ts=$(date +%s)
set +e
"${cmd[@]}"
rc=$?
set -e
end_ts=$(date +%s)
echo "⏱  Exit $rc in $((end_ts - start_ts))s"
exit "$rc"
