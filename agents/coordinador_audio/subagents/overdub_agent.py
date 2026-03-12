"""Subagente OverdubAgent: diseña capas adicionales y aplica timbre transfer con DDSP."""
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from ..config import MODEL, ddsp_mcp
from ..instructions import OVERDUB_AGENT_INSTRUCTION


def _on_tool_error_cut_process(
    tool: BaseTool,
    args: dict,
    context: ToolContext,
    error: Exception,
) -> dict:
    """Si una tool falla (p. ej. MCP session), cortar el proceso: re-lanzar la excepción."""
    raise error


def create_overdub_agent() -> LlmAgent:
    """Subagente que diseña overdubs y aplica timbre transfer con DDSP.
    
    Combina descripción de capas adicionales con capacidad de transformar
    audio usando modelos neuronales DDSP (timbre transfer).
    """
    ddsp_tools = ddsp_mcp()
    
    return LlmAgent(
        name="OverdubAgent",
        model=MODEL,
        description="Experto en diseñar overdubs y aplicar timbre transfer con DDSP: transforma audio a diferentes instrumentos (violin, flute, sax, etc.) manteniendo la melodía original.",
        instruction=OVERDUB_AGENT_INSTRUCTION,
        tools=[ddsp_tools],
        on_tool_error_callback=_on_tool_error_cut_process,
    )
