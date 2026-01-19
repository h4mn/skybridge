# -*- coding: utf-8 -*-
"""
Trello State Extractor - Captura snapshots de boards/listas/cards do Trello.

Permite tirar "fotos" antes e depois de operações, facilitando
verificação de mudanças e debug de demos.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

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
    Extrator de estado do Trello.

    Captura snapshots de boards, listas e cards para comparar
    antes/depois de operações.

    Uso típico em demos::

        snapshot_before = extractor.capture(target=board_id)
        # ... executa operação no Trello ...
        snapshot_after = extractor.capture(target=board_id)
        diff = extractor.compare(snapshot_before, snapshot_after)
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
        from infra.kanban.adapters.trello_adapter import TrelloAdapter

        self.adapter = TrelloAdapter(api_key, api_token, "")

    def capture(
        self,
        target: str,
        depth: int = 3,
        include_extensions: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        **options,
    ) -> Snapshot:
        """
        Captura snapshot do Trello.

        Args:
            target: Board ID do Trello.
            depth: Profundidade (1=board, 2=board+listas, 3=board+listas+cards).
            include_extensions: Ignorado (compatibilidade com interface).
            exclude_patterns: Ignorado (compatibilidade com interface).
            **options: Opções adicionais (cards_since, filter_labels, etc).

        Returns:
            Snapshot com dados capturados.
        """
        from runtime.observability.snapshot.capture import generate_snapshot_id
        from infra.kanban.adapters.git_extractor import get_git_info

        board_id = target
        snapshot_id = generate_snapshot_id(self.subject, board_id)

        # Captura board
        board_result = self._capture_board(board_id, depth, **options)

        if board_result.is_err:
            # Retorna snapshot vazio com erro
            return Snapshot(
                metadata=SnapshotMetadata(
                    snapshot_id=snapshot_id,
                    timestamp=datetime.utcnow(),
                    subject=self.subject,
                    target=board_id,
                    depth=depth,
                    tags={"error": board_result.error},
                ),
                stats=SnapshotStats(
                    total_files=0,
                    total_dirs=0,
                    total_size=0,
                ),
            )

        board_data = board_result.unwrap()

        # Git info
        git_info = get_git_info()

        return Snapshot(
            metadata=SnapshotMetadata(
                snapshot_id=snapshot_id,
                timestamp=datetime.utcnow(),
                subject=self.subject,
                target=board_id,
                depth=depth,
                git_hash=git_info.get("hash"),
                git_branch=git_info.get("branch"),
                tags=options.get("tags", {}),
            ),
            stats=SnapshotStats(
                total_files=board_data.get("total_cards", 0),
                total_dirs=board_data.get("total_lists", 0),
                total_size=0,  # Trello não tem tamanho
            ),
            structure=board_data,
        )

    def compare(self, old: Snapshot, new: Snapshot) -> Diff:
        """
        Compara dois snapshots do Trello.

        Detecta:
        - Cards adicionados
        - Cards removidos
        - Cards modificados (nome, descrição, lista)
        - Cards movidos entre listas

        Args:
            old: Snapshot anterior (antes).
            new: Snapshot posterior (depois).

        Returns:
            Diff com mudanças detectadas.
        """
        from runtime.observability.snapshot.diff import generate_diff_id

        old_cards = {
            c["id"]: c
            for c in old.structure.get("cards", [])
        }
        new_cards = {
            c["id"]: c
            for c in new.structure.get("cards", [])
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
                    path=f"cards/{card_id}",
                    size_delta=1,
                )
            )

        # Cards removidos
        for card_id in removed_ids:
            card = old_cards[card_id]
            changes.append(
                DiffItem(
                    type=DiffChange.REMOVED,
                    path=f"cards/{card_id}",
                    size_delta=-1,
                )
            )

        # Cards modificados ou movidos
        for card_id in common_ids:
            old_card = old_cards[card_id]
            new_card = new_cards[card_id]

            # Verifica se foi movido (mudou de lista)
            if old_card.get("id_list") != new_card.get("id_list"):
                old_list = old_card.get("list_name", "?")
                new_list = new_card.get("list_name", "?")
                changes.append(
                    DiffItem(
                        type=DiffChange.MOVED,
                        path=f"cards/{card_id}",
                        old_path=f"lists/{old_list}/cards/{card_id}",
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
                        path=f"cards/{card_id}",
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

    def _capture_board(self, board_id: str, depth: int, **options) -> Result[dict, str]:
        """
        Captura dados do board.

        Args:
            board_id: ID do board.
            depth: Profundidade da captura.
            **options: Opções adicionais.

        Returns:
            Dados do board com listas e cards.
        """
        # Busca board
        board_result = self._get_board(board_id)
        if board_result.is_err:
            return Result.err(board_result.error)

        board = board_result.unwrap()

        result = {
            "id": board["id"],
            "name": board["name"],
            "url": board["url"],
            "lists": [],
            "cards": [],
            "total_lists": 0,
            "total_cards": 0,
        }

        # Busca listas
        lists_result = self._get_lists(board_id)
        if lists_result.is_ok:
            lists = lists_result.unwrap()
            result["lists"] = lists
            result["total_lists"] = len(lists)

        # Busca cards (depth >= 2)
        if depth >= 2:
            cards_result = self._get_cards(board_id)
            if cards_result.is_ok:
                cards = cards_result.unwrap()
                result["cards"] = cards
                result["total_cards"] = len(cards)

                # Enrich com nomes das listas
                list_names = {lst["id"]: lst["name"] for lst in result["lists"]}
                for card in result["cards"]:
                    card["list_name"] = list_names.get(card.get("idList"), "Unknown")

        return Result.ok(result)

    def _get_board(self, board_id: str) -> Result:
        """Busca board no Trello."""
        import httpx

        try:
            url = f"https://api.trello.com/1/boards/{board_id}"
            params = {
                "key": self.adapter.api_key,
                "token": self.adapter.api_token,
            }

            response = httpx.get(url, params=params, timeout=10.0)

            if response.status_code != 200:
                return Result.err(f"Erro ao buscar board: {response.status_code}")

            return Result.ok(response.json())
        except Exception as e:
            return Result.err(f"Exceção ao buscar board: {e}")

    def _get_lists(self, board_id: str) -> Result:
        """Busca listas do board."""
        import httpx

        try:
            url = f"https://api.trello.com/1/boards/{board_id}/lists"
            params = {
                "key": self.adapter.api_key,
                "token": self.adapter.api_token,
            }

            response = httpx.get(url, params=params, timeout=10.0)

            if response.status_code != 200:
                return Result.err(f"Erro ao buscar listas: {response.status_code}")

            return Result.ok(response.json())
        except Exception as e:
            return Result.err(f"Exceção ao buscar listas: {e}")

    def _get_cards(self, board_id: str) -> Result:
        """Busca cards do board."""
        import httpx

        try:
            url = f"https://api.trello.com/1/boards/{board_id}/cards"
            params = {
                "key": self.adapter.api_key,
                "token": self.adapter.api_token,
                "fields": "all",
                "actions": "commentCard",
            }

            response = httpx.get(url, params=params, timeout=10.0)

            if response.status_code != 200:
                return Result.err(f"Erro ao buscar cards: {response.status_code}")

            return Result.ok(response.json())
        except Exception as e:
            return Result.err(f"Exceção ao buscar cards: {e}")
