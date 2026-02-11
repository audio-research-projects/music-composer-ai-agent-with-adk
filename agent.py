"""
Punto de entrada del agente para ADK (CLI, API, etc.).

El agente real vive en agents/coordinador_audio/ (agent.py + subagents/).
Este módulo reexporta root_agent para compatibilidad con scripts que se ejecutan
desde la raíz del proyecto (p. ej. adk run, import agent).
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agents.coordinador_audio.agent import root_agent
