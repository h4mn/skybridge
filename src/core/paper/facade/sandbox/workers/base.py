"""Protocol e implementação base para Workers do PaperOrchestrator."""

import asyncio
import logging
from abc import abstractmethod
from typing import Protocol

logger = logging.getLogger(__name__)


class Worker(Protocol):
    """Protocol que define a interface de um Worker.

    Workers são componentes que executam tarefas periódicas sob
    coordenação do PaperOrchestrator.

    Attributes:
        name: Identificador único do worker.

    Methods:
        start: Chamado uma vez quando o worker inicia.
        stop: Chamado uma vez quando o worker para.
        tick: Chamado a cada ciclo do orchestrator.
    """

    name: str

    async def start(self) -> None:
        """Inicializa o worker. Chamado uma vez antes do loop principal."""
        ...

    async def stop(self) -> None:
        """Finaliza o worker. Chamado uma vez ao encerrar."""
        ...

    async def tick(self) -> None:
        """Executa uma iteração do worker. Chamado a cada ciclo."""
        ...


class BaseWorker:
    """Implementação base com funcionalidades comuns.

    Fornece:
    - Logging padronizado
    - Controle de estado (running/stopped)
    - Tratamento de erro com continuidade

    Subclasses devem implementar:
    - _do_tick(): Lógica específica do tick
    """

    def __init__(self, name: str):
        self._name = name
        self._running = False
        self._logger = logging.getLogger(f"paper.worker.{name}")

    @property
    def name(self) -> str:
        """Identificador único do worker."""
        return self._name

    @property
    def is_running(self) -> bool:
        """Retorna True se o worker está ativo."""
        return self._running

    async def start(self) -> None:
        """Inicializa o worker."""
        self._running = True
        self._logger.info(f"Worker '{self._name}' iniciado")

    async def stop(self) -> None:
        """Finaliza o worker."""
        self._running = False
        self._logger.info(f"Worker '{self._name}' parado")

    async def tick(self) -> None:
        """Executa uma iteração com tratamento de erro.

        Erros são logados mas não interrompem o loop principal.
        """
        if not self._running:
            return

        try:
            await self._do_tick()
        except Exception as e:
            self._logger.error(
                f"Erro no tick do worker '{self._name}': {e}",
                exc_info=True,
            )
            # Não re-raise: continua rodando

    @abstractmethod
    async def _do_tick(self) -> None:
        """Implementação específica do tick. Deve ser sobrescrito."""
        ...
