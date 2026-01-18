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

    def __init__(
        self,
        trello_adapter: TrelloAdapter,
        default_list_name: str = "📥 Issues",
    ):
        """
        Inicializa serviço de integração.

        Args:
            trello_adapter: Adapter para comunicação com Trello
            default_list_name: Nome da lista onde criar cards (padrão: "📥 Issues")
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

            # Cria o card (sem labels inicialmente)
            result = await self.adapter.create_card(
                title=card_title,
                description=card_description,
                list_name=list_name or self.default_list_name,
                labels=None,  # Labels serão adicionados depois
            )

            if result.is_err:
                return Result.err(result.error)

            card_id = result.unwrap().id
            logger.info(
                f"Card criado no Trello: {card_id} para issue #{issue_number}"
            )

            # Sincroniza labels do GitHub para o Trello
            if labels:
                sync_result = await self._sync_github_labels(
                    card_id=card_id,
                    github_labels=labels,
                )
                if sync_result.is_err:
                    logger.warning(
                        f"Erro ao sincronizar labels: {sync_result.error}"
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

    async def _sync_github_labels(
        self,
        card_id: str,
        github_labels: list[str],
    ) -> Result[None, str]:
        """
        Sincroniza labels do GitHub como tags coloridas no Trello.

        Usa o mesmo mapeamento definido no PRD18:
        - bug → bug (red)
        - feature → feature (green)
        - enhancement → melhoria (blue)
        - documentation → docs (orange)
        - good-first-issue → bom-para-iniciar (yellow)

        Args:
            card_id: ID do card no Trello
            github_labels: Labels da issue do GitHub

        Returns:
            Result OK se sincronizado com sucesso, erro se falhar
        """
        try:
            # Mapeamento de labels (igual ao definido no PRD18)
            label_mapping = {
                "bug": ("bug", "red"),
                "feature": ("feature", "green"),
                "enhancement": ("melhoria", "blue"),
                "documentation": ("docs", "orange"),
                "good-first-issue": ("bom-para-iniciar", "yellow"),
            }

            for github_label in github_labels:
                # Filtra labels técnicas
                if github_label.startswith("status:") or github_label.startswith("triage:"):
                    continue

                # Verifica se há mapeamento para este label
                if github_label not in label_mapping:
                    continue

                trello_label_name, trello_label_color = label_mapping[github_label]

                # Busca ou cria o label no Trello
                label_result = await self.adapter.get_or_create_label(
                    label_name=trello_label_name,
                    color=trello_label_color,
                )

                if label_result.is_err:
                    logger.warning(
                        f"Erro ao criar label '{trello_label_name}': "
                        f"{label_result.error}"
                    )
                    continue

                label_id = label_result.unwrap()

                # Adiciona label ao card
                add_result = await self.adapter.add_label_to_card(
                    card_id=card_id,
                    label_id=label_id,
                )

                if add_result.is_err:
                    logger.warning(
                        f"Erro ao adicionar label '{trello_label_name}' ao card: "
                        f"{add_result.error}"
                    )
                    continue

                logger.info(
                    f"Label '{trello_label_name}' ({trello_label_color}) "
                    f"adicionado ao card {card_id}"
                )

            return Result.ok(None)

        except Exception as e:
            logger.error(f"Erro ao sincronizar labels: {e}")
            return Result.err(f"Erro ao sincronizar labels: {str(e)}")

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
