"""PositionWorker - atualiza cotações e verifica ordens limite."""

import logging
from typing import Callable, List, Optional

from .base import BaseWorker

logger = logging.getLogger(__name__)


# Tipo para callback de mudança de PnL
PnLCallback = Callable[[float, float], None]  # (pnl, pnl_percentual)


class PositionWorker(BaseWorker):
    """Worker que atualiza cotações e monitora ordens limite.

    Responsabilidades:
    - Atualiza preços de mercado das posições
    - Verifica ordens limite pendentes
    - Notifica mudanças de PnL via callback

    Attributes:
        portfolio_id: ID do portfolio monitorado.
        tickers: Lista de tickers para atualizar.
        on_pnl_change: Callback chamado quando PnL muda.
    """

    def __init__(
        self,
        portfolio_id: str = "default",
        tickers: Optional[List[str]] = None,
        on_pnl_change: Optional[PnLCallback] = None,
    ):
        """Inicializa o PositionWorker.

        Args:
            portfolio_id: ID do portfolio (default: "default").
            tickers: Lista de tickers para monitorar.
            on_pnl_change: Callback para mudanças de PnL.
        """
        super().__init__(name="position_worker")
        self._portfolio_id = portfolio_id
        self._tickers = tickers or []
        self._on_pnl_change = on_pnl_change
        self._last_pnl: Optional[float] = None
        self._last_pnl_pct: Optional[float] = None

    @property
    def portfolio_id(self) -> str:
        """ID do portfolio monitorado."""
        return self._portfolio_id

    @property
    def tickers(self) -> List[str]:
        """Lista de tickers monitorados."""
        return self._tickers.copy()

    async def start(self) -> None:
        """Inicializa o worker."""
        await super().start()
        self._logger.info(
            f"PositionWorker iniciado para portfolio '{self._portfolio_id}' "
            f"com {len(self._tickers)} tickers"
        )

    async def _do_tick(self) -> None:
        """Executa atualização de posições.

        Fluxo:
        1. Atualiza cotações dos tickers
        2. Calcula PnL atualizado
        3. Verifica ordens limite
        4. Notifica callback se houve mudança
        """
        # 1. Atualiza cotações (stub - integração real via DataFeedPort)
        await self._update_quotes()

        # 2. Calcula PnL
        pnl, pnl_pct = await self._calculate_pnl()

        # 3. Verifica ordens limite (stub)
        await self._check_limit_orders()

        # 4. Notifica se mudou
        if self._on_pnl_change and (
            self._last_pnl != pnl or self._last_pnl_pct != pnl_pct
        ):
            self._on_pnl_change(pnl, pnl_pct)
            self._logger.debug(f"PnL atualizado: {pnl:.2f} ({pnl_pct:.2f}%)")

        self._last_pnl = pnl
        self._last_pnl_pct = pnl_pct

    async def _update_quotes(self) -> None:
        """Atualiza cotações dos tickers monitorados.

        Stub: Em produção, usaria DataFeedPort para buscar preços reais.
        """
        if not self._tickers:
            return

        self._logger.debug(f"Atualizando cotações: {self._tickers}")
        # TODO: Integrar com DataFeedPort quando disponível
        # quotes = await self._feed.get_quotes(self._tickers)

    async def _calculate_pnl(self) -> tuple[float, float]:
        """Calcula PnL atual do portfolio.

        Returns:
            Tupla (pnl, pnl_percentual).

        Stub: Em produção, usaria ConsultarPortfolioHandler.
        """
        # TODO: Integrar com ConsultarPortfolioHandler
        # result = await self._handler.handle(ConsultarPortfolioQuery(...))
        # return result.pnl, result.pnl_percentual
        return 0.0, 0.0

    async def _check_limit_orders(self) -> None:
        """Verifica ordens limite pendentes.

        Stub: Em produção, verificaria ordens no broker e executaria
        se preço atingiu o limite.
        """
        # TODO: Integrar com BrokerPort
        # orders = await self._broker.listar_ordens_pendentes()
        # for order in orders:
        #     if self._should_execute(order):
        #         await self._broker.executar_ordem(order.id)
        pass
