# -*- coding: utf-8 -*-
"""
GitHub Webhook Server — Servidor para receber webhooks reais do GitHub.

Este script inicia um servidor FastAPI que:
1. Recebe webhooks do GitHub
2. Processa via WebhookProcessor
3. Cria cards no Trello automaticamente
4. Executa agentes (opcional)

Uso:
    python github_webhook_server.py

    Depois configure o webhook no GitHub:
    URL: https://your-ngrok-url.webhook/github
    Secret: (opcional) configure no .env como GITHUB_WEBHOOK_SECRET
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import logging
import hmac
import hashlib

from core.webhooks.application.webhook_processor import WebhookProcessor
from core.webhooks.ports.job_queue_port import JobQueuePort
from core.kanban.application.trello_integration_service import TrelloIntegrationService
from infra.kanban.adapters.trello_adapter import TrelloAdapter

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class InMemoryJobQueue(JobQueuePort):
    """Implementação simples em memória para demo."""

    def __init__(self, ttl_hours: int = 24):
        self._jobs = {}
        self._delivery_ids = {}  # delivery_id → timestamp (para TTL)
        self._ttl = timedelta(hours=ttl_hours)

    def _cleanup_expired_deliveries(self):
        """Remove delivery IDs expirados."""
        if not self._delivery_ids:
            return

        now = datetime.utcnow()
        expired = [
            delivery_id
            for delivery_id, timestamp in self._delivery_ids.items()
            if now - timestamp > self._ttl
        ]

        for delivery_id in expired:
            del self._delivery_ids[delivery_id]

        if expired:
            logger.debug(f"Cleanup: removidos {len(expired)} delivery IDs expirados")

    async def enqueue(self, job):
        """Enfileira job."""
        # Cleanup antes de processar
        self._cleanup_expired_deliveries()

        self._jobs[job.job_id] = job

        # Registra delivery_id com timestamp atual
        if job.event.delivery_id:
            self._delivery_ids[job.event.delivery_id] = datetime.utcnow()

        logger.info(f"Job enfileirado: {job.job_id}")

    async def get_job(self, job_id: str):
        """Busca job por ID."""
        return self._jobs.get(job_id)

    async def complete(self, job_id: str, result: dict | None = None):
        """Marca job como completado."""
        if job_id in self._jobs:
            self._jobs[job_id].mark_completed()
            logger.info(f"Job completado: {job_id}")

    async def fail(self, job_id: str, error: str):
        """Marca job como falhou."""
        if job_id in self._jobs:
            self._jobs[job_id].mark_failed(error)
            logger.error(f"Job falhou: {job_id} - {error}")

    async def dequeue(self):
        """Remove próximo job da fila."""
        # Implementação simples: retorna None (não usado neste servidor)
        return None

    def size(self) -> int:
        """Retorna tamanho da fila."""
        return len(self._jobs)

    async def exists_by_delivery(self, delivery_id: str) -> bool:
        """Verifica se delivery_id já foi processado."""
        # Cleanup antes de verificar
        self._cleanup_expired_deliveries()

        return delivery_id in self._delivery_ids


# Inicializa app
app = FastAPI(title="Skybridge Webhook Server")

# Inicializa dependências
job_queue = InMemoryJobQueue()

# Inicializa TrelloIntegrationService se configurado
trello_service = None
trello_api_key = os.getenv("TRELLO_API_KEY")
trello_api_token = os.getenv("TRELLO_API_TOKEN")
trello_board_id = os.getenv("TRELLO_BOARD_ID")

if trello_api_key and trello_api_token and trello_board_id:
    trello_adapter = TrelloAdapter(trello_api_key, trello_api_token, trello_board_id)
    trello_service = TrelloIntegrationService(trello_adapter)
    logger.info("✅ TrelloIntegrationService inicializado")
else:
    logger.warning("⚠️  Trello não configurado - cards não serão criados")

# Inicializa WebhookProcessor
webhook_processor = WebhookProcessor(job_queue, trello_service)


def verify_github_signature(payload: bytes, signature: str | None, secret: str | None) -> bool:
    """
    Verifica assinatura do webhook do GitHub.

    Args:
        payload: Payload bruto do webhook
        signature: Assinatura do header X-Hub-Signature-256
        secret: Secret do webhook (GITHUB_WEBHOOK_SECRET)

    Returns:
        True se assinatura válida, False caso contrário
    """
    if not secret:
        # Sem secret configurado - pula verificação (apenas para development)
        logger.warning("⚠️  GITHUB_WEBHOOK_SECRET não configurado - pulando verificação de assinatura")
        return True

    if not signature:
        logger.error("❌ Assinatura ausente")
        return False

    # GitHub usa sha256=hash
    if not signature.startswith("sha256="):
        logger.error(f"❌ Formato de assinatura inválido: {signature[:20]}...")
        return False

    signature_hash = signature[7:]  # Remove "sha256="

    # Calcula hash esperado
    expected_hash = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Compara de forma segura
    return hmac.compare_digest(expected_hash, signature_hash)


@app.get("/")
async def root():
    """Health check."""
    return {
        "service": "Skybridge Webhook Server",
        "status": "running",
        "trello_configured": trello_service is not None,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health():
    """Health check detalhado."""
    return {
        "status": "healthy",
        "trello": trello_service is not None,
        "jobs_processed": len(job_queue._jobs),
    }


@app.post("/webhook/github")
async def github_webhook(request: Request):
    """
    Recebe webhook do GitHub.

    Headers esperados:
        X-GitHub-Event: Tipo do evento (ex: "issues", "ping")
        X-Hub-Signature-256: Assinatura HMAC (se secret configurado)
        X-GitHub-Delivery: ID único da entrega

    Body: JSON payload do evento
    """
    try:
        # Lê payload bruto para verificação de assinatura
        payload_bytes = await request.body()
        payload = await request.json()

        # Extrai headers
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        delivery_id = request.headers.get("X-GitHub-Delivery", "")
        signature = request.headers.get("X-Hub-Signature-256")

        correlation_id = delivery_id or "unknown"
        logger.info(
            f"📨 Webhook recebido | correlation_id={correlation_id} | "
            f"event_type={event_type} | delivery={delivery_id}"
        )

        # Verifica assinatura se secret configurado
        webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if webhook_secret:
            if not verify_github_signature(payload_bytes, signature, webhook_secret):
                logger.error("❌ Assinatura inválida")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid signature"}
                )

        # Processa webhook
        result = await webhook_processor.process_webhook(
            source="github",
            event_type=event_type,
            payload=payload,
            signature=signature,
            delivery_id=delivery_id,
        )

        if result.is_ok:
            job_id = result.unwrap()
            if job_id is None:
                # Webhook duplicado, já processado anteriormente
                logger.info(
                    f"✅ Webhook duplicado ignorado | correlation_id={correlation_id}"
                )
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "ignored",
                        "message": "Webhook já processado anteriormente",
                        "correlation_id": correlation_id,
                    }
                )

            logger.info(
                f"✅ Webhook processado | correlation_id={correlation_id} | job_id={job_id}"
            )

            return JSONResponse(
                status_code=200,
                content={
                    "status": "accepted",
                    "job_id": job_id,
                    "correlation_id": correlation_id,
                    "message": "Webhook processado com sucesso"
                }
            )
        else:
            error_msg = result.error
            logger.error(
                f"❌ Erro ao processar webhook | correlation_id={correlation_id} | error={error_msg}"
            )

            return JSONResponse(
                status_code=422,
                content={"error": error_msg, "correlation_id": correlation_id}
            )

    except Exception as e:
        logger.exception(
            f"💥 Erro ao processar webhook | correlation_id={correlation_id} | error={e}"
        )
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


def print_banner():
    """Imprime banner de inicialização."""
    print("\n" + "=" * 80)
    print("🚀 SKYBRIDGE WEBHOOK SERVER")
    print("=" * 80)
    print("\nEste servidor recebe webhooks do GitHub e cria cards no Trello.")
    print("\n📋 Configuração:")
    print(f"  Trello: {'✅ Configurado' if trello_service else '❌ Não configurado'}")
    print(f"  Webhook Secret: {'✅ Configurado' if os.getenv('GITHUB_WEBHOOK_SECRET') else '❌ Não configurado (inseguro)'}")


def start_ngrok(port: int):
    """
    Inicia túnel ngrok automaticamente.

    Args:
        port: Porta local para expor

    Returns:
        URL pública do ngrok ou None se falhar
    """
    ngrok_enabled = os.getenv("NGROK_ENABLED", "false").lower() == "true"

    if not ngrok_enabled:
        return None

    try:
        from pyngrok import ngrok

        # Configura auth token se disponível
        auth_token = os.getenv("NGROK_AUTH_TOKEN")
        if auth_token:
            ngrok.set_auth_token(auth_token)

        # Usa domínio reservado se disponível
        domain = os.getenv("NGROK_DOMAIN")

        if domain:
            tunnel = ngrok.connect(port, domain=domain, bind_tls=True)
            logger.info(f"Túnel Ngrok ativo com domínio reservado: {domain}")
        else:
            tunnel = ngrok.connect(port, bind_tls=True)
            logger.info(f"Túnel Ngrok ativo")

        public_url = tunnel.public_url

        # Imprime URLs coloridas
        print("\n" + "=" * 80)
        print("🌐 NGROK TÚNEL ATIVO")
        print("=" * 80)
        print(f"\n✅ URL Pública: {public_url}")
        print(f"📡 Webhook URL: {public_url}/webhook/github")

        if domain:
            print(f"🔒 Domínio Reservado: {domain}")

        print("\n📋 Para configurar webhook no GitHub:")
        print(f"   1. Vá para: https://github.com/h4mn/skybridge/settings/hooks")
        print(f"   2. Clique em 'Add webhook'")
        print(f"   3. Payload URL: {public_url}/webhook/github")
        print(f"   4. Content type: application/json")
        print(f"   5. Events: Issues → Issues only (opened, edited, closed)")
        print(f"   6. Clique em 'Add webhook'")
        print("\n" + "=" * 80)

        return public_url

    except ImportError:
        logger.warning("pyngrok não instalado - pip install pyngrok")
        print("\n⚠️  pip install pyngrok (para ngrok automático)")
        return None
    except Exception as e:
        logger.error(f"Falha ao iniciar Ngrok: {e}")
        print(f"\n❌ Erro ao iniciar ngrok: {e}")
        return None


if __name__ == "__main__":
    import uvicorn

    print_banner()

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    # Inicia ngrok automaticamente se configurado
    public_url = start_ngrok(port)

    if not public_url:
        # Sem ngrok - mostra instruções manuais
        print("\n🔗 Ngrok não configurado - para webhooks reais, configure:")
        print("   NGROK_ENABLED=true no .env")
        print("   Ou execute: ngrok http 8000")
        print("\n" + "=" * 80)

    logger.info(f"🚀 Iniciando servidor em {host}:{port}")

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    finally:
        # Fecha túnel ngrok ao encerrar
        if public_url:
            try:
                from pyngrok import ngrok
                ngrok.kill()
                logger.info("Túnel ngrok fechado")
            except:
                pass
