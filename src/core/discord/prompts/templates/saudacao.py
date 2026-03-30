# -*- coding: utf-8 -*-
"""
Template de Saudação - Discord Module.

Templates para mensagens de saudação no Discord.

DOC: DDD Migration - Prompts Templates
"""

SAUDACAO_PADRAO = """
👋 **Olá!** Eu sou o SkyBridge, seu assistente de trading.

Estou aqui para ajudar você com:
- 📊 Análise de portfólio
- 📈 Gráficos de desempenho
- ⚙️ Configurações
- 💰 Operações de trading

Como posso ajudar hoje?
"""

SAUDACAO_COM_NOME = """
👋 **Olá, {nome}!** Eu sou o SkyBridge.

Estou pronto para ajudar com suas operações de trading.
O que você gostaria de fazer?
"""


def get_saudacao_padrao() -> str:
    """Retorna saudação padrão."""
    return SAUDACAO_PADRAO


def get_saudacao_personalizada(nome: str) -> str:
    """Retorna saudação personalizada."""
    return SAUDACAO_COM_NOME.format(nome=nome)
