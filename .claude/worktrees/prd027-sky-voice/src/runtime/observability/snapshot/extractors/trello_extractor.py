# -*- coding: utf-8 -*-
"""
Trello-Kanban State Extractor - Captura snapshots comparativos.

Captura estado de ambos os sistemas (Trello API + kanban.db) para
verificar sincronização e detectar dessincronizações.

DOC: runtime/observability/snapshot/extractors/trello_extractor.py
DOC: PRD026 - Integração Kanban com Fluxo Real
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from kernel import Result
from runtime.observability.snapshot.extractors.base import StateExtractor
from runtime.observability.snapshot.models import (
    Diff,
    DiffChange,
    DiffItem,
    DiffSummary,
    Snapshot,
    SnapshotMetadata,
    SnapshotStats,
    SnapshotSubject,
)


class TrelloExtractor(StateExtractor):
    """
    Extrator unificado Trello + Kanban.

    Captura snapshots comparativos de ambos os sistemas:
    - TRELLO: API externa (boards, listas, cards)
    - KANBAN: kanban.db local (boards, lists, cards, history)

    Objetivo: Verificar sincronização entre os dois sistemas.

    Uso típico::

        extractor = TrelloExtractor(api_key, api_token)
        snapshot = extractor.capture(
            target="board_id",  # Trello board_id
            kanban_db="workspace/core/data/kanban.db",
            depth=3
        )
    """

    @property
    def subject(self) -> SnapshotSubject:
        """Dominio deste extrator."""
        return SnapshotSubject.TRELLO

    def __init__(self, api_key: str, api_token: str):
        """
        Inicializa extrator.

        Args:
            api_key: API key do Trello.
            api_token: API token do Trello.
        """
        self.api_key = api_key
        self.api_token = api_token

    def capture(
        self,
        target: str,
        depth: int = 3,
        include_extensions: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        **options,
    ) -> Snapshot:
        """
        Captura snapshot unificado Trello + Kanban.

        Args:
            target: Board ID do Trello (e usado como identificador).
            depth: Profundidade da captura.
            kanban_db: Caminho para kanban.db (em options).
            include_extensions: Ignorado.
            exclude_patterns: Ignorado.
            **options: Opções adicionais.

        Returns:
            Snapshot com dados de ambos os sistemas lado a lado.
        """
        from runtime.observability.snapshot.capture import generate_snapshot_id

        board_id = target
        kanban_db_path = options.get("kanban_db", "workspace/core/data/kanban.db")
        snapshot_id = generate_snapshot_id(self.subject, board_id)

        # Captura Trello API
        trello_result = self._capture_trello(board_id, depth)
        if trello_result.is_err:
            return self._error_snapshot(snapshot_id, board_id, depth, trello_result.error)

        # Captura kanban.db
        kanban_result = self._capture_kanban(kanban_db_path, depth, board_id)
        if kanban_result.is_err:
            return self._error_snapshot(snapshot_id, board_id, depth, kanban_result.error)

        trello_data = trello_result.unwrap()
        kanban_data = kanban_result.unwrap()

        # Mescla dados em structure unificado
        return Snapshot(
            metadata=SnapshotMetadata(
                snapshot_id=snapshot_id,
                timestamp=datetime.utcnow(),
                subject=self.subject,
                target=f"board={board_id} | kanban={kanban_db_path}",
                depth=depth,
                tags=options.get("tags", {}),
            ),
            stats=SnapshotStats(
                total_files=len(trello_data.get("cards", [])),
                total_dirs=len(trello_data.get("lists", [])),
                total_size=0,
            ),
            structure={
                "trello": trello_data,
                "kanban": kanban_data,
            },
        )

    def _error_snapshot(self, snapshot_id: str, target: str, depth: int, error: str) -> Snapshot:
        """Retorna snapshot com erro."""
        return Snapshot(
            metadata=SnapshotMetadata(
                snapshot_id=snapshot_id,
                timestamp=datetime.utcnow(),
                subject=self.subject,
                target=target,
                depth=depth,
                tags={"error": error},
            ),
            stats=SnapshotStats(total_files=0, total_dirs=0, total_size=0),
        )

    def _capture_trello(self, board_id: str, depth: int) -> Result[dict, str]:
        """Captura dados da API do Trello."""
        try:
            # Busca board
            board_result = self._get_board(board_id)
            if board_result.is_err:
                return Result.err(board_result.error)

            # Busca listas
            lists_result = self._get_lists(board_id)
            if lists_result.is_err:
                return Result.err(lists_result.error)

            lists = lists_result.unwrap()

            # Busca cards (depth >= 2)
            cards = []
            if depth >= 2:
                cards_result = self._get_cards(board_id)
                if cards_result.is_ok:
                    cards = cards_result.unwrap()

                    # Enrich com nomes das listas
                    list_names = {lst["id"]: lst["name"] for lst in lists}
                    for card in cards:
                        card["list_name"] = list_names.get(card.get("idList"), "Unknown")

            return Result.ok({
                "id": board_id,
                "lists": lists,
                "cards": cards,
                "total_lists": len(lists),
                "total_cards": len(cards),
            })

        except Exception as e:
            return Result.err(f"Erro ao capturar Trello: {e}")

    def _capture_kanban(self, db_path: str, depth: int, board_id: str) -> Result[dict, str]:
        """Captura dados do kanban.db."""
        import sqlite3

        try:
            path = Path(db_path)
            if not path.exists():
                return Result.err(f"kanban.db não encontrado: {db_path}")

            conn = sqlite3.connect(str(path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            result = {
                "database_path": str(db_path),
                "board_id": board_id,
                "lists": [],
                "cards": [],
                "history": [],
                "total_lists": 0,
                "total_cards": 0,
            }

            # Listas
            cursor.execute("""
                SELECT id, name, position, trello_list_id
                FROM lists
                ORDER BY position
            """)
            for row in cursor.fetchall():
                result["lists"].append({
                    "id": row["id"],
                    "name": row["name"],
                    "position": row["position"],
                    "trello_list_id": row["trello_list_id"],
                })
            result["total_lists"] = len(result["lists"])

            # Cards
            if depth >= 2:
                cursor.execute("""
                    SELECT id, title, description, list_id, position,
                           being_processed, processing_job_id, trello_card_id,
                           issue_number, pr_url, created_at, updated_at
                    FROM cards
                    ORDER BY updated_at DESC
                """)
                for row in cursor.fetchall():
                    # Busca nome e trello_list_id da lista
                    list_name = "Unknown"
                    list_trello_id = None
                    for lst in result["lists"]:
                        if lst["id"] == row["list_id"]:
                            list_name = lst["name"]
                            list_trello_id = lst.get("trello_list_id")
                            break

                    result["cards"].append({
                        "id": row["id"],
                        "title": row["title"],
                        "description": row["description"],
                        "list_id": row["list_id"],
                        "list_name": list_name,
                        "trello_list_id": list_trello_id,
                        "position": row["position"],
                        "being_processed": bool(row["being_processed"]),
                        "processing_job_id": row["processing_job_id"],
                        "trello_card_id": row["trello_card_id"],
                        "issue_number": row["issue_number"],
                        "pr_url": row["pr_url"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    })
                result["total_cards"] = len(result["cards"])

            # Histórico (depth >= 3)
            if depth >= 3:
                cursor.execute("""
                    SELECT id, card_id, event, from_list_id, to_list_id,
                           metadata, created_at
                    FROM card_history
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                for row in cursor.fetchall():
                    result["history"].append({
                        "id": row["id"],
                        "card_id": row["card_id"],
                        "event": row["event"],
                        "from_list_id": row["from_list_id"],
                        "to_list_id": row["to_list_id"],
                        "metadata": row["metadata"],
                        "created_at": row["created_at"],
                    })

            conn.close()
            return Result.ok(result)

        except sqlite3.Error as e:
            return Result.err(f"Erro SQLite: {e}")
        except Exception as e:
            return Result.err(f"Erro ao capturar kanban.db: {e}")

    def compare(self, old: Snapshot, new: Snapshot) -> Diff:
        """
        Compara dois snapshots unificados Trello + Kanban.

        Detecta mudanças no Trello:
        - Cards adicionados
        - Cards removidos
        - Cards modificados (nome, descrição, lista)
        - Cards movidos entre listas

        Nota: Compara apenas dados do Trello. Para comparar sincronização
        Trello ↔ Kanban, use análise personalizada da estrutura unificada.

        Args:
            old: Snapshot anterior (antes).
            new: Snapshot posterior (depois).

        Returns:
            Diff com mudanças detectadas no Trello.
        """
        from runtime.observability.snapshot.diff import generate_diff_id

        # Extrai dados do Trello de ambos os snapshots
        old_trello = old.structure.get("trello", {})
        new_trello = new.structure.get("trello", {})

        old_cards = {
            c["id"]: c
            for c in old_trello.get("cards", [])
        }
        new_cards = {
            c["id"]: c
            for c in new_trello.get("cards", [])
        }

        old_card_ids = set(old_cards.keys())
        new_card_ids = set(new_cards.keys())

        added_ids = new_card_ids - old_card_ids
        removed_ids = old_card_ids - new_card_ids
        common_ids = old_card_ids & new_card_ids

        changes: list[DiffItem] = []

        # Cards adicionados
        for card_id in added_ids:
            card = new_cards[card_id]
            changes.append(
                DiffItem(
                    type=DiffChange.ADDED,
                    path=f"trello/cards/{card_id}",
                    size_delta=1,
                )
            )

        # Cards removidos
        for card_id in removed_ids:
            card = old_cards[card_id]
            changes.append(
                DiffItem(
                    type=DiffChange.REMOVED,
                    path=f"trello/cards/{card_id}",
                    size_delta=-1,
                )
            )

        # Cards modificados ou movidos
        for card_id in common_ids:
            old_card = old_cards[card_id]
            new_card = new_cards[card_id]

            # Verifica se foi movido (mudou de lista)
            if old_card.get("idList") != new_card.get("idList"):
                old_list = old_card.get("list_name", "?")
                new_list = new_card.get("list_name", "?")
                changes.append(
                    DiffItem(
                        type=DiffChange.MOVED,
                        path=f"trello/cards/{card_id}",
                        old_path=f"trello/lists/{old_list}/cards/{card_id}",
                        size_delta=0,
                    )
                )

            # Verifica outras modificações
            if (
                old_card.get("name") != new_card.get("name")
                or old_card.get("desc") != new_card.get("desc")
                or old_card.get("closed") != new_card.get("closed")
            ):
                changes.append(
                    DiffItem(
                        type=DiffChange.MODIFIED,
                        path=f"trello/cards/{card_id}",
                        size_delta=0,
                    )
                )

        return Diff(
            diff_id=generate_diff_id(),
            timestamp=datetime.utcnow(),
            old_snapshot_id=old.metadata.snapshot_id,
            new_snapshot_id=new.metadata.snapshot_id,
            subject=self.subject,
            summary=DiffSummary(
                added_files=len(added_ids),
                removed_files=len(removed_ids),
                modified_files=sum(1 for c in changes if c.type == DiffChange.MODIFIED),
                moved_files=sum(1 for c in changes if c.type == DiffChange.MOVED),
                added_dirs=0,
                removed_dirs=0,
                size_delta=len(added_ids) - len(removed_ids),
            ),
            changes=changes,
        )

    def _get_board(self, board_id: str) -> Result:
        """Busca board no Trello."""
        try:
            url = f"https://api.trello.com/1/boards/{board_id}"
            params = {
                "key": self.api_key,
                "token": self.api_token,
            }

            response = httpx.get(url, params=params, timeout=10.0)

            if response.status_code != 200:
                return Result.err(f"Erro ao buscar board: {response.status_code}")

            return Result.ok(response.json())
        except Exception as e:
            return Result.err(f"Exceção ao buscar board: {e}")

    def _get_lists(self, board_id: str) -> Result:
        """Busca listas do board."""
        try:
            url = f"https://api.trello.com/1/boards/{board_id}/lists"
            params = {
                "key": self.api_key,
                "token": self.api_token,
            }

            response = httpx.get(url, params=params, timeout=10.0)

            if response.status_code != 200:
                return Result.err(f"Erro ao buscar listas: {response.status_code}")

            return Result.ok(response.json())
        except Exception as e:
            return Result.err(f"Exceção ao buscar listas: {e}")

    def _get_cards(self, board_id: str) -> Result:
        """Busca cards do board."""
        try:
            url = f"https://api.trello.com/1/boards/{board_id}/cards"
            params = {
                "key": self.api_key,
                "token": self.api_token,
                "fields": "all",
                "actions": "commentCard",
            }

            response = httpx.get(url, params=params, timeout=10.0)

            if response.status_code != 200:
                return Result.err(f"Erro ao buscar cards: {response.status_code}")

            return Result.ok(response.json())
        except Exception as e:
            return Result.err(f"Exceção ao buscar cards: {e}")
