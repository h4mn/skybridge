# -*- coding: utf-8 -*-
"""Handler para processar DepositarCommand."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from ..commands.depositar import DepositarCommand
from ...ports.paper_state_port import PaperStatePort


@dataclass
class DepositoResult:
    """Resultado do depósito."""
    saldo_anterior: Decimal
    valor_depositado: Decimal
    saldo_atual: Decimal
    moeda: str


class DepositarHandler:
    """Handler para processar comandos de depósito.

    Adiciona saldo ao portfolio via PaperStatePort.
    Suporta depósito em múltiplas moedas.
    """

    def __init__(self, paper_state: PaperStatePort):
        self._paper_state = paper_state

    async def handle(
        self,
        command: DepositarCommand,
        moeda: Optional[str] = None,
        conversion_rate: Optional[Decimal] = None,
    ) -> DepositoResult:
        """Processa o command de depósito.

        Args:
            command: Command com valor a depositar
            moeda: Moeda do depósito (padrão: base_currency = BRL)
            conversion_rate: Taxa de conversão para base_currency

        Returns:
            DepositoResult com saldos antes/depois
        """
        estado = self._paper_state.carregar()
        saldo_anterior = estado.saldo

        # DEBUG: Mostra estado ANTES de modificar
        print(f"[DEPOSITAR_HANDLER] ANTES - cashbook keys: {list(estado.cashbook.keys())}")
        print(f"[DEPOSITAR_HANDLER] ANTES - cashbook id: {id(estado.cashbook)}")

        # Determina moeda do depósito
        currency = moeda or estado.base_currency
        rate = conversion_rate or Decimal("1")

        # Atualiza cashbook no formato v3 (com entries)
        # PRIMEIRO limpa chaves órfãs: mantém apenas base_currency e entries
        cashbook_raw = estado.cashbook.copy()
        if "entries" not in cashbook_raw:
            # Compatibilidade: migra para formato v3
            old_entries = {k: v for k, v in cashbook_raw.items() if k != "base_currency"}
            cashbook = {
                "base_currency": cashbook_raw.get("base_currency", "BRL"),
                "entries": old_entries,
            }
        else:
            # Formato v3: limpa chaves órfãs fora de "entries"
            cashbook = {
                "base_currency": cashbook_raw.get("base_currency", "BRL"),
                "entries": cashbook_raw.get("entries", {}),
            }

        entries = cashbook.get("entries", {})
        if currency not in entries:
            entries[currency] = {"amount": "0", "conversion_rate": str(rate)}

        # Soma ao amount existente
        current_amount = Decimal(str(entries[currency]["amount"]))
        entries[currency]["amount"] = str(current_amount + command.valor)
        entries[currency]["conversion_rate"] = str(rate)

        cashbook["entries"] = entries
        estado.cashbook = cashbook

        print(f"[DEPOSITAR_HANDLER] DEPOIS - cashbook keys: {list(estado.cashbook.keys())}")
        print(f"[DEPOSITAR_HANDLER] DEPOIS - cashbook id: {id(estado.cashbook)}")
        print(f"[DEPOSITAR_HANDLER] DEPOIS - entries[BRL] amount: {entries['BRL']['amount']}")

        self._paper_state.salvar(estado)

        # Recarrega para verificar
        estado_verificado = self._paper_state.carregar()
        print(f"[DEPOSITAR_HANDLER] VERIFICADO - cashbook keys: {list(estado_verificado.cashbook.keys())}")
        print(f"[DEPOSITAR_HANDLER] VERIFICADO - entries[BRL] amount: {estado_verificado.cashbook['entries']['BRL']['amount']}")

        return DepositoResult(
            saldo_anterior=saldo_anterior,
            valor_depositado=command.valor,
            saldo_atual=estado.saldo,
            moeda=currency,
        )
