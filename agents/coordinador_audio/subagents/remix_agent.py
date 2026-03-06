"""Subagente RemixAgent: sintetiza estilos musicales para remixes o piezas con modelos generativos (Suno, Ace)."""
from google.adk.agents.llm_agent import LlmAgent

from ..config import MODEL
from ..instructions import REMIX_AGENT_INSTRUCTION


def create_remix_agent() -> LlmAgent:
    """Subagente que convierte la conversación en un prompt compacto de estilo musical (una línea, descriptores)."""
    return LlmAgent(
        name="RemixAgent",
        model=MODEL,
        description="Experto en sintetizar estilos musicales para remixes o composiciones con modelos generativos (Suno, Ace). Convierte la conversación en una sola línea de descriptores (groove, bajo, instrumentación, textura, estructura, energía).",
        instruction=REMIX_AGENT_INSTRUCTION,
        tools=[],
    )
