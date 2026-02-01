# -*- coding: utf-8 -*-
"""
Script para testar webhook de issue do GitHub localmente.

Simula um webhook POST sem precisar criar uma issue real.
"""
import hashlib
import hmac
import json
import requests

# Configurações
WEBHOOK_URL = "http://localhost:8000/webhooks/github"
# Usa o mesmo segredo do .env
WEBHOOK_SECRET = "c2b572058638253d9225d08846deefdacc3ad1024f33ff7e164cb4033a1f1870"

# Payload de exemplo: issue aberta
payload = {
    "action": "opened",
    "issue": {
        "number": 999,
        "title": "Teste da issue do Webhook",
        "body": "Este é um teste de issue para verificar o processamento do webhook",
        "labels": [{"name": "teste"}],
    },
    "repository": {
        "name": "skybridge",
        "full_name": "h4mn/skybridge",
        "owner": {"login": "h4mn"},
    },
    "sender": {
        "login": "h4mn",
    },
}

# Converte para JSON
payload_json = json.dumps(payload, separators=(",", ":"))
payload_bytes = payload_json.encode()

# Gera assinatura HMAC SHA-256
signature = f"sha256={hmac.new(WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()}"

# Headers
headers = {
    "Content-Type": "application/json",
    "X-Hub-Signature-256": signature,
    "X-GitHub-Event": "issues.opened",
    "X-GitHub-Delivery": "12345-67890-abcde",
}

print(f"📤 Enviando webhook para: {WEBHOOK_URL}")
print(f"📋 Issue number: {payload['issue']['number']}")
print(f"📝 Title: {payload['issue']['title']}")
print()

# Envia requisição
try:
    response = requests.post(WEBHOOK_URL, data=payload_bytes, headers=headers, timeout=10)

    print(f"✅ Status: {response.status_code}")
    print(f"📦 Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code in (200, 202):
        job_id = response.json().get("job_id")
        if job_id:
            print(f"\n🎯 Job ID: {job_id}")
            print(f"🔍 Monitorando: {job_id}")
            print(f"\n📊 Verifique os logs da API para ver o processamento!")

except requests.exceptions.ConnectionError:
    print("❌ Erro: Não foi possível conectar à API")
    print("💡 Certifique-se de que a API está rodando: python -m apps.server.main")
except Exception as e:
    print(f"❌ Erro: {e}")
