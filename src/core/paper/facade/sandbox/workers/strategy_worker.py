"""StrategyWorker - avalia estratégias e executa ordens."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Callable, Optional

from .base import BaseWorker

logger = logging.getLogger(__name__)

SuggestionCallback = Callable[[str, str], None]


class StrategyWorker(BaseWorker):
    """Worker que avalia estratégias e executa ordens via ExecutorDeOrdem.

    Suporta dois modos:
    - **Real**: com strategy, datafeed, executor, tracker — executa trades
    - **Legacy**: com strategy_name, on_suggestion — stub backward-compatible
    """

    def __init__(
        self,
        strategy: Any = None,
        datafeed: Any = None,
        executor: Any = None,
        position_tracker: Any = None,
        tickers: list[str] | None = None,
        periodo_historico: int = 30,
        quantity: int = 100,
        strategy_name: str | None = None,
        on_suggestion: SuggestionCallback | None = None,
        **strategy_params: Any,
    ):
        if strategy is not None:
            self._mode = "real"
            name = f"strategy_{getattr(strategy, 'name', 'unknown')}"
            super().__init__(name=name)
            self._strategy = strategy
            self._datafeed = datafeed
            self._executor = executor
            self._position_tracker = position_tracker
            self._tickers = tickers or []
            self._periodo_historico = periodo_historico
            self._quantity = quantity
            self._strategy_name = None
            self._on_suggestion = None
        else:
            self._mode = "legacy"
            super().__init__(name=f"strategy_{strategy_name or 'default'}")
            self._strategy_name = strategy_name or "default"
            self._on_suggestion = on_suggestion
            self._strategy = None
            self._datafeed = None
            self._executor = None
            self._position_tracker = None
            self._tickers = []
            self._periodo_historico = 30
            self._quantity = 100
        self._params = strategy_params

    @property
    def strategy_name(self) -> str:
        return self._strategy_name or getattr(self._strategy, "name", "unknown")

    async def start(self) -> None:
        await super().start()
        if self._mode == "legacy":
            logger.info(f"StrategyWorker '{self._strategy_name}' iniciado (STUB)")
        else:
            logger.info(
                f"StrategyWorker '{self.name}' iniciado com tickers={self._tickers}"
            )

    async def _do_tick(self) -> None:
        if self._mode == "legacy":
            self._logger.debug(f"StrategyWorker '{self._strategy_name}' tick (stub)")
            return

        from src.core.paper.domain.events.ordem_events import Lado
        from src.core.paper.domain.strategies.signal import DadosMercado, TipoSinal

        for ticker in self._tickers:
            try:
                # 1. Verificar SL/TP antes de avaliar estratégia
                cotacao = await self._datafeed.obter_cotacao(ticker)
                sl_tp_sinal = self._position_tracker.check_price(ticker, cotacao.preco)
                if sl_tp_sinal is not None:
                    await self._executor.executar_ordem(
                        ticker=ticker,
                        lado=Lado.VENDA,
                        quantidade=self._quantity,
                    )
                    self._position_tracker.close_position(ticker)
                    self._logger.info(
                        f"SL/TP acionado: VENDA {ticker} @ {cotacao.preco} ({sl_tp_sinal.razao})"
                    )
                    continue

                # 2. Buscar dados de mercado
                historico = await self._datafeed.obter_historico(ticker, self._periodo_historico)
                dados = DadosMercado(
                    ticker=ticker,
                    preco_atual=cotacao.preco,
                    historico_precos=tuple(c.preco for c in historico),
                )

                # 3. Avaliar estratégia
                sinal = self._strategy.evaluate(dados)
                if sinal is None or sinal.tipo.value == "neutro":
                    continue

                # 4. Executar ordem
                lado = Lado.COMPRA if sinal.tipo == TipoSinal.COMPRA else Lado.VENDA
                await self._executor.executar_ordem(
                    ticker=ticker,
                    lado=lado,
                    quantidade=self._quantity,
                )

                if lado == Lado.COMPRA:
                    self._position_tracker.open_position(ticker, cotacao.preco)
                else:
                    self._position_tracker.close_position(ticker)

                self._logger.info(
                    f"Sinal: {sinal.tipo.value.upper()} {ticker} @ {cotacao.preco} ({sinal.razao})"
                )
            except Exception:
                self._logger.exception(f"Erro no tick para {ticker}")
