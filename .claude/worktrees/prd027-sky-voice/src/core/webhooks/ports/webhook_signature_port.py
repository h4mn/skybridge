# -*- coding: utf-8 -*-
"""
Webhook Signature Port.

Interface abstrata para verificação de assinatura HMAC de webhooks.
Cada fonte (GitHub, Discord, etc) tem seu próprio formato de assinatura.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class WebhookSignaturePort(ABC):
    """
    Port para verificação de assinatura de webhooks.

    Implementações:
    - GitHubSignatureVerifier: HMAC SHA-256 (X-Hub-Signature-256)
    - DiscordSignatureVerifier: Ed25519 (X-Signature-Ed25519)
    - StripeSignatureVerifier: HMAC SHA-256 (Stripe-Signature)

    A verificação de assinatura é crítica para segurança (RNF001),
    garantindo que o webhook vem realmente da fonte declarada.
    """

    @abstractmethod
    def verify(self, payload: bytes, signature: str, secret: str) -> bool:
        """
        Verifica se a assinatura corresponde ao payload.

        Args:
            payload: Corpo bruto da requisição HTTP (bytes)
            signature: Assinatura do header HTTP
            secret: Segredo compartilhado configurado na fonte

        Returns:
            True se assinatura válida, False caso contrário

        Note:
            Use hmac.compare_digest() para comparação constante no tempo
            e prevenir ataques de timing.
        """
        pass

    @abstractmethod
    def extract_signature(self, headers: dict[str, str]) -> str | None:
        """
        Extrai assinatura dos headers HTTP.

        Args:
            headers: Dicionário de headers HTTP

        Returns:
            Assinatura extraída ou None se não presente
        """
        pass

    @property
    @abstractmethod
    def header_name(self) -> str:
        """
        Nome do header HTTP que contém a assinatura.

        Returns:
            Nome do header (ex: "X-Hub-Signature-256")
        """
        pass
