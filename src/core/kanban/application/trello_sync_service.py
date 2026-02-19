# -*- coding: utf-8 -*-
"""
Trello Sync Service - Sincronização bidirecional kanban.db ←→ Trello.

Responsável por sincronizar mudanças do kanban.db com a API do Trello.
Implementa fila de operações para processamento assíncrono e tratamento de conflitos.

DOC: core/kanban/application/trello_sync_service.py
DOC: FLUXO_GITHUB_TRELO_COMPONENTES.md
DOC: ADR024 - Workspace isolation
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from core.kanban.domain.card import Card, CardStatus
from core.kanban.ports.kanban_port import KanbanPort
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter
from kernel import Result

logger = logging.getLogger(__name__)


@dataclass
class SyncOperation:
    """Operação de sincronização na fila."""
    operation: str
    card_id: str
    kwargs: dict
    retry_count: int = 0


class TrelloSyncService:
    """
    Serviço de sincronização bidirecional entre kanban.db e Trello.

    Responsável por:
    - Sincronizar cards criados no kanban.db para o Trello
    - Sincronizar atualizações de cards para o Trello
    - Sincronizar movimentos de cards entre listas
    - Gerenciar fila de operações para processamento assíncrono
    - Detectar e resolver conflitos (última escrita vence)

    Atributes:
        db: Adapter do kanban.db (SQLite)
        trello: Adapter do Trello API
        _queue: asyncio.Queue para operações de sync
        _dlq: Dead Letter Queue para operações falhas
        _worker_task: Task assíncrona do worker
        _max_retries: Número máximo de retries
        _running: Se o worker está rodando
    """

    def __init__(self, db: SQLiteKanbanAdapter, trello: KanbanPort, max_retries: int = 3):
        """
        Inicializa o serviço de sincronização.

        Args:
            db: Adapter do kanban.db
            trello: Adapter do Trello API
            max_retries: Número máximo de retries para operações falhas
        """
        self.db = db
        self.trello = trello
        self._queue: asyncio.Queue = asyncio.Queue()
        self._dlq: list[SyncOperation] = []
        self._worker_task: Optional[asyncio.Task] = None
        self._max_retries = max_retries
        self._running = False

    async def sync_card_created(self, card_id: str) -> Result[Card, str]:
        """
        Sincroniza card criado no kanban.db para o Trello.

        Fluxo:
        1. Busca card no kanban.db
        2. Cria card no Trello via API
        3. Atualiza kanban.db com trello_card_id

        Args:
            card_id: ID do card no kanban.db

        Returns:
            Result.ok(Card) com card atualizado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # 1. Busca card no kanban.db
            card_result = self.db.get_card(card_id)
            if card_result.is_err:
                return Result.err(f"Card não encontrado: {card_result.error}")

            card = card_result.value

            # Se já tem trello_card_id, não precisa sincronizar
            if card.trello_card_id:
                return Result.ok(card)

            # 2. Busca lista para obter nome
            list_result = self.db.get_list(card.list_id)
            if list_result.is_err:
                return Result.err(f"Lista não encontrada: {list_result.error}")

            # 3. Cria card no Trello
            trello_result = await self.trello.create_card(
                title=card.title,
                description=card.description,
                list_name=list_result.value.name,
                labels=card.labels or [],
            )

            if trello_result.is_err:
                return Result.err(f"Erro ao criar no Trello: {trello_result.error}")

            trello_card = trello_result.value

            # 4. Atualiza kanban.db com trello_card_id
            update_result = self.db.update_card(
                card_id,
                trello_card_id=trello_card.id,
            )

            if update_result.is_err:
                return Result.err(f"Erro ao atualizar trello_card_id: {update_result.error}")

            logger.info(
                f"Card sincronizado com Trello: {card_id} → {trello_card.id}"
            )

            return Result.ok(trello_card)

        except Exception as e:
            logger.error(f"Erro ao sincronizar card criado: {e}")
            return Result.err(f"Erro ao sync_card_created: {str(e)}")

    async def sync_card_updated(self, card_id: str) -> Result[Card, str]:
        """
        Sincroniza atualização de card para o Trello.

        Args:
            card_id: ID do card no kanban.db

        Returns:
            Result.ok(Card) com card atualizado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # Busca card atual
            card_result = self.db.get_card(card_id)
            if card_result.is_err:
                return Result.err(f"Card não encontrado: {card_result.error}")

            card = card_result.value

            # Se não tem trello_card_id, não precisa sincronizar
            if not card.trello_card_id:
                return Result.ok(card)

            # Atualiza no Trello
            trello_result = await self.trello.update_card(
                card_id=card.trello_card_id,
                title=card.title,
                description=card.description,
            )

            if trello_result.is_err:
                return Result.err(f"Erro ao atualizar no Trello: {trello_result.error}")

            logger.info(f"Card atualizado no Trello: {card_id}")

            return Result.ok(trello_result.value)

        except Exception as e:
            logger.error(f"Erro ao sincronizar card atualizado: {e}")
            return Result.err(f"Erro ao sync_card_updated: {str(e)}")

    async def sync_card_moved(self, card_id: str) -> Result[Card, str]:
        """
        Sincroniza movimento de card entre listas para o Trello.

        SEMPRE usa trello_list_id da lista local, SEMPRE manipula por ID.
        Emojis são apenas para UI, não para lógica de sincronização.

        Args:
            card_id: ID do card no kanban.db

        Returns:
            Result.ok(Card) com card atualizado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # Busca card atual
            card_result = self.db.get_card(card_id)
            if card_result.is_err:
                return Result.err(f"Card não encontrado: {card_result.error}")

            card = card_result.value

            # Se não tem trello_card_id, não precisa sincronizar
            if not card.trello_card_id:
                return Result.ok(card)

            # Busca lista para obter trello_list_id (SEMPRE usar ID direto)
            list_result = self.db.get_list(card.list_id)
            if list_result.is_err:
                return Result.err(f"Lista não encontrada: {list_result.error}")

            lista = list_result.value
            target_list_id = lista.trello_list_id

            # NOTA: Listas criadas localmente podem não ter trello_list_id ainda
            # Nesse caso, faz fallback para o nome da lista (compatibilidade com Trello)
            if not target_list_id:
                logger.warning(
                    f"Lista '{card.list_id}' ({lista.name}) não tem trello_list_id. "
                    f"Usando nome da lista para mover card no Trello."
                )
                target_list_id = lista.name  # Usa nome em vez de ID

            # Move no Trello usando target_list_id direto (SEM nomes, SEM emojis)
            trello_result = await self.trello.update_card_status(
                card_id=card.trello_card_id,
                status=CardStatus.TODO,  # Placeholder, ignorado quando target_list_id é fornecido
                target_list_id=target_list_id,  # ← SEMPRE usar ID direto
            )

            if trello_result.is_err:
                return Result.err(f"Erro ao mover no Trello: {trello_result.error}")

            logger.info(
                f"Card movido no Trello: {card_id} → lista {target_list_id}"
            )

            return Result.ok(trello_result.value)

        except Exception as e:
            logger.error(f"Erro ao sincronizar card movido: {e}")
            return Result.err(f"Erro ao sync_card_moved: {str(e)}")

    async def sync_from_trello(self, board_id: str, force: bool = False) -> Result[int, str]:
        """
        Sincroniza mudanças do Trello → kanban.db (polling/webhook).

        Fluxo:
        1. Garante que o board e listas existem no kanban.db
        2. Busca todos os cards do Trello
        3. Para cada card, busca correspondente no kanban.db por trello_card_id
        4. Compara timestamps (updated_at)
        5. Se Trello é mais recente (ou force=True), atualiza kanban.db
        6. Se card mudou de lista, move no kanban.db
        7. Se card não existe no kanban.db, cria

        Args:
            board_id: ID do board no Trello
            force: Se True, ignora timestamps e sempre atualiza do Trello

        Returns:
            Result.ok(int) com contagem de cards sincronizados
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            from datetime import datetime

            # 0. Garante que board existe no kanban.db
            logger.info(f"[SYNC] Verificando/criando board no kanban.db para Trello board_id={board_id}")
            boards_result = self.db.list_boards()
            kanban_board_id = None

            if boards_result.is_ok:
                # PRIORIDADE 1: Busca board pelo trello_board_id
                for board in boards_result.value:
                    if hasattr(board, 'trello_board_id') and board.trello_board_id == board_id:
                        kanban_board_id = board.id
                        break

                # PRIORIDADE 2: Se só existe um board, usa ele
                if not kanban_board_id and len(boards_result.value) == 1:
                    kanban_board_id = boards_result.value[0].id
                    logger.info(f"[SYNC] Usando board existente: {kanban_board_id}")

            # Se não encontrou, cria novo board
            if not kanban_board_id:
                from core.kanban.domain.database import KanbanBoard
                new_board = KanbanBoard(
                    id=f"board-trello-{board_id}",
                    name=f"Trello Board {board_id}",
                    trello_board_id=board_id,
                )
                create_board_result = self.db.create_board(new_board)
                if create_board_result.is_ok:
                    kanban_board_id = new_board.id
                    logger.info(f"[SYNC] Board criado: {kanban_board_id}")
                else:
                    return Result.err(f"Erro ao criar board: {create_board_result.error}")

            # 1. Garante que listas padrão existem no kanban.db
            logger.info(f"[SYNC] Verificando listas no board {kanban_board_id}")
            lists_result = self.db.list_lists(kanban_board_id)
            if lists_result.is_ok and not lists_result.value:
                # Board vazio - cria listas padrão da FONTE ÚNICA DA VERDADE
                logger.info(f"[SYNC] Board vazio, criando listas padrão")
                from runtime.config.config import get_trello_kanban_lists_config

                config = get_trello_kanban_lists_config()
                default_lists = config.get_list_names()

                for pos, name in enumerate(default_lists):
                    from core.kanban.domain.database import KanbanList
                    new_list = KanbanList(
                        id=f"list-default-{pos}",
                        board_id=kanban_board_id,
                        name=name,
                        position=pos,
                    )
                    self.db.create_list(new_list)
                logger.info(f"[SYNC] {len(default_lists)} listas padrão criadas")

            # 2. Busca cards do Trello
            logger.info(f"[SYNC] Buscando cards do Trello para board_id={board_id}")
            trello_cards_result = await self.trello.list_cards(board_id)
            if trello_cards_result.is_err:
                return Result.err(f"Erro ao buscar cards do Trello: {trello_cards_result.error}")

            trello_cards = trello_cards_result.value
            synced_count = 0

            logger.info(f"[SYNC] {len(trello_cards)} cards retornados do Trello")

            # 2. Para cada card do Trello
            logger.info(f"[SYNC] Iniciando processamento de {len(trello_cards)} cards do Trello")

            # Busca cards locais uma vez (para não buscar a cada iteração)
            local_cards_result = self.db.list_cards()
            local_cards_by_trello_id = {}
            if local_cards_result.is_ok:
                for lc in local_cards_result.value:
                    if lc.trello_card_id:
                        local_cards_by_trello_id[lc.trello_card_id] = lc

            logger.info(f"[SYNC] {len(local_cards_by_trello_id)} cards locais encontrados com trello_card_id")

            for trello_card in trello_cards:
                trello_id = getattr(trello_card, 'id', 'NO_ID')
                trello_title = getattr(trello_card, 'title', 'NO TITLE')
                trello_status = getattr(trello_card, 'status', None)
                logger.info(f"[SYNC] Card Trello: id={trello_id}, title={trello_title}, status={trello_status}")

                # Busca card local por trello_card_id (usando dicionário)
                local_card = local_cards_by_trello_id.get(trello_id)

                # PRD026 RF-013: Se não existe card local, CRIAR novo card
                if not local_card:
                    # Determina lista destino baseado no status do card Trello
                    trello_status = getattr(trello_card, 'status', None)
                    target_list_id = None

                    # PRIORIDADE 1: Tenta mapear por status
                    if trello_status:
                        # Mapeamento: CardStatus → nome da lista
                        status_to_list_name = {
                            "todo": "A Fazer",
                            "in_progress": "Em Andamento",
                            "review": "Em Revisão",
                            "done": "Publicar",
                            "backlog": "Issues",
                        }
                        expected_list_name = status_to_list_name.get(
                            trello_status.value,
                            trello_status.value.title()
                        )

                        # Busca lista no kanban.db usando padrões flexíveis
                        lists_result = self.db.list_lists(kanban_board_id)
                        if lists_result.is_ok:
                            status_match_patterns = {
                                "todo": ["A Fazer", "To Do", "📋 A Fazer", "todo"],
                                "in_progress": ["Em Andamento", "In Progress", "🚧 Em Andamento", "in progress"],
                                "review": ["Em Revisão", "Review", "👁️ Em Revisão", "review"],
                                "done": ["Publicar", "Done", "🚀 Publicar", "done"],
                                "backlog": ["Issues", "Backlog", "💡 Brainstorm"],
                            }
                            patterns = status_match_patterns.get(trello_status.value, [expected_list_name])

                            for lst in lists_result.value:
                                lst_name_lower = lst.name.lower()
                                for pattern in patterns:
                                    if pattern.lower() in lst_name_lower or lst_name_lower in pattern.lower():
                                        target_list_id = lst.id
                                        break
                                if target_list_id:
                                    break

                    # PRIORIDADE 2: Se não achou por status, busca lista pelo NOME da lista do Trello
                    if not target_list_id:
                        # Tenta pegar o nome da lista diretamente do card Trello
                        # (alguns adapters podem ter list.name no card)
                        trello_list_name = getattr(trello_card, 'list_name', None)
                        if trello_list_name:
                            lists_result = self.db.list_lists(kanban_board_id)
                            if lists_result.is_ok:
                                for lst in lists_result.value:
                                    # Compara ignorando emoji
                                    import re
                                    lst_name_clean = re.sub(r'[\U0001F300-\U0001F9FF]', '', lst.name)
                                    trello_name_clean = re.sub(r'[\U0001F300-\U0001F9FF]', '', trello_list_name)
                                    if lst_name_clean.lower() == trello_name_clean.lower():
                                        target_list_id = lst.id
                                        break

                    # PRIORIDADE 3: Fallback - usa primeira lista disponível
                    if not target_list_id:
                        lists_result = self.db.list_lists(kanban_board_id)
                        if lists_result.is_ok and lists_result.value:
                            target_list_id = lists_result.value[0].id
                            logger.warning(
                                f"Usando primeira lista como fallback para card {trello_card.id}"
                            )
                        else:
                            logger.warning(f"Não encontrou nenhuma lista para card {trello_card.id}, pulando criação")
                            continue

                    # Cria novo card no kanban.db
                    from core.kanban.domain.database import KanbanCard
                    import time

                    new_card = KanbanCard(
                        id=f"card-trello-{trello_card.id}-{int(time.time())}",
                        list_id=target_list_id,
                        title=trello_card.title,
                        description=trello_card.description,
                        position=0,
                        trello_card_id=trello_card.id,
                        being_processed=False,
                    )

                    create_result = self.db.create_card(new_card)
                    if create_result.is_ok:
                        synced_count += 1
                        logger.info(
                            f"✅ Card CRIADO do Trello: {new_card.id} "
                            f"(trello_id={trello_card.id}, lista={target_list_id})"
                        )
                    else:
                        logger.error(f"Erro ao criar card do Trello: {create_result.error}")

                    continue  # Próximo card

                # 3. Card existe: Compara timestamps (última escrita vence)
                trello_updated = getattr(trello_card, 'updated_at', None)
                local_updated = local_card.updated_at

                should_update = force or (trello_updated and local_updated and trello_updated > local_updated)
                print(f"[SYNC] trello_updated={trello_updated}, local_updated={local_updated}, force={force}, will_update={should_update}")

                # Se Trello é mais recente (ou force=True), atualiza
                if should_update:
                    # Atualiza título e descrição
                    update_params = {
                        "title": trello_card.title,
                        "description": trello_card.description,
                    }

                    # Verifica se mudou de lista (status)
                    trello_status = getattr(trello_card, 'status', None)
                    if trello_status:
                        # Busca lista destino pelo nome do status no kanban.db
                        # Tenta múltiplos padrões de nome
                        lists_result = self.db.list_lists(kanban_board_id)
                        if lists_result.is_ok:
                            target_list = None
                            for lst in lists_result.value:
                                # Múltiplos padrões de nome para cada status
                                status_match_patterns = {
                                    "todo": ["A Fazer", "To Do", "📋 A Fazer", "todo"],
                                    "in_progress": ["Em Andamento", "In Progress", "🚧 Em Andamento", "in progress", "doing"],
                                    "review": ["Em Revisão", "Review", "👁️ Em Revisão", "review", "testing"],
                                    "done": ["Publicar", "Done", "🚀 Publicar", "done", "pronto"],
                                    "backlog": ["Issues", "Backlog", "💡 Brainstorm", "brainstorm"],
                                }

                                patterns = status_match_patterns.get(trello_status.value, [trello_status.value.title()])
                                lst_name_lower = lst.name.lower()

                                for pattern in patterns:
                                    if pattern.lower() in lst_name_lower or lst_name_lower in pattern.lower():
                                        target_list = lst
                                        break

                                if target_list:
                                    break
                                    target_list = lst
                                    break

                            if target_list:
                                update_params["list_id"] = target_list.id

                    self.db.update_card(local_card.id, **update_params)
                    synced_count += 1
                    logger.info(
                        f"Card sincronizado do Trello: {local_card.id} "
                        f"(trello_id={trello_card.id})"
                    )

            logger.info(
                f"Sync from Trello completo: {synced_count}/{len(trello_cards)} cards sincronizados"
            )

            return Result.ok(synced_count)

        except Exception as e:
            logger.error(f"Erro ao sync do Trello: {e}")
            return Result.err(f"Erro ao sync_from_trello: {str(e)}")

    async def enqueue_sync_operation(
        self,
        operation: str,
        card_id: str,
        **kwargs
    ) -> Result[None, str]:
        """
        Enfileira operação de sincronização para processamento assíncrono.

        Args:
            operation: Tipo de operação ('create', 'update', 'move', 'delete')
            card_id: ID do card
            **kwargs: Parâmetros adicionais

        Returns:
            Result.ok(None) se operação enfileirada
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            op = SyncOperation(operation=operation, card_id=card_id, kwargs=kwargs)
            await self._queue.put(op)
            logger.info(f"Operação enfileirada: {operation} - {card_id}")
            return Result.ok(None)
        except Exception as e:
            return Result.err(f"Erro ao enfileirar operação: {str(e)}")

    async def start_queue_worker(self) -> None:
        """
        Inicia o worker assíncrono que processa a fila de sincronização.
        """
        if self._running:
            logger.warning("Worker já está rodando")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._queue_worker())
        logger.info("Worker de sincronização iniciado")

    async def stop_queue_worker(self) -> None:
        """
        Para o worker assíncrono.
        """
        if not self._running:
            return

        self._running = False

        # Envia sentinela para parar worker
        await self._queue.put(None)

        if self._worker_task:
            await asyncio.wait_for(self._worker_task, timeout=5)
            self._worker_task = None

        logger.info("Worker de sincronização parado")

    async def _queue_worker(self) -> None:
        """
        Worker assíncrono que processa operações da fila.
        """
        while self._running:
            try:
                # Timeout de 1 segundo para verificar _running
                op = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                # Sentinela para parar
                if op is None:
                    break

                # Processa operação com retry
                await self._process_operation_with_retry(op)

                self._queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro no worker: {e}")

    async def _process_operation_with_retry(self, op: SyncOperation) -> None:
        """
        Processa operação com retry logic.

        Args:
            op: Operação a processar
        """
        max_retries = self._max_retries

        while op.retry_count < max_retries:
            result = await self._execute_operation(op)

            if result.is_ok:
                logger.info(f"Operação {op.operation} - {op.card_id} completada")
                return

            op.retry_count += 1

            if op.retry_count < max_retries:
                # Exponential backoff
                await asyncio.sleep(2 ** op.retry_count)
            else:
                # Max retries atingido - move para DLQ
                logger.error(
                    f"Operação {op.operation} - {op.card_id} falhou após {max_retries} tentativas"
                )
                self._dlq.append(op)

    async def _execute_operation(self, op: SyncOperation) -> Result:
        """
        Executa uma operação de sincronização.

        Args:
            op: Operação a executar

        Returns:
            Result.ok() se sucesso
            Result.err() se falha
        """
        if op.operation == "create":
            return await self.sync_card_created(op.card_id)
        elif op.operation == "update":
            return await self.sync_card_updated(op.card_id)
        elif op.operation == "move":
            return await self.sync_card_moved(op.card_id)
        else:
            return Result.err(f"Operação desconhecida: {op.operation}")

    async def _sync_with_retry(
        self,
        operation: Callable,
        max_retries: int = 3
    ) -> Result:
        """
        Executa operação com retry logic.

        Args:
            operation: Função assíncrona a executar
            max_retries: Número máximo de tentativas

        Returns:
            Result.ok() se sucesso
            Result.err() se falhar após todas as tentativas
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                result = await operation()
                if result.is_ok:
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)

            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** (attempt + 1))

        return Result.err(f"Erro após {max_retries} tentativas: {last_error}")

    def _resolve_conflict(
        self,
        local_updated: datetime,
        trello_updated: datetime,
    ) -> str:
        """
        Resolve conflito de versão usando "última escrita vence".

        Args:
            local_updated: Timestamp da versão local
            trello_updated: Timestamp da versão do Trello

        Returns:
            "local" se local é mais recente
            "trello" se trello é mais recente
        """
        if local_updated > trello_updated:
            return "local"
        else:
            return "trello"

    def get_dlq_size(self) -> int:
        """
        Retorna o número de operações na Dead Letter Queue.

        Returns:
            Tamanho da DLQ
        """
        return len(self._dlq)
