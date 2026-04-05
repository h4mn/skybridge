# -*- coding: utf-8 -*-
"""Handler para processar ResetarCommand."""
from dataclasses import dataclass
from decimal import Decimal

from ..commands.resetar import ResetarCommand
from ...ports.paper_state_port import PaperStatePort


@dataclass
class ResetarResult:
    """Resultado do reset."""
    saldo_anterior: Decimal
    saldo_novo: Decimal
    ordens_removidas: int
    posicoes_removidas: int


class ResetarHandler:
    """Handler para processar comandos de reset.

    Limpa todas as ordens, posições e redefine saldo.
    """

    def __init__(self, paper_state: PaperStatePort):
        self._paper_state = paper_state

    async def handle(self, command: ResetarCommand) -> ResetarResult:
        """Processa o command de reset.

        Args:
            command: Command com novo saldo inicial (opcional)

        Returns:
            ResetarResult com estado anterior e novo
        """
        estado = self._paper_state.carregar()
        saldo_anterior = estado.saldo
        ordens_removidas = len(estado.ordens)
        posicoes_removidas = len(estado.posicoes)

        # Reseta o estado via PaperStatePort
        novo_estado = self._paper_state.resetar(command.saldo_inicial)

        return ResetarResult(
            saldo_anterior=saldo_anterior,
            saldo_novo=novo_estado.saldo,
            ordens_removidas=ordens_removidas,
            posicoes_removidas=posicoes_removidas,
        )
