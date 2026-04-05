"""
Camada de Aplicação - Paper Trading

Esta camada contém os casos de uso do sistema, organizados
em Commands (mudança de estado) e Queries (consultas).

Componentes:
- commands: Intenções de mudança de estado (CriarOrdemCommand)
- queries: Consultas de dados (ConsultarPortfolioQuery)
- handlers: Orquestração de commands e queries
- worker_orchestrator: Sistema de orquestração de workers

Padrão CQRS:
- Commands: Modificam estado, não retornam dados
- Queries: Retornam dados, não modificam estado
"""

from . import commands
from . import queries
from . import handlers
from .worker_orchestrator import (
    StartWorkerCommand,
    StopWorkerCommand,
    HandlerResult,
    WorkerOrchestrationResult,
    StartWorkerHandler,
    StopWorkerHandler,
    OrchestrateWorkersUseCase,
)

__all__ = [
    "commands",
    "queries",
    "handlers",
    "StartWorkerCommand",
    "StopWorkerCommand",
    "HandlerResult",
    "WorkerOrchestrationResult",
    "StartWorkerHandler",
    "StopWorkerHandler",
    "OrchestrateWorkersUseCase",
]
