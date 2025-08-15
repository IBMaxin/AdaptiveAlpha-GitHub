#!/bin/bash
# Run all healing agents in sequence

set -e

source ../.venv/bin/activate
python -m agents.orchestrator_agent
