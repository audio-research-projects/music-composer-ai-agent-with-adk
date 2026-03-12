"""Subagente Compositor: búsqueda en Freesound/RedPanal y composición de obras."""
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from ..config import MCP_DIR, MODEL, mcp_toolset
from ..instructions import COMPOSITOR_INSTRUCTION


def _on_tool_error_cut_process(
    tool: BaseTool,
    args: dict,
    context: ToolContext,
    error: Exception,
) -> dict:
    """Si una tool falla (p. ej. MCP session), cortar el proceso: re-lanzar la excepción."""
    raise error


def create_compositor() -> LlmAgent:
    """Subagente compositor con herramientas de búsqueda en Freesound y RedPanal."""
    freesound = mcp_toolset(
        MCP_DIR / "freesound-mcp-server",
        "mcp_freesound.py",
        "freesound_mcp",
    )
    redpanal = mcp_toolset(
        MCP_DIR / "redpanal-mcp-server",
        "mcp_redpanal.py",
        "redpanal_mcp",
    )
    return LlmAgent(
        name="Compositor",
        model=MODEL,
        description="Compositor sonoro: busca sonidos en Freesound y RedPanal, y crea obras completas con listas ordenadas de sonidos, tiempos sugeridos, y código Supercollider o descripciones para DAW.",
        instruction=COMPOSITOR_INSTRUCTION,
        tools=[freesound, redpanal],
        on_tool_error_callback=_on_tool_error_cut_process,
    )
