# -*- coding: utf-8 -*-
"""
SQLite Adapter para Kanban Database.

Implementa o acesso ao kanban.db (SQLite), que é a FONTE ÚNICA
DA VERDADE do sistema Kanban Skybridge.

DOC: ADR024 - kanban.db em workspace/skybridge/
DOC: core/kanban/domain/schema.sql - Estrutura do banco
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.kanban.domain.database import KanbanBoard, KanbanCard, KanbanList, CardHistory
from core.kanban.domain.card import CardStatus
from kernel import Result


class SQLiteKanbanAdapter:
    """
    Adapter SQLite para Kanban Database.

    Responsável por todas as operações de CRUD no kanban.db.
    Implementa acesso thread-safe via connection pooling.

    Attributes:
        db_path: Caminho para o arquivo SQLite
    """

    def __init__(self, db_path: str | Path):
        """
        Inicializa o adapter.

        Args:
            db_path: Caminho para o arquivo kanban.db
        """
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> Result[None, str]:
        """
        Conecta ao banco e inicializa schema.

        Returns:
            Result.ok(None) se sucesso
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # Cria diretório pai se não existe
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Conecta com parâmetros otimizados
            self._conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,  # Permite uso multi-thread
                isolation_level=None,  # Autocommit mode
            )
            self._conn.row_factory = sqlite3.Row  # Retorna dict-like rows

            # Inicializa schema
            # Caminho: src/infra/kanban/adapters/ → src/core/kanban/domain/schema.sql
            # Resolve path baseado no local do módulo
            # src/infra/kanban/adapters → src/ (4 níveis acima)
            module_path = Path(__file__).resolve()
            src_path = module_path.parent.parent.parent.parent  # Vai para src/
            schema_path = src_path / "core" / "kanban" / "domain" / "schema.sql"

            # Debug: print do schema path

            if schema_path.exists():
                schema_sql = schema_path.read_text(encoding="utf-8")
                self._conn.executescript(schema_sql)

            return Result.ok(None)

        except Exception as e:
            return Result.err(f"Erro ao conectar ao kanban.db: {str(e)}")

    def disconnect(self) -> Result[None, str]:
        """
        Desconecta do banco.

        Returns:
            Result.ok(None) se sucesso
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
            return Result.ok(None)
        except Exception as e:
            return Result.err(f"Erro ao desconectar: {str(e)}")

    # ==========================================================================
    # BOARDS
    # ==========================================================================

    def create_board(self, board: KanbanBoard) -> Result[KanbanBoard, str]:
        """
        Cria um novo board.

        Args:
            board: Dados do board a criar

        Returns:
            Result.ok(board) com board criado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO boards (id, name, trello_board_id, trello_sync_enabled)
                VALUES (?, ?, ?, ?)
                """,
                (board.id, board.name, board.trello_board_id, board.trello_sync_enabled),
            )
            self._conn.commit()

            return Result.ok(board)

        except Exception as e:
            return Result.err(f"Erro ao criar board: {str(e)}")

    def get_board(self, board_id: str) -> Result[KanbanBoard, str]:
        """
        Busca um board por ID.

        Args:
            board_id: ID do board

        Returns:
            Result.ok(board) se encontrado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM boards WHERE id = ?", (board_id,))
            row = cursor.fetchone()

            if not row:
                return Result.err(f"Board {board_id} não encontrado")

            board = KanbanBoard(
                id=row["id"],
                name=row["name"],
                trello_board_id=row["trello_board_id"],
                trello_sync_enabled=bool(row["trello_sync_enabled"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

            return Result.ok(board)

        except Exception as e:
            return Result.err(f"Erro ao buscar board: {str(e)}")

    def list_boards(self) -> Result[list[KanbanBoard], str]:
        """
        Lista todos os boards.

        Returns:
            Result.ok(list[board]) com lista de boards
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM boards ORDER BY created_at DESC, id DESC")
            rows = cursor.fetchall()

            boards = [
                KanbanBoard(
                    id=row["id"],
                    name=row["name"],
                    trello_board_id=row["trello_board_id"],
                    trello_sync_enabled=bool(row["trello_sync_enabled"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                for row in rows
            ]

            return Result.ok(boards)

        except Exception as e:
            return Result.err(f"Erro ao listar boards: {str(e)}")

    # ==========================================================================
    # LISTS
    # ==========================================================================

    def create_list(self, list_obj: KanbanList) -> Result[KanbanList, str]:
        """Cria uma nova lista."""
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO lists (id, board_id, name, position, trello_list_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (list_obj.id, list_obj.board_id, list_obj.name, list_obj.position, list_obj.trello_list_id),
            )
            self._conn.commit()

            return Result.ok(list_obj)

        except Exception as e:
            return Result.err(f"Erro ao criar lista: {str(e)}")

    def get_list(self, list_id: str) -> Result[KanbanList, str]:
        """Busca uma lista por ID."""
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM lists WHERE id = ?", (list_id,))
            row = cursor.fetchone()

            if not row:
                return Result.err(f"Lista {list_id} não encontrada")

            list_obj = KanbanList(
                id=row["id"],
                board_id=row["board_id"],
                name=row["name"],
                position=row["position"],
                trello_list_id=row["trello_list_id"],
            )

            return Result.ok(list_obj)

        except Exception as e:
            return Result.err(f"Erro ao buscar lista: {str(e)}")

    def list_lists(self, board_id: str) -> Result[list[KanbanList], str]:
        """Lista todas as listas de um board."""
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM lists WHERE board_id = ? ORDER BY position ASC",
                (board_id,)
            )
            rows = cursor.fetchall()

            lists_obj = [
                KanbanList(
                    id=row["id"],
                    board_id=row["board_id"],
                    name=row["name"],
                    position=row["position"],
                    trello_list_id=row["trello_list_id"],
                )
                for row in rows
            ]

            return Result.ok(lists_obj)

        except Exception as e:
            return Result.err(f"Erro ao listar listas: {str(e)}")

    # ==========================================================================
    # CARDS (com suporte para Cards Vivos)
    # ==========================================================================

    def create_card(self, card: KanbanCard) -> Result[KanbanCard, str]:
        """
        Cria um novo card.

        Ao criar, se being_processed=True, position é automaticamente 0 (topo).
        Adiciona entrada no histórico do card.
        """
        try:
            cursor = self._conn.cursor()

            # Se está sendo processado, força position=0
            if card.being_processed:
                card = KanbanCard(**{**card.__dict__, "position": 0})

            cursor.execute(
                """
                INSERT INTO cards (
                    id, list_id, title, description, position, labels, due_date,
                    being_processed, processing_started_at, processing_job_id,
                    processing_step, processing_total_steps,
                    issue_number, issue_url, pr_url, trello_card_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card.id,
                    card.list_id,
                    card.title,
                    card.description,
                    card.position,
                    json.dumps(card.labels) if card.labels else None,
                    card.due_date.isoformat() if card.due_date else None,
                    card.being_processed,
                    card.processing_started_at.isoformat() if card.processing_started_at else None,
                    card.processing_job_id,
                    card.processing_step,
                    card.processing_total_steps,
                    card.issue_number,
                    card.issue_url,
                    card.pr_url,
                    card.trello_card_id,
                ),
            )
            self._conn.commit()

            # Adiciona entrada no histórico
            self.add_card_history(
                card_id=card.id,
                event="created",
                to_list_id=card.list_id,
                metadata={"title": card.title, "being_processed": card.being_processed}
            )

            return Result.ok(card)

        except Exception as e:
            return Result.err(f"Erro ao criar card: {str(e)}")

    def get_card(self, card_id: str) -> Result[KanbanCard, str]:
        """Busca um card por ID."""
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
            row = cursor.fetchone()

            if not row:
                return Result.err(f"Card {card_id} não encontrado")

            card = self._row_to_card(row)

            return Result.ok(card)

        except Exception as e:
            return Result.err(f"Erro ao buscar card: {str(e)}")

    def update_card(self, card_id: str, **updates) -> Result[KanbanCard, str]:
        """
        Atualiza campos específicos de um card.

        Adiciona entrada no histórico quando card é movido entre listas
        ou quando being_processed muda.

        Args:
            card_id: ID do card
            **updates: Campos a atualizar (being_processed, position, etc)

        Returns:
            Result.ok(card) com card atualizado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # Busca card atual
            card_result = self.get_card(card_id)
            if card_result.is_err:
                return card_result

            card = card_result.value

            # Rastreia mudanças relevantes para histórico
            from_list_id = card.list_id
            to_list_id = None
            was_processing = card.being_processed
            is_processing = None
            processing_job_id = None

            # Aplica atualizações
            for key, value in updates.items():
                if hasattr(card, key):
                    if key == "labels" and value is not None:
                        value = json.dumps(value) if isinstance(value, list) else value
                    elif key == "due_date" and value is not None:
                        value = value.isoformat() if isinstance(value, datetime) else value
                    elif key == "processing_started_at" and value is not None:
                        value = value.isoformat() if isinstance(value, datetime) else value

                    # Rastreia mudanças para histórico
                    if key == "list_id":
                        to_list_id = value
                    elif key == "being_processed":
                        is_processing = value
                    elif key == "processing_job_id":
                        processing_job_id = value

                    setattr(card, key, value)

            # Monta SQL UPDATE dinâmico
            set_clauses = []
            values = []
            for key in updates.keys():
                set_clauses.append(f"{key} = ?")
                values.append(updates[key])

            if set_clauses:
                sql = f"UPDATE cards SET {', '.join(set_clauses)} WHERE id = ?"
                values.append(card_id)

                cursor = self._conn.cursor()
                cursor.execute(sql, values)
                self._conn.commit()

            # Adiciona histórico para movimentos entre listas
            if to_list_id is not None and to_list_id != from_list_id:
                self.add_card_history(
                    card_id=card_id,
                    event="moved",
                    from_list_id=from_list_id,
                    to_list_id=to_list_id,
                    metadata={"moved_from": from_list_id, "moved_to": to_list_id}
                )

            # Adiciona histórico para mudança de being_processed
            if is_processing is not None and is_processing != was_processing:
                if is_processing:
                    # Card começou a ser processado
                    self.add_card_history(
                        card_id=card_id,
                        event="processing_started",
                        metadata={
                            "processing_job_id": processing_job_id,
                            "processing_step": card.processing_step,
                            "processing_total_steps": card.processing_total_steps,
                        }
                    )
                else:
                    # Card terminou de ser processado
                    self.add_card_history(
                        card_id=card_id,
                        event="processing_completed",
                        metadata={
                            "processing_step": card.processing_step,
                            "processing_total_steps": card.processing_total_steps,
                        }
                    )

            # Adiciona histórico para outras atualizações significativas
            if set_clauses and not to_list_id and is_processing is None:
                self.add_card_history(
                    card_id=card_id,
                    event="updated",
                    metadata={"updated_fields": list(updates.keys())}
                )

            return Result.ok(card)

        except Exception as e:
            return Result.err(f"Erro ao atualizar card: {str(e)}")

    def update_card_status(self, card_id: str, new_status: CardStatus) -> Result[KanbanCard, str]:
        """
        Move card para uma nova lista (status).

        Args:
            card_id: ID do card
            new_status: Novo status (CardStatus enum)

        Returns:
            Result.ok(card) com card atualizado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # Busca lista destino para o status
            list_result = self._get_list_for_status(new_status.value)
            if list_result.is_err:
                return list_result

            target_list_id = list_result.value

            # Atualiza card
            return self.update_card(card_id, list_id=target_list_id)

        except Exception as e:
            return Result.err(f"Erro ao atualizar status: {str(e)}")

    def list_cards(
        self,
        list_id: Optional[str] = None,
        being_processed: Optional[bool] = None,
    ) -> Result[list[KanbanCard], str]:
        """
        Lista cards com filtros opcionais.

        Args:
            list_id: Filtrar por lista específica
            being_processed: Filtrar por cards sendo processados

        Returns:
            Result.ok(list[card]) com cards ordenados (vivos primeiro)
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            cursor = self._conn.cursor()

            # Usa a VIEW que já ordena corretamente
            sql = "SELECT * FROM cards_ordered WHERE 1=1"
            params = []

            if list_id:
                sql += " AND list_id = ?"
                params.append(list_id)

            if being_processed is not None:
                sql += " AND being_processed = ?"
                params.append(being_processed)

            sql += " ORDER BY being_processed DESC, position ASC, created_at DESC"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            cards = [self._row_to_card(row) for row in rows]

            return Result.ok(cards)

        except Exception as e:
            return Result.err(f"Erro ao listar cards: {str(e)}")

    def delete_card(self, card_id: str) -> Result[None, str]:
        """
        Deleta um card.

        Adiciona entrada no histórico antes de deletar.
        """
        try:
            # Busca card antes de deletar para registrar no histórico
            card_result = self.get_card(card_id)

            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
            self._conn.commit()

            # Adiciona entrada no histórico
            if card_result.is_ok:
                self.add_card_history(
                    card_id=card_id,
                    event="deleted",
                    from_list_id=card_result.value.list_id,
                    metadata={
                        "title": card_result.value.title,
                        "deleted_at": datetime.utcnow().isoformat()
                    }
                )

            return Result.ok(None)

        except Exception as e:
            return Result.err(f"Erro ao deletar card: {str(e)}")

    # ==========================================================================
    # CARD HISTORY
    # ==========================================================================

    def add_card_history(
        self,
        card_id: str,
        event: str,
        from_list_id: Optional[str] = None,
        to_list_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Result[CardHistory, str]:
        """Adiciona entrada no histórico do card."""
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO card_history (card_id, event, from_list_id, to_list_id, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    card_id,
                    event,
                    from_list_id,
                    to_list_id,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            self._conn.commit()

            history = CardHistory(
                id=cursor.lastrowid,
                card_id=card_id,
                event=event,
                from_list_id=from_list_id,
                to_list_id=to_list_id,
                metadata=json.dumps(metadata) if metadata else None,
            )

            return Result.ok(history)

        except Exception as e:
            return Result.err(f"Erro ao adicionar histórico: {str(e)}")

    def get_card_history(self, card_id: str) -> Result[list[CardHistory], str]:
        """
        Busca histórico de mudanças de um card.

        Args:
            card_id: ID do card

        Returns:
            Result.ok(list[CardHistory]) com histórico ordenado por created_at DESC
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT * FROM card_history
                WHERE card_id = ?
                ORDER BY created_at DESC
                """,
                (card_id,)
            )
            rows = cursor.fetchall()

            history_list = [
                CardHistory(
                    id=row["id"],
                    card_id=row["card_id"],
                    event=row["event"],
                    from_list_id=row["from_list_id"],
                    to_list_id=row["to_list_id"],
                    metadata=row["metadata"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                )
                for row in rows
            ]

            return Result.ok(history_list)

        except Exception as e:
            return Result.err(f"Erro ao buscar histórico: {str(e)}")

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _row_to_card(self, row: sqlite3.Row) -> KanbanCard:
        """Converte uma linha do banco para objeto KanbanCard."""
        return KanbanCard(
            id=row["id"],
            list_id=row["list_id"],
            title=row["title"],
            description=row["description"],
            position=row["position"],
            labels=json.loads(row["labels"]) if row["labels"] else [],
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
            being_processed=bool(row["being_processed"]),
            processing_started_at=datetime.fromisoformat(row["processing_started_at"]) if row["processing_started_at"] else None,
            processing_job_id=row["processing_job_id"],
            processing_step=row["processing_step"],
            processing_total_steps=row["processing_total_steps"],
            issue_number=row["issue_number"],
            issue_url=row["issue_url"],
            pr_url=row["pr_url"],
            trello_card_id=row["trello_card_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _get_list_for_status(self, status: str) -> Result[str, str]:
        """
        Busca ID da lista correspondente a um status.

        Para compatibilidade com Trello, busca por nome da lista.
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id FROM lists WHERE name = ? LIMIT 1",
                (status,)
            )
            row = cursor.fetchone()

            if not row:
                # Cria lista automaticamente se não existe
                list_id = f"list-{status}"
                self.create_list(
                    KanbanList(
                        id=list_id,
                        board_id="default",
                        name=status,
                        position=0,
                    )
                )
                return Result.ok(list_id)

            return Result.ok(row["id"])

        except Exception as e:
            return Result.err(f"Erro ao buscar lista para status {status}: {str(e)}")
