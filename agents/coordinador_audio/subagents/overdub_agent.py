"""Subagente OverdubAgent: diseña capas adicionales (overdubs) para una pista de audio existente."""
from google.adk.agents.llm_agent import LlmAgent

from ..config import MODEL
from ..instructions import OVERDUB_AGENT_INSTRUCTION


def create_overdub_agent() -> LlmAgent:
    """Subagente que describe una capa sonora adicional para agregar a una pista ya existente."""
    return LlmAgent(
        name="OverdubAgent",
        model=MODEL,
        description="Experto en diseñar overdubs: define un solo instrumento o textura que se agrega a un audio existente. Describe rol musical, articulación e interacción con el groove. No crea estructura nueva ni elementos protagonistas.",
        instruction=OVERDUB_AGENT_INSTRUCTION,
        tools=[],
    )
