"""StrategyWorker - avalia estratégias e executa ordens."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Callable

from .base import BaseWorker

logger = logging.getLogger(__name__)

SuggestionCallback = Callable[[str, str], None]

# ANSI colors — terminal apenas (FileHandler deve usar AnsiStripFormatter)
#
# Linguagem visual semântica:
#   AZUL    → eventos de sistema  ([START], [HEARTBEAT], [TICK], [INIT], [DIAG])
#   AMARELO → alertas/filtros     ([GUARD], [STALE])
#   OURO    → entrada / compra    (POSIÇÃO ABERTA, TP param)
#   LARANJA → saída / venda       (POSIÇÃO FECHADA, FECHAMENTO, Trail)
#   VERDE   → positivo / lucro    (LUCRO, +DI dominante, ADX forte, PnL+)
#   VERMELHO→ negativo / perda    (PERDA, -DI dominante, ADX fraco, PnL-)
#   ROXO    → parâmetros          (SL, configs)
#   DIM     → secundário          (DI perdedor, gap grande)
#
_R = "\033[0m"       # reset
_B = "\033[1m"       # bold
_GOLD = "\033[38;5;220m"
_ORANGE = "\033[38;5;208m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_BLUE = "\033[34m"
_PURPLE = "\033[38;5;183m"
_DIM = "\033[2m"
_YELLOW = "\033[33m"


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
        reversal_collector: Any = None,
        stale_threshold: int = 1,
        write_queue: Any = None,
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
            self._reversal_collector = reversal_collector
            self._stale_threshold = stale_threshold
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
            self._reversal_collector = None
            self._stale_threshold = 1
        self._write_queue = write_queue
        self._tick_count = 0
        self._signal_count = 0
        self._error_count = 0
        self._first_tick_done = False
        self._closed_pnl: list[float] = []
        self._last_prices: dict[str, Decimal] = {}
        self._stale_counts: dict[str, int] = {}
        self._ohlcv_acc: dict[str, dict] = {}  # ticker → {open, high, low, close, minute}
        self._prev_indicators: dict[str, dict] = {}  # ticker → indicators do tick anterior
        self._ticks_since_sl: dict[str, int] = {}  # ticker → ticks desde último SL

    @property
    def strategy_name(self) -> str:
        return self._strategy_name or getattr(self._strategy, "name", "unknown")

    def restore_closed_pnl(self, values: list[float]) -> None:
        """Restaura PnL fechado salvo (facade persistence)."""
        self._closed_pnl = list(values)

    def get_closed_pnl(self) -> list[float]:
        """Retorna lista de PnL fechado para persistência."""
        return list(self._closed_pnl)

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
                f"{_B}{_BLUE}[DIAG]{_R} {ticker}: histórico VAZIO! Preço atual={preco}"
            )
            return

        primeira = historico[0]
        ultima = historico[-1]
        self._logger.info(
            f"{_B}{_BLUE}[DIAG]{_R} {ticker}: {n_pontos} velas de {self._intervalo_historico} "
            f"| range: {primeira.timestamp} → {ultima.timestamp} "
            f"| preco={preco}"
        )
        if n_pontos < 20:
            self._logger.warning(
                f"{_B}{_BLUE}[DIAG]{_R} {ticker}: apenas {n_pontos} pontos — "
                f"estratégia pode não ter dados suficientes para crossover"
            )

    def _log_heartbeat(self, precos_atuais: dict[str, Decimal] | None = None) -> None:
        """Loga resumo a cada 60 ticks com PnL fechado, aberto e posições."""
        if self._tick_count % 60 == 0 and self._tick_count > 0:
            closed_total = sum(self._closed_pnl)
            n_trades = len(self._closed_pnl)
            n_wins = sum(1 for p in self._closed_pnl if p >= 0)
            wr = (n_wins / n_trades * 100) if n_trades > 0 else 0.0
            positions = self._position_tracker.list_positions()
            n_positions = len(positions)

            open_pnl = 0.0
            open_pct = 0.0
            if precos_atuais:
                for pos in positions:
                    ticker = pos["ticker"]
                    entrada = pos["preco_entrada"]
                    atual = precos_atuais.get(ticker)
                    if atual:
                        open_pnl += float((atual - entrada) * self._quantity)
                        open_pct = float((atual - entrada) / entrada * 100)

            sinal_closed = "+" if closed_total >= 0 else ""
            sinal_open = "+" if open_pnl >= 0 else ""
            cor_closed = _GREEN if closed_total >= 0 else _RED
            cor_open = _GREEN if open_pnl >= 0 else _RED

            # SL/TP dinâmicos por posição aberta
            sl_tp_parts = []
            for pos in positions:
                ticker = pos["ticker"]
                tp_pct = pos.get("take_profit_pct", self._position_tracker._take_profit_pct)
                trailing = self._position_tracker.get_trailing_stop(ticker)
                tp_str = f"{_GOLD}TP={float(tp_pct):.3%}{_R}"
                tr_str = f"| {_ORANGE}Trail={float(trailing):,.2f}{_R}" if trailing else ""
                sl_tp_parts.append(f"  {ticker}: {_PURPLE}SL={float(self._position_tracker._stop_loss_pct):.3%}{_R} {tp_str}{tr_str}")

            sl_tp_block = ""
            if sl_tp_parts:
                sl_tp_block = "\n" + "\n".join(sl_tp_parts)

            self._logger.info(
                f"{_B}{_BLUE}[HEARTBEAT]{_R} ticks={self._tick_count} | "
                f"trades={n_trades} WR={wr:.0f}% | "
                f"Fechados: {cor_closed}${sinal_closed}{closed_total:,.2f}{_R} | "
                f"Aberto: {cor_open}${sinal_open}{open_pnl:,.2f} ({sinal_open}{open_pct:.3f}%){_R} | "
                f"Posições: {n_positions}{sl_tp_block}"
            )

    async def _do_tick(self) -> None:
        if self._mode == "legacy":
            self._logger.debug(f"StrategyWorker '{self._strategy_name}' tick (stub)")
            return

        from src.core.paper.domain.events.ordem_events import Lado
        from src.core.paper.domain.strategies.signal import DadosMercado, TipoSinal

        self._tick_count += 1
        precos_atuais: dict[str, Decimal] = {}

        if not self._first_tick_done:
            sl = self._position_tracker._stop_loss_pct
            tp = self._position_tracker._take_profit_pct
            closed_total = sum(self._closed_pnl)
            n_positions = len(self._position_tracker.list_positions())
            cor_pnl = _GREEN if closed_total >= 0 else _RED
            sinal_pnl = "+" if closed_total >= 0 else ""
            self._logger.info(
                f"{_B}{_BLUE}[START]{_R} {_PURPLE}SL={float(sl):.3%}{_R} "
                f"{_GOLD}TP={float(tp):.3%}{_R} | "
                f"Fechados: {cor_pnl}{sinal_pnl}${closed_total:,.2f}{_R} | "
                f"Posições: {n_positions} | tickers={self._tickers}"
            )

        for ticker in self._tickers:
            try:
                # 1. Obter cotação
                cotacao = await self._datafeed.obter_cotacao(ticker)
                precos_atuais[ticker] = cotacao.preco

                # 1b. Persistir tick raw via WriteQueue
                self._persist_tick(ticker, cotacao)

                # 1c. Acumular OHLCV
                self._accumulate_ohlcv(ticker, cotacao)

                # 2. Atualizar trailing stop (antes de check_price — responsabilidade do worker)
                self._position_tracker.update_trailing(ticker, cotacao.preco)
                self._persist_trailing_update(ticker)

                # 2b. Breakeven standalone (+0.10% → SL na entrada)
                bk_result = self._position_tracker.update_breakeven(ticker, cotacao.preco)
                if bk_result is not None:
                    self._logger.info(
                        f"{_B}{_BLUE}BREAKEVEN ATIVADO{_R} {ticker} | "
                        f"gatilho: {bk_result['trigger_price']:.2f} "
                        f"(+{float((bk_result['trigger_price'] - bk_result['breakeven_price']) / bk_result['breakeven_price'] * 100):.3f}%) "
                        f"→ SL posicionado em {bk_result['breakeven_price']:.2f}"
                    )

                # 3. Verificar SL/TP (SEMPRE — mesmo com dados stale)
                sl_tp_sinal = self._position_tracker.check_price(ticker, cotacao.preco)
                if sl_tp_sinal is not None:
                    pos = self._position_tracker.get_position(ticker)
                    preco_exec = sl_tp_sinal.preco
                    entrada = pos["preco_entrada"] if pos else preco_exec
                    pnl_pct = float((preco_exec - entrada) / entrada * 100)
                    pnl_val = float(preco_exec - entrada) * self._quantity
                    lucro = pnl_val >= 0

                    await self._executor.executar_ordem(
                        ticker=ticker,
                        lado=Lado.VENDA,
                        quantidade=self._quantity,
                        preco_limit=preco_exec,
                    )
                    self._position_tracker.close_position(ticker)
                    self._closed_pnl.append(pnl_val)
                    self._signal_count += 1

                    # Persistência: ordem + PnL + fechamento posição
                    self._persist_order(ticker, "SELL", self._quantity, preco_exec, cotacao)
                    self._persist_pnl(ticker, entrada, preco_exec, pnl_val, pnl_pct, sl_tp_sinal.razao)
                    self._persist_position_close(ticker, sl_tp_sinal.razao)

                    if self._reversal_collector and self._reversal_collector.is_tracking(ticker):
                        self._reversal_collector.stop_tracking(ticker, preco_exec)

                    tag = "LUCRO" if lucro else "PERDA"
                    cor_tag = _GREEN if lucro else _RED
                    sinal_pnl = "+" if lucro else ""
                    self._logger.info(
                        f"{_B}{cor_tag}{tag}{_R}: {_B}{_ORANGE}FECHAMENTO{_R} {ticker} @ {preco_exec} "
                        f"| {cor_tag}{sinal_pnl}{pnl_pct:.3f}% (${sinal_pnl}{pnl_val:,.2f}){_R}"
                        f" ({sl_tp_sinal.razao})"
                    )

                    # Rastrear ticks desde SL para cooldown de re-entrada
                    if not lucro:
                        self._ticks_since_sl[ticker] = 0

                    continue

                # 4. ReversalCollector — update (se tracking ativo)
                if self._reversal_collector and self._reversal_collector.is_tracking(ticker):
                    self._reversal_collector.update(ticker, cotacao.preco)

                # 5. Stale Guard — bloqueia apenas novos sinais (silencioso)
                if cotacao.preco == self._last_prices.get(ticker):
                    self._stale_counts[ticker] = self._stale_counts.get(ticker, 0) + 1
                    if self._stale_counts[ticker] >= self._stale_threshold:
                        continue
                else:
                    self._stale_counts[ticker] = 0
                self._last_prices[ticker] = cotacao.preco

                # 5b. Incrementar ticks_since_sl
                if ticker in self._ticks_since_sl:
                    self._ticks_since_sl[ticker] += 1

                # 5c. Dual Entry System — re-entry check
                reentry_state = self._position_tracker.get_reentry_state(ticker)
                if reentry_state is not None:
                    self._position_tracker.tick_reentry(ticker)
                    # Re-fetch state after tick (may have expired)
                    reentry_state = self._position_tracker.get_reentry_state(ticker)

                tem_posicao = self._position_tracker.get_position(ticker) is not None
                cooldown_ok = self._ticks_since_sl.get(ticker, 999) >= 3

                if reentry_state is not None and not tem_posicao and cooldown_ok:
                    preco = cotacao.preco
                    fib_level = reentry_state.get("fib_level")
                    crossover_price = reentry_state["crossover_price"]
                    ind = getattr(self._strategy, '_last_indicators', None)
                    prev_ind = self._prev_indicators.get(ticker)

                    executed = False

                    # Entry 1: Pullback Fibonacci (Buy Limit)
                    if fib_level is not None and preco <= fib_level:
                        await self._executor.executar_ordem(
                            ticker=ticker, lado=Lado.COMPRA,
                            quantidade=self._quantity, preco_limit=preco,
                        )
                        self._position_tracker.open_position(ticker, preco)
                        self._signal_count += 1
                        self._logger.info(
                            f"{_B}{_GOLD}RE-ENTRY (Pullback Fib 61.8%): {ticker} @ {preco}{_R}"
                        )
                        executed = True

                    # Entry 2: Breakout + ADX above threshold
                    elif not executed and preco > crossover_price and ind:
                        adx_curr = ind.get("adx", Decimal("0"))
                        plus_di = ind.get("plus_di", Decimal("0"))
                        minus_di = ind.get("minus_di", Decimal("0"))
                        adx_threshold = getattr(self._strategy, '_adx_threshold', Decimal("25"))

                        if (plus_di > minus_di
                                and adx_curr >= adx_threshold):
                            await self._executor.executar_ordem(
                                ticker=ticker, lado=Lado.COMPRA,
                                quantidade=self._quantity, preco_limit=preco,
                            )
                            self._position_tracker.open_position(ticker, preco)
                            self._signal_count += 1
                            self._logger.info(
                                f"{_B}{_GOLD}RE-ENTRY (Breakout + ADX above): {ticker} @ {preco}{_R}"
                            )
                            executed = True

                    if executed:
                        self._position_tracker.clear_reentry_state(ticker)
                        continue

                # 6. Buscar dados de mercado
                historico = await self._datafeed.obter_historico(
                    ticker, self._periodo_historico, self._intervalo_historico
                )
                dados = DadosMercado(
                    ticker=ticker,
                    preco_atual=cotacao.preco,
                    historico_precos=tuple(c.preco for c in historico),
                    historico_volumes=tuple(c.volume for c in historico),
                    historico_highs=tuple(c.high for c in historico if c.high is not None),
                    historico_lows=tuple(c.low for c in historico if c.low is not None),
                )

                if not self._first_tick_done:
                    self._log_first_tick_diagnostic(
                        ticker, cotacao.preco, len(historico), historico
                    )
                    self._logger.info(
                        f"{_B}{_BLUE}[INIT]{_R} {ticker} @ {cotacao.preco} | "
                        f"trailing={'ON' if self._position_tracker.get_trailing_stop(ticker) else 'OFF'}"
                    )

                # 7. Avaliar estratégia
                sinal = self._strategy.evaluate(dados)

                # 7b. Atualizar _prev_indicators para ADX crossover detection
                ind = getattr(self._strategy, '_last_indicators', None)
                if ind:
                    self._prev_indicators[ticker] = dict(ind)

                # 7c. TP dinâmico — reavaliar pelo ADX atual tick a tick
                if ind and self._position_tracker.get_position(ticker):
                    new_tp = self._strategy._tp_for_adx(ind["adx"])
                    self._position_tracker.update_take_profit(ticker, new_tp)

                if sinal is None or sinal.tipo.value == "neutro":
                    ind = getattr(self._strategy, '_last_indicators', None)
                    if ind:
                        pdi = float(ind["plus_di"])
                        mdi = float(ind["minus_di"])
                        adx_val = float(ind["adx"])
                        vol_r = float(ind["volume_ratio"])
                        gap = abs(pdi - mdi)

                        # DI colors: winner brighter
                        if pdi >= mdi:
                            c_pdi = _GREEN
                            c_mdi = _DIM
                        else:
                            c_pdi = _DIM
                            c_mdi = _RED

                        # ADX color by threshold proximity
                        if adx_val < 20:
                            c_adx = _RED
                        elif adx_val < 25:
                            c_adx = _YELLOW
                        else:
                            c_adx = _GREEN

                        # Gap color by crossover proximity
                        if gap < 5:
                            c_gap = f"{_B}{_GOLD}"
                        elif gap < 10:
                            c_gap = _YELLOW
                        else:
                            c_gap = _DIM

                        # SL/TP/Trail dinâmicos deste tick
                        pos = self._position_tracker.get_position(ticker)
                        sl_pct = pos.get("stop_loss_pct", self._position_tracker._stop_loss_pct) if pos else self._position_tracker._stop_loss_pct
                        tp_pct = pos.get("take_profit_pct", self._position_tracker._take_profit_pct) if pos else None
                        trail = self._position_tracker.get_trailing_stop(ticker)
                        sl_tp_str = f" | {_PURPLE}SL={float(sl_pct):.3%}{_R}"
                        if tp_pct is not None:
                            sl_tp_str += f" {_GOLD}TP={float(tp_pct):.3%}{_R}"
                        if trail is not None:
                            sl_tp_str += f" {_ORANGE}Trail={float(trail):,.2f}{_R}"

                        self._logger.info(
                            f"{_B}{_BLUE}[TICK #{self._tick_count}]{_R} {ticker} @ {cotacao.preco} "
                            f"| {c_pdi}+DI={pdi:.1f}{_R} {c_mdi}-DI={mdi:.1f}{_R} "
                            f"| {c_adx}ADX={adx_val:.1f}{_R} "
                            f"| {c_gap}gap={gap:.1f}{_R} "
                            f"| vol={vol_r:.1f}x{sl_tp_str}"
                        )
                    else:
                        self._logger.info(
                            f"{_B}{_BLUE}[TICK #{self._tick_count}]{_R} {ticker} @ {cotacao.preco}"
                        )
                    continue

                # 8. Position Guard — rejeitar duplicadas e fantasmas
                lado = Lado.COMPRA if sinal.tipo == TipoSinal.COMPRA else Lado.VENDA
                tem_posicao = self._position_tracker.get_position(ticker) is not None

                if lado == Lado.COMPRA and tem_posicao:
                    self._logger.info(
                        f"{_B}{_YELLOW}[GUARD]{_R} compra rejeitada: {ticker} já posicionado"
                    )
                    continue

                if lado == Lado.VENDA and not tem_posicao:
                    self._logger.info(
                        f"{_B}{_YELLOW}[GUARD]{_R} venda rejeitada: {ticker} sem posição"
                    )
                    continue

                # 9. Executar ordem + rastrear posição
                exec_result = await self._executor.executar_ordem(
                    ticker=ticker,
                    lado=lado,
                    quantidade=self._quantity,
                )

                # 9b. Persistir sinal + ordem via WriteQueue
                self._persist_signal(ticker, sinal, cotacao)
                broker_ordem_id = getattr(exec_result, 'ordem_id', '') or ''
                if not isinstance(broker_ordem_id, str):
                    broker_ordem_id = ''
                self._persist_order(ticker, "BUY" if lado == Lado.COMPRA else "SELL",
                                    self._quantity, cotacao.preco, cotacao,
                                    order_id=broker_ordem_id)

                if lado == Lado.COMPRA:
                    tp_pct = getattr(sinal, 'take_profit_pct', None)
                    self._position_tracker.open_position(ticker, cotacao.preco, take_profit_pct=tp_pct)
                    self._persist_position_open(ticker, cotacao.preco, tp_pct)
                    if self._reversal_collector:
                        self._reversal_collector.start_tracking(
                            ticker, cotacao.preco, cotacao.timestamp,
                        )

                    # Criar re-entry state para re-entrada após SL
                    ind = getattr(self._strategy, '_last_indicators', None)
                    if ind:
                        swing_low = ind.get("swing_low")
                        self._position_tracker.set_reentry_state(
                            ticker, crossover_price=cotacao.preco, swing_low=swing_low,
                        )

                    self._signal_count += 1
                    self._logger.info(
                        f"{_B}{_GOLD}POSIÇÃO ABERTA: {ticker} @ {cotacao.preco}{_R}"
                    )
                else:
                    pos = self._position_tracker.get_position(ticker)
                    if pos:
                        entrada = pos["preco_entrada"]
                        pnl_pct = float((cotacao.preco - entrada) / entrada * 100)
                        pnl_val = float(cotacao.preco - entrada) * self._quantity
                        self._closed_pnl.append(pnl_val)
                        lucro = pnl_val >= 0
                        tag = "LUCRO" if lucro else "PERDA"
                        cor_tag = _GREEN if lucro else _RED
                        sinal_pnl = "+" if lucro else ""
                        self._logger.info(
                            f"{_B}{cor_tag}{tag}{_R}: {_B}{_ORANGE}POSIÇÃO FECHADA{_R} {ticker} "
                            f"@ {cotacao.preco} | {cor_tag}{sinal_pnl}{pnl_pct:.3f}% "
                            f"(${sinal_pnl}{pnl_val:,.2f}){_R} ({sinal.razao})"
                        )
                        self._persist_pnl(ticker, entrada, cotacao.preco, pnl_val, pnl_pct, sinal.razao)
                    self._position_tracker.close_position(ticker)
                    self._persist_position_close(ticker, sinal.razao)
                    if self._reversal_collector and self._reversal_collector.is_tracking(ticker):
                        self._reversal_collector.stop_tracking(ticker, cotacao.preco)
                    self._signal_count += 1
            except Exception:
                self._error_count += 1
                self._logger.exception(f"Erro no tick #{self._tick_count} para {ticker}")

        if not self._first_tick_done:
            self._first_tick_done = True

        self._log_heartbeat(precos_atuais)

    # ── Persistence helpers ──

    def _persist_tick(self, ticker: str, cotacao) -> None:
        """Enfileira tick raw para persistência."""
        if not self._write_queue:
            return
        from src.core.paper.adapters.persistence.sqlite_write_queue import SaveTick
        import asyncio
        ts = getattr(cotacao, 'timestamp', '') or ''
        self._write_queue.enqueue_nowait(SaveTick({
            "time": ts,
            "symbol": ticker,
            "broker": "paper",
            "price": str(cotacao.preco),
            "volume": None,
            "side": None,
        }))

    def _persist_order(self, ticker: str, side: str, quantity: int, preco: Decimal,
                       cotacao=None, order_id: str = "") -> None:
        """Enfileira ordem para persistência."""
        if not self._write_queue:
            return
        from src.core.paper.adapters.persistence.sqlite_write_queue import SaveOrder
        from uuid import uuid4
        ts = getattr(cotacao, 'timestamp', '') or ''
        total = float(preco) * quantity
        self._write_queue.enqueue_nowait(SaveOrder({
            "created_at": ts,
            "id": order_id or f"ord-{uuid4().hex[:8]}",
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "price": str(preco),
            "total_value": str(total),
            "currency": "USD",
            "status": "EXECUTADA",
            "executed_at": ts,
            "order_type": "open",
            "broker": "paper",
            "strategy_name": self.strategy_name,
        }))

    def _persist_position_open(self, ticker: str, preco: Decimal, tp_pct: Decimal | None = None) -> None:
        """Enfileira abertura de posição do PositionTracker."""
        if not self._write_queue:
            return
        from src.core.paper.adapters.persistence.sqlite_write_queue import SaveStrategyPosition
        from datetime import datetime
        self._write_queue.enqueue_nowait(SaveStrategyPosition(
            ticker=ticker,
            strategy_name=self.strategy_name,
            data={
                "entry_price": str(preco),
                "side": "long",
                "status": "open",
                "take_profit_pct": str(tp_pct) if tp_pct else None,
                "stop_loss_pct": str(self._position_tracker._stop_loss_pct),
                "opened_at": datetime.now().isoformat(),
                "broker": "paper",
            },
        ))

    def _persist_position_close(self, ticker: str, reason: str = "") -> None:
        """Enfileira fechamento de posição do PositionTracker."""
        if not self._write_queue:
            return
        from src.core.paper.adapters.persistence.sqlite_write_queue import CloseStrategyPosition
        from datetime import datetime
        self._write_queue.enqueue_nowait(CloseStrategyPosition(
            ticker=ticker,
            strategy_name=self.strategy_name,
            data={
                "closed_at": datetime.now().isoformat(),
            },
        ))

    def _persist_trailing_update(self, ticker: str) -> None:
        """Enfileira atualização de trailing stop."""
        if not self._write_queue:
            return
        trailing = self._position_tracker._trailing.get(ticker)
        if not trailing:
            return
        from src.core.paper.adapters.persistence.sqlite_write_queue import SaveStrategyPosition
        self._write_queue.enqueue_nowait(SaveStrategyPosition(
            ticker=ticker,
            strategy_name=self.strategy_name,
            data={
                "trailing_pico": str(trailing["pico"]),
                "trailing_stop": str(trailing["stop"]),
            },
        ))

    def _persist_pnl(self, ticker: str, entry_price: Decimal, exit_price: Decimal,
                     pnl_val: float, pnl_pct: float, reason: str = "") -> None:
        """Enfileira PnL fechado para persistência."""
        if not self._write_queue:
            return
        from src.core.paper.adapters.persistence.sqlite_write_queue import SavePnl
        from datetime import datetime
        self._write_queue.enqueue_nowait(SavePnl({
            "closed_at": datetime.now().isoformat(),
            "ticker": ticker,
            "strategy_name": self.strategy_name,
            "broker": "paper",
            "entry_price": str(entry_price),
            "exit_price": str(exit_price),
            "quantity": self._quantity,
            "side": "long",
            "pnl_value": str(pnl_val),
            "pnl_value_display": pnl_val,
            "pnl_pct": pnl_pct,
            "reason": reason,
        }))

    def _persist_signal(self, ticker: str, sinal, cotacao) -> None:
        """Enfileira sinal para persistência."""
        if not self._write_queue:
            return
        from src.core.paper.adapters.persistence.sqlite_write_queue import SaveSignal
        ts = getattr(cotacao, 'timestamp', '') or ''
        signal_type = "BUY" if sinal.tipo.value == "compra" else "SELL"
        self._write_queue.enqueue_nowait(SaveSignal({
            "created_at": ts,
            "ticker": ticker,
            "strategy_name": self.strategy_name,
            "broker": "paper",
            "signal_type": signal_type,
            "price": str(sinal.preco),
            "reason": sinal.razao,
            "take_profit_pct": str(getattr(sinal, 'take_profit_pct', '')) if hasattr(sinal, 'take_profit_pct') and sinal.take_profit_pct else None,
        }))

    def _accumulate_ohlcv(self, ticker: str, cotacao) -> None:
        """Acumula OHLCV em memória para o minuto atual."""
        ts = getattr(cotacao, 'timestamp', '') or ''
        minute = ts[:16] if ts else ''  # "YYYY-MM-DDTHH:MM"
        price = str(cotacao.preco)

        if ticker not in self._ohlcv_acc:
            self._ohlcv_acc[ticker] = {
                "open": price, "high": price, "low": price, "close": price,
                "minute": minute, "volume": 0,
            }
        else:
            acc = self._ohlcv_acc[ticker]
            if acc["minute"] != minute:
                # Novo minuto — persiste candle anterior e reseta
                self._flush_ohlcv_candle(ticker)
                self._ohlcv_acc[ticker] = {
                    "open": price, "high": price, "low": price, "close": price,
                    "minute": minute, "volume": 0,
                }
            else:
                acc["close"] = price
                if Decimal(price) > Decimal(acc["high"]):
                    acc["high"] = price
                if Decimal(price) < Decimal(acc["low"]):
                    acc["low"] = price
                acc["volume"] = acc.get("volume", 0) + 1

    def _flush_ohlcv_candle(self, ticker: str) -> None:
        """Persiste candle OHLCV acumulado."""
        if not self._write_queue or ticker not in self._ohlcv_acc:
            return
        from src.core.paper.adapters.persistence.sqlite_write_queue import SaveOhlcv
        acc = self._ohlcv_acc[ticker]
        self._write_queue.enqueue_nowait(SaveOhlcv({
            "time": acc["minute"] + ":00",
            "symbol": ticker,
            "broker": "paper",
            "open": acc["open"],
            "high": acc["high"],
            "low": acc["low"],
            "close": acc["close"],
            "volume": acc.get("volume", 0),
            "interval": "1m",
        }))

    def flush_ohlcv(self) -> None:
        """Força flush de todos os candles OHLCV pendentes."""
        for ticker in list(self._ohlcv_acc.keys()):
            self._flush_ohlcv_candle(ticker)
