"""Subagentes del CoordinadorAudio."""
from .compositor import create_compositor
from .musica_concreta import create_musica_concreta_expert

__all__ = ["create_compositor", "create_musica_concreta_expert"]
