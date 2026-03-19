# coding: utf-8
"""
LogScope - Escopo/Categoria de logs.

Define categorias para filtrar logs por tipo/contexto.
Uso combinado com nível (logging.DEBUG, logging.INFO, etc.)
permite filtros poderosos como "apenas errors de voz".
"""

from enum import Enum


class LogScope(Enum):
    """Escopo de log - categoria/contexto da mensagem.

    Usado em conjunto com nível (logging.DEBUG, logging.INFO, etc.)
    para filtros poderosos. Exemplo: "apenas errors de voz".
    """

    ALL = "all"
    SYSTEM = "system"
    USER = "user"
    API = "api"
    DATABASE = "database"
    NETWORK = "network"
    VOICE = "voice"
    MEMORY = "memory"


__all__ = ["LogScope"]
