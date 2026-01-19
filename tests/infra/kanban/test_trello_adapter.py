# -*- coding: utf-8 -*-
"""
Testes para TrelloAdapter.

NOTA: Estes testes requerem credenciais válidas do Trello.
Para executar: export TRELLO_API_KEY="..." TRELLO_API_TOKEN="..."
"""

import os
import pytest

from core.kanban.domain import CardStatus
from infra.kanban.adapters.trello_adapter import (
    TrelloAdapter,
    TrelloConfigError,
    create_trello_adapter,
)


@pytest.mark.skipif(
    not os.getenv("TRELLO_API_KEY") or not os.getenv("TRELLO_API_TOKEN"),
    reason="Requires TRELLO_API_KEY and TRELLO_API_TOKEN"
)
class TestTrelloAdapter:
    """Testes de integração com Trello API."""

    @pytest.fixture
    async def adapter(self):
        """Cria adapter configurado."""
        api_key = os.getenv("TRELLO_API_KEY")
        api_token = os.getenv("TRELLO_API_TOKEN")

        adapter = create_trello_adapter(api_key, api_token)
        yield adapter
        await adapter._close()

    @pytest.mark.asyncio
    async def test_create_adapter_invalid_credentials(self):
        """Testa erro ao criar adapter sem credenciais."""
        with pytest.raises(TrelloConfigError):
            TrelloAdapter(api_key="", api_token="")

        with pytest.raises(TrelloConfigError):
            TrelloAdapter(api_key="key", api_token="")

    @pytest.mark.asyncio
    async def test_get_board(self, adapter):
        """Testa buscar um board público do Trello."""
        # Usar board público de exemplo
        result = await adapter.get_board("5e88ae2f2f103936713e7e3c")

        assert result.is_ok()
        board = result.unwrap()
        assert board.id == "5e88ae2f2f103936713e7e3c"
        assert board.external_source == "trello"

    @pytest.mark.asyncio
    async def test_get_card_not_found(self, adapter):
        """Testa buscar card inexistente."""
        result = await adapter.get_card("card-inexistente-123")

        assert result.is_err()
        assert "não encontrado" in result.unwrap_err()


class TestTrelloAdapterUnit:
    """Testes unitários sem chamar API."""

    def test_factory_function(self):
        """Testa factory create_trello_adapter."""
        adapter = create_trello_adapter("test-key", "test-token")

        assert adapter.api_key == "test-key"
        assert adapter.api_token == "test-token"

    def test_map_status_default(self):
        """Testa mapeamento de status."""
        adapter = create_trello_adapter("key", "token")

        # Mapeamento default é TODO (ainda não implementado cache de listas)
        status = adapter._map_status("any-list-id")
        assert status == CardStatus.TODO
