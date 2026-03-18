# -*- coding: utf-8 -*-
"""
Envelope — Resposta padrão para APIs CQRS.

Padrão de envelope com correlation_id, timestamp e status.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar
from dataclasses import dataclass
import uuid

from ..contracts.result import Result, Status

T = TypeVar("T")


@dataclass
class Envelope(Generic[T]):
    """
    Envelope padrão para respostas de API.

    Segue o padrão CQRS com correlation_id para rastreabilidade.
    """
    correlation_id: str
    timestamp: str
    status: str
    data: T | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(cls, correlation_id: str | None = None) -> "Envelope[T]":
        """Cria um envelope novo com correlation_id gerado."""
        return cls(
            correlation_id=correlation_id or str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            status="unknown",
        )

    @classmethod
    def from_result(cls, result: Result[T, str], correlation_id: str | None = None) -> "Envelope[T]":
        """Cria envelope a partir de um Result."""
        envelope = cls.create(correlation_id)

        if result.is_ok:
            envelope.status = "success"
            envelope.data = result.value
        else:
            envelope.status = "error"
            envelope.error = str(result.error)

        return envelope

    @classmethod
    def success(cls, data: T, correlation_id: str | None = None, metadata: dict | None = None) -> "Envelope[T]":
        """Cria envelope de sucesso."""
        envelope = cls.create(correlation_id)
        envelope.status = "success"
        envelope.data = data
        envelope.metadata = metadata
        return envelope

    @classmethod
    def failure(cls, error: str, correlation_id: str | None = None, metadata: dict | None = None) -> "Envelope[T]":
        """Cria envelope de erro."""
        envelope = cls.create(correlation_id)
        envelope.status = "error"
        envelope.error = error
        envelope.metadata = metadata
        return envelope

    def to_dict(self) -> dict[str, Any]:
        """Converte para dict (para serialização JSON)."""
        return {
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }
