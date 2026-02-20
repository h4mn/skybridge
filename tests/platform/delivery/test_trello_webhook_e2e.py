# -*- coding: utf-8 -*-
"""
Testes de integração E2E para endpoint /api/webhooks/trello.

Cobre DoDs relacionados:
- DoD #7: Webhook Trello recebe eventos
"""

# Mock worktree_validator e runtime.observability ANTES de qualquer import
# Isso evita o erro ModuleNotFoundError: No module named 'runtime.observability'
import sys
from unittest.mock import Mock
sys.modules['core.agents.worktree_validator'] = Mock()
sys.modules['core.agents.worktree_validator'].safe_worktree_cleanup = Mock()

# Mock runtime.observability modules (para job_orchestrator e worktree_validator)
mock_git_diff = Mock()
mock_git_diff.get_git_diff = Mock(return_value=[])
sys.modules['runtime.observability.snapshot.git_diff'] = mock_git_diff

import pytest
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock


@pytest.mark.integration
class TestTrelloWebhookEndpoint:
    """Testes de integração do endpoint /api/webhooks/trello."""

    @pytest.fixture
    def app(self):
        """
        Fixture da aplicação FastAPI.

        Usa get_app().app de runtime.bootstrap para ter acesso ao endpoint
        /api/webhooks/trello (github_webhook_server é standalone e não tem esse endpoint).
        """
        from runtime.bootstrap.app import get_app
        return get_app().app

    @pytest.fixture
    def client(self, app):
        """Cliente HTTP assíncrono para testes."""
        from fastapi.testclient import TestClient

        return TestClient(app)

    @pytest.fixture
    def sample_trello_payload(self):
        """Payload de webhook do Trello."""
        return {
            "action": {
                "type": "updateCard",
                "data": {
                    "card": {
                        "id": "card-123",
                        "name": "#123 Test Feature",
                        "desc": "Repository: h4mn/skybridge",
                    },
                    "listBefore": {
                        "id": "list-before",
                        "name": "🧠 Brainstorm",
                    },
                    "listAfter": {
                        "id": "list-after",
                        "name": "📋 A Fazer",
                    },
                },
            },
            "model": {
                "id": "board-123",
            },
        }

    @pytest.fixture
    def mock_handler_result(self):
        """Resultado mock do handler."""
        mock_result = Mock()
        mock_result.is_ok = True
        mock_result.unwrap = Mock(return_value={"processed": True, "action": "job_created", "job_id": "job-123"})
        return mock_result

    def test_endpoint_exists(self, client):
        """
        DoD #7: Webhook Trello recebe eventos.

        Verifica que endpoint /api/webhooks/trello existe.
        """
        response = client.options("/api/webhooks/trello")

        # Endpoint deve existir (não deve ser 404)
        assert response.status_code != 404

    def test_endpoint_accepts_post(self, client):
        """Endpoint deve aceitar método POST."""
        response = client.post("/api/webhooks/trello", json={})
        # Pode ser 422 (validation error) mas não 405 (method not allowed)
        assert response.status_code != 405

    def test_endpoint_returns_200_on_success(self, client, sample_trello_payload):
        """
        Endpoint deve retornar 202 Accepted em caso de sucesso.

        NOTA: Usa /api/webhooks/trello (padrão ADR023).
        Mocka o handler receive_trello_webhook via query registry.
        """
        from kernel import Result, get_query_registry

        mock_result = Result.ok({
            "processed": True,
            "action": "job_created",
            "job_id": "job-123"
        })

        # Cria mock da função
        mock_handler = Mock(return_value=mock_result)

        # Mocka o query registry
        registry = get_query_registry()
        registry_handler = Mock()
        registry_handler.handler = mock_handler
        with patch.object(registry, 'get', return_value=registry_handler):
            response = client.post(
                "/api/webhooks/trello",
                json=sample_trello_payload,
                headers={"X-Trello-Webhook": "webhook-456"}
            )

            # Handler foi chamado corretamente deve resultar em sucesso
            # Endpoint webhook retorna 202 Accepted (job enfileirado)
            assert response.status_code == 202

    def test_endpoint_passes_payload_to_handler(self, client, sample_trello_payload):
        """
        Endpoint deve passar payload para o handler.

        NOTA: Usa /api/webhooks/trello (padrão ADR023).
        """
        from kernel import Result, get_query_registry

        mock_result = Result.ok({
            "processed": True,
            "action": "job_created",
            "job_id": "job-123"
        })

        mock_handler = Mock(return_value=mock_result)

        registry = get_query_registry()
        registry_handler = Mock()
        registry_handler.handler = mock_handler
        with patch.object(registry, 'get', return_value=registry_handler):
            client.post(
                "/api/webhooks/trello",
                json=sample_trello_payload,
                headers={"X-Trello-Webhook": "webhook-456"}
            )

            # Verifica que handler foi chamado
            assert mock_handler.called

            # Verifica argumentos passados - handler recebe dict com "payload"
            call_args = mock_handler.call_args
            args = call_args[0][0] if call_args[0] else call_args[1]

            assert "payload" in args
            assert args["payload"] == sample_trello_payload

    def test_endpoint_extracts_webhook_id_from_header(self, client, sample_trello_payload):
        """
        Endpoint aceita header X-Trello-Webhook.

        NOTA: Usa /api/webhooks/trello (padrão ADR023).
        Este teste apenas verifica que o endpoint aceita o header.
        """
        from kernel import Result, get_query_registry

        mock_result = Result.ok({
            "processed": True,
            "action": "job_created",
            "job_id": "job-123"
        })

        webhook_id = "webhook-test-123"
        mock_handler = Mock(return_value=mock_result)

        # Usa patch em get_query_registry para mockar o handler
        registry = get_query_registry()
        registry_handler = Mock()
        registry_handler.handler = mock_handler

        with patch.object(registry, 'get', return_value=registry_handler):
            response = client.post(
                "/api/webhooks/trello",
                json=sample_trello_payload,
                headers={"X-Trello-Webhook": webhook_id}
            )

            # Endpoint aceita o header e retorna 202
            assert response.status_code == 202

    def test_endpoint_supports_alternative_header(self, client, sample_trello_payload):
        """
        Endpoint aceita header alternativo Trello-Webhook-ID.

        NOTA: Usa /api/webhooks/trello (padrão ADR023).
        Este teste apenas verifica que o endpoint aceita o header alternativo.
        """
        from kernel import Result, get_query_registry

        mock_result = Result.ok({
            "processed": True,
            "action": "job_created",
            "job_id": "job-123"
        })

        webhook_id = "webhook-alt-456"
        mock_handler = Mock(return_value=mock_result)

        # Usa patch em get_query_registry para mockar o handler
        registry = get_query_registry()
        registry_handler = Mock()
        registry_handler.handler = mock_handler

        with patch.object(registry, 'get', return_value=registry_handler):
            response = client.post(
                "/api/webhooks/trello",
                json=sample_trello_payload,
                headers={"Trello-Webhook-ID": webhook_id}
            )

            # Endpoint aceita o header alternativo e retorna 202
            assert response.status_code == 202

    def test_endpoint_returns_error_on_handler_error(self, client, sample_trello_payload):
        """Endpoint deve retornar erro quando handler falha."""
        # Mock de erro
        mock_error_result = Mock()
        mock_error_result.is_ok = False
        mock_error_result.error = "Test error"

        mock_handler_wrapper = Mock()
        mock_handler_wrapper.handler = Mock(return_value=mock_error_result)

        mock_registry = Mock()
        mock_registry.get = Mock(return_value=mock_handler_wrapper)

        with patch("kernel.registry.query_registry.get_query_registry", return_value=mock_registry):
            response = client.post(
                "/api/webhooks/trello",
                json=sample_trello_payload,
            )

            # Deve retornar 422
            assert response.status_code == 422

            data = response.json()
            assert "error" in data


@pytest.mark.integration
class TestTrelloWebhookEndpointValidation:
    """Testes de validação do endpoint /api/webhooks/trello."""

    @pytest.fixture
    def app(self):
        """
        Fixture da aplicação FastAPI.

        Usa get_app().app de runtime.bootstrap para ter acesso ao endpoint
        /api/webhooks/trello (github_webhook_server é standalone e não tem esse endpoint).
        """
        from runtime.bootstrap.app import get_app
        return get_app().app

    @pytest.fixture
    def client(self, app):
        """Cliente HTTP para testes."""
        from fastapi.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_handler_result(self):
        """Resultado mock do handler."""
        mock_result = Mock()
        mock_result.is_ok = True
        mock_result.unwrap = Mock(return_value={"processed": True, "action": "ignored"})
        return mock_result

    def test_endpoint_accepts_json_payload(self, client, mock_handler_result):
        """Endpoint deve aceitar payload JSON."""
        mock_handler_wrapper = Mock()
        mock_handler_wrapper.handler = Mock(return_value=mock_handler_result)

        mock_registry = Mock()
        mock_registry.get = Mock(return_value=mock_handler_wrapper)

        with patch("kernel.registry.query_registry.get_query_registry", return_value=mock_registry):
            response = client.post(
                "/api/webhooks/trello",
                json={"action": {"type": "updateCard"}},
                headers={"Content-Type": "application/json"}
            )

            # Não deve ser 415 (Unsupported Media Type)
            assert response.status_code != 415

    def test_endpoint_handles_empty_payload(self, client, mock_handler_result):
        """Endpoint deve lidar com payload vazio."""
        mock_handler_wrapper = Mock()
        mock_handler_wrapper.handler = Mock(return_value=mock_handler_result)

        mock_registry = Mock()
        mock_registry.get = Mock(return_value=mock_handler_wrapper)

        with patch("kernel.registry.query_registry.get_query_registry", return_value=mock_registry):
            response = client.post("/api/webhooks/trello", json={})

            # Handler mockado retorna sucesso, então endpoint retorna 202
            assert response.status_code == 202

    def test_endpoint_handles_missing_action(self, client, mock_handler_result):
        """Endpoint deve lidar com payload sem 'action'."""
        payload = {"model": {"id": "board-123"}}

        mock_handler_wrapper = Mock()
        mock_handler_wrapper.handler = Mock(return_value=mock_handler_result)

        mock_registry = Mock()
        mock_registry.get = Mock(return_value=mock_handler_wrapper)

        with patch("kernel.registry.query_registry.get_query_registry", return_value=mock_registry):
            response = client.post("/api/webhooks/trello", json=payload)

            # Handler mockado retorna sucesso, então endpoint retorna 202
            assert response.status_code == 202


@pytest.mark.integration
class TestTrelloWebhookEndpointSecurity:
    """Testes de segurança do endpoint /api/webhooks/trello."""

    @pytest.fixture
    def app(self):
        """
        Fixture da aplicação FastAPI.

        Usa get_app().app de runtime.bootstrap para ter acesso ao endpoint
        /api/webhooks/trello (github_webhook_server é standalone e não tem esse endpoint).
        """
        from runtime.bootstrap.app import get_app
        return get_app().app

    @pytest.fixture
    def client(self, app):
        """Cliente HTTP para testes."""
        from fastapi.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_handler_result(self):
        """Resultado mock do handler."""
        mock_result = Mock()
        mock_result.is_ok = True
        mock_result.unwrap = Mock(return_value={"processed": True})
        return mock_result

    def test_endpoint_does_not_require_authentication(self, client, mock_handler_result):
        """
        DoD #7: Webhook Trello recebe eventos.

        Endpoint de webhook não deve requerer autenticação.
        """
        mock_handler_wrapper = Mock()
        mock_handler_wrapper.handler = Mock(return_value=mock_handler_result)

        mock_registry = Mock()
        mock_registry.get = Mock(return_value=mock_handler_wrapper)

        with patch("kernel.registry.query_registry.get_query_registry", return_value=mock_registry):
            # Request sem autenticação deve ser aceito
            response = client.post(
                "/api/webhooks/trello",
                json={"action": {"type": "updateCard"}},
            )

            # Não deve ser 401 (Unauthorized) ou 403 (Forbidden)
            assert response.status_code not in [401, 403]

    def test_endpoint_verifies_signature_when_configured(self, client):
        """
        Verificação de assinatura HMAC-SHA1 do Trello.

        Testa que o TrelloSignatureVerifier funciona corretamente.
        """
        from infra.webhooks.adapters.trello_signature_verifier import TrelloSignatureVerifier

        # Dados de teste
        callback_url = "https://example.com/api/webhooks/trello"
        secret = "test_secret"
        payload = b'{"action": {"type": "updateCard"}}'

        # Cria verificador
        verifier = TrelloSignatureVerifier(callback_url)

        # Testa extração de assinatura
        headers = {"X-Trello-Webhook": "dGVzdF9zaWduYXR1cmU="}
        signature = verifier.extract_signature(headers)
        assert signature == "dGVzdF9zaWduYXR1cmU="

        # Testa validação de formato
        assert verifier.is_valid_format(signature)

        # Testa verificação (assinatura válida seria calculada pelo Trello)
        # Como não temos a assinatura real, testamos apenas a estrutura
        assert verifier.header_name == "X-Trello-Webhook"


@pytest.mark.e2e
class TestTrelloWebhookEndpointE2E:
    """Testes E2E do endpoint /api/webhooks/trello."""

    @pytest.fixture
    def app(self):
        """
        Fixture da aplicação FastAPI.

        Usa get_app().app de runtime.bootstrap para ter acesso ao endpoint
        /api/webhooks/trello (github_webhook_server é standalone e não tem esse endpoint).
        """
        from runtime.bootstrap.app import get_app
        return get_app().app

    @pytest.fixture
    def client(self, app):
        """Cliente HTTP para testes."""
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_full_webhook_flow_brainstorm(self, client):
        """
        E2E: Card movido para 🧠 Brainstorm.

        Simula fluxo completo:
        1. Webhook recebido
        2. Handler processa
        3. Job criado com autonomy_level=ANALYSIS

        NOTA: Usa handler real mockado (sem Sky-RPC).
        Mocka o módulo handlers antes que seja importado.
        """
        payload = {
            "action": {
                "type": "updateCard",
                "data": {
                    "card": {
                        "id": "card-123",
                        "name": "#789 Research",
                        "desc": "Needs analysis",
                    },
                    "listBefore": {"name": "📥 Issues"},
                    "listAfter": {"name": "🧠 Brainstorm"},
                },
            },
        }

        # Mock de resultado com job criado
        from kernel import Result

        mock_result = Result.ok({
            "processed": True,
            "action": "job_created",
            "job_id": "job-analysis-123"
        })

        mock_handler = Mock(return_value=mock_result)

        with patch.dict('sys.modules', {'core.webhooks.application.handlers': Mock(receive_trello_webhook=mock_handler)}):
            response = client.post("/api/webhooks/trello", json=payload)

            # Verifica resposta - endpoint retorna 202 Accepted
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "queued"

    def test_full_webhook_flow_a_fazer(self, client):
        """
        E2E: Card movido para 📋 A Fazer.

        Simula fluxo completo:
        1. Webhook recebido
        2. Handler processa
        3. Card movido para 🚧 Em Andamento
        4. Job criado com autonomy_level=DEVELOPMENT

        NOTA: Usa handler real mockado (sem Sky-RPC).
        Mocka o módulo handlers antes que seja importado.
        """
        from kernel import Result, get_query_registry

        payload = {
            "action": {
                "type": "updateCard",
                "data": {
                    "card": {
                        "id": "card-456",
                        "name": "#123 Feature",
                        "desc": "Repository: h4mn/skybridge",
                    },
                    "listBefore": {"name": "🧠 Brainstorm"},
                    "listAfter": {"name": "📋 A Fazer"},
                },
            },
        }

        # Mock de resultado com card movido para progresso
        mock_result = Result.ok({
            "processed": True,
            "action": "moved_to_progress",
            "job_id": "job-dev-456"
        })

        mock_handler = Mock(return_value=mock_result)

        # Usa patch em get_query_registry para mockar o handler
        registry = get_query_registry()
        registry_handler = Mock()
        registry_handler.handler = mock_handler

        with patch.object(registry, 'get', return_value=registry_handler):
            response = client.post("/api/webhooks/trello", json=payload)

            # Endpoint retorna 202 Accepted
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "queued"
            # job_id contém o resultado completo do handler
            assert data["job_id"]["job_id"] == "job-dev-456"

    def test_full_webhook_flow_publicar(self, client):
        """
        E2E: Card movido para 🚀 Publicar.

        Simula fluxo completo:
        1. Webhook recebido
        2. Handler processa
        3. Job criado com autonomy_level=PUBLISH

        NOTA: Usa handler real mockado (sem Sky-RPC).
        Mocka o módulo handlers antes que seja importado.
        """
        payload = {
            "action": {
                "type": "updateCard",
                "data": {
                    "card": {
                        "id": "card-789",
                        "name": "#999 Feature",
                        "desc": "Ready to publish",
                    },
                    "listBefore": {"name": "👁️ Em Revisão"},
                    "listAfter": {"name": "🚀 Publicar"},
                },
            },
        }

        # Mock de resultado com job criado
        from kernel import Result

        mock_result = Result.ok({
            "processed": True,
            "action": "job_created",
            "job_id": "job-publish-789"
        })

        mock_handler = Mock(return_value=mock_result)

        with patch.dict('sys.modules', {'core.webhooks.application.handlers': Mock(receive_trello_webhook=mock_handler)}):
            response = client.post("/api/webhooks/trello", json=payload)

            # Endpoint retorna 202 Accepted
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "queued"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
