"""
CoordinadorAudio — Agente router para composición sonora.

- Root agent (CoordinadorAudio): router que recomienda y delega al subagente adecuado.
- Subagentes en subagents/: Compositor (Freesound/RedPanal), MusicaConcretaExpert (paletas sonoras).

Referencias ADK:
- MCP tools: https://google.github.io/adk-docs/tools-custom/mcp-tools/
- Multi-agent: https://google.github.io/adk-docs/agents/multi-agents/
"""
from google.adk.agents.llm_agent import LlmAgent

from .config import MODEL
from .instructions import COORDINADOR_INSTRUCTION
from .subagents import create_compositor, create_musica_concreta_expert


def create_root_agent() -> LlmAgent:
    """Agente raíz tipo router: recomienda subagentes y delega con transfer_to_agent."""
    compositor = create_compositor()
    musica_concreta_expert = create_musica_concreta_expert()

    return LlmAgent(
        name="CoordinadorAudio",
        model=MODEL,
        description="Coordinador de expertos en composición sonora: recomienda y delega a subagentes especializados (Compositor para búsqueda y composición, MusicaConcretaExpert para definir paletas sonoras).",
        instruction=COORDINADOR_INSTRUCTION,
        tools=[],
        sub_agents=[compositor, musica_concreta_expert],
    )


root_agent = create_root_agent()
