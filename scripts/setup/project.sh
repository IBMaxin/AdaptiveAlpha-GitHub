#!/usr/bin/env bash
set -euo pipefail

# Always activate .venv-ft2025 first
if [ -z "${VIRTUAL_ENV:-}" ] || [[ "$VIRTUAL_ENV" != *".venv-ft2025"* ]]; then
	if [ -f ".venv-ft2025/bin/activate" ]; then
		source .venv-ft2025/bin/activate
		echo "Venv activated (.venv-ft2025)"
	else
		echo "Warning: .venv-ft2025 virtual environment not found."
	fi
else
	echo "Venv already active: $VIRTUAL_ENV"
fi

cmd="${1:-help}"

case "$cmd" in
start) make start ;;
stop) make stop ;;
status) make status ;;
install) make venv && source .venv/bin/activate && make install dev-install ;;
*) echo "Usage: $0 {start|stop|status|install}" && exit 1 ;;
esac
