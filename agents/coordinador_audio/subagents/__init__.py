"""Subagentes del CoordinadorAudio."""
from .audio_processor import create_audio_processor
from .compositor import create_compositor
from .folclore_argentino import create_folclore_argentino_expert
from .musica_concreta import create_musica_concreta_expert
from .overdub_agent import create_overdub_agent
from .prompt_builder import create_prompt_builder
from .remix_agent import create_remix_agent

__all__ = [
    "create_audio_processor",
    "create_compositor",
    "create_folclore_argentino_expert",
    "create_musica_concreta_expert",
    "create_overdub_agent",
    "create_prompt_builder",
    "create_remix_agent",
]
