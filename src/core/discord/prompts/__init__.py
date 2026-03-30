# -*- coding: utf-8 -*-
"""
Prompts Module - Sistema de prompts do Discord.

Consolida todos os prompts para uso pelo agente.

DOC: DDD Migration - Prompts Module
"""

from .identidade import get_identity_prompt
from .contexto import get_context_prompt
from .tools_guide import get_tools_guide_prompt
from .seguranca import get_security_prompt


def get_discord_system_prompt() -> str:
    """
    Retorna o prompt completo do sistema Discord.

    Combina identidade, contexto, guia de tools e segurança.
    """
    return f"""
{get_identity_prompt()}

{get_context_prompt()}

{get_tools_guide_prompt()}

{get_security_prompt()}
"""


__all__ = [
    "get_identity_prompt",
    "get_context_prompt",
    "get_tools_guide_prompt",
    "get_security_prompt",
    "get_discord_system_prompt",
]
