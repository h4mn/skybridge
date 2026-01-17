# -*- coding: utf-8 -*-
"""
Trello Adapter — Implementação concreta do KanbanPort.

Integração com a API REST do Trello para gestão de cards e boards.
"""

import logging
from datetime import datetime
from typing import Optional

import httpx

from core.kanban.domain import Board, Card, CardStatus, CardPriority, KanbanList
from core.kanban.ports import KanbanPort
from kernel import Result


logger = logging.getLogger(__name__)


# Trello API base URL
TRELLO_API_BASE = "https://api.trello.com/1"


class TrelloConfigError(Exception):
    """Erro de configuração do Trello (credenciais ausentes)."""


class TrelloAdapter(KanbanPort):
    """
    Adapter para integração com Trello API.

    Implementa KanbanPort usando a API REST do Trello.
    Requer TRELLO_API_KEY e TRELLO_API_TOKEN nas environment variables.
    """

    def __init__(self, api_key: str, api_token: str, board_id: str | None = None):
        """
        Inicializa adapter com credenciais do Trello.

        Args:
            api_key: API Key do Trello (https://trello.com/app-key)
            api_token: Token de autenticação do usuário
            board_id: ID do board padrão (opcional, para buscar listas por nome)
        """
        if not api_key or not api_token:
            raise TrelloConfigError(
                "TRELLO_API_KEY e TRELLO_API_TOKEN são obrigatórios. "
                "Obtenha em: https://trello.com/app-key"
            )

        self.api_key = api_key
        self.api_token = api_token
        self.board_id = board_id
        self._lists_cache: dict[str, str] = {}  # Cache de nome -> idList
        self._client = httpx.AsyncClient(
            base_url=TRELLO_API_BASE,
            params={
                "key": api_key,
                "token": api_token,
            },
            timeout=30.0,
        )

    async def _close(self):
        """Fecha o cliente HTTP."""
        await self._client.aclose()

    async def _get_list_id(self, list_name: str, board_id: str | None = None) -> Result[str, str]:
        """
        Busca o ID de uma lista pelo nome no board.

        Usa cache para evitar múltiplas chamadas à API.

        Args:
            list_name: Nome da lista (ex: "To Do", "In Progress", "Done")
            board_id: ID do board (opcional, usa self.board_id se não fornecido)

        Returns:
            Result com o ID da lista ou mensagem de erro.
        """
        # Verifica cache primeiro
        if list_name in self._lists_cache:
            return Result.ok(self._lists_cache[list_name])

        # Usa board_id fornecido ou o padrão
        target_board = board_id or self.board_id
        if not target_board:
            return Result.err(
                "board_id não fornecido. Configure no adapter ou passe como parâmetro."
            )

        try:
            # Busca listas do board
            response = await self._client.get(f"/boards/{target_board}/lists")
            response.raise_for_status()
            lists_data = response.json()

            # Procura lista pelo nome
            for lst in lists_data:
                if lst.get("name", "").lower() == list_name.lower():
                    list_id = lst["id"]
                    # Salva no cache
                    self._lists_cache[list_name] = list_id
                    logger.info(f"Lista encontrada: {list_name} -> {list_id}")
                    return Result.ok(list_id)

            # Lista não encontrada
            available = [lst.get("name", "") for lst in lists_data]
            return Result.err(
                f"Lista '{list_name}' não encontrada. Disponíveis: {available}"
            )

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao buscar lista {list_name}: {e}")
            return Result.err(f"Erro ao buscar lista: {str(e)}")

    async def list_boards(self) -> Result[list[dict], str]:
        """
        Lista todos os boards acessíveis pelo usuário.

        Returns:
            Result com lista de boards (cada board é um dict com id, name, url)
        """
        try:
            response = await self._client.get("/members/me/boards")
            response.raise_for_status()
            boards = response.json()

            logger.info(f"Encontrados {len(boards)} boards")
            return Result.ok(boards)

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao listar boards: {e}")
            return Result.err(f"Erro ao listar boards: {str(e)}")

    async def get_card(self, card_id: str) -> Result[Card, str]:
        """
        Busca um card por ID.

        GET /1/cards/{id}
        """
        try:
            response = await self._client.get(f"/cards/{card_id}")
            response.raise_for_status()
            data = response.json()

            return Result.ok(self._parse_card(data))

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return Result.err(f"Card não encontrado: {card_id}")
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")

        except Exception as e:
            logger.error(f"Erro ao buscar card {card_id}: {e}")
            return Result.err(f"Erro ao buscar card: {str(e)}")

    async def create_card(
        self,
        title: str,
        description: Optional[str] = None,
        list_name: str = "To Do",
        labels: Optional[list[str]] = None,
        due_date: Optional[str] = None,
        board_id: str | None = None,
    ) -> Result[Card, str]:
        """
        Cria um novo card.

        POST /1/cards

        Args:
            title: Título do card
            description: Descrição do card (opcional)
            list_name: Nome da lista onde criar (padrão: "To Do")
            labels: Labels do card (opcional)
            due_date: Data de vencimento (opcional)
            board_id: ID do board (opcional, usa self.board_id se não fornecido)
        """
        try:
            # Busca o ID da lista pelo nome
            list_id_result = await self._get_list_id(list_name, board_id)
            if list_id_result.is_err:
                return Result.err(list_id_result.error)

            list_id = list_id_result.unwrap()

            # Cria o card com o idList correto
            payload = {
                "name": title,
                "desc": description or "",
                "idList": list_id,
            }

            if due_date:
                payload["due"] = due_date

            if labels:
                payload["labels"] = ",".join(labels)

            response = await self._client.post("/cards", json=payload)
            response.raise_for_status()
            data = response.json()

            logger.info(f"Card criado: {data['id']} - {title} (lista: {list_name})")

            return Result.ok(self._parse_card(data))

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")

        except Exception as e:
            logger.error(f"Erro ao criar card: {e}")
            return Result.err(f"Erro ao criar card: {str(e)}")

    async def update_card_status(
        self,
        card_id: str,
        status: CardStatus,
        correlation_id: Optional[str] = None,
    ) -> Result[Card, str]:
        """
        Atualiza o status de um card movendo-o entre listas.

        PUT /1/cards/{id}
        """
        try:
            # Mapear CardStatus para idList do Trello
            # TODO: Implementar cache de listas para evitar múltiplas chamadas
            # Por enquanto, apenas adiciona comentário com novo status

            comment = f"Status atualizado para: {status.value}"
            if correlation_id:
                comment += f"\n\nCorrelation ID: {correlation_id}"

            await self.add_card_comment(card_id, comment)

            # Buscar card atualizado
            return await self.get_card(card_id)

        except Exception as e:
            logger.error(f"Erro ao atualizar card {card_id}: {e}")
            return Result.err(f"Erro ao atualizar card: {str(e)}")

    async def add_card_comment(
        self,
        card_id: str,
        comment: str,
    ) -> Result[None, str]:
        """
        Adiciona um comentário ao card.

        POST /1/cards/{id}/actions/comments
        """
        try:
            response = await self._client.post(
                f"/cards/{card_id}/actions/comments",
                params={"text": comment},
            )
            response.raise_for_status()

            logger.info(f"Comentário adicionado ao card {card_id}")
            return Result.ok(None)

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")

        except Exception as e:
            logger.error(f"Erro ao adicionar comentário: {e}")
            return Result.err(f"Erro ao adicionar comentário: {str(e)}")

    async def get_board(self, board_id: str) -> Result[Board, str]:
        """
        Busca um board por ID.

        GET /1/boards/{id}
        """
        try:
            response = await self._client.get(f"/boards/{board_id}")
            response.raise_for_status()
            data = response.json()

            return Result.ok(
                Board(
                    id=data["id"],
                    name=data["name"],
                    url=data["url"],
                    external_source="trello",
                )
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return Result.err(f"Board não encontrado: {board_id}")
            return Result.err(f"Erro HTTP {e.response.status_code}")

        except Exception as e:
            logger.error(f"Erro ao buscar board {board_id}: {e}")
            return Result.err(f"Erro ao buscar board: {str(e)}")

    async def list_cards(
        self,
        board_id: Optional[str] = None,
        list_name: Optional[str] = None,
        label: Optional[str] = None,
    ) -> Result[list[Card], str]:
        """
        Lista cards com filtros opcionais.

        GET /1/boards/{id}/cards ou GET /1/lists/{id}/cards
        """
        try:
            cards_data = []

            if board_id:
                response = await self._client.get(f"/boards/{board_id}/cards")
                response.raise_for_status()
                cards_data = response.json()
            elif list_name:
                # TODO: Implementar busca de lista por nome
                return Result.err("Busca por list_name ainda não implementada")

            cards = [self._parse_card(card) for card in cards_data]

            # Filtrar por label se especificado
            if label:
                cards = [c for c in cards if label in (c.labels or [])]

            logger.info(f"Listados {len(cards)} cards")
            return Result.ok(cards)

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}")

        except Exception as e:
            logger.error(f"Erro ao listar cards: {e}")
            return Result.err(f"Erro ao listar cards: {str(e)}")

    def _parse_card(self, data: dict) -> Card:
        """
        Converte resposta da API Trello para entidade Card.

        Args:
            data: Dicionário com dados da API do Trello

        Returns:
            Card instanciado
        """
        # Mapear status Trello para CardStatus
        status = self._map_status(data.get("idList", ""))
        labels = [label["name"] for label in data.get("labels", []) if label.get("name")]

        return Card(
            id=data["id"],
            title=data["name"],
            description=data.get("desc"),
            status=status,
            labels=labels,
            due_date=datetime.fromisoformat(data["due"]) if data.get("due") else None,
            url=data["url"],
            external_source="trello",
        )

    def _map_status(self, trello_list_id: str) -> CardStatus:
        """
        Mapeia ID da lista Trello para CardStatus.

        TODO: Implementar cache de listas para mapeamento correto.
        Por enquanto, assume defaults baseados em posições comuns.
        """
        # Mapeamento simplificado - TODO: fazer lookup real de listas
        return CardStatus.TODO


def create_trello_adapter(api_key: str, api_token: str) -> TrelloAdapter:
    """
    Factory para criar TrelloAdapter configurado.

    Args:
        api_key: Trello API Key
        api_token: Trello API Token

    Returns:
        TrelloAdapter instanciado

    Raises:
        TrelloConfigError: Se credenciais não forem fornecidas
    """
    return TrelloAdapter(api_key=api_key, api_token=api_token)
