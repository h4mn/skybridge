# -*- coding: utf-8 -*-
"""
Template de Erro - Discord Module.

Templates para mensagens de erro no Discord.

DOC: DDD Migration - Prompts Templates
"""

ERRO_PADRAO = """
❌ **Ocorreu um erro**

{mensagem}

Por favor, tente novamente ou contate o suporte se o problema persistir.
"""

ERRO_CANAL_NAO_AUTORIZADO = """
🚫 **Canal não autorizado**

Este canal não está na lista de canais permitidos.

Para adicionar este canal, use: `/discord:access`
"""

ERRO_MENSAGEM_NAO_ENCONTRADA = """
🔍 **Mensagem não encontrada**

Não foi possível encontrar a mensagem `{message_id}`.

Verifique o ID e tente novamente.
"""

ERRO_ANEXO_GRANDE = """
📎 **Anexo muito grande**

O arquivo `{filename}` excede o limite de 25MB.

Por favor, use um link ou compacte o arquivo.
"""

ERRO_RATE_LIMIT = """
⏳ **Muitas solicitações**

Aguarde um momento antes de enviar novas mensagens.

Discord tem limites de taxa para evitar spam.
"""


def get_erro_padrao(mensagem: str) -> str:
    """Retorna erro padrão com mensagem customizada."""
    return ERRO_PADRAO.format(mensagem=mensagem)


def get_erro_canal_nao_autorizado() -> str:
    """Retorna erro de canal não autorizado."""
    return ERRO_CANAL_NAO_AUTORIZADO


def get_erro_mensagem_nao_encontrada(message_id: str) -> str:
    """Retorna erro de mensagem não encontrada."""
    return ERRO_MENSAGEM_NAO_ENCONTRADA.format(message_id=message_id)


def get_erro_anexo_grande(filename: str) -> str:
    """Retorna erro de anexo grande."""
    return ERRO_ANEXO_GRANDE.format(filename=filename)


def get_erro_rate_limit() -> str:
    """Retorna erro de rate limit."""
    return ERRO_RATE_LIMIT
