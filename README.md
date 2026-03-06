# Audio Compositor ADK

Sistema multi-agente para **componer obras sonoras** y **generar prompts para Suno/Ace**, construido con **Google Agent Development Kit (ADK)**. El agente raíz (**CoordinadorAudio**) pregunta BPM y estilo musical, deriva a expertos especializados y puede cerrar el flujo con el **PromptBuilder**, que crea prompts desde plantillas indexadas. Usa herramientas MCP de **Freesound** y **RedPanal**, además de tools propias para el **session state**.

## Estructura del proyecto

- **agent.py** (raíz): importa `root_agent` desde `agents/coordinador_audio/`.
- **agents/coordinador_audio/**: agente raíz (CoordinadorAudio) y subagentes (FolcloreArgentino, MusicaConcreta, Compositor, RemixAgent, OverdubAgent, PromptBuilder).
- **Freesound** (`freesound_mcp`) y **RedPanal** (`redpanal_mcp`): tools MCP para búsqueda de sonidos.
- **docs/AGENTS.md**: documentación de la estructura de agentes y manejo del session state.

Los servidores MCP están en `mcp/` como **submodules** de Git; se bajan con `git submodule update --init --recursive`.

Para la arquitectura de agentes y el manejo del state, ver **[docs/AGENTS.md](docs/AGENTS.md)**.

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
   | `OPENAI_API_KEY`      | **Opción recomendada si quieres que funcione estable.** Key en [OpenAI](https://platform.openai.com/api-keys). Si está definida, se usa OpenAI (p. ej. gpt-4o-mini) y no hace falta OpenRouter. |
   | `OPENROUTER_API_KEY`  | Para usar modelos free vía [OpenRouter](https://openrouter.ai/keys). Solo se usa si no hay `OPENAI_API_KEY`. Puede dar 404 o "Upstream error" con modelos free. |
   | `FREESOUND_API_KEY`   | API key de Freesound (si usas Freesound). |
   | `REDPANAL_USER`       | Usuario de RedPanal (si usas RedPanal). |
   | `REDPANAL_PASSWORD`   | Contraseña de RedPanal. |

   Si defines **`OPENAI_API_KEY`** (cuenta paga), se usa **OpenAI** por defecto (`gpt-4o-mini`); tools y delegación funcionan de forma estable. Si no, se usa **OpenRouter** con el modelo free por defecto; puedes cambiar con `OPENAI_MODEL` o `OPENROUTER_MODEL` en `.env`.

## Uso

### Cómo saber si un modelo es compatible con tools y es free

Este agente usa **tools** (delegación a subagentes, Freesound, RedPanal), así que el modelo en OpenRouter debe soportar **tool/function calling** y, si quieres costo cero, ser **free**.

1. **Modelos que soportan tools**  
   Filtro oficial: [openrouter.ai/models?supported_parameters=tools](https://openrouter.ai/models?supported_parameters=tools). Cualquier modelo listado ahí acepta `tools` en la API.

2. **Ver en la ficha del modelo**  
   Entra en la página del modelo (ej: [Gemma 3 4B (free)](https://openrouter.ai/google/gemma-3-4b-it:free)). Debe aparecer:
   - **Tools** (o "Function calling") en características / parámetros soportados.
   - **$0/M** (o variante "free") si es gratuito.

3. **Sufijo `:free`**  
   En OpenRouter, muchos modelos gratuitos usan el sufijo `:free` en el ID (ej: `google/gemma-3-4b-it:free`). No todos los `:free` soportan tools; hay que comprobarlo en la ficha o en el filtro del punto 1.

Si usas un modelo sin soporte de tools, verás el error: *"No endpoints found that support tool use"* (404).

---

**Importante:** `adk run` se ejecuta desde la raíz (donde está `agent.py`). Para la web usamos `adk web agents`: el agente está en `agents/coordinador_audio/`.

Desde la raíz del proyecto (con el entorno activado):

```bash
# Interfaz por terminal
adk run

# Interfaz web (agente: coordinador_audio). Usar "uv run" para que uv esté en PATH y los MCP arranquen.
uv run adk web agents
```

O usando el script (carga `.env` y lanza la web):

```bash
./scripts/run-web.sh
```

**Si ves "Failed to create MCP session":** los servidores MCP (Freesound, RedPanal) se arrancan con `uv`. Ejecuta desde la raíz con `uv run adk web agents` (o `./scripts/run-web.sh`, que debería usar el mismo entorno). Comprueba que los submodules estén inicializados: `git submodule update --init --recursive`.

El agente raíz (`root_agent`) está definido en `agent.py` y es el que ADK utiliza por defecto. Las variables de entorno (`.env`) se pasan a los servidores MCP vía `StdioServerParameters.env` para que Freesound y RedPanal reciban las API keys. Para detalle de las herramientas MCP, ver **[docs/TOOLS.md](docs/TOOLS.md)**. Para la estructura de agentes y el manejo del session state, ver **[docs/AGENTS.md](docs/AGENTS.md)**.

Documentación oficial de ADK: [Get started (Python)](https://google.github.io/adk-docs/get-started/python/), [MCP tools](https://google.github.io/adk-docs/tools-custom/mcp-tools/), [Multi-agent systems](https://google.github.io/adk-docs/agents/multi-agents/), [Session state](https://google.github.io/adk-docs/sessions/state/).

### Prompt templates (PromptBuilder)

El subagente **PromptBuilder** crea prompts a partir de plantillas almacenadas en la carpeta `prompt_templates/`. Las plantillas se indexan en una base vectorial (Chroma); en tiempo de ejecución el agente **no** lee los archivos .txt, solo consulta el índice por similitud.

- **Dónde poner plantillas:** archivos `.txt` en `prompt_templates/` (un ejemplo de prompt por archivo; el nombre del archivo se usa como referencia).
- **Indexar después de añadir o editar plantillas:**
  ```bash
  uv run python -m scripts.index_prompt_templates
  ```
  Opcional: otro directorio con `--dir ruta/a/mis_plantillas`.
- La base Chroma se guarda en `data/prompt_templates_db/` (está en `.gitignore`). Si no has ejecutado el script, PromptBuilder seguirá funcionando pero con la biblioteca vacía (solo la intención del usuario).

## Dependencias principales

- [google-adk](https://github.com/google/adk) — Agent Development Kit
- [mcp](https://modelcontextprotocol.io/) — Model Context Protocol para herramientas
- [python-dotenv](https://pypi.org/project/python-dotenv/) — Carga de `.env`
- [chromadb](https://www.trychroma.com/) — Base vectorial para plantillas de prompt
- [sentence-transformers](https://www.sbert.net/) — Embeddings locales para indexar y buscar plantillas

Ver `pyproject.toml` para versiones y más dependencias.

## Licencia

Consultar el repositorio para información de licencia.
