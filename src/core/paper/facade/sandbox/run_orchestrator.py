#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de experimento para o PaperOrchestrator.

Demonstra o uso do orchestrator com workers — incluindo StrategyWorker real.

Uso:
    python -m src.core.paper.facade.sandbox.run_orchestrator

Controle:
    Ctrl+C para shutdown graceful.
"""

import asyncio
import logging
import os
import re
import signal
import sys
from decimal import Decimal

from .orchestrator import PaperOrchestrator
from .workers import PositionWorker
from .workers.strategy_worker import StrategyWorker

# Configuração de logging (console colorido + arquivo limpo)
log_file = "logs/guardiao-conservador.log"
os.makedirs("logs", exist_ok=True)

_ansi_re = re.compile(r"\033\[[0-9;]*m")


class _AnsiStripFormatter(logging.Formatter):
    """Formatter que remove ANSI codes — para FileHandler."""
    def format(self, record):
        return _ansi_re.sub("", super().format(record))


_fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_datefmt = "%H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=_fmt,
    datefmt=_datefmt,
    handlers=[
        logging.StreamHandler(),
    ],
)

# FileHandler separado com formatter limpo (sem ANSI)
_fh = logging.FileHandler(log_file, encoding="utf-8")
_fh.setFormatter(_AnsiStripFormatter(_fmt, _datefmt))
logging.getLogger().addHandler(_fh)

logger = logging.getLogger(__name__)

# --- Persistência SQLite ---
DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "paper", "data", "paper_state.db"
)


async def create_orchestrator() -> PaperOrchestrator:
    """Cria e configura o orchestrator com workers."""
    from src.core.paper.adapters.brokers.paper_broker import PaperBroker
    from src.core.paper.adapters.data_feeds.yahoo_finance_feed import YahooFinanceFeed
    from src.core.paper.adapters.persistence.sqlite_paper_state import SQLitePaperState
    from src.core.paper.adapters.persistence.sqlite_write_queue import WriteQueue
    from src.core.paper.domain.events.event_bus import get_event_bus
    from src.core.paper.domain.services.executor_ordem import ExecutorDeOrdem
    from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador
    from src.core.paper.domain.strategies.position_tracker import PositionTracker

    orchestrator = PaperOrchestrator(interval_seconds=1.0)

    # --- Infraestrutura SQLite ---
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    state = SQLitePaperState(DB_PATH)
    queue = WriteQueue(state, flush_interval=0.5, max_batch=50)
    await queue.start()

    # --- Infraestrutura de mercado ---
    datafeed = YahooFinanceFeed()
    broker = PaperBroker(feed=datafeed)
    event_bus = get_event_bus()

    # Validator mínimo que satisfaz ValidatorProtocol
    from src.core.paper.domain.events.ordem_events import OrdemCriada, Lado

    class SimpleValidator:
        async def validar_e_criar_ordem(
            self, ticker: str, lado: Lado, quantidade: int, preco_limit=None
        ) -> OrdemCriada:
            from uuid import uuid4
            return OrdemCriada(
                ordem_id=f"ordem-{uuid4().hex[:8]}",
                ticker=ticker,
                lado=lado,
                quantidade=quantidade,
            )

    executor = ExecutorDeOrdem(
        broker=broker,
        datafeed=datafeed,
        event_bus=event_bus,
        validator=SimpleValidator(),
    )

    # --- Parâmetros validados (backtest 7d 1m BTC-USD) ---
    tickers = ["BTC-USD"]

    # --- StrategyWorker REAL ---
    strategy = GuardiaoConservador()
    tracker = PositionTracker(
        stop_loss_pct=Decimal("0.005"),
        take_profit_pct=Decimal("0.004"),
    )
    strategy_worker = StrategyWorker(
        strategy=strategy,
        datafeed=datafeed,
        executor=executor,
        position_tracker=tracker,
        tickers=["BTC-USD"],
        periodo_historico=7,
        intervalo_historico="1m",
        write_queue=queue,
    )

    # --- Restaurar estado do SQLite (fonte primária) ---
    saved_positions = state.list_open_strategy_positions("guardiao-conservador")
    closed_pnl_rows = state.get_all_closed_pnl()
    closed_pnl_values = [float(r["pnl_value_display"]) for r in closed_pnl_rows]

    if saved_positions:
        for pos in saved_positions:
            restore_data = {
                "ticker": pos["ticker"],
                "preco_entrada": Decimal(pos["entry_price"]),
                "take_profit_pct": Decimal(pos["take_profit_pct"]) if pos.get("take_profit_pct") else None,
            }
            if pos.get("trailing_pico"):
                restore_data["trailing_pico"] = pos["trailing_pico"]
            if pos.get("trailing_stop"):
                restore_data["trailing_stop"] = pos["trailing_stop"]
            tracker.restore_positions([restore_data])
    if closed_pnl_values:
        strategy_worker.restore_closed_pnl(closed_pnl_values)

    n_pos = len(tracker.list_positions())
    if n_pos > 0 or closed_pnl_values:
        total_pnl = sum(closed_pnl_values)
        logger.info(
            f"[STATE] Restaurado do SQLite: {n_pos} posição(ões) aberta(s), "
            f"{len(closed_pnl_values)} trade(s) fechado(s), "
            f"PnL acumulado=${total_pnl:,.2f}"
        )

    # Hook de persistência — flush WriteQueue após cada tick
    async def _on_tick_complete() -> None:
        await queue.flush()

    orchestrator._on_tick_complete = _on_tick_complete
    orchestrator._queue = queue
    orchestrator._state = state
    orchestrator.register(strategy_worker)

    # --- PositionWorker (stub) ---
    def on_pnl_change(pnl: float, pnl_pct: float) -> None:
        logger.info(f"PnL atualizado: R$ {pnl:,.2f} ({pnl_pct:+.2f}%)")

    position_worker = PositionWorker(
        portfolio_id="sandbox",
        tickers=tickers,
        on_pnl_change=on_pnl_change,
    )
    orchestrator.register(position_worker)

    return orchestrator


async def main() -> None:
    """Ponto de entrada principal."""
    logger.info("=" * 50)
    logger.info("Paper Orchestrator - Guardião Conservador")
    logger.info("=" * 50)

    orchestrator = await create_orchestrator()

    # Setup signal handler para Ctrl+C
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def signal_handler() -> None:
        logger.info("\nRecebido sinal de shutdown (Ctrl+C)...")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass

    orchestrator_task = asyncio.create_task(orchestrator.run())
    await shutdown_event.wait()

    logger.info("Iniciando shutdown graceful...")
    await orchestrator.shutdown()
    await orchestrator_task

    # Close WriteQueue + SQLite
    queue = getattr(orchestrator, '_queue', None)
    state = getattr(orchestrator, '_state', None)
    if queue:
        await queue.close()
    if state:
        state.close()

    logger.info("Orchestrator finalizado com sucesso!")
    logger.info("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
        sys.exit(0)
