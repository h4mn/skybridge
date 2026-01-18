# -*- coding: utf-8 -*-
"""
Queue Scenarios — Demos do sistema de fila/messaging.

Port dos demos originais relacionados ao FileBasedJobQueue e
sistema de mensageria.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from os import getenv

from kernel import Result
from runtime.demo.base import (
    BaseDemo,
    DemoCategory,
    DemoContext,
    DemoLifecycle,
    DemoFlow,
    DemoFlowType,
    DemoResult,
)
from runtime.demo.registry import DemoRegistry


@DemoRegistry.register
class QueueE2EDemo(BaseDemo):
    """
    Demo E2E - FileBasedJobQueue + Observabilidade.

    Port de: scripts/demo_fila_e2e.py

    Demonstra o fluxo completo:
    1. Webhook Server enfileira job (FileBasedJobQueue)
    2. Worker desenfileira e processa (mesma fila compartilhada)
    3. Métricas coletadas em /metrics
    """

    demo_id = "queue-e2e"
    demo_name = "Queue E2E Demo - FileBasedJobQueue"
    description = "Demo E2E do sistema de fila com observabilidade completa"
    category = DemoCategory.QUEUE
    required_configs = []
    estimated_duration_seconds = 30
    tags = ["queue", "messaging", "filebased", "metrics", "e2e"]
    related_issues = [33]
    lifecycle = DemoLifecycle.DEV
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.JOB_EXECUTION,
            description="Demonstração do sistema de fila baseado em arquivos com métricas",
            actors=["Webhook Server", "FileBasedJobQueue", "Worker", "/metrics endpoint"],
            steps=[
                "Verificar health da API",
                "Verificar métricas iniciais da fila",
                "Enviar webhook de teste (enfileirar job)",
                "Verificar fila após enqueue",
                "Verificar arquivos da fila",
                "Calcular score de migração",
            ],
            entry_point="api",
            expected_outcome="Job enfileirado, processado e métricas coletadas",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        # Verifica se a API está rodando
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=2.0)
                if response.status_code != 200:
                    return Result.err("API não está saudável")
        except Exception:
            return Result.err("API não está rodando em localhost:8000")

        return Result.ok(None)

    async def run(self, context: DemoContext) -> DemoResult:
        import httpx
        import json
        from pathlib import Path
        from time import time

        api_base_url = "http://localhost:8000"
        queue_dir = Path("workspace/skybridge/fila")

        self.log_info(f"API URL: {api_base_url}")
        self.log_info(f"Queue Dir: {queue_dir}")
        self.log_info(f"Queue Type: FileBasedJobQueue")

        # 1. Verificar health
        self.log_progress(1, 6, "Verificando health da API...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_base_url}/health", timeout=5.0)
                if response.status_code == 200:
                    self.log_success(f"API está saudável: {response.json()['status']}")
                else:
                    return DemoResult.error(f"API retornou status {response.status_code}")
        except Exception as e:
            return DemoResult.error(f"Erro ao conectar na API: {e}")

        # 2. Verificar métricas iniciais
        self.log_progress(2, 6, "Coletando métricas iniciais...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_base_url}/metrics", timeout=5.0)
                if response.status_code == 200:
                    metrics_data = response.json()
                    if metrics_data.get("ok"):
                        metrics = metrics_data["metrics"]
                        self.log_info(f"Queue Size: {metrics['queue_size']}")
                        self.log_info(f"Enqueue Count: {metrics['enqueue_count']}")
                        self.log_info(f"Jobs/Hour: {metrics['jobs_per_hour']:.1f}")
                else:
                    self.log_warning(f"/metrics retornou status {response.status_code}")
        except Exception as e:
            self.log_error(f"Erro ao obter métricas: {e}")

        # 3. Enviar webhook
        self.log_progress(3, 6, "Enviando webhook de teste...")

        webhook_payload = {
            "action": "opened",
            "issue": {
                "number": int(time()),
                "title": "[TESTE] Demo FileBasedJobQueue",
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
                        "X-GitHub-Delivery": f"test-delivery-{int(time())}",
                    },
                    timeout=10.0,
                )

                if response.status_code == 202:
                    result = response.json()
                    job_id = result.get("job_id")
                    self.log_success(f"Webhook aceito: job_id={job_id}")
                elif response.status_code == 200:
                    result = response.json()
                    if result.get("message") == "pong":
                        self.log_info("Ping recebido (evento de teste)")
                    else:
                        self.log_info(f"Response: {result}")
                else:
                    return DemoResult.error(f"Webhook rejeitado: {response.status_code}")
        except Exception as e:
            return DemoResult.error(f"Erro ao enviar webhook: {e}")

        # 4. Verificar fila após enqueue
        self.log_progress(4, 6, "Verificando fila após enqueue...")
        await asyncio.sleep(1)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_base_url}/metrics", timeout=5.0)
                if response.status_code == 200:
                    metrics_data = response.json()
                    if metrics_data.get("ok"):
                        metrics = metrics_data["metrics"]
                        self.log_info(f"Queue Size: {metrics['queue_size']}")
                        self.log_info(f"Enqueue Count: {metrics['enqueue_count']}")
        except Exception as e:
            self.log_error(f"Erro ao verificar fila: {e}")

        # 5. Verificar arquivos da fila
        self.log_progress(5, 6, "Verificando arquivos da fila...")

        if queue_dir.exists():
            jobs_dir = queue_dir / "jobs"
            processing_dir = queue_dir / "processing"
            completed_dir = queue_dir / "completed"

            job_files = list(jobs_dir.glob("*.json")) if jobs_dir.exists() else []
            processing_files = list(processing_dir.glob("*.json")) if processing_dir.exists() else []
            completed_files = list(completed_dir.glob("*.json")) if completed_dir.exists() else []

            self.log_info(f"Jobs (pending): {len(job_files)}")
            self.log_info(f"Processing: {len(processing_files)}")
            self.log_info(f"Completed: {len(completed_files)}")

        # 6. Calcular score de migração
        self.log_progress(6, 6, "Calculando score de decisão de migração...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_base_url}/metrics", timeout=5.0)
                if response.status_code == 200:
                    metrics_data = response.json()
                    if metrics_data.get("ok"):
                        metrics = metrics_data["metrics"]

                        score = (
                            (metrics["jobs_per_hour"] / 20) * 3 +
                            (metrics["enqueue_latency_p95_ms"] / 100) * 2 +
                            (metrics["backlog_age_seconds"] / 300) * 2 +
                            (metrics["disk_usage_mb"] / 500) * 1
                        )

                        self.log_info(f"Score de Migração: {score:.2f}/7")

                        if score >= 5:
                            self.log_success("Recomendação: MIGRAR PARA REDIS")
                        elif score >= 3:
                            self.log_warning("Recomendação: AVALIAR MIGRAÇÃO")
                        else:
                            self.log_success("Recomendação: CONTINUAR STANDALONE")
        except Exception as e:
            self.log_error(f"Erro ao calcular score: {e}")

        self.log_success("Demo concluída!")

        return DemoResult.success(
            message="FileBasedJobQueue demonstrado com sucesso",
            queue_dir=str(queue_dir),
            api_url=api_base_url,
        )
