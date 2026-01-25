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
from infra.webhooks.adapters.file_based_job_queue import FileBasedJobQueue

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


# FileBasedJobQueue substitui InMemoryJobQueue (drop-in replacement)
# Resolve o Problema #1: filas separadas entre processos
# Inclui deduplicação por fingerprint (Camada 2) além de delivery_id (Camada 1)


# Inicializa app
app = FastAPI(title="Skybridge Webhook Server")

# Inicializa dependências
# FileBasedJobQueue: persiste em workspace/skybridge/fila/
# Resolve Problema #1: server e worker compartilham a mesma fila
queue_dir = os.getenv("SKYBRIDGE_QUEUE_DIR", "workspace/skybridge/fila")
job_queue = FileBasedJobQueue(queue_dir=queue_dir)
logger.info(f"✅ FileBasedJobQueue inicializado em: {queue_dir}")

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
        "queue_size": job_queue.size(),
        "queue_type": "FileBasedJobQueue",
    }


@app.get("/metrics")
async def metrics():
    """
    Retorna métricas da fila para observabilidade.

    Endpoint para monitoring e tomada de decisão sobre quando migrar para Redis.
    """
    return job_queue.get_metrics()


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


@app.post("/webhook/trello")
async def trello_webhook(request: Request):
    """
    Recebe webhook do Trello.

    PRD020: Endpoint para webhooks do Trello no fluxo bidirecional Trello → GitHub.

    Headers esperados:
        X-Trello-Webhook: ID do webhook (para verificação)
        Trello-Webhook-ID: ID do webhook alternativo

    Body: JSON payload do evento Trello
    """
    import asyncio

    try:
        # Lê payload
        payload = await request.json()

        # Extrai headers
        trello_webhook_id = request.headers.get("X-Trello-Webhook") or request.headers.get("Trello-Webhook-ID", "")

        correlation_id = trello_webhook_id or "unknown"
        logger.info(
            f"📩 Webhook Trello recebido | correlation_id={correlation_id}"
        )

        # Verifica assinatura se secret configurado (Trello usa HMAC-SHA1)
        webhook_secret = os.getenv("TRELLO_WEBHOOK_SECRET")
        if webhook_secret:
            # Trello envia a assinatura no header X-Trello-Signature ou similar
            # Nota: Trello não sempre envia assinatura, então só verificamos se presente
            signature = request.headers.get("X-Trello-Signature") or request.headers.get("Trello-Signature")
            if signature:
                # TODO: Implementar verificação HMAC-SHA1 do Trello
                # Por enquanto, apenas log warning
                logger.warning("⚠️  Verificação de assinatura Trello não implementada")

        # Processa webhook via Sky-RPC handler
        from kernel.registry import get_handler
        from kernel.security.auth import AuthContext

        # Cria contexto de autenticação (webhooks não requerem auth)
        auth_context = AuthContext.create_anonymous()

        # Chama handler via Sky-RPC
        handler = get_handler("webhooks.trello.receive")
        if not handler:
            logger.error("❌ Handler webhooks.trello.receive não encontrado")
            return JSONResponse(
                status_code=500,
                content={"error": "Handler not found", "correlation_id": correlation_id}
            )

        # Executa handler
        import concurrent.futures
        loop = asyncio.get_event_loop()

        def run_handler():
            return handler.invoke({"payload": payload, "trello_webhook_id": trello_webhook_id}, auth_context)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(executor, run_handler)

        if result.is_ok:
            response_data = result.unwrap()
            logger.info(
                f"✅ Webhook Trello processado | correlation_id={correlation_id} | action={response_data.get('action', 'unknown')}"
            )

            return JSONResponse(
                status_code=200,
                content={
                    "status": "accepted",
                    "correlation_id": correlation_id,
                    "action": response_data.get("action", "unknown"),
                    "job_id": response_data.get("job_id"),
                    "message": "Webhook processado com sucesso"
                }
            )
        else:
            error_msg = result.error
            logger.error(
                f"❌ Erro ao processar webhook Trello | correlation_id={correlation_id} | error={error_msg}"
            )

            return JSONResponse(
                status_code=422,
                content={"error": error_msg, "correlation_id": correlation_id}
            )

    except Exception as e:
        logger.exception(
            f"💥 Erro ao processar webhook Trello | correlation_id={correlation_id} | error={e}"
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
