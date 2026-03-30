# -*- coding: utf-8 -*-
"""Prompts Templates - Templates de mensagens Discord."""

from .saudacao import get_saudacao_padrao, get_saudacao_personalizada
from .erro import (
    get_erro_padrao,
    get_erro_canal_nao_autorizado,
    get_erro_mensagem_nao_encontrada,
    get_erro_anexo_grande,
    get_erro_rate_limit,
)
from .progresso import (
    get_progresso_iniciado,
    get_progresso_em_andamento,
    get_progresso_concluido,
    get_progresso_erro,
)

__all__ = [
    "get_saudacao_padrao",
    "get_saudacao_personalizada",
    "get_erro_padrao",
    "get_erro_canal_nao_autorizado",
    "get_erro_mensagem_nao_encontrada",
    "get_erro_anexo_grande",
    "get_erro_rate_limit",
    "get_progresso_iniciado",
    "get_progresso_em_andamento",
    "get_progresso_concluido",
    "get_progresso_erro",
]
