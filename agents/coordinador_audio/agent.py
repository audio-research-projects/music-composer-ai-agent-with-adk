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
    create_overdub_agent,
    create_prompt_builder,
    create_remix_agent,
)


def create_root_agent() -> LlmAgent:
    """Agente raíz: pregunta BPM y estilo, delega al experto adecuado (folclore, concreta, compositor, remix, overdub, prompt)."""
    compositor = create_compositor()
    folclore_argentino_expert = create_folclore_argentino_expert()
    musica_concreta_expert = create_musica_concreta_expert()
    overdub_agent = create_overdub_agent()
    prompt_builder = create_prompt_builder()
    remix_agent = create_remix_agent()

    return LlmAgent(
        name="CoordinadorAudio",
        model=MODEL,
        description="Coordinador de expertos en composición sonora: pregunta BPM y estilo, deriva a FolcloreArgentinoExpert, MusicaConcretaExpert, Compositor, RemixAgent, OverdubAgent o PromptBuilder según la necesidad.",
        instruction=COORDINADOR_INSTRUCTION,
        tools=[update_intent_state],
        sub_agents=[
            folclore_argentino_expert,
            musica_concreta_expert,
            compositor,
            remix_agent,
            overdub_agent,
            prompt_builder,
        ],
    )


root_agent = create_root_agent()
