# -*- coding: utf-8 -*-
"""
Commands - Paper Trading

Commands representam intenções de mudança de estado no sistema.
Seguem o padrão Command para encapsular operações.

Commands implementados:
- CriarOrdemCommand: Criar uma nova ordem de compra/venda
- DepositarCommand: Depositar saldo no portfolio
- ResetarCommand: Resetar portfolio para estado inicial

Commands planejados (futuro):
- CancelarOrdemCommand: Cancelar uma ordem existente
- AtualizarStopLossCommand: Atualizar nível de stop loss

Exemplo:
    command = CriarOrdemCommand(
        ticker="PETR4.SA",
        lado="COMPRA",
        quantidade=100,
        preco_limite=Decimal("28.50"),
    )
    await handler.handle(command)
"""

from .criar_ordem import CriarOrdemCommand
from .depositar import DepositarCommand
from .resetar import ResetarCommand

__all__ = [
    "CriarOrdemCommand",
    "DepositarCommand",
    "ResetarCommand",
]
