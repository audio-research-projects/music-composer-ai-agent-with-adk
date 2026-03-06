"""Tool para guardar en session.state lo que se recopila (BPM, género, resumen de intención)."""
from google.adk.tools.tool_context import ToolContext


# Claves de state usadas por coordinador, expertos y PromptBuilder
STATE_KEY_BPM = "intent_bpm"
STATE_KEY_GENRE = "intent_genre"
STATE_KEY_SUMMARY = "intent_summary"


def update_intent_state(
    bpm: str | int | None = None,
    genre: str | None = None,
    summary: str | None = None,
    tool_context: ToolContext | None = None,
) -> dict:
    """
    Guarda en el state de la sesión los datos recopilados (BPM, género, resumen).

    Llama a esta herramienta cuando tengas BPM y/o estilo musical y/o un resumen
    de la intención del usuario, para que el siguiente agente (experto o PromptBuilder)
    pueda leerlo desde session.state.

    Args:
        bpm: Tempo deseado (número o string, ej. 90 o "80-100").
        genre: Estilo o género (ej. "zamba", "música concreta", "electrónica").
        summary: Resumen libre de la intención (subgénero, carácter, instrumentación, etc.).
        tool_context: Inyectado por el ADK; no lo rellenes tú.

    Returns:
        dict con status y las claves actualizadas en state.
    """
    if tool_context is None:
        return {"status": "error", "error_message": "No hay contexto de sesión.", "updated": []}
    state = tool_context.state
    updated = []
    if bpm is not None:
        state[STATE_KEY_BPM] = str(bpm).strip()
        updated.append(STATE_KEY_BPM)
    if genre is not None:
        state[STATE_KEY_GENRE] = str(genre).strip()
        updated.append(STATE_KEY_GENRE)
    if summary is not None:
        state[STATE_KEY_SUMMARY] = str(summary).strip()
        updated.append(STATE_KEY_SUMMARY)
    return {"status": "success", "updated": updated}
