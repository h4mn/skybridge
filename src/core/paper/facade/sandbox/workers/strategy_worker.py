"""StrategyWorker - avalia estratégias e executa ordens."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Callable, Optional

from .base import BaseWorker

logger = logging.getLogger(__name__)

SuggestionCallback = Callable[[str, str], None]

# ANSI colors — terminal apenas (FileHandler deve usar AnsiStripFormatter)
_R = "\033[0m"       # reset
_B = "\033[1m"       # bold
_GOLD = "\033[38;5;220m"
_ORANGE = "\033[38;5;208m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_BLUE = "\033[34m"
_PURPLE = "\033[38;5;183m"


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
        intervalo_historico: str = "1d",
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
            self._intervalo_historico = intervalo_historico
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
            self._intervalo_historico = "1d"
            self._quantity = 100
        self._params = strategy_params
        self._tick_count = 0
        self._signal_count = 0
        self._error_count = 0
        self._first_tick_done = False

    @property
    def strategy_name(self) -> str:
        return self._strategy_name or getattr(self._strategy, "name", "unknown")

    async def start(self) -> None:
        await super().start()
        if self._mode == "legacy":
            logger.info(f"StrategyWorker '{self._strategy_name}' iniciado (STUB)")
        else:
            logger.info(
                f"StrategyWorker '{self.name}' iniciado "
                f"tickers={self._tickers} periodo={self._periodo_historico}d "
                f"intervalo={self._intervalo_historico}"
            )

    def _log_first_tick_diagnostic(
        self, ticker: str, preco: Decimal, n_pontos: int, historico: list
    ) -> None:
        """Loga diagnóstico detalhado no primeiro tick para validar dados."""
        if not historico:
            self._logger.warning(
                f"[DIAG] {ticker}: histórico VAZIO! Preço atual={preco}"
            )
            return

        primeira = historico[0]
        ultima = historico[-1]
        self._logger.info(
            f"[DIAG] {ticker}: {n_pontos} velas de {self._intervalo_historico} "
            f"| range: {primeira.timestamp} → {ultima.timestamp} "
            f"| preco={preco}"
        )
        if n_pontos < 20:
            self._logger.warning(
                f"[DIAG] {ticker}: apenas {n_pontos} pontos — "
                f"estratégia pode não ter dados suficientes para crossover"
            )

    def _log_heartbeat(self, precos_atuais: dict[str, Decimal] | None = None) -> None:
        """Loga resumo a cada 10 ticks com PnL flutuante."""
        if self._tick_count % 10 == 0 and self._tick_count > 0:
            parts = [
                f"ticks={self._tick_count}",
                f"sinais={self._signal_count}",
                f"erros={self._error_count}",
            ]

            positions = self._position_tracker.list_positions()
            if positions and precos_atuais:
                for pos in positions:
                    ticker = pos["ticker"]
                    entrada = pos["preco_entrada"]
                    atual = precos_atuais.get(ticker)
                    if atual:
                        pnl_pct = float((atual - entrada) / entrada * 100)
                        pnl_val = float(atual - entrada) * self._quantity
                        cor_pnl = _BLUE if pnl_val >= 0 else _PURPLE
                        parts.append(
                            f"{ticker}: {cor_pnl}{_B}PnL ${pnl_val:+,.2f} "
                            f"({pnl_pct:+.3f}%){_R}"
                        )

            self._logger.info(f"[HEARTBEAT] {' | '.join(parts)}")

    async def _do_tick(self) -> None:
        if self._mode == "legacy":
            self._logger.debug(f"StrategyWorker '{self._strategy_name}' tick (stub)")
            return

        from src.core.paper.domain.events.ordem_events import Lado
        from src.core.paper.domain.strategies.signal import DadosMercado, TipoSinal

        self._tick_count += 1
        precos_atuais: dict[str, Decimal] = {}

        for ticker in self._tickers:
            try:
                # 1. Verificar SL/TP antes de avaliar estratégia
                cotacao = await self._datafeed.obter_cotacao(ticker)
                precos_atuais[ticker] = cotacao.preco
                sl_tp_sinal = self._position_tracker.check_price(ticker, cotacao.preco)
                if sl_tp_sinal is not None:
                    await self._executor.executar_ordem(
                        ticker=ticker,
                        lado=Lado.VENDA,
                        quantidade=self._quantity,
                    )
                    self._position_tracker.close_position(ticker)
                    self._signal_count += 1
                    is_tp = "Take Profit" in sl_tp_sinal.razao
                    cor = _GREEN if is_tp else _RED
                    tag = "TAKE PROFIT" if is_tp else "STOP LOSS"
                    self._logger.info(
                        f"{cor}{_B}{tag}: VENDA {ticker} @ {cotacao.preco} "
                        f"({sl_tp_sinal.razao}){_R}"
                    )
                    continue

                # 2. Buscar dados de mercado
                historico = await self._datafeed.obter_historico(
                    ticker, self._periodo_historico, self._intervalo_historico
                )
                dados = DadosMercado(
                    ticker=ticker,
                    preco_atual=cotacao.preco,
                    historico_precos=tuple(c.preco for c in historico),
                )

                # Diagnóstico no primeiro tick
                if not self._first_tick_done:
                    self._log_first_tick_diagnostic(
                        ticker, cotacao.preco, len(historico), historico
                    )

                # 3. Avaliar estratégia
                sinal = self._strategy.evaluate(dados)

                if sinal is None or sinal.tipo.value == "neutro":
                    self._logger.info(
                        f"[TICK #{self._tick_count}] {ticker} @ {cotacao.preco} "
                        f"| {len(historico)} velas | sem sinal"
                    )
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

                self._signal_count += 1
                cor = _GOLD if sinal.tipo == TipoSinal.COMPRA else _ORANGE
                self._logger.info(
                    f"{cor}{_B}SINAL: {sinal.tipo.value.upper()} {ticker} "
                    f"@ {cotacao.preco} ({sinal.razao}){_R}"
                )
            except Exception:
                self._error_count += 1
                self._logger.exception(f"Erro no tick #{self._tick_count} para {ticker}")

        if not self._first_tick_done:
            self._first_tick_done = True

        self._log_heartbeat(precos_atuais)
