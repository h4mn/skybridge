#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de teste para criar issue via API REST simples."""

import requests

BASE_URL = "http://localhost:8000"

def create_issue_direct():
    """Cria issue chamando a API REST diretamente (sem SkyRPC)."""

    # Payload
    payload = {
        "title": "Bug: Uso incorreto de NotImplemented em DemoRegistry",
        "body": "## Localizacao\nArquivo: src/runtime/demo/registry.py linha 61\n\n## Problema\nO codigo usa is NotImplemented ao inves de hasattr() ou == NotImplemented\n\n## Por que e errado\nNotImplemented e para metodos binarios especiais como __add__\n\n## Solucao\nUsar abc.ABC com @abstractmethod ou verificar com hasattr()\n\nLabels: automated, bug, code-smell",
        "labels": ["automated", "bug", "code-smell"],
    }

    print("=== CRIANDO ISSUE VIA API REST ===")
    print(f"Título: {payload['title']}")
    print(f"Labels: {', '.join(payload['labels'])}")
    print()

    # Chama endpoint direto
    print("Enviando requisição para /api/observability/github/create-issue...")
    response = requests.post(
        f"{BASE_URL}/api/observability/github/create-issue",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            print(f"\n✅ **ISSUE CRIADA COM SUCESSO!**")
            print(f"   Número: #{result['issue_number']}")
            print(f"   URL: {result['issue_url']}")
            print(f"   Labels: {', '.join(result['labels'])}")
            print()
            print("📊 **Acompanhe em tempo real:**")
            print(f"   🌐 GitHub: {result['issue_url']}")
            print(f"   🎭 Eventos: http://localhost:8000/web/#/events")
            print(f"   🎯 Trello: Card deve ser criado automaticamente")
        else:
            print(f"\n❌ Erro: {result.get('error')}")
    else:
        print(f"\n❌ Erro HTTP {response.status_code}: {response.text}")

if __name__ == "__main__":
    create_issue_direct()
