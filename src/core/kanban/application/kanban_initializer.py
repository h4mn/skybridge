# -*- coding: utf-8 -*-
"""
Kanban Initializer - Cria estrutura inicial do kanban.db.

Responsável por criar board e listas padrão do Kanban Skybridge.

Listas padrão (conforme setup do Trello):
1. Issues
2. Brainstorm
3. A Fazer
4. Em Andamento
5. Em Revisão
6. Publicar

DOC: core/kanban/application/kanban_initializer.py
DOC: ADR024 - Workspace isolation
"""

import logging
from pathlib import Path

from core.kanban.domain.database import KanbanBoard, KanbanList
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter

logger = logging.getLogger(__name__)


# Listas padrão do Kanban Skybridge (conforme Trello)
DEFAULT_LISTS = [
    {"name": "Issues", "position": 0},
    {"name": "Brainstorm", "position": 1},
    {"name": "A Fazer", "position": 2},
    {"name": "Em Andamento", "position": 3},
    {"name": "Em Revisão", "position": 4},
    {"name": "Publicar", "position": 5},
]


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

        # Cria apenas as listas padrão que não existem
        created_count = 0
        for lst in DEFAULT_LISTS:
            if lst["name"] not in existing_lists:
                list_obj = KanbanList(
                    id=f"list-{lst['name'].lower().replace(' ', '-')}",
                    board_id=board.id,
                    name=lst["name"],
                    position=lst["position"],
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
