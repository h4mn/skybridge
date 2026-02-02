#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste do comando `sb agent issue`.

Este script testa se o handler github.create_issue está funcionando.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests

# Configuração
BASE_URL = "http://127.0.0.1:8888"
GITHUB_REPO = "h4mn/skybridge"  # Substitua pelo seu repo se necessário


def test_agent_issue():
    """Testa o comando agent issue."""

    # Dados de teste
    titulo = "Teste CLI - Issue automática"
    desc = """
## Issue de teste

Esta issue foi criada automaticamente pelo comando `sb agent issue`.

### Objetivo
Testar a integração entre CLI e GitHub API.

### Labels
`automated`, `test`
"""

    labels = "automated, test"

    print(f"=== TESTE: sb agent issue ===")
    print(f"Título: {titulo}")
    print(f"Descrição: {desc[:50]}...")
    print(f"Labels: {labels}")
    print()

    # 1. Obter ticket
    print("1. Obtendo ticket...")
    ticket_response = requests.get(
        f"{BASE_URL}/ticket",
        params={"method": "github.createissue"}
    )
    if ticket_response.status_code != 200:
        print(f"✗ Erro ao obter ticket: {ticket_response.text}")
        return False

    ticket_data = ticket_response.json()
    if not ticket_data.get("ok"):
        print(f"✗ Erro ao obter ticket: {ticket_data}")
        return False

    ticket_id = ticket_data["ticket"]["id"]
    print(f"✓ Ticket obtido: {ticket_id}")

    # 2. Preparar envelope
    print("2. Preparando envelope...")
    envelope = {
        "ticket_id": ticket_id,
        "detail": {
            "context": "github",
            "action": "create_issue",
            "payload": {
                "title": titulo,
                "body": desc,
                "labels": labels.split(", "),
            },
        },
    }
    print("✓ Envelope preparado")

    # 3. Executar envelope
    print("3. Executando envelope (chamando GitHub API)...")
    env_response = requests.post(
        f"{BASE_URL}/envelope",
        json=envelope,
        headers={"Content-Type": "application/json"},
    )

    if env_response.status_code != 200:
        print(f"✗ Erro na execução: {env_response.text}")
        return False

    result = env_response.json()
    if result.get("ok"):
        issue_data = result.get("result")
        print(f"✓ Issue criada com sucesso!")
        print(f"  Número: #{issue_data.get('issue_number')}")
        print(f"  URL: {issue_data.get('issue_url')}")
        print(f"  Labels: {', '.join(issue_data.get('labels', []))}")
        print()
        print("=== SUCESSO ===")
        return True
    else:
        print(f"✗ Erro: {result.get('error')}")
        return False


if __name__ == "__main__":
    import sys

    try:
        success = test_agent_issue()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n✗ Interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
