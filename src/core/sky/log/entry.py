# coding: utf-8
"""
LogEntry - Entry de log imutável.

Usa logging padrão do Python (nível = int) e permite
escopo para categorização adicional.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.sky.log.scope import LogScope

# Enum é singleton e imutável, seguro usar como default
_LOG_SCOPE_DEFAULT = LogScope.ALL


@dataclass(frozen=True)
class LogEntry:
    """Entry de log imutável.

    Attributes:
        level: Nível do log (usar logging.DEBUG, logging.INFO, etc.)
        message: Mensagem de log
        timestamp: Timestamp da mensagem
        scope: Escopo/categoria da mensagem (default: LogScope.ALL)
        context: Metadados adicionais opcionais (default: None)
    """

    level: int
    message: str
    timestamp: datetime
    scope: LogScope = _LOG_SCOPE_DEFAULT
    context: dict[str, Any] | None = None

    def matches_filter(self, level_min: int, scope: LogScope) -> bool:
        """Verifica se este entry passa pelos filtros de nível e escopo.

        Args:
            level_min: Nível mínimo (ex: logging.ERROR mostra ERROR e CRITICAL)
            scope: Escopo desejado (LogScope.ALL mostra todos)

        Returns:
            True se entry passa por AMBOS os filtros (AND lógico)
        """
        # Filtro por nível
        if self.level < level_min:
            return False

        # Filtro por escopo: ALL ignora o scope do entry
        if scope is not LogScope.ALL:
            # Escopo específico: filtra por scope do entry
            if self.scope != scope:
                return False

        return True


__all__ = ["LogEntry"]
