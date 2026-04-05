#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste do depósito via FastAPI TestClient."""
import sys
sys.path.insert(0, 'B:/_repositorios/skybridge')

from fastapi.testclient import TestClient
from src.core.paper.facade.api.app import create_app

# Cria app e cliente
app = create_app()
client = TestClient(app)

# Limpa arquivo antes
import json
with open('B:/_repositorios/skybridge/paper_state.json', 'w') as f:
    json.dump({
        "version": 3,
        "updated_at": "2026-03-29T20:00:00",
        "saldo_inicial": 100000.0,
        "base_currency": "BRL",
        "cashbook": {
            "base_currency": "BRL",
            "entries": {
                "BRL": {"amount": "100000", "conversion_rate": "1"}
            }
        },
        "ordens": {},
        "posicoes": {},
        "portfolios": {},
        "default_id": None
    }, f)

# Testa depósito
print("=== ANTES ===")
with open('B:/_repositorios/skybridge/paper_state.json') as f:
    d = json.load(f)
    print(f"BRL: {d['cashbook']['entries']['BRL']['amount']}")
    print(f"Keys: {list(d['cashbook'].keys())}")

response = client.post(
    "/api/v1/paper/portfolio/deposito",
    json={"valor": 555, "currency": "BRL"}
)

print(f"\n=== RESPOSTA ===")
print(f"Status: {response.status_code}")
print(f"JSON: {response.json()}")

print("\n=== DEPOIS ===")
with open('B:/_repositorios/skybridge/paper_state.json') as f:
    d = json.load(f)
    print(f"BRL: {d['cashbook']['entries']['BRL']['amount']}")
    print(f"Keys: {list(d['cashbook'].keys())}")
    if len(d['cashbook']) > 2:
        print("🔴 CHAVE ÓRFÃ DETECTADA!")
    else:
        print("✅ Estrutura limpa!")
