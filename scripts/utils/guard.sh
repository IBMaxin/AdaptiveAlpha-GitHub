#!/usr/bin/env bash
# Hardened guard: validates tools, config.json schema quirks, and common conflicts.
# Optional auto-fix mode: set AUTO_FIX=1 to patch config.json in-place where safe.
set -Eeuo pipefail

CONFIG="${1:-user_data/config.json}"
STRAT="${2:-SmaRsiStrategy}"

DAYS="${DAYS:-}"
TIMERANGE="${TIMERANGE:-}"

fail() {
	echo "❌ $*" >&2
	exit 2
}
warn() { echo "⚠️  $*" >&2; }
info() { echo "ℹ️  $*"; }

command -v freqtrade >/dev/null || fail "freqtrade not found (pipx install freqtrade)."
command -v jq >/dev/null || fail "jq not found (run: sudo apt-get install -y jq)."

[[ -f "$CONFIG" ]] || fail "Missing config: $CONFIG"
jq -e . "$CONFIG" >/dev/null || fail "Config is not valid JSON: $CONFIG"

jget() { jq -r "$1 // empty" "$CONFIG"; }

EXCH="$(jget '.exchange.name')"
[[ -n "$EXCH" ]] || fail "exchange.name missing in $CONFIG (expected 'binanceus')."
[[ "$EXCH" == "binanceus" ]] || warn "exchange.name is '$EXCH' (expected 'binanceus')."

SC="$(jget '.stake_currency')"
[[ -n "$SC" ]] || warn "stake_currency missing; consider 'USDT'."

SL="$(jget '.stoploss')"
if [[ -z "$SL" ]]; then
	if [[ "${AUTO_FIX:-0}" == "1" ]]; then
		info "Adding stoploss=-0.10"
		tmp="$(mktemp)"
		jq '.stoploss = (-0.10)' "$CONFIG" >"$tmp" && mv "$tmp" "$CONFIG"
	else
		warn "stoploss missing; add: \"stoploss\": -0.10"
	fi
fi

if ! jq -e '(.fee|type)=="number" and (.fee>=0 and .fee<=0.1)' "$CONFIG" >/dev/null; then
	if [[ "${AUTO_FIX:-0}" == "1" ]]; then
		info "Normalizing fee to 0.001 (number)"
		tmp="$(mktemp)"
		jq '.fee = 0.001' "$CONFIG" >"$tmp" && mv "$tmp" "$CONFIG"
	else
		warn "fee must be a number (0..0.1). Example: \"fee\": 0.001"
	fi
fi

if jq -e 'has("protections")' "$CONFIG" >/dev/null; then
	if [[ "${AUTO_FIX:-0}" == "1" ]]; then
		info "Removing deprecated protections block"
		tmp="$(mktemp)"
		jq 'del(.protections)' "$CONFIG" >"$tmp" && mv "$tmp" "$CONFIG"
	else
		fail "Deprecated key 'protections' present. Remove it or run with AUTO_FIX=1."
	fi
fi

if jq -e 'has("api_server")' "$CONFIG" >/dev/null; then
	if jq -e '.api_server.enabled==false' "$CONFIG" >/dev/null; then
		if [[ "${AUTO_FIX:-0}" == "1" ]]; then
			info "Removing api_server (disabled)"
			tmp="$(mktemp)"
			jq 'del(.api_server)' "$CONFIG" >"$tmp" && mv "$tmp" "$CONFIG"
		else
			fail "api_server present. Remove it or run with AUTO_FIX=1."
		fi
	fi
fi

if jq -e 'has("telegram")' "$CONFIG" >/dev/null; then
	if [[ "${AUTO_FIX:-0}" == "1" ]]; then
		info "Normalizing telegram block (disabled, token/chat_id empty)"
		tmp="$(mktemp)"
		jq '.telegram = {"enabled": false, "token": "", "chat_id": ""}' "$CONFIG" >"$tmp" && mv "$tmp" "$CONFIG"
	else
		for k in enabled token chat_id; do
			jq -e ".telegram | has(\"$k\")" "$CONFIG" >/dev/null || fail "telegram.$k missing; set AUTO_FIX=1 or add empty value."
		done
	fi
fi

if ! jq -e 'has("exit_pricing")' "$CONFIG" >/dev/null; then
	if [[ "${AUTO_FIX:-0}" == "1" ]]; then
		info "Adding minimal exit_pricing block"
		tmp="$(mktemp)"
		jq '.exit_pricing={"price_side":"same","use_order_book":false,"order_book_top":1}' "$CONFIG" >"$tmp" && mv "$tmp" "$CONFIG"
	else
		warn "exit_pricing missing; some versions require it."
	fi
fi

if [[ -n "$DAYS" ]] && jq -e 'has("timerange") and (.timerange|tostring|length>0)' "$CONFIG" >/dev/null; then
	if [[ "${AUTO_FIX:-0}" == "1" ]]; then
		info "Removing timerange to avoid conflict with --days"
		tmp="$(mktemp)"
		jq 'del(.timerange)' "$CONFIG" >"$tmp" && mv "$tmp" "$CONFIG"
	else
		fail "--days conflicts with .timerange in config. Delete timerange or set AUTO_FIX=1."
	fi
fi

STRAT_FILE="user_data/strategies/${STRAT}.py"
if [[ ! -f "$STRAT_FILE" ]]; then
	warn "Strategy file not found: $STRAT_FILE (class $STRAT). Backtest may fail."
fi

if ! freqtrade list-strategies -c "$CONFIG" >/dev/null 2>&1; then
	warn "freqtrade list-strategies failed (non-fatal). If backtest fails, run: make fix-config"
fi

echo "✅ Guards passed."
