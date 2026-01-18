# -*- coding: utf-8 -*-
"""
Sky-RPC Registry — Registro unificado para handlers RPC com introspecção e reload.

Baseado em PRD009 e SPEC004.
"""

from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field
from pathlib import Path
import importlib
import inspect

from .query_registry import QueryRegistry, QueryHandler, get_query_registry
from kernel.schemas.schemas import (
    SkyRpcDiscovery,
    SkyRpcHandler,
    Kind,
    ReloadResponse,
)


@dataclass
class ReloadSnapshot:
    """Snapshot do registry antes do reload (para rollback)."""
    handlers: Dict[str, QueryHandler]
    timestamp: str
    version: str


class SkyRpcRegistry:
    """
    Registry extendido para Sky-RPC com introspecção e reload.

    Funcionalidades:
    - Herda do QueryRegistry existente
    - Introspecção via get_discovery()
    - Reload dinâmico via reload()
    - Rollback automático em caso de erro
    """

    def __init__(self, base_registry: Optional[QueryRegistry] = None):
        self._base = base_registry or get_query_registry()
        self._snapshot: Optional[ReloadSnapshot] = None
        self._version = "0.3.0"
        self._module_cache: Dict[str, Any] = {}

    @property
    def version(self) -> str:
        """Versão do Sky-RPC."""
        return self._version

    def register(
        self,
        name: str,
        handler: Callable[..., Any],
        description: str | None = None,
        *,
        kind: str = "query",
        module: str | None = None,
        auth_required: bool = True,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        **kwargs
    ) -> None:
        """Registra um handler RPC."""
        # Detecta automaticamente o módulo se não informado
        if module is None:
            module = inspect.getmodule(handler).__name__ if inspect.isfunction(handler) else "unknown"

        self._base.register(
            name=name,
            handler=handler,
            description=description,
            kind=kind,
            auth=auth_required,
            input_schema=input_schema,
            output_schema=output_schema,
            **kwargs
        )

    def get(self, name: str) -> QueryHandler | None:
        """Retorna um handler pelo nome."""
        return self._base.get(name)

    def has(self, name: str) -> bool:
        """Verifica se um handler existe."""
        return self._base.has(name)

    def list_all(self) -> list[QueryHandler]:
        """Lista todos os handlers registrados."""
        return self._base.list_all()

    def fuzzy_search(
        self,
        query: str,
        *,
        limit: int = 5,
        min_score: int = 60
    ) -> list[dict[str, Any]]:
        """
        Busca handlers usando fuzzy matching e retorna metadados enriquecidos.

        Args:
            query: String de busca (pode conter erros de digitação)
            limit: Número máximo de resultados a retornar
            min_score: Score mínimo (0-100) para considerar um match

        Returns:
            Lista de dicionários com metadados dos handlers encontrados

        Examples:
            >>> results = skyrpc_registry.fuzzy_search("fileop")
            >>> [r["method"] for r in results]
            ["file_ops.read", "file_ops.write"]
        """
        from typing import Callable
        raw_results = self._base.fuzzy_search(query, limit=limit, min_score=min_score)

        # Enriquece com metadados adicionais
        enriched_results = []
        for name, handler, score in raw_results:
            enriched_results.append({
                "method": name,
                "score": score,
                "kind": handler.kind,
                "description": handler.description,
                "module": getattr(handler, "module", "unknown"),
                "auth_required": getattr(handler, "auth_required", True),
            })

        return enriched_results

    def get_discovery(self) -> SkyRpcDiscovery:
        """
        Retorna catálogo de handlers para introspecção.

        Conforme SPEC004:
        - method: nome canônico
        - kind: query ou command
        - module: caminho do módulo Python
        - description: descrição do handler
        - auth_required: se requer autenticação
        - input_schema: JSON Schema do input
        - output_schema: JSON Schema do output
        """
        handlers = self._base.list_all()

        discovery_dict: Dict[str, SkyRpcHandler] = {}
        for h in handlers:
            discovery_dict[h.name] = SkyRpcHandler(
                method=h.name,
                kind=Kind(h.kind) if isinstance(h.kind, str) else Kind.QUERY,
                module=getattr(h, 'module', 'unknown'),
                description=h.description,
                auth_required=getattr(h, 'auth_required', True),
                input_schema=h.input_schema,
                output_schema=h.output_schema,
            )

        return SkyRpcDiscovery(
            version=self._version,
            discovery=discovery_dict,
            total=len(discovery_dict)
        )

    def _create_snapshot(self) -> ReloadSnapshot:
        """Cria snapshot do estado atual do registry."""
        handlers_copy = {name: handler for name, handler in self._base._handlers.items()}
        return ReloadSnapshot(
            handlers=handlers_copy,
            timestamp=__import__('datetime').datetime.utcnow().isoformat() + "Z",
            version=self._version
        )

    def reload(
        self,
        packages: list[str],
        *,
        preserve_on_error: bool = True
    ) -> ReloadResponse:
        """
        Recarrega o registry a partir do código atual.

        Args:
            packages: Lista de pacotes para rediscover
            preserve_on_error: Se True, restaura snapshot em caso de erro

        Returns:
            ReloadResponse com handlers adicionados/removidos
        """
        from .discovery import discover_modules

        # Cria snapshot para rollback
        self._snapshot = self._create_snapshot()

        # Guarda estado anterior para comparação
        before_methods = set(self._base._handlers.keys())

        try:
            # Limpa registry atual
            self._base.clear()

            # Rediscover pacotes
            discovered = discover_modules(packages, include_submodules=True)

            # Coleta handlers recarregados
            after_methods = set(self._base._handlers.keys())

            added = list(after_methods - before_methods)
            removed = list(before_methods - after_methods)

            return ReloadResponse(
                ok=True,
                added=added,
                removed=removed,
                total=len(after_methods),
                version=self._version
            )

        except Exception as e:
            # Rollback para snapshot anterior
            if preserve_on_error and self._snapshot:
                self._base._handlers = self._snapshot.handlers
                self._snapshot = None

            raise RuntimeError(f"Reload failed, previous registry preserved: {e}")

    def restore_snapshot(self) -> bool:
        """Restaura o último snapshot (rollback manual)."""
        if self._snapshot is None:
            return False

        self._base._handlers = self._snapshot.handlers
        self._snapshot = None
        return True


# Singleton global
_skyrpc_registry: Optional[SkyRpcRegistry] = None


def get_skyrpc_registry() -> SkyRpcRegistry:
    """Retorna o registry Sky-RPC global (singleton)."""
    global _skyrpc_registry
    if _skyrpc_registry is None:
        _skyrpc_registry = SkyRpcRegistry()
    return _skyrpc_registry
