#!/usr/bin/env bash
# Inicializa y descarga los servidores MCP (submodules).
# Ejecutar desde la raíz del repo: ./scripts/setup-mcp.sh
set -e
cd "$(dirname "$0")/.."
git submodule update --init --recursive
echo "MCP servers listos en mcp/freesound-mcp-server y mcp/redpanal-mcp-server"
