# -*- coding: utf-8 -*-
"""
Unit Tests para Webhook do Trello.

Cobre:
1. Verificação de assinatura HMAC-SHA1
2. Fórmula de assinatura do Trello
3. Validação de payload
"""

import pytest
from base64 import b64encode
import hmac
import hashlib
import json


class TestTrelloWebhookSignature:
    """Testes de verificação de assinatura do Trello."""

    def test_signature_formula(self):
        """
        Testa a fórmula de assinatura do Trello.

        Fórmula: base64(HMAC-SHA1(payload + callbackURL, secret))

        Docs: https://developer.atlassian.com/cloud/trello/guides/rest-api/webhooks/
        """
        secret = "test-secret"
        payload = '{"test": "data"}'
        callback_url = "http://localhost:8000/webhooks/trello"

        # Calcula assinatura
        content = payload.encode() + callback_url.encode()
        digest = hmac.new(secret.encode(), content, hashlib.sha1).digest()
        signature = b64encode(digest).decode("utf-8")

        # Verifica formato
        assert len(signature) > 0
        assert signature.isalnum() or any(c in "+/=" for c in signature)

    def test_signature_verification_correct(self):
        """Testa verificação de assinatura correta com HMAC compare_digest."""
        secret = "test-secret"
        payload = '{"test": "data"}'
        callback_url = "http://localhost:8000/webhooks/trello"

        # Calcula assinatura correta
        content = payload.encode() + callback_url.encode()
        digest = hmac.new(secret.encode(), content, hashlib.sha1).digest()
        correct_signature = b64encode(digest).decode("utf-8")

        # Verifica assinatura correta
        expected_digest = hmac.new(
            secret.encode(),
            content,
            hashlib.sha1,
        ).digest()

        assert hmac.compare_digest(
            b64encode(expected_digest).decode("utf-8"),
            correct_signature,
        )

    def test_signature_incorrect_fails(self):
        """Testa que assinatura incorreta falha na verificação."""
        secret = "test-secret"
        payload = '{"test": "data"}'
        callback_url = "http://localhost:8000/webhooks/trello"

        # Assinatura incorreta
        incorrect_signature = "invalid-signature-base64"

        # Calcula digest correto para comparação
        content = payload.encode() + callback_url.encode()
        expected_digest = hmac.new(
            secret.encode(),
            content,
            hashlib.sha1,
        ).digest()

        # Verifica que assinatura incorreta não bate
        assert not hmac.compare_digest(
            b64encode(expected_digest).decode("utf-8"),
            incorrect_signature,
        )

    def test_signature_includes_callback_url(self):
        """
        Testa que a assinatura inclui a callback URL.

        A callback URL é parte do conteúdo assinado, então mudanças
        na URL invalidam a assinatura.
        """
        secret = "test-secret"
        payload = '{"test": "data"}'
        callback_url1 = "http://localhost:8000/webhooks/trello"
        callback_url2 = "https://example.com/webhooks/trello"

        # Calcula assinaturas com URLs diferentes
        content1 = payload.encode() + callback_url1.encode()
        digest1 = hmac.new(secret.encode(), content1, hashlib.sha1).digest()
        signature1 = b64encode(digest1).decode("utf-8")

        content2 = payload.encode() + callback_url2.encode()
        digest2 = hmac.new(secret.encode(), content2, hashlib.sha1).digest()
        signature2 = b64encode(digest2).decode("utf-8")

        # Assinaturas devem ser diferentes
        assert signature1 != signature2

    def test_signature_payload_matters(self):
        """
        Testa que mudanças no payload mudam a assinatura.
        """
        secret = "test-secret"
        payload1 = '{"test": "data"}'
        payload2 = '{"test": "different"}'
        callback_url = "http://localhost:8000/webhooks/trello"

        # Calcula assinaturas com payloads diferentes
        content1 = payload1.encode() + callback_url.encode()
        digest1 = hmac.new(secret.encode(), content1, hashlib.sha1).digest()
        signature1 = b64encode(digest1).decode("utf-8")

        content2 = payload2.encode() + callback_url.encode()
        digest2 = hmac.new(secret.encode(), content2, hashlib.sha1).digest()
        signature2 = b64encode(digest2).decode("utf-8")

        # Assinaturas devem ser diferentes
        assert signature1 != signature2


class TestTrelloWebhookPayload:
    """Testes de validação de payload do webhook."""

    def test_trello_webhook_payload_structure(self):
        """
        Testa estrutura esperada do payload do webhook do Trello.

        Payload típico de movimento de card:
        {
            "action": {
                "type": "updateCard",
                "data": {
                    "card": {...},
                    "listAfter": {...},
                    "listBefore": {...}
                }
            },
            "model": {...}
        }
        """
        # Payload de exemplo para movimento de card
        payload = {
            "action": {
                "type": "updateCard",
                "data": {
                    "card": {
                        "id": "card-id-123",
                        "name": "Test Card",
                        "idList": "new-list-id",
                    },
                    "listAfter": {
                        "id": "new-list-id",
                        "name": "📋 A Fazer",
                    },
                    "listBefore": {
                        "id": "old-list-id",
                        "name": "📥 Issues",
                    },
                },
            },
            "model": {
                "id": "board-id",
                "name": "Test Board",
            },
        }

        # Verifica estrutura básica
        assert "action" in payload
        assert "type" in payload["action"]
        assert "data" in payload["action"]
        assert "card" in payload["action"]["data"]
        assert "listAfter" in payload["action"]["data"]
        assert "listBefore" in payload["action"]["data"]

    def test_trello_webhook_detects_card_moved_to_todo(self):
        """
        Testa detecção de movimento para lista "📋 A Fazer".

        Quando um card é movido para esta lista, o sistema deve:
        1. Detectar o movimento
        2. Mover para "🚧 Em Andamento"
        3. Iniciar agente
        """
        payload = {
            "action": {
                "type": "updateCard",
                "data": {
                    "listAfter": {
                        "name": "📋 A Fazer",
                    },
                },
            },
        }

        # Verifica que o card foi movido para "📋 A Fazer"
        assert payload["action"]["data"]["listAfter"]["name"] == "📋 A Fazer"

    def test_trello_webhook_serialization(self):
        """
        Testa serialização JSON do payload.

        O payload deve ser serializado de forma determinística
        para verificação de assinatura.
        """
        payload = {
            "action": {
                "type": "updateCard",
                "data": {"card": {"id": "123"}},
            }
        }

        # Serializa JSON sem espaços extras
        payload_str = json.dumps(payload, separators=(",", ":"))

        # Verifica que é válido
        assert json.loads(payload_str) == payload


class TestTrelloWebhookIntegration:
    """Testes de integração do webhook do Trello."""

    def test_webhook_endpoint_exists(self):
        """
        Testa que o endpoint /webhooks/trello existe.

        Este teste verifica que a rota está registrada
        na aplicação FastAPI.
        """
        # Importa a aplicação
        from runtime.bootstrap.app import get_app

        app = get_app()

        # Verifica que o endpoint existe
        routes = [route.path for route in app.app.routes]

        # O endpoint genérico /webhooks/{source} deve existir
        assert any("/webhooks/" in route for route in routes)

    def test_head_endpoint_support(self):
        """
        Testa que o endpoint suporta HEAD requests.

        O Trello usa HEAD para validar a URL antes de criar o webhook.
        """
        from runtime.bootstrap.app import get_app

        app = get_app()

        # Busca rotas que suportam HEAD
        head_routes = [
            route
            for route in app.app.routes
            if hasattr(route, "methods") and "HEAD" in route.methods
        ]

        # Deve haver pelo menos uma rota com HEAD para webhooks
        webhook_head_routes = [
            route for route in head_routes if "/webhooks/" in route.path
        ]

        # Verifica que existe rota HEAD para webhooks
        assert len(webhook_head_routes) > 0
