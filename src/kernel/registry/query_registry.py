# -*- coding: utf-8 -*-
"""
Query Registry — Registro e discovery de query handlers.

Simples implementação de registry para pattern CQRS.
"""

from typing import Callable, TypeVar, Dict, Any
from dataclasses import dataclass

from ..contracts.result import Result
from ..envelope.envelope import Envelope

Q = TypeVar("Q")  # Query type
R = TypeVar("R")  # Result type


@dataclass
class QueryHandler:
    """Wrapper para query handler."""
    name: str
    handler: Callable[..., Result[Any, str]]
    description: str | None = None
    kind: str = "query"
    notification_allowed: bool = False
    tags: list[str] | None = None
    auth: str | None = None
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


class QueryRegistry:
    """
    Registry centralizado para query handlers.

    Usage:
        registry = QueryRegistry()
        registry.register("health", health_handler, "Health check endpoint")
        handler = registry.get("health")
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, QueryHandler] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Result[Any, str]],
        description: str | None = None,
        *,
        kind: str = "query",
        notification_allowed: bool = False,
        tags: list[str] | None = None,
        auth: str | None = None,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> None:
        """Registra um query handler."""
        if "_" in name:
            raise ValueError(
                f"Query handler name must use context.action (no underscores): {name}"
            )
        if name in self._handlers:
            raise ValueError(f"Query handler already registered: {name}")
        self._handlers[name] = QueryHandler(
            name=name,
            handler=handler,
            description=description,
            kind=kind,
            notification_allowed=notification_allowed,
            tags=tags,
            auth=auth,
            input_schema=input_schema,
            output_schema=output_schema,
        )

    def get(self, name: str) -> QueryHandler | None:
        """Retorna um handler pelo nome."""
        return self._handlers.get(name)

    def list_all(self) -> list[QueryHandler]:
        """Lista todos os handlers registrados."""
        return list(self._handlers.values())

    def has(self, name: str) -> bool:
        """Verifica se um handler existe."""
        return name in self._handlers

    def clear(self) -> None:
        """Limpa handlers registrados (uso em testes)."""
        self._handlers.clear()


# Singleton global
_query_registry = QueryRegistry()


def get_query_registry() -> QueryRegistry:
    """Retorna o registry global."""
    return _query_registry
