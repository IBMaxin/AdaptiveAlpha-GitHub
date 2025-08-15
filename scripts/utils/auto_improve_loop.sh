#!/bin/bash
# Automated improving project loop: generates, tests, and improves strategies in a loop
# Usage: ./scripts/auto_improve_loop.sh [cycles]

set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

CYCLES=${1:-10}

for ((i = 1; i <= CYCLES; i++)); do
	echo "[auto_improve_loop] === Cycle $i/$CYCLES ==="
	python -m agents.self_loop_agent --spec "auto" --config config.json --max-loops 1
	# Optionally, add more checks or notifications here
	sleep 2
	echo "[auto_improve_loop] Cycle $i complete."
done

echo "[auto_improve_loop] All cycles complete."
