"""
Thin wrapper so ADK can find root_agent for the agent name 'coordinador_audio'.

ADK looks for: coordinador_audio.agent.root_agent when you run from project root.
The actual agent is defined in agents/coordinador_audio/agent.py.
"""
from agents.coordinador_audio.agent import root_agent

__all__ = ["root_agent"]
