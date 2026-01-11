# -*- coding: utf-8 -*-
"""
GitHub Webhook Signature Verifier.

Verifica assinaturas HMAC SHA-256 de webhooks do GitHub.

Formato:
- Header: X-Hub-Signature-256
- Valor: sha256=<hex_signature>
- Algoritmo: HMAC-SHA256

Referência:
https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
"""
from __future__ import annotations

import hmac
import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skybridge.core.contexts.webhooks.ports.webhook_signature_port import (
        WebhookSignaturePort,
    )

from skybridge.core.contexts.webhooks.ports.webhook_signature_port import (
    WebhookSignaturePort,
)


class GitHubSignatureVerifier(WebhookSignaturePort):
    """
    Verificador de assinatura de webhooks do GitHub.

    Usa HMAC SHA-256 para verificar que o webhook vem realmente
    do GitHub e não foi adulterado.

    Example:
        >>> verifier = GitHubSignatureVerifier()
        >>> signature = "sha256=abc123..."
        >>> payload = b'{"action": "opened"}'
        >>> secret = "my_webhook_secret"
        >>> verifier.verify(payload, signature, secret)
        True
    """

    HEADER_NAME = "X-Hub-Signature-256"
    PREFIX = "sha256="

    @property
    def header_name(self) -> str:
        """Retorna nome do header HTTP."""
        return self.HEADER_NAME

    def verify(self, payload: bytes, signature: str, secret: str) -> bool:
        """
        Verifica se a assinatura é válida.

        Args:
            payload: Corpo bruto da requisição (bytes)
            signature: Assinatura do header (formato: sha256=...)
            secret: Segredo do webhook configurado no GitHub

        Returns:
            True se assinatura válida, False caso contrário

        Raises:
            ValueError: Se formato de assinatura inválido
        """
        if not signature.startswith(self.PREFIX):
            return False

        # Extrai hash da assinatura (remove "sha256=")
        signature_hash = signature[len(self.PREFIX) :]

        # Calcula HMAC esperado
        mac = hmac.new(secret.encode(), payload, hashlib.sha256)
        expected_signature = mac.hexdigest()

        # Compara em tempo constante para prevenir timing attacks
        return hmac.compare_digest(expected_signature, signature_hash)

    def extract_signature(self, headers: dict[str, str]) -> str | None:
        """
        Extrai assinatura dos headers HTTP.

        Args:
            headers: Dicionário de headers HTTP

        Returns:
            Assinatura extraída ou None se não presente
        """
        return headers.get(self.HEADER_NAME)

    def is_valid_format(self, signature: str) -> bool:
        """
        Verifica se formato de assinatura é válido.

        Args:
            signature: Assinatura para validar

        Returns:
            True se formato válido (começa com "sha256=")
        """
        return signature.startswith(self.PREFIX)
