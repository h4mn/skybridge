# -*- coding: utf-8 -*-
"""
Trello Webhook Signature Verifier.

Verifica assinaturas HMAC SHA-1 de webhooks do Trello.

Documentação:
- https://developer.atlassian.com/cloud/trello/guides/rest-api/webhooks/
- Header: X-Trello-Webhook
- Valor: base64_digest
- Algoritmo: HMAC-SHA1

Fórmula Trello:
    signature = base64(HMAC-SHA1(payload + callbackURL, secret))

Diferença GitHub vs Trello:
- GitHub: HMAC-SHA256, formato "sha256=<hex>", assina apenas payload
- Trello: HMAC-SHA1, formato base64 puro, assina payload + callbackURL
"""

import hmac
import hashlib
from base64 import b64encode
from typing import Final

from core.webhooks.ports.webhook_signature_port import (
    WebhookSignaturePort,
)


class TrelloSignatureVerifier(WebhookSignaturePort):
    """
    Verificador de assinatura de webhooks do Trello.

    Usa HMAC-SHA1 para verificar que o webhook vem realmente
    do Trello.

    Fórmula Trello:
        signature = base64(HMAC-SHA1(payload + callbackURL, secret))

    Example:
        >>> verifier = TrelloSignatureVerifier(callback_url="https://example.com/webhook/trello")
        >>> signature = "YWJjMTIz..."  # header X-Trello-Webhook
        >>> verifier.verify(payload, signature, secret)
        True
    """

    HEADER_NAME: Final[str] = "X-Trello-Webhook"

    @property
    def header_name(self) -> str:
        """Retorna o nome do header HTTP da assinatura."""
        return self.HEADER_NAME

    def __init__(self, callback_url: str):
        """
        Inicializa verificador.

        Args:
            callback_url: URL usada na criação do webhook (necessária para verificação!)
        """
        self.callback_url = callback_url

    def verify(self, payload: bytes, signature: str, secret: str) -> bool:
        """
        Verifica assinatura do webhook do Trello.

        Args:
            payload: Corpo da requisição (bytes)
            signature: Assinatura do header (formato base64)
            secret: API Secret do Power-Up (não é o API Token!)

        Returns:
            True se assinatura válida

        Fórmula Trello:
            content = payload + callbackURL
            hash = HMAC-SHA1(content, secret)
            signature = base64(hash)

        Note:
            O callback_url deve ser EXATAMENTE a mesma URL usada na criação do webhook.
        """
        if not signature:
            return False

        # Concatena payload + callback URL (fórmula Trello)
        content = payload + self.callback_url.encode()

        # Calcula HMAC-SHA1 esperado
        mac = hmac.new(secret.encode(), content, hashlib.sha1)
        expected_signature = b64encode(mac.digest()).decode()

        # Compara em tempo constante
        return hmac.compare_digest(expected_signature, signature)

    def extract_signature(self, headers: dict[str, str]) -> str | None:
        """
        Extrai assinatura dos headers HTTP.

        Args:
            headers: Headers da requisição

        Returns:
            Assinatura ou None se não presente
        """
        return headers.get(self.HEADER_NAME) or headers.get("Trello-Webhook")

    def is_valid_format(self, signature: str) -> bool:
        """
        Valida formato da assinatura.

        Args:
            signature: Assinatura para validar

        Returns:
            True se formato válido (base64)
        """
        if not signature:
            return False

        # Trello usa base64 puro (sem prefixo)
        try:
            # Tenta decodificar como base64
            from base64 import b64decode

            b64decode(signature)
            return True
        except Exception:
            return False


# Factory function
def create_trello_signature_verifier(callback_url: str) -> TrelloSignatureVerifier:
    """
    Factory para criar verificador de assinatura Trello.

    Args:
        callback_url: URL usada na criação do webhook

    Returns:
        Instância de TrelloSignatureVerifier
    """
    return TrelloSignatureVerifier(callback_url)
