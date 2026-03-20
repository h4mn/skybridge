# -*- coding: utf-8 -*-
"""
Feature Toggle para Voice API.

DOC: openspec/changes/voice-api-isolation/tasks.md - Fase 1, Task 1.4
Variável de ambiente: SKYBRIDGE_VOICE_API_ENABLED
Default: 0 (desabilitado) - mantém comportamento legado
"""

import os
from typing import Optional


def is_voice_api_enabled() -> bool:
    """
    Verifica se a Voice API está habilitada via feature toggle.

    Returns:
        True se SKYBRIDGE_VOICE_API_ENABLED=1, False caso contrário

    Note:
        - Default: False (comportamento legado)
        - Valor "1" ou "true" (case-insensitive) → True
        - Qualquer outro valor → False
    """
    env_value = os.getenv("SKYBRIDGE_VOICE_API_ENABLED", "0").lower()

    # Aceita "1" ou "true" como habilitado
    return env_value in ("1", "true", "yes")


def get_voice_api_port() -> int:
    """
    Retorna a porta configurada para a Voice API.

    Returns:
        Número da porta (default: 8765)

    Note:
        Variável: VOICE_API_PORT (default: 8765)
        Usada pelo cliente para conectar à API
    """
    port_str = os.getenv("VOICE_API_PORT", "8765")

    try:
        return int(port_str)
    except ValueError:
        # Se inválido, usa default
        return 8765


def get_voice_api_url() -> str:
    """
    Retorna a URL base da Voice API.

    Returns:
        URL completa (ex: "http://127.0.0.1:8765")

    Note:
        Variável: VOICE_API_HOST (default: "127.0.0.1")
        Variável: VOICE_API_PORT (default: "8765")
    """
    host = os.getenv("VOICE_API_HOST", "127.0.0.1")
    port = get_voice_api_port()

    return f"http://{host}:{port}"


__all__ = [
    "is_voice_api_enabled",
    "get_voice_api_port",
    "get_voice_api_url",
]
