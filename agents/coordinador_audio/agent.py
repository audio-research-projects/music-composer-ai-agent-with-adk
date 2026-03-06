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
from .intent_state import update_intent_state
from .subagents import (
    create_compositor,
    create_folclore_argentino_expert,
    create_musica_concreta_expert,
    create_prompt_builder,
)


def create_root_agent() -> LlmAgent:
    """Agente raíz: pregunta BPM y estilo, delega al experto y el flujo termina en PromptBuilder (Suno)."""
    compositor = create_compositor()
    folclore_argentino_expert = create_folclore_argentino_expert()
    musica_concreta_expert = create_musica_concreta_expert()
    prompt_builder = create_prompt_builder()

    return LlmAgent(
        name="CoordinadorAudio",
        model=MODEL,
        description="Coordinador de expertos en composición sonora: pregunta BPM y estilo musical, deriva a FolcloreArgentinoExpert, MusicaConcretaExpert o Compositor, y el flujo termina en PromptBuilder para generar el prompt para Suno desde plantillas.",
        instruction=COORDINADOR_INSTRUCTION,
        tools=[update_intent_state],
        sub_agents=[folclore_argentino_expert, musica_concreta_expert, compositor, prompt_builder],
    )


root_agent = create_root_agent()
