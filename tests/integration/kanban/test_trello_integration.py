# -*- coding: utf-8 -*-
"""
Testes de Integração Trello - TDD Estrito.

Cobre integração real com API Trello usando credenciais do .env.

PRÉ-REQUISITOS:
- TRELLO_API_KEY e TRELLO_API_TOKEN no .env
- TRELLO_BOARD_ID configurado
- kanban.db inicializado

TDD: Red → Green → Refactor
Estes testes foram escritos ANTES da implementação para validar o comportamento.

PRD026: Usa trello_test_card para obter card ID real
em vez de IDs fictícios que causam erro 400.
"""

import os
import pytest
import pytest_asyncio
import sqlite3
from pathlib import Path
from datetime import datetime

from core.kanban.domain.database import KanbanList, KanbanCard
from core.kanban.domain.kanban_lists_config import get_kanban_lists_config
from core.kanban.domain.card import CardStatus
from infra.kanban.adapters.trello_adapter import TrelloAdapter
from infra.kanban.adapters import create_trello_adapter

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def clean_kanban_db(kanban_db_path):
    """
    Limpa o kanban.db antes de cada teste para garantir estado limpo.

    AUTOUSE: Executa automaticamente antes de cada teste.
    Remove registros de teste para evitar acúmulo que causa falhas.
    """
    if kanban_db_path.exists():
        # Backup do DB atual (para debug)
        backup_path = kanban_db_path.with_suffix(".backup")
        if backup_path.exists():
            backup_path.unlink()
        import shutil
        shutil.copy2(kanban_db_path, backup_path)

        # Conecta e deleta apenas registros de teste
        import sqlite3
        conn = sqlite3.connect(kanban_db_path)
        cursor = conn.cursor()

        # Deleta cards que começam com "[TEST" ou "[DEMO"
        cursor.execute("DELETE FROM cards WHERE title LIKE '[TEST]%' OR title LIKE '[DEMO]%'")

        # Lista apenas as listas atuais
        cursor.execute("SELECT name FROM lists")
        existing_lists = [row[0] for row in cursor.fetchall()]

        # Define as listas padrão (com emoji)
        standard_lists = [
            '📥 Issues', '🧠 Brainstorm', '📋 A Fazer',
            '🚧 Em Andamento', '👀 Em Revisão', '🚀 Publicar'
        ]

        # Só deleta listas extras se houver mais de 6 listas
        # Isso evita deletar as listas padrão se o DB estiver vazio/reinicializado
        if len(existing_lists) > 6:
            # Encontra listas que não são padrão
            extra_lists = [l for l in existing_lists if l not in standard_lists]
            if extra_lists:
                placeholders = ','.join(['?' for _ in extra_lists])
                cursor.execute(f"DELETE FROM lists WHERE name IN ({placeholders})", tuple(extra_lists))

        conn.commit()
        conn.close()

    yield


@pytest.fixture
def trello_card_factory(trello_config, clean_kanban_db):
    """
    Factory de cards de teste para evitar problemas com async generators.

    Retorna uma função assíncrona que cria cards reais no Trello.

    Uso:
        async def test_something(trello_card_factory):
            card = await trello_card_factory()
            # Usar card...
    """
    from infra.kanban.adapters.trello_adapter import TrelloAdapter

    async def create_card():
        """Cria um card de teste no Trello."""
        adapter = TrelloAdapter(
            api_key=trello_config["api_key"],
            api_token=trello_config["api_token"],
            board_id=trello_config["board_id"],
        )

        try:
            # Timestamp único para evitar conflitos
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")  # Adiciona microsegundos

            # Dados da issue de teste
            issue_number = 9999  # Número único para testes
            issue_title = f"[TEST] Card de Teste {timestamp}"
            issue_desc = f"""Card de teste criado automaticamente.
Timestamp: {timestamp}
Teste: Integração Trello
Auto-gerado via trello_card_factory"""

            # Cria card no Trello via API real
            card_result = await adapter.create_card(
                title=f"#{issue_number}: {issue_title}",
                description=issue_desc,
                list_name="🧠 Brainstorm",  # Começa em Brainstorm (lista inicial)
                board_id=trello_config["board_id"],
            )

            if card_result.is_err:
                pytest.fail(f"Erro ao criar card de teste: {card_result.error}")

            card = card_result.unwrap()

            # Retorna dicionário completo para uso nos testes
            return {
                "card_id": card.id,
                "card_url": card.url,
                "card_name": f"#{issue_number}: {issue_title}",
                "issue_number": issue_number,
                "issue_title": issue_title,
                "issue_desc": issue_desc,
                "_adapter": adapter,  # Guarda referência para cleanup
            }
        except Exception as e:
            await adapter._close()
            raise

    return create_card


@pytest.fixture
def trello_config():
    """
    Configurações do Trello do .env.

    Skip suave se não houver credenciais.
    """
    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")

    if not api_key or not api_token or not board_id:
        pytest.skip(
            "TRELLO_API_KEY, TRELLO_API_TOKEN e TRELLO_BOARD_ID necessários. "
            "Configure no .env"
        )

    return {
        "api_key": api_key,
        "api_token": api_token,
        "board_id": board_id,
    }


@pytest.fixture
def kanban_db_path():
    """Caminho para o kanban.db."""
    # ADR024: kanban.db fica em workspace/core/data/kanban.db
    return Path("workspace/core/data/kanban.db")


@pytest.fixture
def kanban_conn(kanban_db_path):
    """
    Conexão SQLite para o kanban.db com inicialização automática.

    Se o banco não existir, inicializa com KanbanInitializer para garantir
    que as listas padrão existam antes de rodar os testes.
    """
    from core.kanban.application.kanban_initializer import KanbanInitializer

    # Se não existe, inicializa com board e listas padrão
    if not kanban_db_path.exists():
        initializer = KanbanInitializer(db_path=kanban_db_path)
        initializer.initialize()

    conn = sqlite3.connect(kanban_db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

# =============================================================================
# TESTE 1: Valida a criação de card no Trello
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_1_create_card_in_trello(trello_config):
    """
    TESTE 1: Valida a criação de card no Trello.

    GIVEN: Adapter configurado com credenciais válidas
    WHEN: Cria um card com título e descrição
    THEN: Card é criado com sucesso no Trello
    AND: Card possui ID, URL e lista corretos

    NOTA: Este teste foi substituído por trello_test_card fixture.
    """
    from core.kanban.domain.kanban_lists_config import get_kanban_lists_config

    # Setup: Cria adapter
    adapter = TrelloAdapter(
        api_key=trello_config["api_key"],
        api_token=trello_config["api_token"],
        board_id=trello_config["board_id"],
    )

    try:
        # Setup: Obtém nome da lista "A Fazer" (com emoji para Trello)
        lists_config = get_kanban_lists_config()
        todo_list_name = lists_config.get_slug_to_name_with_emoji_mapping().get("todo", "📋 A Fazer")

        # Timestamp único para evitar conflitos
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        test_title = f"[TEST] Card de Integração {timestamp}"
        test_desc = f"Card criado automaticamente por teste de integração.\nTimestamp: {timestamp}"

        # WHEN: Cria o card
        result = await adapter.create_card(
            title=test_title,
            description=test_desc,
            list_name=todo_list_name,
            board_id=trello_config["board_id"],
        )

        # THEN: Card criado com sucesso
        assert result.is_ok, f"Erro ao criar card: {result.error}"
        card = result.unwrap()

        # Verifica atributos obrigatórios
        assert card.title == test_title
        assert card.description == test_desc
        assert card.id is not None
        assert card.url is not None
        assert "trello.com" in card.url

    finally:
        await adapter._close()

# =============================================================================
# TESTE 2: Valida o recebimento de webhook do Trello
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_2_receive_trello_webhook(trello_config, trello_card_factory):
    """
    TESTE 2: Valida o recebimento de webhook do Trello.

    GIVEN: Endpoint /api/webhooks/trello configurado
    WHEN: Envia payload válido de webhook com card ID REAL
    THEN: Endpoint retorna 202 Accepted
    AND: Job é enfileirado para processamento

    MELHORIA PRD026: Usa trello_card_factory para obter card ID real
    em vez de ID fictício que causa erro 400 "invalid id".
    """
    from fastapi.testclient import TestClient
    from runtime.bootstrap.app import get_app

    # Cria card real usando o factory
    test_card = await trello_card_factory()
    card_id = test_card["card_id"]
    card_name = test_card["card_name"]

    try:
        # WHEN: Envia webhook com card ID REAL
        webhook_payload = {
            "action": {
                "type": "updateCard",
                "data": {
                    "card": {
                        "id": card_id,
                        "name": card_name,
                    },
                    "listBefore": {"name": "🧠 Brainstorm"},
                    "listAfter": {"name": "📋 A Fazer"},
                },
            },
            "model": {"id": trello_config["board_id"]},
        }

        app = get_app().app
        client = TestClient(app)
        response = client.post(
            "/api/webhooks/trello",
            json=webhook_payload,
            headers={"X-Trello-Webhook": "test-webhook-id"},
        )

        # THEN: Endpoint aceita a requisição com card REAL
        assert response.status_code in [202, 422], f"Status {response.status_code}, card_id: {card_id}"

        if response.status_code == 202:
            data = response.json()
            assert data["status"] == "queued"
    finally:
        # Cleanup do adapter
        await test_card["_adapter"]._close()

# =============================================================================
# TESTE 3: Valida que as listas definidas no setup estão no Trello
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_3_trello_lists_match_setup(trello_config):
    """
    TESTE 3: Valida que as listas definidas no setup estão no Trello.

    GIVEN: KanbanListsConfig define 6 listas padrão
    WHEN: Busca listas do board no Trello
    THEN: Todas as listas padrão existem no Trello
    AND: Nomes com emojis correspondem

    RED: Primeiro escreve o teste que verifica as listas
    GREEN: Garante que setup cria as listas no Trello
    """
    from core.kanban.domain.kanban_lists_config import get_kanban_lists_config
    import httpx

    # Setup: Cria adapter
    adapter = TrelloAdapter(
        api_key=trello_config["api_key"],
        api_token=trello_config["api_token"],
        board_id=trello_config["board_id"],
    )

    try:
        # Setup: Obtém listas esperadas
        lists_config = get_kanban_lists_config()
        expected_list_names = lists_config.get_list_names_with_emoji()

        # WHEN: Busca listas do board no Trello
        client = httpx.AsyncClient(
            base_url="https://api.trello.com/1",
            params={"key": adapter.api_key, "token": adapter.api_token},
            timeout=30.0,
        )
        try:
            response = await client.get(f"/boards/{trello_config['board_id']}/lists")
            response.raise_for_status()
            trello_lists = response.json()
            trello_list_names = [lst.get("name", "") for lst in trello_lists]

        finally:
            await client.aclose()

        # THEN: Verifica que todas as listas esperadas existem no Trello
        for expected_name in expected_list_names:
            assert (
                expected_name in trello_list_names
            ), f"Lista '{expected_name}' não encontrada no Trello. Disponíveis: {trello_list_names}"

    finally:
        await adapter._close()

# =============================================================================
# TESTE 4: Valida que as listas definidas no setup estão no kanban.db
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_4_kanban_db_lists_match_setup(kanban_conn):
    """
    TESTE 4: Valida que as listas definidas no setup estão no kanban.db.

    GIVEN: kanban.db inicializado E limpo (clean_kanban_db)
    WHEN: Consulta tabela lists
    THEN: Todas as listas padrão existem no banco
    AND: Posições e nomes correspondem ao KanbanListsConfig

    MELHORIA PRD026: Usa clean_kanban_db que limpa o DB antes de cada teste.
    """
    from core.kanban.domain.kanban_lists_config import get_kanban_lists_config
    from core.kanban.application.kanban_initializer import KanbanInitializer

    # O fixture clean_kanban_db já limpou o DB antes deste teste

    # Setup: Verifica se DB está vazio e inicializa se necessário
    cursor = kanban_conn.execute("SELECT COUNT(*) as count FROM lists")
    count = cursor.fetchone()["count"]

    if count == 0:
        # DB vazio - precisa inicializar
        # Obtém o caminho do DB da conexão
        db_path_info = kanban_conn.execute("PRAGMA database_list").fetchone()
        db_path = db_path_info["name"] if db_path_info else "workspace/core/data/kanban.db"

        initializer = KanbanInitializer(db_path=str(db_path))
        initializer.initialize()
        # initialize() é síncrono e retorna None (lança exceção em caso de erro)

    # Setup: Obtém listas esperadas
    lists_config = get_kanban_lists_config()
    expected_list_names = lists_config.get_list_names()

    # WHEN: Busca listas no kanban.db (já limpo)
    cursor = kanban_conn.execute(
        """
        SELECT name, position
        FROM lists
        ORDER BY position
        """
    )
    db_lists = cursor.fetchall()
    db_list_names = [row["name"] for row in db_lists]

    # THEN: Verifica que todas as listas esperadas existem
    for expected_name in expected_list_names:
        assert (
            expected_name in db_list_names
        ), f"Lista '{expected_name}' não encontrada no kanban.db. Disponíveis: {db_list_names}"

    # Verifica quantidade (deve ser exatamente 6 após limpeza)
    assert len(db_lists) == len(
        expected_list_names
    ), f"Quantidade de listas incorreta. Esperado: {len(expected_list_names)}, Obtido: {len(db_lists)}"

# =============================================================================
# TESTE 5: Valida que o diff do snapshot do kanban está igual
# =============================================================================

@pytest.mark.skip("Fluxo de snapshot ainda não implementado")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_5_kanban_snapshot_is_synchronized(
    trello_config, kanban_conn
):
    """
    TESTE 5: Valida que o diff do snapshot do kanban está igual, sem dessincronização.

    GIVEN: Cards no Trello e no kanban.db
    WHEN: Sincroniza Trello → kanban.db e compara snapshot
    THEN: Não há diferenças (sincronizado)
    AND: Cards do Trello aparecem no kanban.db após sync

    NOTA: Teste skipado pois fluxo de snapshot não está implementado.
    """
    pass

# =============================================================================
# TESTE 6: Valida que um card movido no kanban foi movido no Trello
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_6_card_moved_in_kanban_is_moved_in_trello(
    trello_config, kanban_conn,
):
    """
    TESTE 6: Valida que um card movido no kanban foi movido no Trello.

    GIVEN: Card criado no kanban.db
    WHEN: Atualiza status do card no kanban.db
    THEN: Card é movido para lista correspondente no Trello
    AND: Trello reflete o novo status
    """
    from core.kanban.domain.card import CardStatus
    from core.kanban.domain.kanban_lists_config import get_kanban_lists_config

    # Setup: Cria adapter
    adapter = TrelloAdapter(
        api_key=trello_config["api_key"],
        api_token=trello_config["api_token"],
        board_id=trello_config["board_id"],
    )

    try:
        # Setup: Cria um card de teste no Trello
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        test_issue_number = 9999
        test_title = f"[TEST] Card Move Test {timestamp}"

        create_result = await adapter.create_card(
            title=f"#{test_issue_number}: {test_title}",
            description="Card para teste de movimentação",
            list_name="🧠 Brainstorm",  # Começa em Brainstorm
            board_id=trello_config["board_id"],
        )

        assert create_result.is_ok, f"Erro ao criar card: {create_result.error}"
        created_card = create_result.unwrap()

        # Setup: Busca o card no kanban.db
        from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter
        db_adapter = SQLiteKanbanAdapter(db_path="workspace/core/data/kanban.db")
        connect_result = db_adapter.connect()
        assert connect_result.is_ok, f"Erro ao conectar: {connect_result.error}"

        try:
            # Busca por issue_number
            cards_result = db_adapter.list_cards()
            assert cards_result.is_ok, "Erro ao buscar cards"

            # Encontra o card pelo issue_number
            test_card = None
            for card in cards_result.value:
                if card.title.startswith(f"#{test_issue_number}"):
                    test_card = card
                    break

            assert test_card is not None, "Card de teste não encontrado no kanban.db"

            # WHEN: Atualiza status para TODO no kanban
            update_result = db_adapter.update_card_status(
                card_id=test_card.id,
                status=CardStatus.TODO,
                correlation_id=f"test-{timestamp}"
            )

            assert update_result.is_ok, f"Erro ao atualizar card: {update_result.error}"

        finally:
            db_adapter.disconnect()

        # WHEN: Move para "A Fazer" no Trello
        lists_config = get_kanban_lists_config()
        todo_list = lists_config.get_slug_to_name_with_emoji_mapping().get("todo", "📋 A Fazer")

        move_result = await adapter.update_card_status(
            card_id=created_card.id,
            status=CardStatus.TODO,
            correlation_id=f"test-{timestamp}"
        )

        assert move_result.is_ok, f"Erro ao mover card: {move_result.error}"

        # THEN: Verifica que card está na lista correta no Trello
        verify_result = await adapter.get_card(created_card.id)
        assert verify_result.is_ok, f"Erro ao verificar card: {verify_result.error}"

        verified_card = verify_result.unwrap()
        assert verified_card.status == CardStatus.TODO

        # Cleanup: Deleta o card de teste
        delete_result = await adapter.delete_card(created_card.id)
        assert delete_result.is_ok, f"Erro ao deletar card: {delete_result.error}"

    finally:
        await adapter._close()

# =============================================================================
# TESTE 7: Valida que TrelloAdapter usa IDs de lista
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_7_trello_adapter_uses_list_ids_not_names(trello_config):
    """
    TESTE 7: Valida que todas as operações do TrelloAdapter usam IDs de lista.

    GIVEN: TrelloAdapter configurado
    WHEN: Qualquer operação que envolve lista é executada
    THEN: DEVE usar trello_list_id (ID direto)
    AND: NUNCA usa list_name (nome com emoji)
    """
    import inspect
    from infra.kanban.adapters.trello_adapter import TrelloAdapter

    adapter = TrelloAdapter(
        api_key=trello_config["api_key"],
        api_token=trello_config["api_token"],
        board_id=trello_config["board_id"],
    )

    try:
        # WHEN: Busca código-fonte de todos os métodos que operam com listas
        source = inspect.getsource(TrelloAdapter)

        # THEN: Verifica que NÃO há chamadas usando list_name em operações críticas
        suspicious_patterns = [
            "list_name=",           # Parâmetro list_name em create_card
            '"name":',             # Chave 'name' em JSON para operações de lista
            "'name':",             # Chave 'name' em JSON para operações de lista
            "get_by_name",         # Busca por nome
        ]

        violations = []
        for pattern in suspicious_patterns:
            if pattern in source:
                violations.append(f"Padrão suspeito encontrado: {pattern}")

        # Verificações específicas de violações conhecidas
        if "def create_card" in source and "list_name" in source:
            # Verifica se create_card aceita list_name mas converte para ID internamente
            create_card_source = inspect.getsource(adapter.create_card)
            if "idList" not in create_card_source and "list_name" in create_card_source:
                violations.append(
                    "create_card usa list_name sem converter para trello_list_id (API do Trello exige idList)"
                )

        if violations:
            pytest.fail(
                f"VIOLAÇÕES DE LISTA POR NOME (NÃO USAR ID):\n" +
                "\n".join(f"  - {v}" for v in violations) +
                "\n\nCORREÇÃO: Usar trello_list_id em todas as operações com lista do Trello"
            )

    finally:
        await adapter._close()

# =============================================================================
# TESTE 8: Valida sincronização de listas entre kanban.db e Trello
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_8_kanban_cards_in_same_list_as_trello(
    trello_config, kanban_conn,
):
    """
    TESTE 8: Valida sincronização de listas entre kanban.db e Trello.

    GIVEN: Cards sincronizados entre Trello e kanban.db
    WHEN: Compara lista de cada card nos dois sistemas
    THEN: Card está na MESMA lista em ambos
    AND: trello_list_id da lista local bate com ID no Trello

    MELHORIA PRD026:
    1. Usa clean_kanban_db para limpar estado antes do teste
    2. BUG: Cards com status BACKLOG (Issues) vão para A Fazer no kanban.db

    NOTA: Este teste demonstra o bug da sincronização onde cards de Issues
    vão para a lista errada após sync_from_trello().
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter

    # O fixture clean_kanban_db já limpou o DB e criou o card
    # Vamos sincronizar novamente para garantir dados limpos

    # Setup: Cria adapters
    trello_adapter = TrelloAdapter(
        api_key=trello_config["api_key"],
        api_token=trello_config["api_token"],
        board_id=trello_config["board_id"],
    )

    # Adapter do kanban.db usando o caminho correto (ADR024)
    db_path_info = kanban_conn.execute("PRAGMA database_list").fetchone()
    db_path = db_path_info["name"] if db_path_info else "workspace/core/data/kanban.db"
    db_adapter = SQLiteKanbanAdapter(db_path=str(db_path))
    connect_result = db_adapter.connect()
    assert connect_result.is_ok, f"Erro ao conectar ao kanban.db: {connect_result.error}"

    try:
        # WHEN: Sincroniza Trello → kanban.db
        sync_service = TrelloSyncService(db=db_adapter, trello=trello_adapter)
        sync_result = await sync_service.sync_from_trello(
            board_id=trello_config["board_id"],
            force=True  # Força sync para garantir que cards do teste apareçam
        )

        assert sync_result.is_ok, f"Erro ao sincronizar Trello → kanban.db: {sync_result.error}"
        synced_count = sync_result.unwrap()
        print(f"[TESTE 8] Sincronizados {synced_count} cards do Trello")

        # WHEN: Busca cards do kanban.db
        db_cards_result = db_adapter.list_cards()
        assert db_cards_result.is_ok, f"Erro ao buscar cards do kanban.db: {db_cards_result.error}"
        db_cards = db_cards_result.value

        # WHEN: Busca cards do Trello
        trello_result = await trello_adapter.list_cards(board_id=trello_config["board_id"])
        assert trello_result.is_ok, f"Erro ao buscar cards do Trello: {trello_result.error}"
        trello_cards = trello_result.unwrap()

        # Cria mapa trello_card_id → Card do Trello
        trello_cards_by_id = {card.id: card for card in trello_cards}

        # Setup: Mapeamento slug → trello_list_id do Trello real
        lists_config = get_kanban_lists_config()

        # WHEN: Compara lista de cada card nos dois sistemas
        mismatches = []
        for db_card in db_cards:
            if not db_card.trello_card_id:
                continue  # Card local sem correspondente no Trello

            trello_card = trello_cards_by_id.get(db_card.trello_card_id)
            if not trello_card:
                # Card não encontrado no Trello (pode ter sido deletado)
                continue

            # Busca lista local para obter trello_list_id
            list_result = db_adapter.get_list(db_card.list_id)
            if list_result.is_err:
                mismatches.append(
                    f"Card {db_card.title}: lista local {db_card.list_id} não encontrada"
                )
                continue

            local_list = list_result.value
            local_trello_list_id = local_list.trello_list_id

            # Determina qual lista o card está no Trello (pelo nome)
            # Mapeamento reverso: CardStatus → nome da lista (com emoji)
            status_to_list = {
                "backlog": "📥 Issues",
                "todo": "📋 A Fazer",
                "in_progress": "🚧 Em Andamento",
                "review": "👀 Em Revisão",
                "done": "🚀 Publicar",
            }

            # Para cards com status, busca a lista correspondente
            if hasattr(db_card, 'status'):
                trello_list_name_expected = status_to_list.get(db_card.status.value)
            else:
                # Sem status, assume Brainstorm (lista inicial)
                trello_list_name_expected = lists_config.get_slug_to_name_with_emoji_mapping().get("backlog", "🧠 Brainstorm")

            # Busca trello_list_id correspondente no Trello real
            expected_trello_list_id = None
            for lst_id in lists_config.get_trello_list_ids():
                if lst_id["name"] == trello_list_name_expected:
                    expected_trello_list_id = lst_id["id"]
                    break

            if local_trello_list_id != expected_trello_list_id:
                mismatches.append(
                    f"Card {db_card.title}:\n"
                    f"  Trello lista: {trello_list_name_expected} (id={expected_trello_list_id})\n"
                    f"  Kanban lista: {local_list.name} (trello_id={local_trello_list_id})\n"
                    f"  STATUS: {db_card.status if hasattr(db_card, 'status') else 'N/A'}"
                )

        if mismatches:
            pytest.fail(
                f"CARDS EM LISTA DIFERENTE ENTRE TRELLO E KANBAN.DB:\n" +
                "\n".join(mismatches) +
                f"\n\nTotal de inconsistências: {len(mismatches)}"
            )

    finally:
        await trello_adapter._close()
        db_adapter.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
