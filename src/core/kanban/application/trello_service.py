# -*- coding: utf-8 -*-
"""
Trello Service — Serviço centralizado para gerenciar Trello.

Orquestra auto-configuração de listas Kanban, sincronização de labels
e detecção de movimentos de cards para iniciar agentes.
"""

import logging
from typing import Optional

from infra.kanban.adapters.trello_adapter import TrelloAdapter
from kernel import Result
from runtime.config.config import TrelloKanbanListsConfig, get_trello_kanban_lists_config


logger = logging.getLogger(__name__)


class TrelloService:
    """
    Serviço centralizado para gerenciar integração com Trello.

    Responsabilidades:
    - Auto-configurar listas Kanban no board
    - Detectar movimentos de cards para triggers de agentes
    - Sincronizar labels do GitHub para Trello
    """

    def __init__(
        self,
        trello_adapter: TrelloAdapter,
        kanban_config: TrelloKanbanListsConfig | None = None,
    ):
        """
        Inicializa serviço Trello.

        Args:
            trello_adapter: Adapter para comunicação com Trello
            kanban_config: Configuração das listas Kanban (usa default se não fornecido)
        """
        self.adapter = trello_adapter
        self.kanban_config = kanban_config or get_trello_kanban_lists_config()
        self._board_id = trello_adapter.board_id

    async def initialize_board(
        self,
        board_id: str | None = None,
    ) -> Result[dict[str, dict], str]:
        """
        Inicializa board Trello criando/verificando listas Kanban.

        Args:
            board_id: ID do board (usa adapter.board_id se não fornecido)

        Returns:
            Result com dict contendo infos das listas:
            {
                "list_name": {"id": "list_id", "color": "#hex", "created": bool}
            }
        """
        target_board = board_id or self._board_id
        if not target_board:
            return Result.err("board_id não configurado")

        if not self.kanban_config.auto_create_lists:
            logger.info("Auto-configuração de listas desativada")
            return Result.ok({})

        logger.info(f"Inicializando board Trello: {target_board}")

        # Busca configuração das listas
        list_names = self.kanban_config.get_list_names()
        list_colors = self.kanban_config.get_list_colors()

        # Chama auto_configure_lists do adapter
        result = await self.adapter.auto_configure_lists(
            list_names=list_names,
            list_colors=list_colors,
            board_id=target_board,
        )

        if result.is_err:
            return Result.err(f"Erro ao configurar listas: {result.error}")

        lists_info = result.unwrap()
        logger.info(f"Board inicializado com {len(lists_info)} listas")

        return Result.ok(lists_info)

    async def handle_card_moved_to_todo(
        self,
        card_id: str,
    ) -> Result[None, str]:
        """
        Handle webhook: detecta movimento para '📋 A Fazer' e inicia agente.

        Este método é chamado quando o webhook do Trello detecta que um card
        foi movido para a lista "📋 A Fazer". O comportamento é:

        1. Verifica se o card está realmente em "📋 A Fazer"
        2. Move automaticamente para "🚧 Em Andamento"
        3. Inicia o agente (via JobOrchestrator)

        Args:
            card_id: ID do card que foi movido

        Returns:
            Result OK se processado com sucesso, erro se falhar
        """
        try:
            # Busca informações do card
            card_result = await self.adapter.get_card(card_id)
            if card_result.is_err:
                return Result.err(f"Card não encontrado: {card_result.error}")

            card = card_result.unwrap()

            logger.info(
                f"Card detectado em '📋 A Fazer': {card.title} "
                f"(issue_url: {card.url})"
            )

            # Move automaticamente para "🚧 Em Andamento"
            move_result = await self.adapter.move_card_to_list(
                card_id=card_id,
                target_list_name=self.kanban_config.progress,
            )

            if move_result.is_err:
                return Result.err(
                    f"Erro ao mover para '{self.kanban_config.progress}': "
                    f"{move_result.error}"
                )

            # Adiciona comentário de início
            await self.adapter.add_card_comment(
                card_id=card_id,
                comment=f"🚀 **Iniciando Processamento**\n\n"
                f"Card movido de '{self.kanban_config.todo}' para "
                f"'{self.kanban_config.progress}'.\n\n"
                f"Agente será iniciado em breve...",
            )

            logger.info(
                f"Card {card_id} movido para '{self.kanban_config.progress}' - "
                f"agente será iniciado"
            )

            # TODO: Iniciar agente via JobOrchestrator
            # Isso será implementado na integração com o sistema de agentes

            return Result.ok(None)

        except Exception as e:
            logger.error(f"Erro ao processar card {card_id}: {e}")
            return Result.err(f"Erro ao processar card: {str(e)}")

    async def sync_github_labels_to_trello(
        self,
        card_id: str,
        github_labels: list[str],
        board_id: str | None = None,
    ) -> Result[None, str]:
        """
        Sincroniza labels do GitHub como tags coloridas no Trello.

        Args:
            card_id: ID do card no Trello
            github_labels: Labels da issue do GitHub
            board_id: ID do board (usa adapter.board_id se não fornecido)

        Returns:
            Result OK se sincronizado com sucesso, erro se falhar
        """
        if not self.kanban_config.sync_github_labels:
            logger.debug("Sincronização de labels desativada")
            return Result.ok(None)

        if not github_labels:
            logger.debug("Nenhum label para sincronizar")
            return Result.ok(None)

        try:
            target_board = board_id or self._board_id
            if not target_board:
                return Result.err("board_id não configurado")

            # Mapeia labels do GitHub para labels do Trello
            label_mapping = self.kanban_config.label_mapping

            for github_label in github_labels:
                # Verifica se há mapeamento para este label
                if github_label not in label_mapping:
                    logger.debug(f"Label '{github_label}' não mapeado, ignorando")
                    continue

                trello_label_name, trello_label_color = label_mapping[github_label]

                # Busca ou cria o label no Trello
                label_result = await self.adapter.get_or_create_label(
                    label_name=trello_label_name,
                    color=trello_label_color,
                    board_id=target_board,
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

    async def get_list_id_by_name(
        self,
        list_name: str,
        board_id: str | None = None,
    ) -> Result[str, str]:
        """
        Busca ID de uma lista pelo nome.

        Args:
            list_name: Nome da lista
            board_id: ID do board (usa adapter.board_id se não fornecido)

        Returns:
            Result com ID da lista ou erro
        """
        return await self.adapter._get_list_id(list_name, board_id)

    async def verify_list_exists(
        self,
        list_name: str,
        board_id: str | None = None,
    ) -> Result[bool, str]:
        """
        Verifica se uma lista existe no board.

        Args:
            list_name: Nome da lista
            board_id: ID do board (usa adapter.board_id se não fornecido)

        Returns:
            Result com True se existe, False caso contrário
        """
        result = await self.adapter._get_list_id(list_name, board_id)

        if result.is_ok:
            return Result.ok(True)
        elif "não encontrada" in result.error:
            return Result.ok(False)
        else:
            return Result.err(result.error)

    async def setup_webhook(
        self,
        callback_url: str,
        description: str = "Skybridge Trello Webhook",
    ) -> Result[dict, str]:
        """
        Configura webhook automaticamente no Trello.

        Verifica se já existe um webhook para o board com a mesma callback URL.
        Se não existir, cria um novo.

        Args:
            callback_url: URL pública para receber webhooks (ex: Ngrok URL)
            description: Descrição do webhook

        Returns:
            Result com dados do webhook criado/existente
        """
        target_board = self._board_id
        if not target_board:
            return Result.err("board_id não configurado")

        try:
            # Primeiro, lista webhooks existentes
            list_result = await self.adapter.list_webhooks()
            if list_result.is_err:
                return Result.err(f"Erro ao listar webhooks: {list_result.error}")

            existing_webhooks = list_result.unwrap()

            # Verifica se já existe webhook para este board com mesma callback URL
            for webhook in existing_webhooks:
                if (
                    webhook.get("idModel") == target_board
                    and webhook.get("callbackURL") == callback_url
                ):
                    logger.info(f"Webhook já existe: {webhook['id']}")
                    return Result.ok(webhook)

            # Cria novo webhook
            create_result = await self.adapter.create_webhook(
                callback_url=callback_url,
                description=description,
                id_model=target_board,
            )

            if create_result.is_err:
                return Result.err(f"Erro ao criar webhook: {create_result.error}")

            webhook_data = create_result.unwrap()
            logger.info(f"Webhook configurado: {webhook_data['id']}")
            return Result.ok(webhook_data)

        except Exception as e:
            logger.error(f"Erro ao configurar webhook: {e}")
            return Result.err(f"Erro ao configurar webhook: {str(e)}")

    async def cleanup_webhooks(
        self,
        callback_url: str | None = None,
    ) -> Result[int, str]:
        """
        Remove webhooks órfãos ou duplicados.

        Args:
            callback_url: Se fornecido, apenas deleta webhooks com esta callback URL

        Returns:
            Result com número de webhooks deletados
        """
        try:
            list_result = await self.adapter.list_webhooks()
            if list_result.is_err:
                return Result.err(f"Erro ao listar webhooks: {list_result.error}")

            webhooks = list_result.unwrap()
            deleted_count = 0

            for webhook in webhooks:
                # Filtra por callback URL se fornecida
                if callback_url and webhook.get("callbackURL") != callback_url:
                    continue

                # Deleta webhook
                delete_result = await self.adapter.delete_webhook(webhook["id"])
                if delete_result.is_ok:
                    deleted_count += 1

            logger.info(f"{deleted_count} webhook(s) deletado(s)")
            return Result.ok(deleted_count)

        except Exception as e:
            logger.error(f"Erro ao limpar webhooks: {e}")
            return Result.err(f"Erro ao limpar webhooks: {str(e)}")
