"""Subagente MusicaConcretaExpert: definición de paletas sonoras por sección."""
from google.adk.agents.llm_agent import LlmAgent

from ..config import MODEL
from ..instructions import MUSICA_CONCRETA_EXPERT_INSTRUCTION
from ..intent_state import update_intent_state


def create_musica_concreta_expert() -> LlmAgent:
    """Subagente experto en definición de paletas sonoras para música concreta."""
    return LlmAgent(
        name="MusicaConcretaExpert",
        model=MODEL,
        description="Experto en composición de música concreta: ayuda a definir con precisión los sonidos para cada sección de una obra (tipo, frecuencias, comportamiento, timbre). Guía mediante preguntas y sugerencias para construir una paleta sonora clara.",
        instruction=MUSICA_CONCRETA_EXPERT_INSTRUCTION,
        tools=[update_intent_state],
    )
