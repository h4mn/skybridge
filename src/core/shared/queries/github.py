# -*- coding: utf-8 -*-
"""
GitHub Queries — Queries para interagir com GitHub API.

Handlers para criar issues, pull requests e outras operações no GitHub.
"""

import asyncio
import os
from typing import TypedDict

from kernel import Result
from kernel.registry.decorators import query


class CreateIssueInput(TypedDict):
    """Input para criar issue."""
    title: str
    body: str
    labels: list[str] | None


class IssueData(TypedDict):
    """Dados de resposta da issue criada."""
    issue_number: int
    issue_url: str
    issue_title: str
    issue_body: str
    labels: list[str]


@query(
    name="github.createissue",
    description="Cria uma nova issue no GitHub",
    tags=["github", "issues"],
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Título da issue"
            },
            "body": {
                "type": "string",
                "description": "Corpo da issue (descrição completa)"
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Labels para adicionar (opcional)",
                "default": ["automated"]
            }
        },
        "required": ["title", "body"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "issue_number": {"type": "integer"},
            "issue_url": {"type": "string"},
            "issue_title": {"type": "string"},
            "issue_body": {"type": "string"},
            "labels": {"type": "array", "items": {"type": "string"}},
        },
    },
)
def create_issue_query(input: CreateIssueInput) -> Result[IssueData, str]:
    """
    Query handler para criar issue no GitHub.

    Args:
        input: Dicionário com title, body e labels (opcional)

    Returns:
        Result com dados da issue criada ou erro
    """
    async def _create_issue():
        from infra.github.github_api_client import create_github_client

        # Obtém configuração do GitHub via environment variables
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return Result.err("GITHUB_TOKEN não configurado")

        repo = os.getenv("GITHUB_REPO", "h4mn/skybridge")
        if not repo:
            return Result.err("GITHUB_REPO não configurado (formato: owner/repo)")

        # Cria cliente
        client = create_github_client(token=token)

        try:
            # Cria issue
            result = await client.create_issue(
                repo=repo,
                title=input["title"],
                body=input["body"],
                labels=input.get("labels", ["automated"]),
            )

            if result.is_err:
                return Result.err(result.error)

            return Result.ok(result.value)

        finally:
            await client.close()

    # Executa função async
    return asyncio.run(_create_issue())
