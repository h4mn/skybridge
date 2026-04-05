"""PaperOrchestrator - coordenador de workers para Paper Trading."""

import asyncio
import logging
from typing import Callable, Optional

from .workers.base import Worker

logger = logging.getLogger(__name__)


class PaperOrchestrator:
    """Coordena workers e mantém o sistema de paper trading "vivo".

    O orchestrator gerencia um loop assíncrono que executa workers
    periodicamente, permitindo:
    - Atualização de cotações em tempo real
    - Verificação de ordens limite
    - Execução de estratégias automatizadas
    - Backtests com dados históricos

    Example:
        ```python
        orchestrator = PaperOrchestrator(interval_seconds=10.0)
        orchestrator.register(PositionWorker(portfolio_id="main"))
        orchestrator.register(StrategyWorker())

        # Roda até receber sinal de shutdown
        await orchestrator.run()
        ```

    Attributes:
        interval_seconds: Intervalo entre ciclos de tick.
    """

    def __init__(
        self,
        interval_seconds: float = 10.0,
        on_tick_complete: Optional[Callable[[], None]] = None,
    ):
        """Inicializa o orchestrator.

        Args:
            interval_seconds: Intervalo entre ciclos (default: 10s).
            on_tick_complete: Callback opcional chamado após cada ciclo.
        """
        self._workers: dict[str, Worker] = {}
        self._interval = interval_seconds
        self._running = False
        self._on_tick_complete = on_tick_complete
        self._logger = logging.getLogger("paper.orchestrator")

    @property
    def is_running(self) -> bool:
        """Retorna True se o orchestrator está ativo."""
        return self._running

    @property
    def worker_count(self) -> int:
        """Número de workers registrados."""
        return len(self._workers)

    def register(self, worker: Worker) -> None:
        """Registra um worker para execução.

        Args:
            worker: Worker a ser registrado.

        Raises:
            ValueError: Se já existe worker com mesmo nome.
        """
        if worker.name in self._workers:
            raise ValueError(f"Worker '{worker.name}' já registrado")

        self._workers[worker.name] = worker
        self._logger.info(f"Worker '{worker.name}' registrado")

    def unregister(self, name: str) -> Optional[Worker]:
        """Remove um worker pelo nome.

        Args:
            name: Nome do worker.

        Returns:
            Worker removido ou None se não encontrado.
        """
        worker = self._workers.pop(name, None)
        if worker:
            self._logger.info(f"Worker '{name}' removido")
        return worker

    async def run(self) -> None:
        """Loop principal do orchestrator.

        Executa workers em paralelo a cada intervalo até shutdown()
        ser chamado ou ocorrer erro não tratado.

        O loop é resiliente: erros em workers não interrompem o loop.
        """
        self._running = True
        self._logger.info(
            f"Orchestrator iniciado com {len(self._workers)} workers "
            f"(intervalo: {self._interval}s)"
        )

        # Inicia todos os workers
        await self._start_all_workers()

        try:
            while self._running:
                await self._tick_all_workers()

                if self._on_tick_complete:
                    self._on_tick_complete()

                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            self._logger.info("Orchestrator recebeu CancelledError")
        finally:
            await self.shutdown()

    async def _start_all_workers(self) -> None:
        """Inicializa todos os workers registrados."""
        for name, worker in self._workers.items():
            try:
                await worker.start()
            except Exception as e:
                self._logger.error(f"Erro ao iniciar worker '{name}': {e}")

    async def _tick_all_workers(self) -> None:
        """Executa tick de todos os workers em paralelo."""
        if not self._workers:
            return

        # Executa todos os ticks em paralelo
        tasks = [
            asyncio.create_task(worker.tick(), name=f"tick:{name}")
            for name, worker in self._workers.items()
        ]

        # Aguarda todos completarem (erros são tratados dentro do tick)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def shutdown(self) -> None:
        """Encerra o orchestrator graciosamente.

        Para todos os workers e marca o orchestrator como inativo.
        """
        if not self._running:
            return

        self._running = False
        self._logger.info("Iniciando shutdown do orchestrator...")

        # Para todos os workers
        for name, worker in self._workers.items():
            try:
                await worker.stop()
            except Exception as e:
                self._logger.error(f"Erro ao parar worker '{name}': {e}")

        self._logger.info("Orchestrator finalizado")
