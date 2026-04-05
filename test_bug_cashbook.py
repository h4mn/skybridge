#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste detalhado do bug do cashbook."""
import sys
sys.path.insert(0, 'B:/_repositorios/skybridge')

from decimal import Decimal
from src.core.paper.adapters.persistence.json_file_paper_state import JsonFilePaperState

# Carrega estado
state = JsonFilePaperState("B:/_repositorios/skybridge/paper_state.json")

# Mostra estado antes
print("=== ANTES ===")
d1 = state.carregar()
print(f"Cashbook keys: {list(d1.cashbook.keys())}")
print(f"Cashbook entries keys: {list(d1.cashbook.get('entries', {}).keys())}")

# Simula o que o DepositarHandler faz
import copy
estado = state.carregar()
currency = "BRL"
command_valor = Decimal("500")

# O código do handler
cashbook_raw = estado.cashbook.copy()
print(f"\n[cashbook_raw keys]: {list(cashbook_raw.keys())}")

if "entries" not in cashbook_raw:
    print("SEM entries - migra")
    old_entries = {k: v for k, v in cashbook_raw.items() if k != "base_currency"}
    cashbook = {
        "base_currency": cashbook_raw.get("base_currency", "BRL"),
        "entries": old_entries,
    }
else:
    print("COM entries - limpa")
    cashbook = {
        "base_currency": cashbook_raw.get("base_currency", "BRL"),
        "entries": cashbook_raw.get("entries", {}),
    }

print(f"[cashbook limpo keys]: {list(cashbook.keys())}")

# Modifica entries
entries = cashbook.get("entries", {})
if currency not in entries:
    entries[currency] = {"amount": "0", "conversion_rate": "1"}

current_amount = Decimal(str(entries[currency]["amount"]))
entries[currency]["amount"] = str(current_amount + command_valor)
print(f"[BRL amount após soma]: {entries[currency]['amount']}")

# Atualiza cashbook
cashbook["entries"] = entries
print(f"[cashbook entries keys]: {list(cashbook['entries'].keys())}")

# Salva no estado
estado.cashbook = cashbook
print(f"[estado.cashbook keys]: {list(estado.cashbook.keys())}")

# Salva
state.salvar(estado)

# Verifica depois
print("\n=== DEPOIS ===")
d2 = state.carregar()
print(f"Cashbook keys: {list(d2.cashbook.keys())}")
if "BRL" in d2.cashbook and "BRL" not in d2.cashbook.get("entries", {}):
    print("🔴 CHAVE ÓRFÃ DETECTADA!")
elif len(d2.cashbook) > 2:
    print(f"🔴 CHAVE ÓRFÃ DETECTADA! (>2 chaves): {list(d2.cashbook.keys())}")
else:
    print("✅ Estrutura limpa!")
