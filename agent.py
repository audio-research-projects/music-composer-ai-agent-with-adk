"""
Audio Compositor — Agente que compone una obra sonora a partir de un prompt,
usando Freesound y RedPanal vía MCP.

Sigue los patrones de ADK para multi-agentes y MCP:
- https://google.github.io/adk-docs/agents/multi-agents/
- https://google.github.io/adk-docs/tools-custom/mcp-tools/
- Modelo vía LiteLLM (OpenRouter): https://google.github.io/adk-docs/agents/models/litellm/
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

# Modelo vía OpenRouter (LiteLLM). Ejemplo: Gemma 2 9B free tier.
# La API key se lee de OPENROUTER_API_KEY en .env (nunca commitear la key).
MODEL = LiteLlm(model="openrouter/google/gemma-2-9b-it:free")

BASE_DIR = Path(__file__).resolve().parent
MCP_DIR = BASE_DIR / "mcp"

# Variables que los servidores MCP deben recibir por entorno (StdioServerParameters.env)
MCP_ENV_KEYS = ("FREESOUND_API_KEY", "REDPANAL_USER", "REDPANAL_PASSWORD", "GOOGLE_API_KEY")


def _mcp_env() -> dict[str, str]:
    """Entorno para los subprocesos MCP (solo claves necesarias)."""
    return {k: v for k, v in os.environ.items() if k in MCP_ENV_KEYS and v}


COMPOSITOR_INSTRUCTION = """Eres un compositor sonoro. Tu tarea es crear una obra o pieza de audio a partir del prompt del usuario.

Flujo de trabajo:
1. Interpreta el prompt: estilo, atmósfera, instrumentos, duración, estructura (intro, desarrollo, cierre).
2. Busca sonidos en Freesound (FreesoundAgent) con búsqueda por contenido o por características MIR cuando convenga.
3. Busca sonidos en RedPanal (RedPanalAgent) por género, etiquetas o listando audios.
4. Selecciona los sonidos más adecuados; si necesitas refinar, usa get_freesound_basic_info, get_audio_detail o análisis.
5. Componer la obra:
   - Entrega una lista ordenada de sonidos: fuente (Freesound/RedPanal), ID o nombre, orden de aparición, y sugerencia de inicio/duración en la pieza.
   - Opcionalmente, si el usuario lo pide, sugiere código Supercollider o una descripción para un DAW para reproducir la pieza.
6. Para RedPanal puedes usar download_sample con la URL del archivo para obtener un WAV local; para Freesound indica el ID y la URL para que el usuario pueda descargar.

Responde en el mismo idioma que use el usuario. Sé concreto con IDs, nombres y tiempos."""


def mcp_toolset(directory: Path, script: str, name: str) -> McpToolset:
    """Crea un McpToolset para un servidor MCP en stdio (uv run)."""
    return McpToolset(
        name=name,
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="uv",
                args=["--directory", str(directory), "run", script],
                env=_mcp_env() or None,  # Pasa API keys al subproceso MCP (ver ADK MCP tools)
            )
        ),
    )


def create_root_agent() -> LlmAgent:
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

    freesound_agent = LlmAgent(
        name="FreesoundAgent",
        model=MODEL,
        description="Busca y obtiene información o análisis de sonidos en Freesound.org (búsqueda por contenido, MIR, descriptores). Delega aquí cuando el usuario necesite muestras de Freesound.",
        tools=[freesound],
    )
    redpanal_agent = LlmAgent(
        name="RedPanalAgent",
        model=MODEL,
        description="Lista, detalla y descarga audios de RedPanal.org; puede subir audios con autenticación. Delega aquí para catálogo o descargas de RedPanal.",
        tools=[redpanal],
    )

    return LlmAgent(
        name="AudioCompositor",
        model=MODEL,
        description="Compone una obra sonora a partir de un prompt del usuario usando Freesound y RedPanal.",
        instruction=COMPOSITOR_INSTRUCTION,
        sub_agents=[freesound_agent, redpanal_agent],
    )


root_agent = create_root_agent()
