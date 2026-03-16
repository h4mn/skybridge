"""
Processamento de Texto para Sky.

Este módulo fornece funções para processamento de texto,
incluindo limpeza de markdown para TTS e outras utilidades.
"""

from .markdown import strip_for_tts, strip_markdown, MarkdownCleanupConfig

__all__ = [
    "strip_for_tts",
    "strip_markdown",
    "MarkdownCleanupConfig",
]
