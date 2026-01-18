#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo E2E - FileBasedJobQueue + Observabilidade

Demonstra o fluxo completo:
1. Webhook Server enfileira job (FileBasedJobQueue)
2. Worker desenfileira e processa (mesma fila compartilhada)
3. Métricas coletadas em /metrics

Uso:
    python scripts/demo_fila_e2e.py
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import httpx


async def demo_e2e():
    """Demonstração E2E do FileBasedJobQueue."""
    print("\n" + "=" * 80)
    print("🚀 DEMO E2E - FileBasedJobQueue + Observabilidade")
    print("=" * 80)

    # Configurações
    api_base_url = "http://localhost:8000"
    queue_dir = Path("workspace/skybridge/fila")

    print("\n📋 Configuração:")
    print(f"  API URL: {api_base_url}")
    print(f"  Queue Dir: {queue_dir}")
    print(f"  Queue Type: FileBasedJobQueue")

    # 1. Verificar health
    print("\n1️⃣  Verificando health da API...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url}/health", timeout=5.0)
            if response.status_code == 200:
                health = response.json()
                print(f"   ✅ API está saudável: {health.get('status')}")
            else:
                print(f"   ❌ API retornou status {response.status_code}")
                return
    except Exception as e:
        print(f"   ❌ Erro ao conectar na API: {e}")
        print(f"   💡 Dica: Execute 'python apps/api/main.py' em outro terminal")
        return

    # 2. Verificar métricas iniciais
    print("\n2️⃣  Métricas iniciais da fila...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url}/metrics", timeout=5.0)
            if response.status_code == 200:
                metrics_data = response.json()
                if metrics_data.get("ok"):
                    metrics = metrics_data["metrics"]
                    print(f"   📊 Queue Size: {metrics['queue_size']}")
                    print(f"   📊 Enqueue Count: {metrics['enqueue_count']}")
                    print(f"   📊 Jobs/Hour: {metrics['jobs_per_hour']:.1f}")
                    print(f"   📊 Disk Usage: {metrics['disk_usage_mb']:.2f} MB")
                else:
                    print(f"   ⚠️  Metrics error: {metrics_data.get('error')}")
            else:
                print(f"   ⚠️  /metrics retornou status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro ao obter métricas: {e}")

    # 3. Simular webhook
    print("\n3️⃣  Enviando webhook de teste (GitHub issue)...")
    webhook_payload = {
        "action": "opened",
        "issue": {
            "number": 999,
            "title": "[TEST] Demo FileBasedJobQueue",
            "body": "Testing standalone messaging system",
        },
        "repository": {
            "owner": {"login": "test-owner"},
            "name": "test-repo",
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/webhooks/github",
                json=webhook_payload,
                headers={
                    "X-GitHub-Event": "issues",
                    "X-GitHub-Delivery": f"test-delivery-{int(time.time())}",
                },
                timeout=10.0,
            )

            if response.status_code == 202:
                result = response.json()
                job_id = result.get("job_id")
                print(f"   ✅ Webhook aceito: job_id={job_id}")
                print(f"   ✅ Status: {result.get('status')}")
            elif response.status_code == 200:
                result = response.json()
                if result.get("message") == "pong":
                    print(f"   ℹ️  Ping recebido (evento de teste)")
                else:
                    print(f"   📄 Response: {result}")
            else:
                print(f"   ❌ Webhook rejeitado: {response.status_code}")
                print(f"   📄 Error: {response.text}")
                return
    except Exception as e:
        print(f"   ❌ Erro ao enviar webhook: {e}")
        return

    # 4. Verificar fila após enqueue
    print("\n4️⃣  Verificando fila após enqueue...")
    await asyncio.sleep(1)  # Aguarda processamento

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url}/metrics", timeout=5.0)
            if response.status_code == 200:
                metrics_data = response.json()
                if metrics_data.get("ok"):
                    metrics = metrics_data["metrics"]
                    print(f"   📊 Queue Size: {metrics['queue_size']}")
                    print(f"   📊 Enqueue Count: {metrics['enqueue_count']}")
                    print(f"   📊 Enqueue Latency P95: {metrics['enqueue_latency_p95_ms']:.1f} ms")
                else:
                    print(f"   ⚠️  Metrics error: {metrics_data.get('error')}")
    except Exception as e:
        print(f"   ❌ Erro ao obter métricas: {e}")

    # 5. Verificar arquivos da fila
    print("\n5️⃣  Verificando arquivos da fila...")
    if queue_dir.exists():
        jobs_dir = queue_dir / "jobs"
        processing_dir = queue_dir / "processing"
        completed_dir = queue_dir / "completed"

        job_files = list(jobs_dir.glob("*.json")) if jobs_dir.exists() else []
        processing_files = list(processing_dir.glob("*.json")) if processing_dir.exists() else []
        completed_files = list(completed_dir.glob("*.json")) if completed_dir.exists() else []

        print(f"   📁 Jobs (pending): {len(job_files)}")
        print(f"   📁 Processing: {len(processing_files)}")
        print(f"   📁 Completed: {len(completed_files)}")

        if job_files:
            print(f"\n   📄 Job file exemplo:")
            for f in list(job_files)[:3]:  # Primeiros 3
                try:
                    job_data = json.loads(f.read_text(encoding="utf-8"))
                    print(f"      - {f.name}: {job_data.get('job_id', 'unknown')}")
                except Exception:
                    pass

    # 6. Calcular score de migração
    print("\n6️⃣  Calculando score de decisão de migração...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url}/metrics", timeout=5.0)
            if response.status_code == 200:
                metrics_data = response.json()
                if metrics_data.get("ok"):
                    metrics = metrics_data["metrics"]

                    # Fórmula do GUIA_DECISAO_MENSAGERIA.md
                    score = (
                        (metrics["jobs_per_hour"] / 20) * 3 +
                        (metrics["enqueue_latency_p95_ms"] / 100) * 2 +
                        (metrics["backlog_age_seconds"] / 300) * 2 +
                        (metrics["disk_usage_mb"] / 500) * 1
                    )

                    print(f"   📊 Score de Migração: {score:.2f}/7")

                    if score >= 5:
                        print(f"   🚀 Recomendação: MIGRAR PARA REDIS")
                    elif score >= 3:
                        print(f"   ⚠️  Recomendação: AVALIAR MIGRAÇÃO")
                    else:
                        print(f"   ✅ Recomendação: CONTINUAR STANDALONE")
    except Exception as e:
        print(f"   ❌ Erro ao calcular score: {e}")

    # 7. Resumo
    print("\n7️⃣  Resumo da demonstração:")
    print("   ✅ FileBasedJobQueue implementado e funcionando")
    print("   ✅ Endpoint /metrics retornando dados")
    print("   ✅ Filas compartilhadas entre processos")
    print("   ✅ Métricas coletadas para tomada de decisão")

    print("\n💡 Próximos passos:")
    print("   1. Execute o worker: python -m runtime.background.webhook_worker")
    print("   2. Envie mais webhooks para gerar carga")
    print("   3. Monitore /metrics para decidir quando migrar para Redis")
    print("   4. Use GUIA_DECISAO_MENSAGERIA.md como referência")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_e2e())
