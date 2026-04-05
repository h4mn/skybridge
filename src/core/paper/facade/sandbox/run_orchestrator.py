#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de experimento para o PaperOrchestrator.

Demonstra o uso do orchestrator com workers.

Uso:
    python -m src.core.paper.facade.sandbox.run_orchestrator

Controle:
    Ctrl+C para shutdown graceful.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from .orchestrator import PaperOrchestrator
from .workers import PositionWorker, StrategyWorker, BacktestWorker

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


def create_orchestrator() -> PaperOrchestrator:
    """Cria e configura o orchestrator com workers.

    Returns:
        Orchestrator configurado com PositionWorker.
    """
    orchestrator = PaperOrchestrator(interval_seconds=10.0)

    # PositionWorker com callback de PnL
    def on_pnl_change(pnl: float, pnl_pct: float) -> None:
        logger.info(f"PnL atualizado: R$ {pnl:,.2f} ({pnl_pct:+.2f}%)")

    position_worker = PositionWorker(
        portfolio_id="sandbox",
        tickers=["PETR4.SA", "BTC-USD"],
        on_pnl_change=on_pnl_change,
    )
    orchestrator.register(position_worker)

    # StrategyWorker (stub)
    strategy_worker = StrategyWorker(
        strategy_name="momentum",
        on_suggestion=lambda t, a: logger.info(f"Sugestão: {a} {t}"),
    )
    orchestrator.register(strategy_worker)

    # BacktestWorker (stub)
    backtest_worker = BacktestWorker(
        backtest_id="test_2026",
        on_progress=lambda c, t: logger.info(f"Backtest: {c}/{t}"),
    )
    orchestrator.register(backtest_worker)

    return orchestrator


async def main() -> None:
    """Ponto de entrada principal."""
    logger.info("=" * 50)
    logger.info("Paper Orchestrator - Sandbox Experiment")
    logger.info("=" * 50)

    orchestrator = create_orchestrator()

    # Setup signal handler para Ctrl+C
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def signal_handler() -> None:
        logger.info("\nRecebido sinal de shutdown (Ctrl+C)...")
        shutdown_event.set()

    # Registra handler para SIGINT (Ctrl+C)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows não suporta add_signal_handler
            pass

    # Executa orchestrator em background
    orchestrator_task = asyncio.create_task(orchestrator.run())

    # Aguarda sinal de shutdown
    await shutdown_event.wait()

    # Inicia shutdown graceful
    logger.info("Iniciando shutdown graceful...")
    await orchestrator.shutdown()

    # Aguarda task do orchestrator finalizar
    await orchestrator_task

    logger.info("Orchestrator finalizado com sucesso!")
    logger.info("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
        sys.exit(0)
