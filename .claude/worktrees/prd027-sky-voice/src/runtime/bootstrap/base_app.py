# -*- coding: utf-8 -*-
"""
BaseApp — Template Method Pattern para execução de servidor.

DOC: runtime/bootstrap/base_app.py
DOC: PRD022 - Servidor Unificado

Implementa Template Method Pattern onde:
- BaseApp define o esqueleto de execução (run())
- Subclasses implementam _get_uvicorn_kwargs() com suas diferenças
- SSL é suportado por ambas via config (SKYBRIDGE_SSL_ENABLED)

Design Pattern: Template Method
- run() é o template method
- _get_uvicorn_kwargs() é o passo primitivo que varia
- Hooks _before_run() e _after_run() para extensão
"""

import uvicorn
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path

from runtime.config.config import get_config, get_ssl_config
from runtime.observability.logger import get_logger


class BaseApp(ABC):
    """
    Classe base com Template Method para execução de servidor.

    Responsável por:
    - Definir o esqueleto de execução (run)
    - Delegar configuração de uvicorn para subclasses (_get_uvicorn_kwargs)
    - Suportar SSL via configuração compartilhada
    - Fornecer hooks para extensão (_before_run, _after_run)

    Subclasses devem implementar:
    - _get_uvicorn_kwargs(): retorna kwargs específicos para uvicorn
    - _get_host(): retorna host (pode usar config)
    - _get_port(): retorna port (pode usar config)
    """

    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(level=self.config.log_level)

    def run(self, host: str | None = None, port: int | None = None) -> None:
        """
        Template Method: executa servidor com uvicorn.

        Esqueleto de execução que:
        1. Chama _before_run() (hook para setup)
        2. Obtém kwargs da subclasse (_get_uvicorn_kwargs)
        3. Adiciona config de SSL (compartilhado)
        4. Executa uvicorn.run()
        5. Chama _after_run() (hook para cleanup)

        Args:
            host: Host para bind (None usa _get_host())
            port: Porta para listen (None usa _get_port())
        """
        # Resolve host e port
        host = host or self._get_host()
        port = port or self._get_port()

        # 1. Hook: antes de rodar
        self._before_run()

        # 2. Obtém kwargs customizados da subclasse
        uvicorn_kwargs = self._get_uvicorn_kwargs(host, port)

        # 3. Adiciona SSL (compartilhado entre subclasses)
        ssl_config = get_ssl_config()
        if ssl_config.enabled:
            if ssl_config.cert_file and ssl_config.key_file:
                uvicorn_kwargs["ssl_certfile"] = ssl_config.cert_file
                uvicorn_kwargs["ssl_keyfile"] = ssl_config.key_file
            else:
                self.logger.warning(
                    "SSL habilitado mas cert/key não configurados",
                    extra={"cert_file": ssl_config.cert_file, "key_file": ssl_config.key_file}
                )

        # Log de startup
        self.logger.info(
            f"Iniciando {self.__class__.__name__}",
            extra={
                "host": host,
                "port": port,
                "ssl_enabled": ssl_config.enabled,
            }
        )

        # 4. Executa uvicorn
        print()  # Separador antes dos logs do uvicorn
        from runtime.observability.logger import print_separator
        print_separator("─", 60)

        uvicorn.run(**uvicorn_kwargs)

        # 5. Hook: depois de rodar
        self._after_run()

        print()  # Separador depois dos logs
        print_separator("═", 60)

    # Hooks para subclasses sobrescreverem
    def _before_run(self) -> None:
        """Hook executado antes de uvicorn.run()."""
        pass

    def _after_run(self) -> None:
        """Hook executado depois que uvicorn.run() retorna."""
        pass

    # Métodos abstratos que subclasses DEVEM implementar
    @abstractmethod
    def _get_uvicorn_kwargs(self, host: str, port: int) -> Dict[str, Any]:
        """
        Retorna kwargs específicos para uvicorn.run().

        Cada subclasse define seus próprios kwargs:
        - SkybridgeApp: SSL (quando habilitado), log_level padrão
        - SkybridgeServer: log_config customizado, access_log=False

        Args:
            host: Host resolvedido
            port: Porta resolvida

        Returns:
            Dict com kwargs para uvicorn.run()
        """
        pass

    @abstractmethod
    def _get_host(self) -> str:
        """Retorna host para bindar (usa config por padrão)."""
        pass

    @abstractmethod
    def _get_port(self) -> int:
        """Retorna porta para listen (usa config por padrão)."""
        pass


def get_base_app() -> BaseApp:
    """
    Factory para obter instância de BaseApp (para uso em testes).

    Returns:
        Instância concreta de BaseApp (SkybridgeApp ou SkybridgeServer)
    """
    # Esta função permite obter a app sem instanciar diretamente
    # Útil para testes e injeção de dependências
    raise NotImplementedError("Use SkybridgeApp ou SkybridgeServer diretamente")


# Para compatibilidade com código existente
def _get_uvicorn_kwargs_original():
    """
    Implementação original de SkybridgeApp.run() para referência.

    DOC: Mantido para comparação durante refactor.
    """
    from runtime.config.config import get_ssl_config
    from runtime.observability.logger import print_separator

    ssl_config = get_ssl_config()

    uvicorn_kwargs = {
        "app": None,  # Será preenchido pelo caller
        "host": None,  # Será preenchido pelo caller
        "port": None,  # Será preenchido pelo caller
        "log_level": None,  # Será preenchido pelo caller
    }

    if ssl_config.enabled:
        if ssl_config.cert_file and ssl_config.key_file:
            uvicorn_kwargs["ssl_certfile"] = ssl_config.cert_file
            uvicorn_kwargs["ssl_keyfile"] = ssl_config.key_file
        else:
            logger = get_logger()
            logger.warning(
                "SSL habilitado mas cert/key não configurados",
                extra={"cert_file": ssl_config.cert_file, "key_file": ssl_config.key_file}
            )

    return uvicorn_kwargs
