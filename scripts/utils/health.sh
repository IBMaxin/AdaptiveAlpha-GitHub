#!/usr/bin/env bash
set -euo pipefail

LM="${LMSTUDIO_BASE_URL:-http://localhost:1234/v1}"
OR="${OPENROUTER_BASE_URL:-https://openrouter.ai/api/v1}"
KEY="${OPENROUTER_API_KEY:-}"

echo "🔎 Checking LM Studio at $LM ..."
if curl -sS -m 3 "$LM/models" >/dev/null; then
	echo "✅ LM Studio OK"
else
	echo "❌ LM Studio not responding"
fi

if [ -n "$KEY" ]; then
	echo "🔎 Checking OpenRouter ..."
	if curl -sS -m 5 -H "Authorization: Bearer $KEY" "$OR/models" >/dev/null; then
		echo "✅ OpenRouter OK"
	else
		echo "❌ OpenRouter check failed (key set but request failed)"
	fi
else
	echo "ℹ️  OpenRouter not tested (no API key set)"
fi
