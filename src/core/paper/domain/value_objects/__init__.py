"""
Value Objects do Domínio - Paper Trading

Value objects são objetos imutáveis sem identidade própria,
definidos apenas por seus atributos.

Value Objects planejados:
- Preco: Valor monetário com precisão decimal
- Ticker: Código de negociação de ativo (ex: "PETR4")
- Quantidade: Número inteiro de unidades
- Lado: Direção da operação (COMPRA/VENDA)
- StopLoss: Nível de acionamento de stop

Exemplo:
    ticker = Ticker("PETR4")
    preco = Preco(Decimal("28.50"))
    quantidade = Quantidade(100)
"""

from .ticker import Ticker

__all__ = ['Ticker']
