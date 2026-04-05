"""Entidade Portfolio - Agregado raiz do domínio Paper Trading."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Portfolio:
    """Portfolio de paper trading.
    
    Agregado raiz que contém posições e gerencia o estado
    do portfólio de simulação.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    nome: str = "Portfolio Paper Trading"
    saldo_inicial: float = 100000.0
    saldo_atual: float = field(default=100000.0)
    criado_em: datetime = field(default_factory=datetime.now)
    
    def depositar(self, valor: float) -> None:
        """Deposita valor no portfolio."""
        if valor <= 0:
            raise ValueError("Valor deve ser positivo")
        self.saldo_atual += valor
    
    def retirar(self, valor: float) -> None:
        """Retira valor do portfolio."""
        if valor <= 0:
            raise ValueError("Valor deve ser positivo")
        if valor > self.saldo_atual:
            raise ValueError("Saldo insuficiente")
        self.saldo_atual -= valor
    
    def pnl(self) -> float:
        """Calcula o PnL (Profit and Loss) do portfolio."""
        return self.saldo_atual - self.saldo_inicial
    
    def pnl_percentual(self) -> float:
        """Calcula o PnL percentual."""
        return (self.pnl() / self.saldo_inicial) * 100
