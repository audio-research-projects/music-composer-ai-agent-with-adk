"""Subagente AudioProcessor: procesamiento de audio con FFmpeg y SoX."""
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from ..config import MODEL, ffmpeg_mcp, sox_mcp
from ..instructions import AUDIO_PROCESSOR_INSTRUCTION


def _on_tool_error_cut_process(
    tool: BaseTool,
    args: dict,
    context: ToolContext,
    error: Exception,
) -> dict:
    """Si una tool falla (p. ej. MCP session), cortar el proceso: re-lanzar la excepción."""
    raise error


def create_audio_processor() -> LlmAgent:
    """Subagente especializado en procesamiento de audio con FFmpeg y SoX.
    
    Proporciona herramientas para:
    - FFmpeg: transcodificar, recortar, concatenar, mezclar, extraer audio de video, ajustar volumen, fades
    - SoX: reverb, chorus, flanger, pitch shift, tempo change, compresión, filtros, normalización, análisis
    """
    ffmpeg_tools = ffmpeg_mcp()
    sox_tools = sox_mcp()
    
    return LlmAgent(
        name="AudioProcessor",
        model=MODEL,
        description="Procesador de audio experto: edición lineal, efectos, análisis y conversión con FFmpeg y SoX.",
        instruction=AUDIO_PROCESSOR_INSTRUCTION,
        tools=[ffmpeg_tools, sox_tools],
        on_tool_error_callback=_on_tool_error_cut_process,
    )
