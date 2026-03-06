# Estructura de agentes y manejo del state

Este documento describe la arquitectura multi-agente del proyecto y cómo se utiliza el **session state** para compartir información entre agentes.

## Arquitectura de agentes

El sistema está organizado como un **router coordinador** con subagentes especializados. El agente raíz (**CoordinadorAudio**) recibe al usuario, recopila información clave (BPM, estilo musical) y delega al subagente más adecuado mediante `transfer_to_agent`.

```
                    ┌─────────────────────┐
                    │  CoordinadorAudio   │  (root)
                    │  - Pregunta BPM     │
                    │  - Pregunta estilo   │
                    │  - update_intent_state
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────────┐    ┌─────────────────┐
│ FolcloreArg.  │    │ MusicaConcreta     │    │ Compositor       │
│ Expert        │    │ Expert             │    │ (Freesound/     │
│               │    │                    │    │  RedPanal)      │
└───────┬───────┘    └─────────┬─────────┘    └─────────────────┘
        │                      │
        └──────────┬──────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
┌────────────┐ ┌─────────┐ ┌──────────────┐
│ RemixAgent │ │Overdub  │ │ PromptBuilder │  (cierre del flujo)
│            │ │Agent    │ │ (plantillas)  │
└────────────┘ └─────────┘ └──────────────┘
```

## Subagentes

| Subagente | Uso | Herramientas |
|-----------|-----|--------------|
| **FolcloreArgentinoExpert** | Folclore argentino (zamba, chacarera, chamamé, milonga, cueca). Afina subgénero, carácter, instrumentación. | `update_intent_state` |
| **MusicaConcretaExpert** | Paletas sonoras por sección (tipo, frecuencias, comportamiento, timbre). | `update_intent_state` |
| **Compositor** | Búsqueda de sonidos (Freesound, RedPanal), composición de obras, listas de sonidos, Supercollider/DAW. | Freesound MCP, RedPanal MCP |
| **RemixAgent** | Sintetiza estilos para remixes o piezas con Suno/Ace. Produce una línea de descriptores (groove, bajo, instrumentación, textura). | — |
| **OverdubAgent** | Diseña una capa adicional (overdub) para una pista existente. Un solo instrumento o textura, rol musical, articulación. | — |
| **PromptBuilder** | Cierra el flujo: crea el prompt final para Suno desde plantillas indexadas. Lee del state si hay datos recopilados. | `search_prompt_templates`, `build_prompt` |

## Flujo típico

1. **Usuario** pide algo (ej: "quiero una zamba de 90 BPM para Suno").
2. **CoordinadorAudio** pregunta BPM y estilo si faltan, llama `update_intent_state` con lo que tenga y transfiere al experto adecuado.
3. **Experto** (FolcloreArgentino, MusicaConcreta, etc.) afina la idea y puede actualizar el state con `update_intent_state` antes de transferir.
4. **PromptBuilder** (cuando el objetivo es Suno) lee del state (`intent_bpm`, `intent_genre`, `intent_summary`) y genera el prompt final con `build_prompt`.

---

## Manejo del session state

El ADK proporciona `session.state`: un diccionario clave-valor asociado a la sesión de conversación. Se usa para acumular información recopilada a lo largo del flujo y que los agentes posteriores puedan leerla sin depender solo del historial del chat.

### Claves utilizadas

| Clave | Tipo | Descripción |
|-------|------|-------------|
| `intent_bpm` | str | Tempo deseado (ej. `"90"` o `"80-100"`). |
| `intent_genre` | str | Estilo o género (ej. `"zamba"`, `"música concreta"`). |
| `intent_summary` | str | Resumen libre: subgénero, carácter, instrumentación, paleta, etc. |

Definidas en `agents/coordinador_audio/intent_state.py` como `STATE_KEY_*`.

### Tool: `update_intent_state`

La herramienta `update_intent_state` escribe en `session.state` mediante el `ToolContext` que el ADK inyecta automáticamente.

**Parámetros (todos opcionales):**
- `bpm`: tempo (número o string)
- `genre`: estilo/género
- `summary`: resumen de la intención

Solo se actualizan las claves cuyos valores sean no nulos.

**Quién la usa:**
- **CoordinadorAudio**: cuando tiene BPM y/o estilo antes de transferir.
- **FolcloreArgentinoExpert** y **MusicaConcretaExpert**: cuando afinan la intención antes de transferir al PromptBuilder.

### Lectura del state

El **PromptBuilder** lee el state de dos formas:

1. **Inyección en la instrucción** con placeholders opcionales del ADK:
   - `{intent_bpm?}` — valor de `intent_bpm` o vacío si no existe
   - `{intent_genre?}` — valor de `intent_genre` o vacío si no existe
   - `{intent_summary?}` — valor de `intent_summary` o vacío si no existe

2. **En la tool `build_prompt`**: si `user_intent` viene vacío pero hay `tool_context`, la función construye la intención automáticamente desde `intent_bpm`, `intent_genre` e `intent_summary` del state.

### Persistencia del state

- Con **InMemorySessionService** (por defecto en desarrollo): el state se pierde al reiniciar la app.
- Con **DatabaseSessionService** o **VertexAiSessionService**: el state se persiste y sobrevive entre reinicios.

Ver [ADK — State](https://google.github.io/adk-docs/sessions/state/) para prefijos opcionales (`user:`, `app:`, `temp:`) y alcance.
