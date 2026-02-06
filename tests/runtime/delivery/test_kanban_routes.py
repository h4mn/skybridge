# -*- coding: utf-8 -*-
"""
⚠️ ARQUIVO MANTIDO PARA REFERÊNCIA DO PRD026 ⚠️

Este arquivo contém testes da Fase 1 (legado) do Kanban que usava TrelloAdapter.
A Fase 2 (PRD024) implementou kanban.db como fonte única da verdade, tornando
estes testes obsoletos para uso em produção.

MOTIVO DA MANUTENÇÃO:
- Pesquisa para PRD026 (integração Kanban com fluxo real)
- Referência de como o TrelloAdapter funcionava
- Pode ser útil para implementar sincronização Trello ↔ kanban.db

NÃO EXECUTAR ESTES TESTES - estão desatualizados em relação à arquitetura atual.
Use tests/integration/kanban/*.py para testes da Fase 2.

---

Testes das rotas Kanban (Fase 1: Leitura).

DOC: runtime/delivery/kanban_routes.py - /api/kanban/board
DOC: ADR024 - Workspace isolation via X-Workspace header

Testa o endpoint de visualização Kanban em modo leitura que reflete
o estado atual do board Trello, respeitando o isolamento de workspaces.

Fluxo de dados:
Frontend (Kanban.tsx) → useQuery(['kanban-board'])
    → apiClient.get('/kanban/board')
    → [X-Workspace: core] adicionado automaticamente
    → WorkspaceMiddleware carrega .env do workspace
    → kanban_routes.get_kanban_board()
    → TrelloAdapter → API Trello
    → Retorna board + cards + lists
    → Frontend renderiza colunas com cards
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))


class TestKanbanBoardRoute:
    """Testes do endpoint GET /api/kanban/board."""

    @pytest.fixture
    def mock_trello_adapter(self):
        """Mock do TrelloAdapter para testes isolados."""
        from kernel import Result
        from core.kanban.domain import Board, Card, CardStatus
        from datetime import datetime
        from unittest.mock import Mock

        mock = Mock()  # Mock síncrono, não AsyncMock

        # Mock get_board retornando Result.ok com Board
        mock_board = Board(
            id="board123",
            name="Test Board",
            url="https://trello.com/b/board123"
        )
        mock.get_board = AsyncMock(return_value=Result.ok(mock_board))

        # Mock list_cards retornando Result.ok com lista de Cards
        mock_card1 = Card(
            id="card1",
            title="Test Card 1",
            description="Description 1",
            status=CardStatus.TODO,
            labels=["bug", "feature"],
            due_date=datetime(2024, 2, 1, 10, 0, 0),
            url="https://trello.com/c/card1",
            created_at=datetime(2024, 1, 15, 10, 0, 0)
        )
        mock_card2 = Card(
            id="card2",
            title="Test Card 2",
            description=None,
            status=CardStatus.TODO,
            labels=[],
            due_date=None,
            url="https://trello.com/c/card2",
            created_at=None
        )
        mock.list_cards = AsyncMock(return_value=Result.ok([mock_card1, mock_card2]))

        # Mock initialize_status_cache retornando Result.ok
        mock.initialize_status_cache = AsyncMock(return_value=Result.ok(None))

        # Mock do _client para _fetch_board_lists
        mock._client = AsyncMock()
        mock._client.get = AsyncMock(return_value=Mock(
            raise_for_status=Mock(),
            json=lambda: [
                {"id": "list1", "name": "To Do", "pos": 0},
                {"id": "list2", "name": "Doing", "pos": 1}
            ]
        ))
        mock._list_status_cache = {"list1": CardStatus.TODO, "list2": CardStatus.IN_PROGRESS}

        return mock

    @pytest.fixture
    def mock_trello_config(self):
        """Mock do TrelloConfig para testes."""
        from runtime.config.config import TrelloConfig
        return TrelloConfig(
            api_key="test_key",
            api_token="test_token",
            board_id="board123"
        )

    @pytest.fixture
    def client_with_mocks(self, mock_trello_adapter, mock_trello_config):
        """
        TestClient com mocks configurados.

        DOC: ADR024 - Usa X-Workspace header para isolamento.
        """
        from runtime.delivery.kanban_routes import create_kanban_router

        # Criar app mínimo para testes
        from fastapi import FastAPI
        app = FastAPI()

        # Factory function mock que retorna o mock_trello_adapter
        def mock_factory(**kwargs):
            return mock_trello_adapter

        # Mock do get_trello_config e cria router com factory mock
        with patch("runtime.delivery.kanban_routes.get_trello_config", return_value=mock_trello_config):
            router = create_kanban_router(trello_adapter_factory=mock_factory)
            app.include_router(router, prefix="/api")  # Router já tem prefixo /kanban

        return TestClient(app)

    def test_get_kanban_board_success(self, client_with_mocks, mock_trello_adapter):
        """
        Testa que /api/kanban/board retorna board + cards + lists.

        DOC: runtime/delivery/kanban_routes.py - Endpoint deve retornar:
        - board: {id, name, url}
        - cards: Array de KanbanCard
        - lists: Array de {id, name, position}

        Given: Trello configurado e board com cards
        When: GET /api/kanban/board com X-Workspace: core
        Then: Retorna 200 com board + cards + lists
        """
        response = client_with_mocks.get(
            "/api/kanban/board",
            headers={"X-Workspace": "core"}
        )

        # Verifica status OK
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        # Verifica estrutura principal
        assert "ok" in data
        assert data["ok"] is True
        assert "board" in data
        assert "cards" in data
        assert "lists" in data

        # Verifica board
        assert data["board"]["id"] == "board123"
        assert data["board"]["name"] == "Test Board"
        assert data["board"]["url"] == "https://trello.com/b/board123"

        # Verifica cards
        assert len(data["cards"]) == 2
        card1 = data["cards"][0]
        assert card1["id"] == "card1"
        assert card1["title"] == "Test Card 1"
        assert card1["description"] == "Description 1"
        assert card1["url"] == "https://trello.com/c/card1"
        assert card1["due_date"] == "2024-02-01T10:00:00"  # isoformat sem timezone
        assert "bug" in card1["labels"]
        assert "feature" in card1["labels"]

        # Verifica que TrelloAdapter foi chamado
        mock_trello_adapter.get_board.assert_called_once()
        mock_trello_adapter.list_cards.assert_called_once()
        mock_trello_adapter.initialize_status_cache.assert_called_once()

    def test_get_kanban_board_empty_board(self, client_with_mocks, mock_trello_adapter):
        """
        Testa que board vazio retorna 200 com array vazio.

        Given: Trello configurado mas sem cards
        When: GET /api/kanban/board
        Then: Retorna 200 com cards vazio
        """
        from kernel import Result
        mock_trello_adapter.list_cards.return_value = Result.ok([])

        response = client_with_mocks.get(
            "/api/kanban/board",
            headers={"X-Workspace": "core"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["cards"] == []

    def test_get_kanban_board_not_configured(self):
        """
        Testa que sem credenciais Trello retorna 503.

        DOC: runtime/delivery/kanban_routes.py - Sem TRELLO_* vars
        deve retornar 503 com mensagem "Trello not configured..."

        Given: Workspace sem TRELLO_API_KEY
        When: GET /api/kanban/board
        Then: Retorna 503 com mensagem de erro
        """
        from fastapi import FastAPI
        from runtime.delivery.kanban_routes import create_kanban_router

        app = FastAPI()
        app.state.workspace = "core"

        # Mock get_trello_config retornando config inválido (sem credenciais)
        from runtime.config.config import TrelloConfig
        invalid_config = TrelloConfig(api_key=None, api_token=None, board_id=None)

        with patch("runtime.delivery.kanban_routes.get_trello_config", return_value=invalid_config):
            router = create_kanban_router()
            app.include_router(router, prefix="/api")  # Router já tem prefixo /kanban

            client = TestClient(app)
            response = client.get(
                "/api/kanban/board",
                headers={"X-Workspace": "core"}
            )

        # Verifica status code e mensagem
        assert response.status_code == 503, f"Expected 503, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "Trello not configured" in data["detail"]

    def test_get_kanban_board_trello_api_error(self, client_with_mocks, mock_trello_adapter):
        """
        Testa que erro da API Trello retorna 500.

        DOC: runtime/delivery/kanban_routes.py - Erro HTTP do Trello
        deve ser propagado como 500 Internal Server Error.

        Given: Trello API retorna erro
        When: GET /api/kanban/board
        Then: Retorna 500 com mensagem de erro
        """
        # Simula get_board retornando Result.err
        from kernel import Result
        mock_trello_adapter.get_board.return_value = Result.err("Unauthorized")

        response = client_with_mocks.get(
            "/api/kanban/board",
            headers={"X-Workspace": "core"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Unauthorized" in data["detail"] or "Error fetching" in data["detail"]

    def test_kanban_card_has_required_fields(self, client_with_mocks, mock_trello_adapter):
        """
        Testa que cards retornados têm todos os campos obrigatórios.

        DOC: runtime/delivery/kanban_routes.py - KanbanCard deve ter:
        - id, title, description, status, labels, due_date, url, list_name, created_at

        Given: Card com todos os campos
        When: GET /api/kanban/board
        Then: Card retornado tem todos os campos obrigatórios
        """
        from kernel import Result
        from core.kanban.domain import Card, CardStatus
        from datetime import datetime

        mock_card = Card(
            id="card123",
            title="Complete Feature",
            description="Implement all requirements",
            status=CardStatus.TODO,
            labels=["feature", "high-priority"],
            due_date=datetime(2024, 2, 15, 10, 0, 0),
            url="https://trello.com/c/card123",
            created_at=datetime(2024, 1, 20, 10, 0, 0)
        )
        mock_trello_adapter.list_cards.return_value = Result.ok([mock_card])

        response = client_with_mocks.get(
            "/api/kanban/board",
            headers={"X-Workspace": "core"}
        )

        assert response.status_code == 200
        data = response.json()
        card = data["cards"][0]

        # Verifica todos os campos obrigatórios
        assert "id" in card
        assert "title" in card
        assert "description" in card
        assert "status" in card
        assert "labels" in card
        assert "due_date" in card
        assert "url" in card
        assert "list_name" in card
        assert "created_at" in card

        # Verifica tipos
        assert isinstance(card["id"], str)
        assert isinstance(card["title"], str)
        assert isinstance(card["labels"], list)
        assert card["status"] in ["backlog", "todo", "in_progress", "review", "done", "blocked", "challenge"]

    def test_kanban_status_mapping(self, client_with_mocks, mock_trello_adapter):
        """
        Testa que listas Trello são mapeadas para CardStatus corretamente.

        DOC: infra/kanban/adapters/trello_adapter.py - initialize_status_cache()
        mapeia nomes de listas para CardStatus:
        - "🧠 Brainstorm"/"💡 Brainstorm" → BACKLOG
        - "📋 A Fazer" → TODO
        - "🚧 Em Andamento" → IN_PROGRESS
        - "👀 Em Revisão"/"✅ Em Teste" → REVIEW
        - "⚔️ Desafio" → CHALLENGE
        - "🚀 Publicar"/"✅ Pronto" → DONE
        - "Blocked" → BLOCKED

        Given: Board com listas variadas
        When: GET /api/kanban/board
        Then: Cards têm status mapeado corretamente
        """
        from kernel import Result
        from core.kanban.domain import Card, CardStatus

        # Simula board com cards de status variados
        mock_cards = [
            Card(id="card1", title="Idea", description=None, status=CardStatus.BACKLOG,
                  labels=[], due_date=None, url="https://trello.com/c/card1"),
            Card(id="card2", title="Task", description=None, status=CardStatus.TODO,
                  labels=[], due_date=None, url="https://trello.com/c/card2"),
            Card(id="card3", title="Work in progress", description=None, status=CardStatus.IN_PROGRESS,
                  labels=[], due_date=None, url="https://trello.com/c/card3")
        ]
        mock_trello_adapter.list_cards.return_value = Result.ok(mock_cards)

        response = client_with_mocks.get(
            "/api/kanban/board",
            headers={"X-Workspace": "core"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verifica que status foi atribuído (mesmo que genérico no mock)
        # O teste real de mapeamento fica no TrelloAdapter
        for card in data["cards"]:
            assert "status" in card
            assert card["status"] in ["backlog", "todo", "in_progress", "review", "done", "blocked", "challenge"]


class TestKanbanBoardIntegration:
    """Testes de integração do endpoint Kanban."""

    def test_kanban_endpoint_registered(self):
        """
        Testa que o endpoint /api/kanban/board está registrado.

        Given: Servidor Skybridge iniciado
        When: Verifica rotas registradas
        Then: /api/kanban/board existe
        """
        from runtime.bootstrap.app import SkybridgeApp

        app = SkybridgeApp()
        routes = []
        for route in app.app.routes:
            if hasattr(route, "path"):
                routes.append(route.path)

        # Verifica que alguma rota kanban existe
        kanban_routes = [r for r in routes if "kanban" in r.lower()]
        assert len(kanban_routes) > 0, "Nenhuma rota /kanban encontrada"

    def test_kanban_workspace_header_required(self):
        """
        Testa que X-Workspace header é respeitado (ADR024).

        DOC: ADR024 - Isolamento de workspaces via X-Workspace header.
        Cada workspace tem seu próprio .env com TRELLO_* vars.

        Given: Dois workspaces com configs diferentes
        When: GET /api/kanban/board com X-Workspace diferente
        Then: Retorna board do workspace correspondente
        """
        # Este teste verifica apenas que o endpoint existe
        # A lógica de isolamento é testada em test_workspace_middleware
        from runtime.bootstrap.app import SkybridgeApp

        app = SkybridgeApp()

        # Verifica que rota existe (path completo inclui prefixo /api)
        for route in app.app.routes:
            if hasattr(route, "path") and "kanban/board" in route.path:
                assert route.methods is not None
                assert "GET" in route.methods
                break
        else:
            pytest.fail("Rota /kanban/board não encontrada")


# TODO(human): Implementar teste de integração real com Trello
#
# Contexto: Os testes atuais usam mocks para garantir isolamento e velocidade.
# Porém, precisamos validar que a integração real com a API Trello funciona.
#
# Seu Task: Adicionar um teste marcado com @pytest.mark.integration que:
# 1. Usa TRELLO_API_KEY, TRELLO_API_TOKEN, TRELLO_BOARD_ID do ambiente
# 2. Faz chamada real à API Trello via TrelloAdapter
# 3. Verifica que o board retornado contém cards reais
# 4. Verifica que os status estão mapeados corretamente
# 5. Roda apenas quando variáveis de ambiente estão configuradas
#
# Guidance: Use pytest.skipIf para pular teste quando sem credenciais.
# Use fixtures do conftest.py para setup. Considere usar @pytest.mark_slow
# para testes que fazem chamadas de rede reais.
