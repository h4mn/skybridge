# -*- coding: utf-8 -*-
"""
HandlerResult.

Resultado padrão para operações de handlers CQRS.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HandlerResult:
    """
    Resultado de uma operação de handler.

    Usado por todos os handlers CQRS para retornar
    sucesso/erro de forma padronizada.
    """

    success: bool
    """Indica se a operação foi bem-sucedida."""

    message_id: str | None = None
    """ID da mensagem criada (quando aplicável)."""

    error: str | None = None
    """Mensagem de erro (quando success=False)."""

    @classmethod
    def success_with_message(cls, message_id: str) -> "HandlerResult":
        """Cria resultado de sucesso com ID de mensagem."""
        return cls(success=True, message_id=message_id)

    @classmethod
    def failure(cls, error: str) -> "HandlerResult":
        """Cria resultado de falha com mensagem de erro."""
        return cls(success=False, error=error)
