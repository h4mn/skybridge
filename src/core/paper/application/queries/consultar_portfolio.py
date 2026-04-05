"""Query para consultar portfolio."""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from src.core.paper.domain.currency import Currency


@dataclass
class ConsultarPortfolioQuery:
    """Query para consultar o estado do portfolio."""

    portfolio_id: Optional[str] = None
    base_currency: Optional[Currency] = None  # Moeda alvo para consolidação


@dataclass
class CashbookEntryResult:
    """Entrada do cashbook no resultado do portfolio."""
    currency: str
    amount: float
    conversion_rate: float
    value_in_base_currency: float


@dataclass
class PortfolioResult:
    """Resultado da consulta do portfolio."""

    id: str
    nome: str
    saldo_inicial: float
    saldo_atual: float
    pnl: float
    pnl_percentual: float
    currency: Currency = Currency.BRL  # Moeda do resultado
    cashbook: Dict[str, Any] = field(default_factory=dict)  # Saldo por moeda
    base_currency: str = "BRL"  # Moeda base do cashbook
