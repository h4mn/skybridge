# -*- coding: utf-8 -*-
"""
Porta do Paper State - Paper Trading

Define a interface para gestão unificada do estado do paper trading.
Esta porta resolve o conflito de múltiplos writers no paper_state.json.

Schema v2 unificado:
{
    "version": 2,
    "updated_at": "2026-03-27T20:00:00Z",
    "saldo": 95158.0,
    "saldo_inicial": 100000.0,
    "ordens": {...},
    "posicoes": {...},
    "portfolios": {...},
    "default_id": "..."
}
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from enum import IntEnum
from typing import Any, Dict, Optional


class PaperStateVersion(IntEnum):
    """
    Versões do schema do paper_state.json.

    V1: Legado - broker e repository escreviam separadamente
    V2: Unificado - PaperStatePort como único dono do arquivo
    V3: Multi-currency - CashBook com múltiplas moedas
    """
    V1 = 1  # Legado (broker + repo separados)
    V2 = 2  # Unificado
    V3 = 3  # Multi-currency (CashBook)
    CURRENT = V3  # Versão atual do schema


@dataclass
class PaperStateData:
    """
    Schema v3 do paper_state.json.

    Esta dataclass representa o estado unificado do paper trading,
    consolidando dados do broker e do repository.

    V3 adiciona suporte multi-moeda via CashBook.
    """

    version: int = field(default_factory=lambda: PaperStateVersion.CURRENT)
    updated_at: str = ""
    saldo_inicial: Decimal = Decimal("100000")
    base_currency: str = "BRL"
    cashbook: Dict[str, Any] = field(default_factory=lambda: {
        "base_currency": "BRL",
        "entries": {
            "BRL": {"amount": "100000", "conversion_rate": "1"}
        }
    })
    ordens: Dict[str, Any] = field(default_factory=dict)
    posicoes: Dict[str, Any] = field(default_factory=dict)
    portfolios: Dict[str, Any] = field(default_factory=dict)
    default_id: Optional[str] = None

    @property
    def saldo(self) -> Decimal:
        """Saldo total em moeda base (compatibilidade)."""
        total = Decimal("0")
        entries = self.cashbook.get("entries", {})
        for entry in entries.values():
            amount = Decimal(str(entry.get("amount", "0")))
            rate = Decimal(str(entry.get("conversion_rate", "0")))
            total += amount * rate
        return total

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável."""
        # LIMPA cashbook IN-PLACE ao serializar (garante estrutura v3 válida)
        # Remove chaves órfãs diretamente do dict self.cashbook
        keys_to_remove = [k for k in self.cashbook.keys() if k not in ("base_currency", "entries")]
        for key in keys_to_remove:
            del self.cashbook[key]

        return {
            "version": self.version,
            "updated_at": self.updated_at,
            "saldo": float(self.saldo),  # Compatibilidade (calculado)
            "saldo_inicial": float(self.saldo_inicial),
            "base_currency": self.base_currency,
            "cashbook": self.cashbook,
            "ordens": self.ordens,
            "posicoes": self.posicoes,
            "portfolios": self.portfolios,
            "default_id": self.default_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperStateData":
        """Cria instância a partir de dicionário."""
        # Default cashbook baseado no saldo legado (formato CashBook.from_dict)
        default_cashbook = {
            "base_currency": "BRL",
            "entries": {
                "BRL": {"amount": str(data.get("saldo", "100000")), "conversion_rate": "1"}
            }
        }

        # Carrega cashbook e LIMPA chaves órfãs (garante estrutura v3 válida)
        raw_cashbook = data.get("cashbook", default_cashbook)
        clean_cashbook = {
            "base_currency": raw_cashbook.get("base_currency", "BRL"),
            "entries": raw_cashbook.get("entries", {}),
        }

        return cls(
            version=data.get("version", PaperStateVersion.CURRENT),
            updated_at=data.get("updated_at", ""),
            saldo_inicial=Decimal(str(data.get("saldo_inicial", "100000"))),
            base_currency=data.get("base_currency", "BRL"),
            cashbook=clean_cashbook,
            ordens=data.get("ordens", {}),
            posicoes=data.get("posicoes", {}),
            portfolios=data.get("portfolios", {}),
            default_id=data.get("default_id"),
        )


class PaperStatePort(ABC):
    """
    Interface para gestão unificada do estado do paper trading.

    Esta porta é o único ponto de acesso ao paper_state.json,
    eliminando conflitos entre broker e repository.

    Implementações:
    - JsonFilePaperState: Persistência em arquivo JSON
    - InMemoryPaperState: Para testes (não persiste)
    """

    @abstractmethod
    def carregar(self) -> PaperStateData:
        """
        Carrega o estado do paper trading.

        Se o arquivo não existir, cria um novo estado com schema v2.
        Se existir em v1, migra automaticamente para v2.

        Returns:
            PaperStateData com o estado atual
        """
        pass

    @abstractmethod
    def salvar(self, estado: PaperStateData) -> None:
        """
        Salva o estado do paper trading.

        Atualiza updated_at automaticamente.

        Args:
            estado: Estado a ser persistido
        """
        pass

    @abstractmethod
    def resetar(self, saldo_inicial: Optional[Decimal] = None) -> PaperStateData:
        """
        Reseta o estado para valores iniciais.

        Args:
            saldo_inicial: Novo saldo inicial (opcional)

        Returns:
            PaperStateData resetado
        """
        pass
