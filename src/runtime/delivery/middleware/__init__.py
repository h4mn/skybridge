# -*- coding: utf-8 -*-
"""
Webhook Authentication Middleware.

Middleware para verificação de assinatura HMAC de webhooks.

NOTE: A verificação de assinatura é feita DENTRO da rota, não aqui no middleware,
para evitar consumir o request.body (que só pode ser lido uma vez).
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse


async def verify_webhook_signature(
    payload: bytes, signature: str, source: str
) -> Response | None:
    """
    Verifica assinatura HMAC do webhook.

    Args:
        payload: Body da requisição (bytes)
        signature: Assinatura do header
        source: Fonte do webhook (github, discord, etc)

    Returns:
        None se assinatura válida, JSONResponse com erro se inválida
    """
    from runtime.config.config import get_webhook_config
    from infra.webhooks.adapters.github_signature_verifier import (
        GitHubSignatureVerifier,
    )
    from runtime.observability.logger import get_logger

    logger = get_logger()

    config = get_webhook_config()

    # Verificadores disponíveis
    verifiers = {
        "github": GitHubSignatureVerifier(),
        # "discord": DiscordSignatureVerifier(),  # Phase 2
        # "youtube": YouTubeSignatureVerifier(),  # Phase 2
    }

    verifier = verifiers.get(source)
    if not verifier:
        # Fonte sem verificador - permite por enquanto
        logger.warning(f"Sem verificador para source: {source}")
        return None

    # Busca segredo
    secret = getattr(config, f"{source}_secret", None)
    if not secret:
        logger.error(f"Segredo não configurado para source: {source}")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Secret not configured"},
        )

    # Verifica assinatura
    if not verifier.verify(payload, signature, secret):
        logger.warning(
            f"Assinatura inválida para source: {source}",
            extra={"signature_prefix": signature[:10] + "..."},
        )
        return JSONResponse(
            status_code=401,
            content={"ok": False, "error": "Invalid signature"},
        )

    return None
