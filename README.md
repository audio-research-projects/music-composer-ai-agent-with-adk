# Audio Compositor ADK

Agente multi-agente para **componer una obra sonora a partir de un prompt**, construido con **Google Agent Development Kit (ADK)** y **Gemini 2.0 Flash**. Coordina dos subagentes que usan servidores MCP (Model Context Protocol): **Freesound** y **RedPanal**.

Dale al agente una descripción (por ejemplo: "una pieza de 2 minutos, ambiente lluvia y cuerdas, intro suave y climax al final") y buscará sonidos en ambas bases, los seleccionará y te entregará una composición ordenada (lista de sonidos, tiempos sugeridos y, si lo pides, código Supercollider o descripción para DAW).

## Estructura del proyecto

- **AudioCompositor** (agente raíz): interpreta el prompt del usuario y orquesta la composición delegando en los subagentes.
- **FreesoundAgent**: herramientas MCP de [Freesound](https://freesound.org/) — búsqueda por contenido/MIR, info y análisis.
- **RedPanalAgent**: herramientas MCP de [RedPanal](https://redpanal.org/) — listar, detalle, descargar (y subir) audios.

Los servidores MCP están en `mcp/` como **submodules** de Git; se bajan de sus repos al clonar o con `git submodule update --init --recursive`.

## Requisitos

- **Python** ≥ 3.10
- **uv** (para ejecutar los servidores MCP)
- Cuenta y API key en los servicios que uses (Freesound, RedPanal)

## Instalación

1. Clonar el repositorio (incluyendo los servidores MCP) y entrar en el directorio:

   ```bash
   git clone --recurse-submodules <URL_DEL_REPO>
   cd audio-compositor-adk
   ```

   Si ya clonaste sin submodules, bajar los MCP con:

   ```bash
   git submodule update --init --recursive
   # o: ./scripts/setup-mcp.sh
   ```

2. Crear y activar un entorno virtual (recomendado):

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   # .venv\Scripts\activate   # Windows
   ```

3. Instalar dependencias con uv o pip:

   ```bash
   uv sync
   # o: pip install -e .
   ```

4. Los servidores MCP ya están en `mcp/` (submodules). Comprobar que se ejecutan con:

   ```bash
   uv --directory mcp/freesound-mcp-server run mcp_freesound.py
   uv --directory mcp/redpanal-mcp-server run mcp_redpanal.py
   ```

5. Copiar variables de entorno y completarlas:

   ```bash
   cp .env.example .env
   ```

   Editar `.env` y rellenar:

   | Variable              | Descripción |
   |-----------------------|-------------|
   | `GOOGLE_API_KEY`      | API key de Google AI (Gemini). Opcional si solo usas OpenRouter. |
   | `OPENROUTER_API_KEY`  | API key de [OpenRouter](https://openrouter.ai/keys) para el modelo Gemma 3 (LiteLLM). |
   | `FREESOUND_API_KEY`   | API key de Freesound (si usas Freesound). |
   | `REDPANAL_USER`       | Usuario de RedPanal (si usas RedPanal). |
   | `REDPANAL_PASSWORD`   | Contraseña de RedPanal. |

   Por defecto el agente usa **Gemma 3 12B vía OpenRouter** (`openrouter/google/gemma-3-12b-it`). Para cambiar a Gemma 3 4B edita `agent.py`: `MODEL = LiteLlm(model="openrouter/google/gemma-3-4b-it")`.

## Uso

Desde la raíz del proyecto (con el entorno activado):

```bash
# Interfaz por terminal (desde este directorio)
adk run

# Interfaz web: ejecutar desde el directorio **padre** que contiene este proyecto
# (el nombre de la carpeta debe ser un módulo Python válido, p. ej. audio_compositor_adk)
adk web
```

El agente raíz (`root_agent`) está definido en `agent.py` y es el que ADK utiliza por defecto. Las variables de entorno (`.env`) se pasan a los servidores MCP vía `StdioServerParameters.env` para que Freesound y RedPanal reciban las API keys. Para detalle de las herramientas MCP, ver **[docs/TOOLS.md](docs/TOOLS.md)**. Documentación oficial de ADK: [Get started (Python)](https://google.github.io/adk-docs/get-started/python/), [MCP tools](https://google.github.io/adk-docs/tools-custom/mcp-tools/), [Multi-agent systems](https://google.github.io/adk-docs/agents/multi-agents/).

## Dependencias principales

- [google-adk](https://github.com/google/adk) — Agent Development Kit
- [mcp](https://modelcontextprotocol.io/) — Model Context Protocol para herramientas
- [python-dotenv](https://pypi.org/project/python-dotenv/) — Carga de `.env`

Ver `pyproject.toml` para versiones y más dependencias.

## Licencia

Consultar el repositorio para información de licencia.
