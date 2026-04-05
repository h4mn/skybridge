# Workers do Paper Orchestrator
"""
Workers especializados para o PaperOrchestrator.

Workers disponíveis:
- PositionWorker: Atualiza cotações e verifica ordens limite
- StrategyWorker: Avalia condições e sugere ações (stub)
- BacktestWorker: Roda simulação com dados históricos (stub)
"""

from .base import Worker, BaseWorker
from .position_worker import PositionWorker
from .strategy_worker import StrategyWorker
from .backtest_worker import BacktestWorker

__all__ = [
    "Worker",
    "BaseWorker",
    "PositionWorker",
    "StrategyWorker",
    "BacktestWorker",
]
