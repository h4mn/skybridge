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


def create_orchestrator() -> PaperOrchestrator:
    """Cria e configura o orchestrator com workers."""
    from src.core.paper.adapters.brokers.paper_broker import PaperBroker
    from src.core.paper.adapters.data_feeds.yahoo_finance_feed import YahooFinanceFeed
    from src.core.paper.domain.events.event_bus import get_event_bus
    from src.core.paper.domain.services.executor_ordem import ExecutorDeOrdem
    from src.core.paper.domain.services.validador_ordem import ValidadorDeOrdem
    from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador
    from src.core.paper.domain.strategies.position_tracker import PositionTracker

    orchestrator = PaperOrchestrator(interval_seconds=60.0)

    # --- Infraestrutura ---
    datafeed = YahooFinanceFeed()
    broker = PaperBroker(feed=datafeed)
    event_bus = get_event_bus()

    # Validator mínimo que satisfaz ValidatorProtocol
    from src.core.paper.domain.events.ordem_events import OrdemCriada, Lado

    class SimpleValidator:
        async def validar_e_criar_ordem(
            self, ticker: str, lado: Lado, quantidade: int, preco_limit=None
        ) -> OrdemCriada:
            return OrdemCriada(
                ordem_id=f"ordem-{ticker}-{lado.value}",
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

    # --- StrategyWorker REAL ---
    strategy = GuardiaoConservador()
    tracker = PositionTracker(
        stop_loss_pct=Decimal("0.0025"),
        take_profit_pct=Decimal("0.005"),
    )
    strategy_worker = StrategyWorker(
        strategy=strategy,
        datafeed=datafeed,
        executor=executor,
        position_tracker=tracker,
        tickers=["BTC-USD"],
        periodo_historico=30,
        intervalo_historico="1m",
    )
    orchestrator.register(strategy_worker)

    # --- PositionWorker (stub) ---
    def on_pnl_change(pnl: float, pnl_pct: float) -> None:
        logger.info(f"PnL atualizado: R$ {pnl:,.2f} ({pnl_pct:+.2f}%)")

    position_worker = PositionWorker(
        portfolio_id="sandbox",
        tickers=["BTC-USD"],
        on_pnl_change=on_pnl_change,
    )
    orchestrator.register(position_worker)

    return orchestrator


async def main() -> None:
    """Ponto de entrada principal."""
    logger.info("=" * 50)
    logger.info("Paper Orchestrator - Guardião Conservador")
    logger.info("=" * 50)

    orchestrator = create_orchestrator()

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

    logger.info("Orchestrator finalizado com sucesso!")
    logger.info("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
        sys.exit(0)
