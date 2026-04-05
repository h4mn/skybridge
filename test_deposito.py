#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste manual do DepositarHandler."""
import sys
sys.path.insert(0, 'B:/_repositorios/skybridge')

from decimal import Decimal
from src.core.paper.adapters.persistence.json_file_paper_state import JsonFilePaperState
from src.core.paper.application.handlers.depositar_handler import DepositarHandler
from src.core.paper.application.commands.depositar import DepositarCommand

# Carrega estado
state = JsonFilePaperState("B:/_repositorios/skybridge/paper_state.json")
estado = state.carregar()

print("=== ESTADO ANTES ===")
print(f"BRL entries: {estado.cashbook['entries']['BRL']}")
print(f"Cashbook keys: {list(estado.cashbook.keys())}")
print(f"Saldo: {estado.saldo}")

# Testa depósito
handler = DepositarHandler(state)
command = DepositarCommand(valor=Decimal("999"))

import asyncio
result = asyncio.run(handler.handle(command, moeda="BRL"))

print("\n=== RESULTADO ===")
print(f"Saldo anterior: {result.saldo_anterior}")
print(f"Valor depositado: {result.valor_depositado}")
print(f"Saldo atual: {result.saldo_atual}")

# Recarrega estado
estado2 = state.carregar()
print("\n=== ESTADO DEPOIS ===")
print(f"BRL entries: {estado2.cashbook['entries']['BRL']}")
print(f"Cashbook keys: {list(estado2.cashbook.keys())}")
print(f"Saldo: {estado2.saldo}")
