"""
Entidades do Domínio - Paper Trading

Entidades são objetos com identidade única que persistem ao longo do tempo.

Entidades planejadas:
- Portfolio: Conjunto de posições e saldo disponível
- Ordem: Intenção de compra/venda de um ativo
- Posicao: Quantidade detida de um ativo específico
- Historico: Registro de operações realizadas

Exemplo:
    portfolio = Portfolio(
        id="portfolio-001",
        saldo_disponivel=Decimal("10000.00"),
        posicoes=[]
    )
"""

from .portfolio import Portfolio

__all__ = ['Portfolio']
