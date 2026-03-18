# coding: utf-8
"""
Observability do domínio Sky.

Abstrações para logging e métricas, independentes de infraestrutura.

O domínio core.sky NÃO deve depender de runtime.observability.
Esta camada fornece interfaces que o domínio pode usar, enquanto
a infraestrutura (runtime) fornece as implementações concretas.

Uso:
    from core.sky.observability import SkyLogger, SilentLogger

    class MyComponent:
        def __init__(self, logger: SkyLogger | None = None):
            self._logger = logger or SilentLogger()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SkyLogger(ABC):
    """
    Abstração de logger para o domínio Sky.

    Implementações concretas ficam em runtime.observability.
    """

    @abstractmethod
    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log em nível DEBUG."""
        pass

    @abstractmethod
    def info(self, msg: str, **kwargs: Any) -> None:
        """Log em nível INFO."""
        pass

    @abstractmethod
    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log em nível WARNING."""
        pass

    @abstractmethod
    def error(self, msg: str, **kwargs: Any) -> None:
        """Log em nível ERROR."""
        pass

    @abstractmethod
    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log em nível CRITICAL."""
        pass


class SilentLogger(SkyLogger):
    """
    Implementação fallback que não faz nada.

    Usada quando nenhum logger é injetado, permitindo que
    o domínio funcione sem dependência de infraestrutura.
    """

    def debug(self, msg: str, **kwargs: Any) -> None:
        pass

    def info(self, msg: str, **kwargs: Any) -> None:
        pass

    def warning(self, msg: str, **kwargs: Any) -> None:
        pass

    def error(self, msg: str, **kwargs: Any) -> None:
        pass

    def critical(self, msg: str, **kwargs: Any) -> None:
        pass


__all__ = ["SkyLogger", "SilentLogger"]
