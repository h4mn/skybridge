# -*- coding: utf-8 -*-
"""
Kanban Initializer - Cria estrutura inicial do kanban.db.

Responsável por criar board e listas padrão do Kanban Skybridge.

DOC: core/kanban/application/kanban_initializer.py
DOC: ADR024 - Workspace isolation
DOC: ADR020 - Integração Trello (get_list_names como fonte única da verdade)
"""

import logging
from pathlib import Path

from core.kanban.domain.database import KanbanBoard, KanbanList
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter
from runtime.config.config import get_trello_kanban_lists_config

logger = logging.getLogger(__name__)


class KanbanInitializer:
    """
    Inicializador do Kanban Skybridge.

    Responsável por:
    - Criar board padrão "Skybridge"
    - Criar listas padrão do Kanban
    - Inicializar kanban.db em workspace/skybridge/

    Atributes:
        adapter: Adapter do kanban.db (SQLite)
    """

    def __init__(self, db_path: str | Path):
        """
        Inicializa o initializer.

        Args:
            db_path: Caminho para o arquivo kanban.db
        """
        self.db_path = Path(db_path)
        self.adapter = SQLiteKanbanAdapter(self.db_path)
        self.config = get_trello_kanban_lists_config()

    def initialize(self) -> None:
        """
        Inicializa o kanban.db com board e listas padrão.

        Garante que as listas padrão existam, mesmo se o board já existir.
        """
        # Conecta ao banco
        result = self.adapter.connect()
        if result.is_err:
            logger.error(f"Erro ao conectar ao kanban.db: {result.error}")
            return

        logger.info(f"Kanban DB conectado: {self.db_path}")

        # Verifica se board padrão já existe
        boards_result = self.adapter.list_boards()

        # Usa board existente ou cria o padrão
        if boards_result.is_ok and boards_result.value:
            # Usa o primeiro board existente
            board = boards_result.value[0]
            logger.info(f"Board existente encontrado: {board.id} - {board.name}")
        else:
            # Cria board padrão
            board = KanbanBoard(
                id="skybridge-main",
                name="Skybridge",
                trello_board_id=None,
                trello_sync_enabled=False,
            )
            create_result = self.adapter.create_board(board)
            if create_result.is_ok:
                board = create_result.value
            logger.info(f"Board criado: {board.id} - {board.name}")

        # Verifica quais listas padrão já existem
        lists_result = self.adapter.list_lists(board.id)
        existing_lists = set()
        if lists_result.is_ok:
            existing_lists = {lst.name for lst in lists_result.value}
            logger.info(f"Listas existentes: {existing_lists}")

        # Obtém listas padrão da FONTE ÚNICA DA VERDADE (config.py)
        # NOTA: Usa get_list_names_with_emoji() para compatibilidade com Trello
        # O Trello usa nomes com emoji (ex: "🚧 Em Andamento")
        default_list_names = self.config.get_list_names_with_emoji()

        # Cria apenas as listas padrão que não existem
        created_count = 0
        for position, list_name in enumerate(default_list_names):
            if list_name not in existing_lists:
                # Gera ID baseado no slug técnico em vez do nome com emoji
                # Ex: "🚧 Em Andamento" → "list-progress" (em vez de "list-em-andamento")
                list_def = self.config.get_definition_by_name(list_name)
                slug = list_def.slug if list_def else "unknown"
                list_obj = KanbanList(
                    id=f"list-{slug}",
                    board_id=board.id,
                    name=list_name,
                    position=position,
                )
                self.adapter.create_list(list_obj)
                logger.info(f"Lista criada: {list_obj.id} - {list_obj.name}")
                created_count += 1

        if created_count > 0:
            logger.info(f"{created_count} listas criadas com sucesso!")
        else:
            logger.info("Todas as listas padrão já existem.")

    def disconnect(self) -> None:
        """Desconecta do banco."""
        self.adapter.disconnect()
