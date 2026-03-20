# coding: utf-8
"""
Bootstrap stages - Estágios individuais do bootstrap.

Cada stage é responsável por inicializar um componente específico.
"""

from .voice_api import VoiceAPIStage, get_voice_api_stage, _stage_voice_api

__all__ = [
    "VoiceAPIStage",
    "get_voice_api_stage",
    "_stage_voice_api",
]
