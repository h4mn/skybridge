# coding: utf-8
"""
Adapter entre runtime.observability e core.sky.observability.

Este módulo fornece a implementação de SkyLogger usando o
SkybridgeLogger existente, permitindo que o domínio core.sky
use logging sem dependência direta de runtime.

Uso:
    from runtime.observability.logger import get_logger
    from runtime.observability.adapters import RuntimeLoggerAdapter

    sky_logger = RuntimeLoggerAdapter(get_logger("mycomponent"))
    my_component = MyComponent(logger=sky_logger)
"""

from typing import Any

from core.sky.observability import SkyLogger


class RuntimeLoggerAdapter(SkyLogger):
    """
    Adapter que implementa SkyLogger usando SkybridgeLogger.

    Permite que componentes do domínio usem o logger de runtime
    sem acoplamento direto.
    """

    def __init__(self, logger) -> None:
        """
        Inicializa adapter.

        Args:
            logger: Instância de SkybridgeLogger do runtime.
        """
        self._logger = logger

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log em nível DEBUG."""
        self._logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log em nível INFO."""
        self._logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log em nível WARNING."""
        self._logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log em nível ERROR."""
        self._logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log em nível CRITICAL."""
        self._logger.critical(msg, **kwargs)


__all__ = ["RuntimeLoggerAdapter"]
