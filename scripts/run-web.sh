#!/usr/bin/env bash
# Lanza la interfaz web de ADK (adk web).
# Usa el directorio agents/ para que el combo muestre solo el agente "audio_compositor"
# y no carpetas como docs, mcp, scripts (ADK trata cada subdir de AGENTS_DIR como un agente).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
exec adk web agents "$@"
