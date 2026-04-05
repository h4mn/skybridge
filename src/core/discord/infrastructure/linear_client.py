# -*- coding: utf-8 -*-
"""
Cliente simples para a API do Linear.

Usa GraphQL para criar issues no projeto Inbox.
DOC: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _get_linear_api_key() -> str | None:
    """
    Obtém a API Key do Linear de múltiplas fontes.

    Ordem de prioridade:
    1. Variável de ambiente LINEAR_API_KEY
    2. Seção "env" do ~/.claude/settings.json

    Returns:
        A API Key ou None se não encontrada
    """
    # 1. Tentar variável de ambiente
    api_key = os.getenv("LINEAR_API_KEY")
    if api_key:
        return api_key

    # 2. Tentar settings.json do Claude Code
    try:
        settings_path = Path.home() / ".claude" / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
                api_key = settings.get("env", {}).get("LINEAR_API_KEY")
                if api_key:
                    logger.info("LINEAR_API_KEY lida do settings.json")
                    return api_key
    except Exception as e:
        logger.debug(f"Não foi possível ler settings.json: {e}")

    return None


# Configurações
LINEAR_API_KEY = _get_linear_api_key()
LINEAR_API_URL = "https://api.linear.app/graphql"

# Headers padrão
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"{LINEAR_API_KEY}" if LINEAR_API_KEY else "",
}

# Query GraphQL para criar issue
CREATE_ISSUE_MUTATION = """
mutation createIssue(
    $title: String!
    $description: String!
    $teamId: String!
    $projectId: String!
    $labelIds: [String!]
) {
    issueCreate(
        input: {
            title: $title
            description: $description
            teamId: $teamId
            projectId: $projectId
            labelIds: $labelIds
        }
    ) {
        success
        issue {
            id
            identifier
            title
            url
        }
    }
}
"""


class LinearClientError(Exception):
    """Erro na comunicação com a API do Linear."""

    pass


async def create_issue(
    title: str,
    description: str,
    team_id: str,
    project_id: str,
    label_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Cria uma issue no Linear via GraphQL API.

    Args:
        title: Título da issue
        description: Descrição em Markdown
        team_id: ID do time (ex: "c5045b7c-63c0-4d67-8d9e-90b6988a9509")
        project_id: ID do projeto (ex: "02be2007-fd29-4f1c-8dc8-6b1d854a4a70")
        label_ids: Lista de IDs dos labels

    Returns:
        Dict com dados da issue criada:
        {
            "id": "UUID",
            "identifier": "SKI-123",
            "title": "Título",
            "url": "https://linear.app/..."
        }

    Raises:
        LinearClientError: Se a requisição falhar
    """
    if not LINEAR_API_KEY:
        raise LinearClientError(
            "LINEAR_API_KEY não configurada. "
            "Adicione ao .env: LINEAR_API_KEY=lin_api_..."
        )

    if label_ids is None:
        label_ids = []

    # Preparar payload GraphQL
    payload = {
        "query": CREATE_ISSUE_MUTATION,
        "variables": {
            "title": title,
            "description": description,
            "teamId": team_id,
            "projectId": project_id,
            "labelIds": label_ids,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                LINEAR_API_URL,
                json=payload,
                headers=DEFAULT_HEADERS,
            )

            # Linear retorna 200 mesmo com erros de GraphQL
            data = response.json()

            # Verificar erros GraphQL
            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Erro desconhecido")
                logger.error(f"Erro GraphQL Linear: {error_msg}")

                # TODO: Se erro for "Entity not found in validateAccess: labelIds",
                #       criar script de sync para buscar labels do Linear e atualizar
                #       os IDs hardcoded em todos os arquivos (inbox_slash.py, inbox.py, etc.)
                #       Isso evita labels desatualizados causando erros silenciosos.
                if "labelIds" in error_msg or "label" in error_msg.lower():
                    logger.error(
                        "TODO: Criar sync de labels! Os label IDs hardcoded estão "
                        "desatualizados. Implementar: src/core/discord/scripts/sync_labels.py"
                    )

                raise LinearClientError(f"Erro Linear API: {error_msg}")

            # Extrair dados da issue criada
            issue_data = data.get("data", {}).get("issueCreate", {})
            success = issue_data.get("success", False)

            if not success or not issue_data.get("issue"):
                raise LinearClientError("Falha ao criar issue (success=false)")

            issue = issue_data["issue"]
            logger.info(f"Issue criada: {issue['identifier']} - {issue['title']}")

            return {
                "id": issue["id"],
                "identifier": issue["identifier"],
                "title": issue["title"],
                "url": issue["url"],
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"Erro HTTP Linear: {e.response.status_code}")
        raise LinearClientError(f"Erro HTTP {e.response.status_code}: {e}") from e

    except httpx.RequestError as e:
        logger.error(f"Erro de requisição Linear: {e}")
        raise LinearClientError(f"Erro de conexão: {e}") from e

    except Exception as e:
        logger.error(f"Erro inesperado ao criar issue: {e}")
        raise LinearClientError(f"Erro: {e}") from e


async def create_inbox_issue(
    title: str,
    description: str,
    label_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Cria uma issue no projeto Inbox.

    Shortcut para create_issue com o teamId e projectId do Inbox.

    Args:
        title: Título da issue
        description: Descrição em Markdown
        label_ids: Lista de IDs dos labels

    Returns:
        Dict com dados da issue criada
    """
    # Inbox - IDs fixos
    INBOX_TEAM_ID = "c5045b7c-63c0-4d67-8d9e-90b6988a9509"  # Skybridge
    INBOX_PROJECT_ID = "02be2007-fd29-4f1c-8dc8-6b1d854a4a70"  # Inbox - Backlog de Ideias

    return await create_issue(
        title=title,
        description=description,
        team_id=INBOX_TEAM_ID,
        project_id=INBOX_PROJECT_ID,
        label_ids=label_ids,
    )
