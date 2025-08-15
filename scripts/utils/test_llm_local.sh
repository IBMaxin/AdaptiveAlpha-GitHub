#!/bin/bash
# Test if local LM Studio is being used by the agent system
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate
python scripts/test_llm_local.py
