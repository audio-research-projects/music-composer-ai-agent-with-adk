#!/usr/bin/env bash
# Lanza la web de ADK; "uv run" asegura que uv esté en PATH para los servidores MCP.
cd "$(dirname "$0")"
[[ -f .env ]] && set -a && source .env && set +a
exec uv run adk web agents "$@"
