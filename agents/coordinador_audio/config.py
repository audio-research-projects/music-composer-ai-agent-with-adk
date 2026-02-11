"""Configuración compartida: .env, modelo LiteLLM (OpenAI u OpenRouter), MCP."""
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.models import LiteLlm
from mcp import StdioServerParameters

# Raíz del proyecto (agents/coordinador_audio/ -> subir 2 niveles)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
    load_dotenv()

# Prioridad: si tienes OPENAI_API_KEY (paga), se usa OpenAI (estable, tools bien soportados).
# Si no, se usa OpenRouter (OPENROUTER_API_KEY + modelo free; puede dar 404/upstream).
if os.environ.get("OPENAI_API_KEY", "").strip():
    _model_id = os.environ.get("OPENAI_MODEL", "openai/gpt-4o-mini").strip()
    MODEL = LiteLlm(model=_model_id)  # LiteLLM usa OPENAI_API_KEY automáticamente
else:
    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        raise RuntimeError(
            "Define OPENROUTER_API_KEY en .env (https://openrouter.ai/keys) o "
            "OPENAI_API_KEY (https://platform.openai.com/api-keys) para usar OpenAI."
        )
    _model_id = os.environ.get(
        "OPENROUTER_MODEL",
        "openrouter/meta-llama/llama-3.2-3b-instruct:free",
    ).strip()
    MODEL = LiteLlm(model=_model_id)
MCP_DIR = BASE_DIR / "mcp"
MCP_ENV_KEYS = ("FREESOUND_API_KEY", "REDPANAL_USER", "REDPANAL_PASSWORD", "GOOGLE_API_KEY")


def _mcp_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k in MCP_ENV_KEYS and v}


def mcp_toolset(directory: Path, script: str, name: str) -> McpToolset:
    """Crea un McpToolset para un servidor MCP en stdio (uv run)."""
    uv_cmd = shutil.which("uv") or "uv"  # ruta absoluta si está en PATH (evita "Failed to create MCP session")
    return McpToolset(
        tool_name_prefix=name,
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=uv_cmd,
                args=["--directory", str(directory.resolve()), "run", script],
                env=_mcp_env() or None,
            )
        ),
    )
