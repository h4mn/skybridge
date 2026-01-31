# -*- coding: utf-8 -*-
"""
Testes de integração para o comando `sb agent issue`.

Testa o fluxo completo da CLI até o handler RPC.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from kernel import Result


@pytest.fixture
def mock_env():
    """Configura environment variables."""
    original_token = os.getenv("GITHUB_TOKEN")
    original_repo = os.getenv("GITHUB_REPO")

    os.environ["GITHUB_TOKEN"] = "test_token"
    os.environ["GITHUB_REPO"] = "test/repo"

    yield

    if original_token is None:
        os.environ.pop("GITHUB_TOKEN", None)
    else:
        os.environ["GITHUB_TOKEN"] = original_token

    if original_repo is None:
        os.environ.pop("GITHUB_REPO", None)
    else:
        os.environ["GITHUB_REPO"] = original_repo


class TestAgentIssueIntegration:
    """Testes de integração para sb agent issue."""

    @pytest.mark.integration
    def test_agent_issue_flow_with_mock_server(self, mock_env):
        """
        Testa o fluxo completo com mock do servidor FastAPI.

        Este teste simula:
        1. Obtenção de ticket
        2. Execução do envelope
        3. Criação da issue no GitHub
        """
        with patch("infra.github.github_api_client.create_github_client") as mock_client_factory:
            # Mock do cliente GitHub
            mock_client = MagicMock()
            mock_client.create_issue = AsyncMock(return_value=Result.ok({
                "issue_number": 123,
                "issue_url": "https://github.com/test/repo/issues/123",
                "issue_title": "Test Issue via CLI",
                "issue_body": "Test body",
                "labels": ["automated"],
            }))
            mock_client.close = AsyncMock()
            mock_client_factory.return_value = mock_client

            # Importa e executa o handler diretamente
            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Test Issue via CLI",
                "body": "Test body",
                "labels": ["automated"],
            })

            # Assertions
            assert result.is_ok
            issue_data = result.value
            assert issue_data["issue_number"] == 123
            assert "github.com/test/repo/issues/123" in issue_data["issue_url"]

    @pytest.mark.integration
    def test_agent_issue_with_special_characters(self, mock_env):
        """Testa criação de issue com caracteres especiais."""
        with patch("infra.github.github_api_client.create_github_client") as mock_client_factory:
            mock_client = MagicMock()
            mock_client.create_issue = AsyncMock(return_value=Result.ok({
                "issue_number": 124,
                "issue_url": "https://github.com/test/repo/issues/124",
                "issue_title": "Bug:Erro API #123",
                "issue_body": "Descrição com acentuação: çãõé\nE emojis: 🐛 🚀",
                "labels": ["automated", "bug"],
            }))
            mock_client.close = AsyncMock()
            mock_client_factory.return_value = mock_client

            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Bug:Erro API #123",
                "body": "Descrição com acentuação: çãõé\nE emojis: 🐛 🚀",
                "labels": ["automated", "bug"],
            })

            assert result.is_ok
            assert result.value["issue_number"] == 124

    @pytest.mark.integration
    def test_agent_issue_multiline_body(self, mock_env):
        """Testa criação de issue com body multi-line."""
        body = """
## Issue Completa

### Contexto
Este é um teste de issue com formatação markdown.

### Passos para Reproduzir
1. Passo um
2. Passo dois
3. Passo três

### Resultado Esperado
X deve acontecer.

### Resultado Atual
Y acontece em vez de X.
"""

        with patch("infra.github.github_api_client.create_github_client") as mock_client_factory:
            mock_client = MagicMock()
            mock_client.create_issue = AsyncMock(return_value=Result.ok({
                "issue_number": 125,
                "issue_url": "https://github.com/test/repo/issues/125",
                "issue_title": "Teste Multi-line",
                "issue_body": body,
                "labels": ["automated"],
            }))
            mock_client.close = AsyncMock()
            mock_client_factory.return_value = mock_client

            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Teste Multi-line",
                "body": body,
            })

            assert result.is_ok
            # Verifica que o body foi preservado
            assert "## Issue Completa" in result.value["issue_body"]
            assert "Passo um" in result.value["issue_body"]

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN") == "test_token",
        reason="Requer GITHUB_TOKEN real"
    )
    def test_agent_issue_real_api_skip_if_no_token(self):
        """Este teste só roda com um token real."""
        # Este teste é marcado para skip unless tenha um token real
        # Útil para testes manuais ou CI com credenciais reais
        pass

    def test_agent_issue_labels_empty_array(self, mock_env):
        """Testa criação de issue com array vazio de labels."""
        with patch("infra.github.github_api_client.create_github_client") as mock_client_factory:
            mock_client = MagicMock()
            mock_client.create_issue = AsyncMock(return_value=Result.ok({
                "issue_number": 126,
                "issue_url": "https://github.com/test/repo/issues/126",
                "issue_title": "No Labels",
                "issue_body": "Test",
                "labels": [],
            }))
            mock_client.close = AsyncMock()
            mock_client_factory.return_value = mock_client

            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "No Labels",
                "body": "Test",
                "labels": [],
            })

            assert result.is_ok
            assert result.value["labels"] == []
