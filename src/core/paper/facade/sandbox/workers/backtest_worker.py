"""BacktestWorker - roda simulação com dados históricos (stub)."""

import logging
from typing import Any, Callable, Optional

from .base import BaseWorker

logger = logging.getLogger(__name__)

# Tipo para callback de progresso
ProgressCallback = Callable[[int, int], None]  # (current, total)


class BacktestWorker(BaseWorker):
    """Worker que executa backtests com dados históricos.

    Responsabilidades:
    - Carregar dados históricos
    - Simular execução de estratégia
    - Calcular métricas de performance

    Status: STUB - Interface definida, implementação pendente.

    Attributes:
        backtest_id: ID do backtest em execução.
        on_progress: Callback para atualizações de progresso.
    """

    def __init__(
        self,
        backtest_id: str = "default",
        on_progress: Optional[ProgressCallback] = None,
        **backtest_params: Any,
    ):
        """Inicializa o BacktestWorker.

        Args:
            backtest_id: ID do backtest.
            on_progress: Callback para progresso.
            **backtest_params: Parâmetros do backtest (start, end, etc).
        """
        super().__init__(name=f"backtest_{backtest_id}")
        self._backtest_id = backtest_id
        self._on_progress = on_progress
        self._params = backtest_params

    @property
    def backtest_id(self) -> str:
        """ID do backtest em execução."""
        return self._backtest_id

    async def start(self) -> None:
        """Inicializa o worker."""
        await super().start()
        self._logger.info(
            f"BacktestWorker '{self._backtest_id}' iniciado (STUB)"
        )

    async def _do_tick(self) -> None:
        """Executa uma iteração do backtest.

        Stub: Apenas loga. Implementação futura:
        - Carregar dados do período
        - Simular ordens
        - Atualizar métricas
        """
        self._logger.debug(
            f"BacktestWorker '{self._backtest_id}' tick (stub - sem ação)"
        )

        # Stub: Em produção, processaria dados históricos
        # data = await self._load_historical_data()
        # for bar in data:
        #     await self._process_bar(bar)
        #     if self._on_progress:
        #         self._on_progress(current, total)
