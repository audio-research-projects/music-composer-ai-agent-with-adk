"""Subagente FolcloreArgentinoExpert: experto en folclore argentino (zamba, chacarera, chamamé, etc.)."""
from google.adk.agents.llm_agent import LlmAgent

from ..config import MODEL
from ..instructions import FOLCLORE_ARGENTINO_EXPERT_INSTRUCTION
from ..intent_state import update_intent_state


def create_folclore_argentino_expert() -> LlmAgent:
    """Subagente experto en folclore argentino; afina estilo y deriva a PromptBuilder para Suno."""
    return LlmAgent(
        name="FolcloreArgentinoExpert",
        model=MODEL,
        description="Experto en folclore argentino: zamba, chacarera, chamamé, milonga, cueca, etc. Ayuda a definir subgénero, carácter, instrumentación y región. Una vez definido, transfiere al PromptBuilder para generar el prompt final para Suno.",
        instruction=FOLCLORE_ARGENTINO_EXPERT_INSTRUCTION,
        tools=[update_intent_state],
    )
