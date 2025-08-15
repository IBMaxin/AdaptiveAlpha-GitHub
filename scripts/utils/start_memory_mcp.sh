#!/usr/bin/env bash
# Script to start the Memory MCP server for local development
set -euo pipefail
echo "Starting Memory MCP server..."
npx -y @modelcontextprotocol/server-memory
