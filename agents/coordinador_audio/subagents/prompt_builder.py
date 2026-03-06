"""Subagente PromptBuilder: crea prompts a partir de plantillas .txt indexadas en Chroma."""
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.tool_context import ToolContext

from ..config import MODEL
from ..instructions import PROMPT_BUILDER_INSTRUCTION
from ..intent_state import STATE_KEY_BPM, STATE_KEY_GENRE, STATE_KEY_SUMMARY
from ..prompt_templates.store import search


def search_prompt_templates(query: str, n_results: int = 5) -> dict:
    """
    Busca plantillas de prompt por similitud semántica con la consulta.

    Usa la base de plantillas indexada (archivos .txt en prompt_templates/). Devuelve
    los fragmentos más relevantes para que el agente pueda elegir o combinar.

    Args:
        query: Descripción de lo que el usuario quiere (estilo, atmósfera, uso).
        n_results: Número máximo de plantillas a devolver (por defecto 5).

    Returns:
        dict con status y lista "templates": cada elemento tiene "text", "source", "metadata".
    """
    try:
        results = search(query=query, n_results=n_results)
        return {
            "status": "success",
            "templates": [
                {"text": r["text"], "source": r["source"], "metadata": r.get("metadata", {})}
                for r in results
            ],
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e), "templates": []}


def build_prompt(
    user_intent: str = "",
    template_snippets: list[str] | None = None,
    tool_context: ToolContext | None = None,
) -> dict:
    """
    Construye un prompt final combinando la intención del usuario con fragmentos de plantillas.

    Si user_intent está vacío pero hay session state (intent_bpm, intent_genre, intent_summary),
    se construye la intención desde el state. Si ya obtuviste fragmentos con search_prompt_templates,
    pásalos en template_snippets.

    Args:
        user_intent: Lo que el usuario quiere (estilo, duración, Suno, etc.). Opcional si hay state.
        template_snippets: Lista opcional de textos de plantillas a incorporar.
        tool_context: Inyectado por el ADK; se usa para leer intent_* del session state.

    Returns:
        dict con status, "prompt" (texto final listo para usar) y "usage_note".
    """
    try:
        intent = user_intent.strip() if user_intent else ""
        if not intent and tool_context and tool_context.state:
            parts = []
            if tool_context.state.get(STATE_KEY_BPM):
                parts.append(f"BPM: {tool_context.state[STATE_KEY_BPM]}")
            if tool_context.state.get(STATE_KEY_GENRE):
                parts.append(f"Género/estilo: {tool_context.state[STATE_KEY_GENRE]}")
            if tool_context.state.get(STATE_KEY_SUMMARY):
                parts.append(tool_context.state[STATE_KEY_SUMMARY])
            intent = " ".join(parts) if parts else "Composición para Suno"
        if not intent:
            intent = "Composición para Suno"
        if template_snippets:
            snippets = template_snippets
        else:
            results = search(query=intent, n_results=3)
            snippets = [r["text"] for r in results]
        if not snippets:
            prompt = intent
            usage_note = "Sin plantillas similares; prompt basado solo en tu descripción. Úsalo en el Compositor o copia a Suno/ACE."
        else:
            parts = [intent]
            for s in snippets:
                if s.strip() and s.strip() not in parts:
                    parts.append(s.strip())
            prompt = "\n\n".join(parts)
            usage_note = "Combinado con ejemplos de la biblioteca. Puedes usarlo aquí con el Compositor o copiarlo a Suno/ACE."
        return {
            "status": "success",
            "prompt": prompt,
            "usage_note": usage_note,
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e), "prompt": "", "usage_note": ""}


def create_prompt_builder() -> LlmAgent:
    """Subagente que ayuda a crear o refinar prompts desde plantillas indexadas."""
    return LlmAgent(
        name="PromptBuilder",
        model=MODEL,
        description="Experto en crear prompts para composición sonora o para herramientas externas (Suno, ACE). Busca en una biblioteca de plantillas por similitud y combina con la intención del usuario para producir un prompt listo para usar en el Compositor o para copiar fuera.",
        instruction=PROMPT_BUILDER_INSTRUCTION,
        tools=[search_prompt_templates, build_prompt],
    )
