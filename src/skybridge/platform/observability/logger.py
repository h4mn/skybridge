# -*- coding: utf-8 -*-
"""
Logger — Logging estruturado com correlation ID.

Logger simples que pode ser expandido para JSON logging.
"""

import logging
import sys
from datetime import datetime
from typing import Any


class SkybridgeLogger:
    """
    Logger estruturado para Skybridge.

    TODO: Evoluir para JSON logging e adicionar handlers de arquivo.
    """

    def __init__(self, name: str = "skybridge", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Handler de console
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _format(self, message: str, extra: dict[str, Any] | None = None) -> str:
        """Formata mensagem com extra context."""
        if extra:
            parts = [message]
            for key, value in extra.items():
                parts.append(f"{key}={value}")
            return " | ".join(parts)
        return message

    def info(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log info."""
        self.logger.info(self._format(message, extra))

    def error(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log error."""
        self.logger.error(self._format(message, extra))

    def warning(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log warning."""
        self.logger.warning(self._format(message, extra))

    def debug(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log debug."""
        self.logger.debug(self._format(message, extra))


# Singleton global
_logger: SkybridgeLogger | None = None


def get_logger(name: str = "skybridge", level: str = "INFO") -> SkybridgeLogger:
    """Retorna logger global."""
    global _logger
    if _logger is None:
        _logger = SkybridgeLogger(name, level)
    return _logger
