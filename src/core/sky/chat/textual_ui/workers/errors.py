# coding: utf-8
"""
Tratamento de erros e timeout para workers.

Wrapper para workers com retry, timeout e captura de erros.
"""

import asyncio
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from core.sky.chat.textual_ui.workers.queue import (
    WorkerQueue,
    WorkerEvent,
    WorkerEventType,
)

T = TypeVar("T")


class WorkerError(Exception):
    """Erro na execução de um worker."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """
        Inicializa WorkerError.

        Args:
            message: Mensagem de erro.
            cause: Causa raiz (exceção original).
        """
        super().__init__(message)
        self.cause = cause


def with_timeout(timeout_seconds: float = 30.0):
    """
    Decorador para adicionar timeout a funcoes assincronas.

    Args:
        timeout_seconds: Tempo limite em segundos.

    Returns:
        Funcao decorada com timeout.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                raise WorkerError(f"Timeout apos {timeout_seconds}s")

        return wrapper

    return decorator


def with_error_handling(queue=None):
    """
    Decorador para capturar erros e enviar para fila.

    Args:
        queue: Fila para enviar erros (opcional).

    Returns:
        Funcao decorada com tratamento de erros.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if queue:
                    await queue.put(WorkerEventType.ERROR, {"error": str(e), "type": type(e).__name__})
                raise WorkerError(f"Erro em {func.__name__}: {e}", cause=e) from e

        return wrapper

    return decorator


__all__ = ["WorkerError", "with_timeout", "with_error_handling"]
