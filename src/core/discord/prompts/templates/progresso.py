# -*- coding: utf-8 -*-
"""
Template de Progresso - Discord Module.

Templates para mensagens de progresso no Discord.

DOC: DDD Migration - Prompts Templates
"""

PROGRESSO_INICIADO = """
⏳ **{titulo}**

Iniciando processamento...
"""

PROGRESSO_EM_ANDAMENTO = """
⏳ **{titulo}**

{barra} {porcentagem}%

{status}
"""

PROGRESSO_CONCLUIDO = """
✅ **{titulo}**

Processamento concluído com sucesso!

{resumo}
"""

PROGRESSO_ERRO = """
❌ **{titulo}**

Ocorreu um erro durante o processamento:

{erro}
"""


def get_progresso_iniciado(titulo: str) -> str:
    """Retorna mensagem de início de progresso."""
    return PROGRESSO_INICIADO.format(titulo=titulo)


def get_progresso_em_andamento(titulo: str, barra: str, porcentagem: int, status: str) -> str:
    """Retorna mensagem de progresso em andamento."""
    return PROGRESSO_EM_ANDAMENTO.format(
        titulo=titulo,
        barra=barra,
        porcentagem=porcentagem,
        status=status
    )


def get_progresso_concluido(titulo: str, resumo: str = "") -> str:
    """Retorna mensagem de progresso concluído."""
    return PROGRESSO_CONCLUIDO.format(titulo=titulo, resumo=resumo)


def get_progresso_erro(titulo: str, erro: str) -> str:
    """Retorna mensagem de erro de progresso."""
    return PROGRESSO_ERRO.format(titulo=titulo, erro=erro)
