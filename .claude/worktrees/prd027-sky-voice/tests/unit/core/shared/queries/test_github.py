# -*- coding: utf-8 -*-
"""
Testes para GitHub Queries.

Testa o handler github.createissue para criar issues via GitHub API.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from kernel import Result


@pytest.fixture
def mock_github_env():
    """Configura variáveis de ambiente para GitHub."""
    original_token = os.getenv("GITHUB_TOKEN")
    original_repo = os.getenv("GITHUB_REPO")

    os.environ["GITHUB_TOKEN"] = "test_token_123"
    os.environ["GITHUB_REPO"] = "test/repo"

    yield

    # Restore
    if original_token is None:
        os.environ.pop("GITHUB_TOKEN", None)
    else:
        os.environ["GITHUB_TOKEN"] = original_token

    if original_repo is None:
        os.environ.pop("GITHUB_REPO", None)
    else:
        os.environ["GITHUB_REPO"] = original_repo


class TestCreateIssueQuery:
    """Testes para create_issue_query."""

    def test_create_issue_success(self, mock_github_env):
        """Testa criação de issue com sucesso."""
        # Mock completo do cliente GitHub
        mock_client = MagicMock()
        mock_client.create_issue = AsyncMock(return_value=Result.ok({
            "issue_number": 42,
            "issue_url": "https://github.com/test/repo/issues/42",
            "issue_title": "Test Issue",
            "issue_body": "Test body",
            "labels": ["automated", "bug"],
        }))
        mock_client.close = AsyncMock()

        # Patch da factory function
        with patch("infra.github.github_api_client.create_github_client", return_value=mock_client):
            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Test Issue",
                "body": "Test body",
                "labels": ["automated", "bug"],
            })

            # Assert
            assert result.is_ok
            issue_data = result.value
            assert issue_data["issue_number"] == 42
            assert issue_data["issue_url"] == "https://github.com/test/repo/issues/42"
            assert issue_data["issue_title"] == "Test Issue"
            assert issue_data["labels"] == ["automated", "bug"]

            # Verifica que o cliente foi chamado corretamente
            mock_client.create_issue.assert_called_once_with(
                repo="test/repo",
                title="Test Issue",
                body="Test body",
                labels=["automated", "bug"],
            )

    def test_create_issue_default_labels(self, mock_github_env):
        """Testa criação de issue com labels padrão."""
        mock_client = MagicMock()
        mock_client.create_issue = AsyncMock(return_value=Result.ok({
            "issue_number": 43,
            "issue_url": "https://github.com/test/repo/issues/43",
            "issue_title": "Test",
            "issue_body": "Body",
            "labels": ["automated"],
        }))
        mock_client.close = AsyncMock()

        with patch("infra.github.github_api_client.create_github_client", return_value=mock_client):
            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Test",
                "body": "Body",
            })

            assert result.is_ok
            assert result.value["labels"] == ["automated"]

    def test_create_issue_without_token(self):
        """Testa erro quando GITHUB_TOKEN não está configurado."""
        # Remove token
        original_token = os.getenv("GITHUB_TOKEN")
        os.environ.pop("GITHUB_TOKEN", None)

        try:
            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Test",
                "body": "Body",
            })

            assert result.is_err
            assert "GITHUB_TOKEN não configurado" in result.error
        finally:
            # Restore
            if original_token:
                os.environ["GITHUB_TOKEN"] = original_token

    def test_create_issue_github_api_error(self, mock_github_env):
        """Testa erro da API do GitHub."""
        mock_client = MagicMock()
        mock_client.create_issue = AsyncMock(return_value=Result.err(
            "Erro HTTP 401: Bad credentials"
        ))
        mock_client.close = AsyncMock()

        with patch("infra.github.github_api_client.create_github_client", return_value=mock_client):
            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Test",
                "body": "Body",
            })

            assert result.is_err
            assert "Erro HTTP 401" in result.error

    def test_create_issue_minimal_input(self, mock_github_env):
        """Testa criação de issue com input mínimo."""
        mock_client = MagicMock()
        mock_client.create_issue = AsyncMock(return_value=Result.ok({
            "issue_number": 44,
            "issue_url": "https://github.com/test/repo/issues/44",
            "issue_title": "Minimal",
            "issue_body": "",
            "labels": ["automated"],
        }))
        mock_client.close = AsyncMock()

        with patch("infra.github.github_api_client.create_github_client", return_value=mock_client):
            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Minimal",
                "body": "",
            })

            assert result.is_ok
            assert result.value["issue_number"] == 44

    def test_create_issue_with_long_description(self, mock_github_env):
        """Testa criação de issue com descrição longa."""
        long_body = "A" * 10000  # 10k caracteres

        mock_client = MagicMock()
        mock_client.create_issue = AsyncMock(return_value=Result.ok({
            "issue_number": 45,
            "issue_url": "https://github.com/test/repo/issues/45",
            "issue_title": "Long Issue",
            "issue_body": long_body,
            "labels": ["automated"],
        }))
        mock_client.close = AsyncMock()

        with patch("infra.github.github_api_client.create_github_client", return_value=mock_client):
            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Long Issue",
                "body": long_body,
            })

            assert result.is_ok
            assert result.value["issue_body"] == long_body

    def test_create_issue_many_labels(self, mock_github_env):
        """Testa criação de issue com muitas labels."""
        labels = [f"label{i}" for i in range(20)]

        mock_client = MagicMock()
        mock_client.create_issue = AsyncMock(return_value=Result.ok({
            "issue_number": 46,
            "issue_url": "https://github.com/test/repo/issues/46",
            "issue_title": "Many Labels",
            "issue_body": "Test",
            "labels": labels,
        }))
        mock_client.close = AsyncMock()

        with patch("infra.github.github_api_client.create_github_client", return_value=mock_client):
            from core.shared.queries.github import create_issue_query

            result = create_issue_query({
                "title": "Many Labels",
                "body": "Test",
                "labels": labels,
            })

            assert result.is_ok
            assert len(result.value["labels"]) == 20
