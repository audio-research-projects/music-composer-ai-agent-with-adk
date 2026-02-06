# Herramientas MCP del Audio Compositor

El agente utiliza dos servidores MCP cuyos repositorios viven en `mcp/`. La integración sigue la guía de ADK [MCP tools](https://google.github.io/adk-docs/tools-custom/mcp-tools/) (`McpToolset`, `StdioConnectionParams`, `StdioServerParameters`).

- **Freesound**: `mcp/freesound-mcp-server` — búsqueda y análisis de sonidos en [Freesound.org](https://freesound.org).
- **RedPanal**: `mcp/redpanal-mcp-server` — listado, detalle, descarga y subida de audios en [RedPanal](https://redpanal.org).

---

## Freesound MCP (`freesound_mcp`)

Requiere `FREESOUND_API_KEY` en el entorno. Obtener key: https://freesound.org/home/login/?next=/apiv2/apply

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `get_freesound_basic_info` | Información básica de un sonido por ID | `sound_id: str` |
| `get_freesound_search_by_content` | Búsqueda por texto (descripción de contenido) | `sound_content_description: str` |
| `get_freesound_descriptor` | Descriptor de análisis (ej. `lowlevel.spectral_centroid`). Ver [analysis_docs](https://freesound.org/docs/api/analysis_docs.html) | `sound_id: str`, `descriptor: str` |
| `get_freesound_full_sound_analysis` | Análisis completo del sonido (normalizado) | `sound_id: str` |
| `get_freesound_search_by_mir_features` | Búsqueda por características MIR (duración, bpm, descriptores numéricos 0..1) | `sound_mir_features_description: str` |

### Ejemplos de uso (desde el agente)

- Buscar sonidos: `get_freesound_search_by_content("rain ambience")`
- Ver análisis: `get_freesound_full_sound_analysis("12345")` o `get_freesound_descriptor("12345", "lowlevel.spectral_centroid")`

---

## RedPanal MCP (`redpanal_mcp`)

Opcionalmente `REDPANAL_USER` y `REDPANAL_PASSWORD` para subir audios.

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `list_audios` | Lista audios con filtros opcionales | `genre: str = None`, `tag: str = None`, `page: int = 1`, `page_size: int = 10` |
| `get_audio_detail` | Detalle de un audio por ID | `audio_id: int` |
| `download_sample` | Descarga un archivo por URL y lo convierte a WAV; devuelve ruta e info | `soundfile_url: str` |
| `upload_audio` | Sube un audio (requiere auth) | `file_path`, `name`, `description`, `use_type`, `genre`, `instrument`, `tags: list` |

### Ejemplos de uso (desde el agente)

- Listar por género/etiqueta: `list_audios(genre="ambient", tag="field-recording")`
- Detalle: `get_audio_detail(123)`
- Descargar y obtener WAV: `download_sample("https://redpanal.org/.../archivo.mp3")`

---

## Flujo de composición sugerido

1. **Interpretar el prompt** del usuario (estilo, atmósfera, instrumentos, duración, estructura).
2. **Buscar en Freesound** con `get_freesound_search_by_content` (y opcionalmente MIR) para encontrar candidatos.
3. **Buscar en RedPanal** con `list_audios` (género/tag) para más candidatos.
4. **Refinar** con `get_freesound_basic_info` / `get_audio_detail` y, si hace falta, análisis con `get_freesound_full_sound_analysis` o `get_freesound_descriptor`.
5. **Componer la obra** como:
   - Lista ordenada de sonidos (ID, fuente, orden, sugerencia de inicio/duración), y/o
   - Script o descripción para Supercollider/DAW si el usuario lo pide.
6. **Descargar** los elegidos con `download_sample` (RedPanal) cuando haya URLs; para Freesound el usuario puede descargar desde la web con el ID devuelto.
