# -*- coding: utf-8 -*-
"""
Teste de webhook com issue simples para criar script hello world.

Este teste envia uma issue que pede ao subagente para criar
um script Python hello world simples.
"""
import hashlib
import hmac
import json
import requests
import time
from datetime import datetime

# Configurações
WEBHOOK_URL = "http://localhost:8000/webhooks/github"
WEBHOOK_SECRET = "c2b572058638253d9225d08846deefdacc3ad1024f33ff7e164cb4033a1f1870"

# Issue payload - pede para criar script hello world
payload = {
    "action": "opened",
    "issue": {
        "number": 1001,  # Issue número 1001
        "title": "Create hello world script",
        "body": """## Task
Create a simple Python hello world script.

## Requirements
- Create a file called `hello_world.py` in the root of the repository
- The script should print "Hello, World!" when executed
- Keep it simple and straightforward

## Expected Result
A working Python script that prints hello world.
""",
        "labels": [{"name": "good-first-issue"}, {"name": "enhancement"}]
    },
    "repository": {
        "name": "skybridge",
        "full_name": "h4mn/skybridge",
        "owner": {"login": "h4mn"}
    },
    "sender": {"login": "test-user"}
}

# Prepara signature
payload_bytes = json.dumps(payload).encode("utf-8")
signature = f"sha256={hmac.new(WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()}"

# Headers
headers = {
    "Content-Type": "application/json",
    "X-GitHub-Event": "issues.opened",
    "X-Hub-Signature-256": signature,
    "X-GitHub-Delivery": f"{datetime.utcnow().isoformat()}",
}

print("📤 Enviando webhook para criar hello world script")
print(f"📋 Issue number: {payload['issue']['number']}")
print(f"📝 Title: {payload['issue']['title']}")
print()

# Envia webhook
response = requests.post(WEBHOOK_URL, json=payload, headers=headers)

print(f"✅ Status: {response.status_code}")
print(f"📦 Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 202:
    job_id = response.json().get("job_id")
    print(f"\n🎯 Job ID: {job_id}")
    print(f"🔍 Monitorando: {job_id}")
    print()
    print("📊 Aguardando processamento...")

    # Aguarda processamento
    time.sleep(5)

    print()
    print("🔍 Verificando worktree e branch criados...")
    print("📁 Worktree deve estar em: ../skybridge-auto/")
    print("🌲 Branch deve ser: webhook/github/issue/1001/<suffix>")
    print()
    print("📊 Verifique os logs da API para ver o que o subagente fez!")
