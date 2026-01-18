# -*- coding: utf-8 -*-
"""
Query Registry — Registro e discovery de query handlers.

Simples implementação de registry para pattern CQRS.
"""

from typing import Callable, TypeVar, Dict, Any, List, Tuple
from dataclasses import dataclass

from ..contracts.result import Result
from ..envelope.envelope import Envelope

try:
    from thefuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

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

    def fuzzy_search(
        self,
        query: str,
        *,
        limit: int = 5,
        min_score: int = 60,
        scorer: Callable[[str, str], int] | None = None
    ) -> List[Tuple[str, QueryHandler, int]]:
        """
        Busca handlers usando fuzzy matching.

        Args:
            query: String de busca (pode conter erros de digitação)
            limit: Número máximo de resultados a retornar
            min_score: Score mínimo (0-100) para considerar um match
            scorer: Função de scorer personalizada (padrão: fuzz.ratio)

        Returns:
            Lista de tuplas (name, handler, score) ordenada por score (decrescente)

        Examples:
            >>> registry.fuzzy_search("fileop")
            [("file_ops.read", handler, 90), ("file_ops.write", handler, 90)]

            >>> registry.fuzzy_search("webook")
            [("webhooks.receive", handler, 85)]
        """
        if not FUZZY_AVAILABLE:
            # Se thefuzz não está disponível, retorna busca exata com substring
            results = []
            query_lower = query.lower()
            for name, handler in self._handlers.items():
                if query_lower in name.lower():
                    # Score simples baseado em posição e comprimento
                    score = max(0, 100 - (len(name) - len(query)) * 2)
                    results.append((name, handler, score))
            return sorted(results, key=lambda x: x[2], reverse=True)[:limit]

        # Lista de nomes disponíveis
        choices = list(self._handlers.keys())

        # Usa o scorer padrão (fuzz.partial_ratio) se não fornecido
        # partial_ratio é melhor para encontrar substrings
        if scorer is None:
            scorer = fuzz.partial_ratio

        # Extrai matches fuzzy
        fuzzy_results = process.extract(
            query,
            choices,
            limit=limit * 2,  # Pega mais resultados para filtrar depois
            scorer=scorer
        )

        # Filtra por score mínimo e retorna com handlers
        results = []
        for name, score in fuzzy_results:
            if score >= min_score:
                results.append((name, self._handlers[name], score))
            else:
                break  # Como está ordenado, pode parar

        return results[:limit]

    def clear(self) -> None:
        """Limpa handlers registrados (uso em testes)."""
        self._handlers.clear()


# Singleton global
_query_registry = QueryRegistry()


def get_query_registry() -> QueryRegistry:
    """Retorna o registry global."""
    return _query_registry
