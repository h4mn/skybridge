# -*- coding: utf-8 -*-
"""
Commit Message Generator via Agente.

PRD018 Fase 3: Gera commit messages no estilo Conventional Commits
usando contexto do issue GitHub (título, body, labels).

A commit message é gerada após o agente modificar arquivos e
após os guardrails passarem.
"""
from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.webhooks.domain import WebhookJob

from kernel.contracts.result import Result


class CommitMessageGenerator:
    """
    Gera commit messages via Agente usando contexto do issue.

    A mensagem segue o padrão Conventional Commits:
    - feat, fix, docs, refactor, chore, test
    - Escopo opcional
    - Descrição concisa
    - Body explicativo (opcional)
    - Referência ao issue (#N)

    Attributes:
        agent_adapter: Adapter para chamar o agente
    """

    # Conventional commit types
    COMMIT_TYPES = {
        "bug": "fix",
        "fix": "fix",
        "enhancement": "feat",
        "feature": "feat",
        "documentation": "docs",
        "refactor": "refactor",
        "test": "test",
        "chore": "chore",
        "ci": "ci",
        "perf": "perf",
        "style": "style",
    }

    def __init__(self, agent_adapter=None):
        """
        Inicializa gerador.

        Args:
            agent_adapter: Adapter do agente (opcional, cria ClaudeCodeAdapter se None)
        """
        if agent_adapter is None:
            from core.webhooks.infrastructure.agents.claude_agent import ClaudeCodeAdapter
            agent_adapter = ClaudeCodeAdapter()
        self.agent_adapter = agent_adapter

    async def generate(self, job: "WebhookJob", worktree_path: str) -> Result[str, str]:
        """
        Gera commit message usando Agente.

        Args:
            job: Job de webhook com contexto do issue
            worktree_path: Caminho para o worktree

        Returns:
            Result com commit message ou erro

        Note:
            O agente é chamado com um prompt específico para gerar
            a commit message baseada no contexto do issue e diff.
        """
        # Extrai contexto do issue
        issue = job.event.payload.get("issue", {})
        repository = job.event.payload.get("repository", {})

        issue_number = issue.get("number")
        issue_title = issue.get("title", "")
        issue_body = issue.get("body", "")
        issue_labels = [l.get("name", "") for l in issue.get("labels", [])]

        # Detecta tipo de commit baseado em labels
        commit_type = self._detect_commit_type(issue_labels)

        # Extrai diff das mudanças
        diff_result = await self._get_diff_summary(worktree_path)
        if diff_result.is_err:
            return Result.err(f"Erro ao obter diff: {diff_result.error}")

        diff_summary = diff_result.value

        # Constrói prompt para o agente
        prompt = self._build_prompt(
            issue_number=issue_number,
            issue_title=issue_title,
            issue_body=issue_body,
            issue_labels=issue_labels,
            commit_type=commit_type,
            diff_summary=diff_summary,
        )

        # Chama agente para gerar commit message
        # NOTA: Usamos uma abordagem simples chamando via API do Claude
        # em vez de usar o ClaudeCodeAdapter completo para essa tarefa simples
        commit_message = await self._call_agent_for_commit_message(prompt)

        if not commit_message:
            # Fallback para mensagem gerada heuristicamente
            commit_message = self._generate_fallback_message(
                commit_type=commit_type,
                issue_title=issue_title,
                issue_number=issue_number,
            )

        return Result.ok(commit_message)

    def _detect_commit_type(self, labels: list[str]) -> str:
        """
        Detecta tipo de commit baseado em labels do GitHub.

        Args:
            labels: Lista de labels do issue

        Returns:
            Tipo de commit (feat, fix, docs, etc)
        """
        labels_lower = [l.lower() for l in labels]

        for label, commit_type in self.COMMIT_TYPES.items():
            if label in labels_lower:
                return commit_type

        return "chore"  # Default

    async def _get_diff_summary(self, worktree_path: str) -> Result[str, str]:
        """
        Obtém resumo das mudanças (git diff --stat).

        Args:
            worktree_path: Caminho para o worktree

        Returns:
            Result com resumo do diff ou erro
        """
        try:
            # git diff --stat para resumo estatístico
            diff_stat = subprocess.check_output(
                ["git", "diff", "--stat"],
                cwd=worktree_path,
                text=True,
                stderr=subprocess.DEVNULL,
            )

            # git diff --name-only para lista de arquivos
            diff_files = subprocess.check_output(
                ["git", "diff", "--name-only"],
                cwd=worktree_path,
                text=True,
                stderr=subprocess.DEVNULL,
            )

            # Combina as informações
            summary = f"Files changed:\n{diff_files.strip()}\n\nStatistics:\n{diff_stat.strip()}"

            return Result.ok(summary)

        except subprocess.CalledProcessError as e:
            return Result.err(f"Erro ao executar git diff: {e}")
        except FileNotFoundError:
            return Result.err("Git não encontrado")

    def _build_prompt(
        self,
        issue_number: int,
        issue_title: str,
        issue_body: str,
        issue_labels: list[str],
        commit_type: str,
        diff_summary: str,
    ) -> str:
        """
        Constrói prompt para o agente gerar commit message.

        Args:
            issue_number: Número do issue
            issue_title: Título do issue
            issue_body: Body do issue
            issue_labels: Labels do issue
            commit_type: Tipo de commit detectado
            diff_summary: Resumo do diff

        Returns:
            Prompt completo para o agente
        """
        return f"""Generate a conventional commit message for this GitHub issue.

Issue: #{issue_number} - {issue_title}

{issue_body[:1000] if issue_body else '(No description)'}

Labels: {', '.join(issue_labels) if issue_labels else 'none'}
Commit type: {commit_type}

Changes made:
{diff_summary}

Generate ONLY the commit message, nothing else. Use this format:

{commit_type}(scope): description

More detailed explanatory text, if needed. Wrap text to ~72 characters.

Reference the issue with: Fixes #{issue_number}

Keep it under 500 characters total. Be concise and clear.
"""

    async def _call_agent_for_commit_message(self, prompt: str) -> str | None:
        """
        Chama agente para gerar commit message.

        Args:
            prompt: Prompt para o agente

        Returns:
            Commit message gerada ou None

        Note:
            Esta é uma implementação simplificada.
            Em produção, pode usar a API Anthropic ou outro serviço.
        """
        # Implementação simplificada - em produção usar API real
        # Por agora, retorna None para usar fallback
        # TODO: Integrar com API Anthropic ou similar
        return None

    def _generate_fallback_message(
        self,
        commit_type: str,
        issue_title: str,
        issue_number: int,
    ) -> str:
        """
        Gera commit message via heurística (fallback).

        Args:
            commit_type: Tipo de commit
            issue_title: Título do issue
            issue_number: Número do issue

        Returns:
            Commit message gerada heuristicamente
        """
        # Limpa título do issue
        title_clean = issue_title.strip()
        # Remove Issue #123 do título se presente
        title_clean = title_clean.replace(f"Issue #{issue_number}", "").strip()
        title_clean = title_clean.replace(f"#{issue_number}", "").strip()

        # Primeira letra minúscula
        if title_clean:
            title_clean = title_clean[0].lower() + title_clean[1:]

        # Limita tamanho
        if len(title_clean) > 72:
            title_clean = title_clean[:69] + "..."

        return f"{commit_type}: {title_clean}\n\nFixes #{issue_number}\n\n> \"Autonomy with quality is sustainable autonomy\" – made by Sky"
