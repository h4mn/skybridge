# -*- coding: utf-8 -*-
"""
Demo: Teste de Sincronização de Labels GitHub → Trello.

Este script simula o recebimento de um webhook do GitHub com uma issue
contendo labels e verifica se eles são corretamente sincronizados para o
Trello como tags coloridas.

Labels configurados:
    - bug → bug (red)
    - feature → feature (green)
    - enhancement → melhoria (blue)
    - documentation → docs (orange)
    - good-first-issue → bom-para-iniciar (yellow)
"""
import hashlib
import hmac
import json
import sys
import time
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests

# Configurações
WEBHOOK_URL = "http://localhost:8000/webhooks/github"
WEBHOOK_SECRET = "c2b572058638253d9225d08846deefdacc3ad1024f33ff7e164cb4033a1f1870"


def create_github_webhook_payload(
    issue_number: int,
    title: str,
    labels: list[str],
    body: str | None = None,
) -> dict:
    """Cria payload de webhook do GitHub para issue aberta."""
    return {
        "action": "opened",
        "issue": {
            "number": issue_number,
            "title": title,
            "body": body or "Issue de teste para sincronização de labels",
            "labels": [{"name": label} for label in labels],
            "user": {"login": "test-user"},
            "html_url": f"https://github.com/test/repo/issues/{issue_number}",
        },
        "repository": {
            "name": "skybridge-test",
            "full_name": "h4mn/skybridge-test",
            "owner": {"login": "h4mn"},
        },
        "sender": {"login": "test-user"},
    }


def send_webhook(payload: dict) -> tuple[int, dict]:
    """Envia webhook para o servidor local."""
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_bytes = payload_json.encode()

    signature = f"sha256={hmac.new(WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()}"

    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature,
        "X-GitHub-Event": "issues.opened",
        "X-GitHub-Delivery": f"test-{int(time.time())}",
    }

    response = requests.post(WEBHOOK_URL, data=payload_bytes, headers=headers, timeout=10)
    return response.status_code, response.json() if response.content else {}


def print_header(title: str):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_label_sync():
    """Testa sincronização de labels GitHub → Trello."""

    print_header("🧪 Demo: Sincronização de Labels GitHub → Trello")

    # Teste 1: Issue com label 'feature'
    print("\n📋 Teste 1: Issue com label 'feature' (verde)")
    print("   Labels: feature, enhancement")

    payload1 = create_github_webhook_payload(
        issue_number=501,
        title="[Feature] Adicionar sistema de cache",
        labels=["feature", "enhancement"],
        body="Implementar cache redis para consultas frequentes",
    )

    print(f"   📦 Issue #{payload1['issue']['number']}: {payload1['issue']['title']}")
    print(f"   🏷️  Labels: {', '.join(payload1['issue']['labels'][l]['name'] for l in range(len(payload1['issue']['labels'])))}")

    try:
        status, response = send_webhook(payload1)
        if status in (200, 202):
            print(f"   ✅ Webhook recebido: {status}")
            if "job_id" in response:
                print(f"   🎯 Job ID: {response['job_id']}")
        else:
            print(f"   ❌ Erro: {status} - {response}")
    except Exception as e:
        print(f"   ❌ Erro ao enviar webhook: {e}")
        return

    time.sleep(2)

    # Teste 2: Issue com múltiplos labels
    print("\n📋 Teste 2: Issue com múltiplos labels")
    print("   Labels: bug, documentation, good-first-issue")

    payload2 = create_github_webhook_payload(
        issue_number=502,
        title="[Bug] Corrigir erro de autenticação",
        labels=["bug", "documentation", "good-first-issue"],
        body="Erro 403 ao tentar autenticar com token inválido",
    )

    print(f"   📦 Issue #{payload2['issue']['number']}: {payload2['issue']['title']}")
    print(f"   🏷️  Labels: {', '.join(l['name'] for l in payload2['issue']['labels'])}")

    try:
        status, response = send_webhook(payload2)
        if status in (200, 202):
            print(f"   ✅ Webhook recebido: {status}")
            if "job_id" in response:
                print(f"   🎯 Job ID: {response['job_id']}")
        else:
            print(f"   ❌ Erro: {status} - {response}")
    except Exception as e:
        print(f"   ❌ Erro ao enviar webhook: {e}")
        return

    print_header("✅ Testes Enviados!")

    print("\n📝 Próximos Passos:")
    print("   1. Verifique os logs do servidor para ver o processamento")
    print("   2. Abra o Trello e confira se os cards foram criados com os labels coloridos")
    print("   3. Labels esperados:")
    print("      • feature → verde")
    print("      • enhancement → azul (melhoria)")
    print("      • bug → vermelho")
    print("      • documentation → laranja (docs)")
    print("      • good-first-issue → amarelo (bom-para-iniciar)")

    print("\n💡 Para monitorar os logs em tempo real:")
    print("   tail -f <arquivo_de_log_do_servidor>")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        test_label_sync()
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar à API")
        print("💡 Certifique-se de que a API está rodando: python -m apps.api.main")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
        sys.exit(0)
