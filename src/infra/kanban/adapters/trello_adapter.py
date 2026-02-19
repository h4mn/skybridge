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

        NOTA: Cache removido por não ser necessário - volume de operações não justifica otimização.

        Args:
            list_name: Nome da lista (ex: "To Do", "In Progress", "Done")
            board_id: ID do board (opcional, usa self.board_id se não fornecido)

        Returns:
            Result com o ID da lista ou mensagem de erro.
        """
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
        target_list_id: Optional[str] = None,
    ) -> Result[Card, str]:
        """
        Atualiza o status de um card movendo-o entre listas.

        PUT /1/cards/{id}

        Args:
            card_id: ID do card no Trello
            status: Novo status (CardStatus enum)
            correlation_id: ID de correlação para rastreamento
            target_list_id: ID da lista no Trello (se fornecido, usa diretamente,
                            sem buscar por nome - RECOMENDADO para evitar problemas
                            com nomes que têm emojis ou mudanças)

        NOTA: Sempre que possível, passe target_list_id diretamente para
        evitar dependência de nomes de listas que podem mudar.
        """
        try:
            # Se target_list_id fornecido, usa diretamente (RECOMENDADO)
            if target_list_id:
                logger.info(f"Usando target_list_id direto: {target_list_id}")
                list_id = target_list_id
            else:
                # Fallback: mapeamento CardStatus → nome da lista (EVITAR USAR)
                # DOC: Este mapeamento é frágil pois depende de nomes com emojis
                status_to_list_name = {
                    CardStatus.BACKLOG: "🧠 Brainstorm",
                    CardStatus.TODO: "📋 A Fazer",
                    CardStatus.IN_PROGRESS: "🚧 Em Andamento",
                    CardStatus.REVIEW: "👀 Em Revisão",
                    CardStatus.DONE: "🚀 Publicar",
                    CardStatus.BLOCKED: "📥 Issues",
                    CardStatus.CHALLENGE: "🧠 Brainstorm",
                }

                list_name = status_to_list_name.get(status)
                if not list_name:
                    return Result.err(f"Status {status.value} não mapeado para lista Trello")

                # Busca ID da lista de destino
                list_id_result = await self._get_list_id(list_name)
                if list_id_result.is_err:
                    return Result.err(f"Erro ao buscar lista '{list_name}': {list_id_result.error}")

                list_id = list_id_result.unwrap()

            # Move o card atualizando idList
            response = await self._client.put(
                f"/cards/{card_id}",
                json={"idList": list_id}
            )
            response.raise_for_status()

            success_msg = f"Card {card_id} movido para lista {list_id} (status={status.value})"
            logger.info(success_msg)
            print(f"[TRELLO_ADAPTER] ✅ {success_msg}")  # Print explícito

            # Buscar card atualizado
            return await self.get_card(card_id)

        except httpx.HTTPStatusError as e:
            error_msg = f"Erro HTTP {e.response.status_code} ao mover card {card_id}: {e.response.text[:200]}"
            logger.error(error_msg)
            print(f"[TRELLO_ADAPTER] ❌ {error_msg}")  # Print explícito para garantir visibilidade
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text[:200]}")

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

        NOTA: Busca listas do board para popular o nome da lista em cada card,
        pois a API de cards retorna apenas idList sem o nome.
        """
        try:
            cards_data = []
            target_board = board_id or self.board_id

            if target_board:
                response = await self._client.get(f"/boards/{target_board}/cards")
                response.raise_for_status()
                cards_data = response.json()

                # Busca listas do board para mapear idList → nome
                lists_response = await self._client.get(f"/boards/{target_board}/lists")
                lists_response.raise_for_status()
                lists_data = lists_response.json()

                # Cria mapeamento idList → nome da lista
                list_names = {lst["id"]: lst.get("name", "") for lst in lists_data}

                # Popula o campo "list" em cada card com o nome da lista
                for card_data in cards_data:
                    card_data["list"] = {"name": list_names.get(card_data.get("idList", ""), "Unknown")}

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

        REGRA DE OURO: NÃO EXISTE PADRÃO.
        - Lista reconhecida → CardStatus correspondente
        - Lista NÃO reconhecida → CardStatus.UNKNOWN (requer atenção manual)

        NOTA: UNKNOWN é usado para marcar cards que precisam de correção
        manual, ao invés de usar um padrão silencioso que mascara problemas.

        DOC: Listas válidas são configuradas via KanbanListsConfig. Se uma
        lista não reconhecida for encontrada, isso indica uma desincronização
        entre Trello e configuração local.

        Args:
            data: Dicionário com dados da API do Trello

        Returns:
            Card instanciado (status pode ser UNKNOWN se lista não reconhecida)
        """
        # Determina status baseado no nome da lista (se disponível)
        status = None  # Sem padrão - determinado explicitamente
        list_match_found = False

        if "list" in data and isinstance(data["list"], dict):
            list_name = data["list"].get("name", "")
            list_name_lower = list_name.lower()

            # Mapeamento de padrões de nome de lista → CardStatus
            if "brainstorm" in list_name_lower:
                status = CardStatus.BACKLOG
                list_match_found = True
            elif "a fazer" in list_name_lower or "todo" in list_name_lower:
                status = CardStatus.TODO
                list_match_found = True
            elif "em andamento" in list_name_lower or "progress" in list_name_lower:
                status = CardStatus.IN_PROGRESS
                list_match_found = True
            elif "em revisão" in list_name_lower or "review" in list_name_lower:
                status = CardStatus.REVIEW
                list_match_found = True
            elif "publicar" in list_name_lower or "done" in list_name_lower or "pronto" in list_name_lower:
                status = CardStatus.DONE
                list_match_found = True
            elif "issues" in list_name_lower:
                status = CardStatus.BLOCKED
                list_match_found = True

            # Se lista existe mas não foi reconhecida
            if not list_match_found and list_name:
                logger.warning(
                    f"[TRELLO_ADAPTER] ⚠️ Lista não reconhecida: '{list_name}'. "
                    f"ERRO: Lista não mapeada para CardStatus. "
                    f"Usando CardStatus.UNKNOWN (requer atenção manual). "
                    f"Verifique KanbanListsConfig para listas válidas."
                )
                # Lista existe mas não reconhecida - UNKNOWN requer atenção manual
                status = CardStatus.UNKNOWN
            elif not list_name:
                logger.warning(
                    f"[TRELLO_ADAPTER] ⚠️ Campo 'list.name' vazio no card {data.get('id')}. "
                    f"Usando CardStatus.UNKNOWN (requer atenção manual)."
                )
                status = CardStatus.UNKNOWN
        else:
            # Campo 'list' ausente completamente
            logger.warning(
                f"[TRELLO_ADAPTER] ⚠️ Campo 'list' ausente no card {data.get('id')}. "
                f"Usando CardStatus.UNKNOWN (requer atenção manual). "
                f"Verifique se a API do Trello retornou dados completos."
            )
            status = CardStatus.UNKNOWN

        labels = [label["name"] for label in data.get("labels", []) if label.get("name")]

        # Parse timestamps da API Trello
        # dateLastActivity é o último update do card (sempre UTC)
        updated_at = None
        if data.get("dateLastActivity"):
            try:
                # Trello retorna UTC (termina com Z)
                dt = datetime.fromisoformat(data["dateLastActivity"].replace("Z", "+00:00"))
                # Converte para UTC naive (remove timezone mas mantém valor UTC)
                # Isso garante que comparações funcionam mesmo com timezone diferente
                updated_at = dt.replace(tzinfo=None)
            except (ValueError, AttributeError):
                pass

        return Card(
            id=data["id"],
            title=data["name"],
            description=data.get("desc"),
            status=status,
            labels=labels,
            due_date=datetime.fromisoformat(data["due"]).replace(tzinfo=None) if data.get("due") else None,
            url=data["url"],
            external_source="trello",
            updated_at=updated_at,
        )

    async def auto_configure_lists(
        self,
        list_names: list[str],
        list_colors: dict[str, str] | None = None,
        board_id: str | None = None,
    ) -> Result[dict[str, dict], str]:
        """
        Verifica e cria listas no board se não existirem.

        Args:
            list_names: Lista de nomes das listas Kanban em ordem
            list_colors: Mapeamento opcional de nome da lista → cor (hex)
            board_id: ID do board (usa self.board_id se não fornecido)

        Returns:
            Result com dict contendo infos das listas criadas/verificadas:
            {
                "list_name": {"id": "list_id", "color": "#hex", "created": bool}
            }
        """
        target_board = board_id or self.board_id
        if not target_board:
            return Result.err("board_id não fornecido")

        # Busca listas existentes
        try:
            response = await self._client.get(f"/boards/{target_board}/lists")
            response.raise_for_status()
            existing_lists = response.json()

            # Mapeia nome → id das listas existentes
            existing_by_name = {
                lst["name"]: lst["id"]
                for lst in existing_lists
                if not lst.get("closed")  # Ignora listas arquivadas
            }

            logger.info(f"Listas existentes: {list(existing_by_name.keys())}")

            results: dict[str, dict] = {}

            # Verifica/cria cada lista
            for list_name in list_names:
                if list_name in existing_by_name:
                    # Lista já existe
                    results[list_name] = {
                        "id": existing_by_name[list_name],
                        "color": list_colors.get(list_name) if list_colors else None,
                        "created": False,
                    }
                    logger.info(f"✓ Lista já existe: {list_name}")
                else:
                    # Cria lista
                    color = list_colors.get(list_name) if list_colors else None
                    create_result = await self.create_list_with_color(
                        list_name=list_name,
                        color=color,
                        board_id=target_board,
                    )

                    if create_result.is_err:
                        return Result.err(
                            f"Erro ao criar lista '{list_name}': {create_result.error}"
                        )

                    list_data = create_result.unwrap()
                    results[list_name] = {
                        "id": list_data["id"],
                        "color": color,
                        "created": True,
                    }
                    logger.info(f"✓ Lista criada: {list_name}")

            return Result.ok(results)

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao configurar listas: {e}")
            return Result.err(f"Erro ao configurar listas: {str(e)}")

    async def create_list_with_color(
        self,
        list_name: str,
        color: str | None = None,
        board_id: str | None = None,
        pos: str | None = None,
    ) -> Result[dict, str]:
        """
        Cria uma lista com cor específica (via subscribed).

        Nota: Trello API não suporta cores de lista diretamente.
        A cor é aplicada via subscrição à lista (muda a cor de fundo no UI).

        Args:
            list_name: Nome da lista
            color: Cor em hex (ex: "#0077BE") - usada para subscrição
            board_id: ID do board (usa self.board_id se não fornecido)
            pos: Posição da lista ("bottom", "top", ou número)

        Returns:
            Result com dict contendo id e name da lista criada
        """
        target_board = board_id or self.board_id
        if not target_board:
            return Result.err("board_id não fornecido")

        try:
            payload = {"name": list_name, "idBoard": target_board}

            if pos:
                payload["pos"] = pos
            else:
                # Coloca no final por padrão
                payload["pos"] = "bottom"

            # Cria a lista
            response = await self._client.post("/lists", json=payload)
            response.raise_for_status()
            list_data = response.json()

            list_id = list_data["id"]

            # Se cor fornecida, tenta aplicar via subscrição
            # (muda cor de fundo da lista no UI)
            if color:
                await self._client.put(
                    f"/lists/{list_id}",
                    json={"subscribed": True},
                )
                logger.info(f"Lista '{list_name}' criada com cor {color}")

            return Result.ok({"id": list_id, "name": list_name})

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao criar lista '{list_name}': {e}")
            return Result.err(f"Erro ao criar lista: {str(e)}")

    async def move_card_to_list(
        self,
        card_id: str,
        target_list_name: str,
        board_id: str | None = None,
    ) -> Result[None, str]:
        """
        Move um card para outra lista.

        Args:
            card_id: ID do card a mover
            target_list_name: Nome da lista de destino
            board_id: ID do board (usa self.board_id se não fornecido)

        Returns:
            Result OK se sucesso, erro se falhar
        """
        try:
            # Busca ID da lista de destino
            list_id_result = await self._get_list_id(target_list_name, board_id)
            if list_id_result.is_err:
                return Result.err(list_id_result.error)

            target_list_id = list_id_result.unwrap()

            # Move o card atualizando idList
            response = await self._client.put(
                f"/cards/{card_id}",
                json={"idList": target_list_id},
            )
            response.raise_for_status()

            logger.info(f"Card {card_id} movido para '{target_list_name}'")
            return Result.ok(None)

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao mover card {card_id}: {e}")
            return Result.err(f"Erro ao mover card: {str(e)}")

    async def get_or_create_label(
        self,
        label_name: str,
        color: str,
        board_id: str | None = None,
    ) -> Result[str, str]:
        """
        Busca ou cria um label no board.

        Args:
            label_name: Nome do label
            color: Cor do label (red, orange, yellow, green, blue, purple, pink, black, sky, lime)
            board_id: ID do board (usa self.board_id se não fornecido)

        Returns:
            Result com ID do label
        """
        target_board = board_id or self.board_id
        if not target_board:
            return Result.err("board_id não fornecido")

        try:
            # Busca labels existentes
            response = await self._client.get(f"/boards/{target_board}/labels")
            response.raise_for_status()
            labels = response.json()

            # Procura label com mesmo nome
            for label in labels:
                if label.get("name", "").lower() == label_name.lower():
                    logger.info(f"Label já existe: {label_name}")
                    return Result.ok(label["id"])

            # Cria novo label
            response = await self._client.post(
                f"/boards/{target_board}/labels",
                json={
                    "name": label_name,
                    "color": color,
                },
            )
            response.raise_for_status()
            label_data = response.json()

            logger.info(f"Label criado: {label_name} ({color})")
            return Result.ok(label_data["id"])

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao buscar/criar label '{label_name}': {e}")
            return Result.err(f"Erro ao buscar/criar label: {str(e)}")

    async def add_label_to_card(
        self,
        card_id: str,
        label_id: str,
    ) -> Result[None, str]:
        """
        Adiciona um label a um card.

        Args:
            card_id: ID do card
            label_id: ID do label a adicionar

        Returns:
            Result OK se sucesso, erro se falhar
        """
        try:
            # Primeiro busca os labels atuais do card
            response = await self._client.get(f"/cards/{card_id}")
            response.raise_for_status()
            card_data = response.json()

            # Obtém lista atual de labels (idLabels)
            current_labels = card_data.get("idLabels", [])

            # Adiciona o novo label se ainda não estiver presente
            if label_id not in current_labels:
                current_labels.append(label_id)

                # Atualiza o card com a nova lista de labels
                response = await self._client.put(
                    f"/cards/{card_id}",
                    json={"idLabels": current_labels},
                )
                response.raise_for_status()

                logger.info(f"Label {label_id} adicionado ao card {card_id}")
            else:
                logger.debug(f"Label {label_id} já está no card {card_id}")

            return Result.ok(None)

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao adicionar label {label_id} ao card {card_id}: {e}")
            return Result.err(f"Erro ao adicionar label: {str(e)}")

    async def create_webhook(
        self,
        callback_url: str,
        description: str = "Skybridge Trello Webhook",
        id_model: str | None = None,
    ) -> Result[dict, str]:
        """
        Cria um webhook no Trello para monitorar mudanças em um model.

        Args:
            callback_url: URL pública que receberá os webhooks (ex: Ngrok URL)
            description: Descrição do webhook
            id_model: ID do model a monitorar (board, card, etc.) - usa self.board_id se não fornecido

        Returns:
            Result com dados do webhook criado (id, description, callbackURL, etc.)

        Example:
            >>> result = await adapter.create_webhook(
            ...     callback_url="https://seu-ngrok-url.webhooks/trello",
            ...     id_model="board123"
            ... )
        """
        target_model = id_model or self.board_id
        if not target_model:
            return Result.err("id_model não fornecido e board_id não configurado")

        try:
            # Verifica se callback URL está acessível (Trello faz HEAD request)
            # NOTA: Em dev com Ngrok, isso deve funcionar
            logger.info(f"Criando webhook para model {target_model} → {callback_url}")

            # POST /1/tokens/{token}/webhooks
            webhook_url = f"/tokens/{self.api_token}/webhooks"
            payload = {
                "description": description,
                "callbackURL": callback_url,
                "idModel": target_model,
            }

            response = await self._client.post(webhook_url, json=payload)
            response.raise_for_status()
            webhook_data = response.json()

            logger.info(f"Webhook criado: {webhook_data['id']}")
            return Result.ok(webhook_data)

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else str(e)
            return Result.err(
                f"Erro HTTP {e.response.status_code} ao criar webhook: {error_detail}"
            )
        except Exception as e:
            logger.error(f"Erro ao criar webhook: {e}")
            return Result.err(f"Erro ao criar webhook: {str(e)}")

    async def list_webhooks(self) -> Result[list[dict], str]:
        """
        Lista todos os webhooks criados pelo token atual.

        Returns:
            Result com lista de webhooks
        """
        try:
            response = await self._client.get(f"/tokens/{self.api_token}/webhooks")
            response.raise_for_status()
            webhooks = response.json()

            logger.info(f"{len(webhooks)} webhook(s) encontrado(s)")
            return Result.ok(webhooks)

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao listar webhooks: {e}")
            return Result.err(f"Erro ao listar webhooks: {str(e)}")

    async def delete_webhook(self, webhook_id: str) -> Result[None, str]:
        """
        Deleta um webhook existente.

        Args:
            webhook_id: ID do webhook a deletar

        Returns:
            Result OK se deletado com sucesso
        """
        try:
            response = await self._client.delete(f"/webhooks/{webhook_id}")
            response.raise_for_status()

            logger.info(f"Webhook {webhook_id} deletado")
            return Result.ok(None)

        except httpx.HTTPStatusError as e:
            return Result.err(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Erro ao deletar webhook {webhook_id}: {e}")
            return Result.err(f"Erro ao deletar webhook: {str(e)}")


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
