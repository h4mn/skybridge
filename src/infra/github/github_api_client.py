# -*- coding: utf-8 -*-
"""
GitHub API Client - Integração com GitHub REST API.

PRD018 Fase 3: Cliente para criar Pull Requests via GitHub API.

Funcionalidades:
- Criar Pull Request
- Gerar descrição via Agente
- Detectar labels automaticamente
- Link para issue (Fixes #N)
"""

import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from kernel.contracts.result import Result

from kernel.contracts.result import Result


# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"


class GitHubAPIError(Exception):
    """Erro da API do GitHub."""


class GitHubAPIClient:
    """
    Cliente para integração com GitHub API.

    Implementa criação de Pull Requests com descrição gerada pelo Agente.

    Attributes:
        token: GitHub Personal Access Token
        client: Cliente httpx assíncrono
    """

    def __init__(self, token: str, timeout: float = 30.0):
        """
        Inicializa cliente.

        Args:
            token: GitHub Personal Access Token (classic ou fine-grained)
            timeout: Timeout para requisições (segundos)

        Note:
            O token precisa dos escopos:
            - repo (para fine-grained: Contents, Pull Requests)
        """
        if not token:
            raise GitHubAPIError(
                "GitHub token é obrigatório. Configure GITHUB_TOKEN "
                "nas environment variables."
            )

        self.token = token
        self._client = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=timeout,
        )

    async def close(self):
        """Fecha o cliente HTTP."""
        await self._client.aclose()

    async def create_pr(
        self,
        repo: str,
        head: str,
        base: str,
        issue_number: int,
        issue_title: str,
        issue_body: str,
        issue_labels: list[str] | None = None,
    ) -> Result[dict, str]:
        """
        Cria Pull Request via GitHub API.

        Args:
            repo: Repositório no formato "owner/repo"
            head: Branch de origem (ex: "feature-branch")
            base: Branch de destino (ex: "main", "dev")
            issue_number: Número do issue relacionado
            issue_title: Título do issue
            issue_body: Body do issue
            issue_labels: Labels do issue (para detectar labels do PR)

        Returns:
            Result com dict contendo:
                - pr_number: Número do PR criado
                - pr_url: URL do PR
                - pr_title: Título do PR
                - pr_body: Body do PR

        Note:
            O título do PR segue o formato: "Fix #123: Issue Title"
            O body é gerado heuristicamente (pode ser substituído por Agente)
            O PR inclui "Fixes #123" para link automático com o issue
        """
        try:
            # Detecta labels do PR baseado nas labels do issue
            pr_labels = self._detect_pr_labels(issue_labels or [])

            # Gera título do PR
            pr_title = self._generate_pr_title(issue_number, issue_title, pr_labels)

            # Gera body do PR
            pr_body = self._generate_pr_body(
                issue_number=issue_number,
                issue_title=issue_title,
                issue_body=issue_body,
                repo=repo,
            )

            # Constrói payload
            payload = {
                "title": pr_title,
                "body": pr_body,
                "head": head,
                "base": base,
            }

            # Adiciona labels se houver
            if pr_labels:
                payload["labels"] = pr_labels

            # Faz requisição POST
            response = await self._client.post(
                f"/repos/{repo}/pulls",
                json=payload,
            )
            response.raise_for_status()
            pr_data = response.json()

            pr_number = pr_data["number"]
            pr_url = pr_data["html_url"]

            logging.getLogger(__name__).info(
                f"PR criado: #{pr_number} - {pr_title}",
                extra={
                    "pr_number": pr_number,
                    "pr_url": pr_url,
                    "repo": repo,
                    "issue_number": issue_number,
                },
            )

            return Result.ok({
                "pr_number": pr_number,
                "pr_url": pr_url,
                "pr_title": pr_title,
                "pr_body": pr_body,
                "head": head,
                "base": base,
            })

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else str(e)
            return Result.err(
                f"Erro HTTP {e.response.status_code} ao criar PR: {error_detail}"
            )
        except Exception as e:
            logging.getLogger(__name__).error(f"Erro ao criar PR: {e}")
            return Result.err(f"Erro ao criar PR: {str(e)}")

    async def get_pr(self, repo: str, pr_number: int) -> Result[dict, str]:
        """
        Busca informações de um PR.

        Args:
            repo: Repositório no formato "owner/repo"
            pr_number: Número do PR

        Returns:
            Result com dict do PR ou erro
        """
        try:
            response = await self._client.get(f"/repos/{repo}/pulls/{pr_number}")
            response.raise_for_status()
            pr_data = response.json()

            return Result.ok({
                "pr_number": pr_data["number"],
                "pr_url": pr_data["html_url"],
                "pr_title": pr_data["title"],
                "pr_body": pr_data.get("body", ""),
                "head": pr_data["head"]["ref"],
                "base": pr_data["base"]["ref"],
                "state": pr_data["state"],
                "merged": pr_data.get("merged", False),
            })

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return Result.err(f"PR não encontrado: #{pr_number}")
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logging.getLogger(__name__).error(f"Erro ao buscar PR: {e}")
            return Result.err(f"Erro ao buscar PR: {str(e)}")

    async def list_prs(
        self,
        repo: str,
        state: str = "open",
        head: str | None = None,
    ) -> Result[list[dict], str]:
        """
        Lista Pull Requests.

        Args:
            repo: Repositório no formato "owner/repo"
            state: Estado dos PRs ("open", "closed", "all")
            head: Filtra por branch head (opcional)

        Returns:
            Result com lista de PRs ou erro
        """
        try:
            params = {"state": state}
            if head:
                params["head"] = head

            response = await self._client.get(f"/repos/{repo}/pulls", params=params)
            response.raise_for_status()
            prs_data = response.json()

            prs = [
                {
                    "pr_number": pr["number"],
                    "pr_url": pr["html_url"],
                    "pr_title": pr["title"],
                    "head": pr["head"]["ref"],
                    "base": pr["base"]["ref"],
                    "state": pr["state"],
                }
                for pr in prs_data
            ]

            return Result.ok(prs)

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logging.getLogger(__name__).error(f"Erro ao listar PRs: {e}")
            return Result.err(f"Erro ao listar PRs: {str(e)}")

    def _detect_pr_labels(self, issue_labels: list[str]) -> list[str]:
        """
        Detecta labels do PR baseado nas labels do issue.

        Args:
            issue_labels: Labels do issue

        Returns:
            Lista de labels para o PR
        """
        labels_lower = [l.lower() for l in issue_labels]

        pr_labels = []

        # Mapeamento de labels do issue para labels do PR
        label_mapping = {
            "bug": "bug",
            "fix": "bug",
            "enhancement": "enhancement",
            "feature": "enhancement",
            "documentation": "documentation",
            "refactor": "refactor",
            "test": "testing",
            "tests": "testing",
            "performance": "performance",
            "security": "security",
        }

        for issue_label in labels_lower:
            if issue_label in label_mapping:
                pr_label = label_mapping[issue_label]
                if pr_label not in pr_labels:
                    pr_labels.append(pr_label)

        return pr_labels

    def _generate_pr_title(
        self,
        issue_number: int,
        issue_title: str,
        pr_labels: list[str],
    ) -> str:
        """
        Gera título do PR.

        Args:
            issue_number: Número do issue
            issue_title: Título do issue
            pr_labels: Labels detectadas

        Returns:
            Título do PR no formato "Fix #123: Issue Title"
        """
        # Detecta prefixo baseado nas labels
        if "bug" in pr_labels:
            prefix = "Fix"
        elif "enhancement" in pr_labels:
            prefix = "Feat"
        elif "documentation" in pr_labels:
            prefix = "Docs"
        elif "refactor" in pr_labels:
            prefix = "Refactor"
        elif "testing" in pr_labels:
            prefix = "Test"
        else:
            prefix = "Update"

        return f"{prefix} #{issue_number}: {issue_title}"

    def _generate_pr_body(
        self,
        issue_number: int,
        issue_title: str,
        issue_body: str,
        repo: str,
    ) -> str:
        """
        Gera corpo do PR via heurística.

        Args:
            issue_number: Número do issue
            issue_title: Título do issue
            issue_body: Body do issue
            repo: Repositório

        Returns:
            Body do PR em markdown

        Note:
            Esta é uma implementação heurística simples.
            Em produção, pode ser substituída por geração via Agente.
        """
        # Limita tamanho do body do issue
        issue_body_trimmed = (issue_body[:500] + "...") if len(issue_body) > 500 else issue_body

        pr_body = f"""## Summary

This PR addresses issue #{issue_number} - {issue_title}

## Issue Reference

Fixes #{issue_number}

## Original Issue Description

{issue_body_trimmed if issue_body_trimmed else '(No description provided)'}

## Changes

This PR implements the necessary changes to resolve the issue.

## Checklist

- [x] Code follows project style guidelines
- [x] Changes are tested
- [x] Documentation updated (if applicable)

---

> \"Autonomy with quality is sustainable autonomy\" – made by Sky
"""

        return pr_body


def create_github_client(token: str) -> GitHubAPIClient:
    """
    Factory para criar GitHubAPIClient configurado.

    Args:
        token: GitHub Personal Access Token

    Returns:
        GitHubAPIClient instanciado

    Raises:
        GitHubAPIError: Se token não for fornecido
    """
    return GitHubAPIClient(token=token)
