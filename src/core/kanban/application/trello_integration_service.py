# -*- coding: utf-8 -*-
"""
Trello Integration Service — Integra issues do GitHub com cards do Trello.

Service que cria automaticamente cards no Trello quando issues são abertas no GitHub.
"""

import logging
from typing import Optional

from infra.kanban.adapters.trello_adapter import TrelloAdapter
from kernel.contracts.result import Result


logger = logging.getLogger(__name__)


class TrelloIntegrationService:
    """
    Serviço de integração entre GitHub Issues e Trello Cards.

    Responsabilidades:
    - Criar cards no Trello para issues abertas
    - Adicionar metadados (issue URL, número, autor)
    - Retornar card_id para rastreamento futuro
    """

    def __init__(self, trello_adapter: TrelloAdapter, default_list_name: str = "🎯 Foco Janeiro - Março"):
        """
        Inicializa serviço de integração.

        Args:
            trello_adapter: Adapter para comunicação com Trello
            default_list_name: Nome da lista onde criar cards (padrão)
        """
        self.adapter = trello_adapter
        self.default_list_name = default_list_name

    async def create_card_from_github_issue(
        self,
        issue_number: int,
        issue_title: str,
        issue_body: str | None,
        issue_url: str,
        author: str,
        repo_name: str,
        labels: list[str] | None = None,
        list_name: str | None = None,
    ) -> Result[str, str]:
        """
        Cria card no Trello a partir de uma issue do GitHub.

        Args:
            issue_number: Número da issue
            issue_title: Título da issue
            issue_body: Descrição da issue (opcional)
            issue_url: URL da issue no GitHub
            author: Autor da issue
            repo_name: Nome do repositório (ex: "skybridge/skybridge")
            labels: Labels da issue (para tags no Trello)
            list_name: Nome da lista (usa default se não fornecido)

        Returns:
            Result com card_id ou mensagem de erro
        """
        try:
            # Monta descrição formatada
            card_description = self._format_card_description(
                issue_number=issue_number,
                issue_body=issue_body,
                issue_url=issue_url,
                author=author,
                repo_name=repo_name,
            )

            # Adiciona prefixo ao título
            card_title = f"#{issue_number} {issue_title}"

            # Adiciona labels como tags
            trello_labels = self._prepare_labels(labels)

            # Cria o card
            result = await self.adapter.create_card(
                title=card_title,
                description=card_description,
                list_name=list_name or self.default_list_name,
                labels=trello_labels if trello_labels else None,
            )

            if result.is_err:
                return Result.err(result.error)

            card_id = result.unwrap().id
            logger.info(
                f"Card criado no Trello: {card_id} para issue #{issue_number}"
            )

            # Adiciona comentário inicial
            await self.adapter.add_card_comment(
                card_id=card_id,
                comment=f"📝 Card criado automaticamente a partir da issue #{issue_number} do GitHub.\n\n"
                f"Aguardando processamento pelo agente..."
            )

            return Result.ok(card_id)

        except Exception as e:
            logger.error(f"Erro ao criar card para issue #{issue_number}: {e}")
            return Result.err(f"Erro ao criar card: {str(e)}")

    def _format_card_description(
        self,
        issue_number: int,
        issue_body: str | None,
        issue_url: str,
        author: str,
        repo_name: str,
    ) -> str:
        """Formata descrição do card com metadados da issue."""
        body = issue_body or "*Sem descrição*"

        return f"""**Issue do GitHub**

**Repositório:** {repo_name}
**Issue:** #{issue_number}
**Autor:** @{author}
**URL:** [Ver no GitHub]({issue_url})

---

**Descrição:**

{body}

---

*Este card foi criado automaticamente pelo sistema de integração GitHub → Trello.*"""

    def _prepare_labels(self, github_labels: list[str] | None) -> list[str]:
        """
        Prepara labels do GitHub para uso no Trello.

        Args:
            github_labels: Labels da issue do GitHub

        Returns:
            Lista de labels formatadas
        """
        if not github_labels:
            return []

        # Filtra labels que fazem sentido no Trello
        # Remove labels muito técnicas ou temporárias
        filtered = [
            label for label in github_labels
            if not label.startswith("status:")
            and not label.startswith("triage:")
            and len(label) < 30  # Limite de tamanho
        ]

        return filtered

    async def update_card_progress(
        self,
        card_id: str,
        phase: str,
        status: str,
    ) -> Result[None, str]:
        """
        Atualiza card no Trello com progresso do agente.

        Args:
            card_id: ID do card no Trello
            phase: Fase atual (ex: "Análise", "Implementação")
            status: Status atual

        Returns:
            Result vazio ou mensagem de erro
        """
        try:
            comment = f"""🔄 **Progresso do Agente**

**Fase:** {phase}
**Status:** {status}

---
*Atualização automática durante processamento da issue.*"""

            result = await self.adapter.add_card_comment(card_id, comment)
            if result.is_err:
                return Result.err(result.error)

            return Result.ok(None)

        except Exception as e:
            logger.error(f"Erro ao atualizar card {card_id}: {e}")
            return Result.err(f"Erro ao atualizar card: {str(e)}")

    async def mark_card_complete(
        self,
        card_id: str,
        summary: str,
        changes: list[str],
    ) -> Result[None, str]:
        """
        Marca card como completo no Trello.

        Args:
            card_id: ID do card no Trello
            summary: Resumo da implementação
            changes: Lista de mudanças realizadas

        Returns:
            Result vazio ou mensagem de erro
        """
        try:
            changes_text = "\n".join(f"- {c}" for c in changes)

            comment = f"""✅ **Implementação Concluída**

**Resumo:**
{summary}

**Mudanças:**
{changes_text}

---
*Issue processada automaticamente pelo agente Skybridge.*"""

            result = await self.adapter.add_card_comment(card_id, comment)
            if result.is_err:
                return Result.err(result.error)

            return Result.ok(None)

        except Exception as e:
            logger.error(f"Erro ao finalizar card {card_id}: {e}")
            return Result.err(f"Erro ao finalizar card: {str(e)}")
