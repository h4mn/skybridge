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


class TestTrelloAdapterCredentials:
    """Testes de credenciais do adapter - não requer API Trello."""

    @pytest.mark.asyncio
    async def test_create_adapter_invalid_credentials(self):
        """Testa erro ao criar adapter sem credenciais."""
        with pytest.raises(TrelloConfigError):
            TrelloAdapter(api_key="", api_token="")

        with pytest.raises(TrelloConfigError):
            TrelloAdapter(api_key="key", api_token="")


# Testes de integração que requerem credenciais
# NOTA: Temporariamente desabilitados devido a bug no pytest-asyncio 0.21.1
# com skipif + async fixtures. Esses testes funcionam quando executados manualmente.

@pytest.mark.skip(reason="TODO: pytest-asyncio bug with skipif + async fixtures - requires manual testing")
@pytest.mark.asyncio
async def test_get_board():
    """Testa buscar um board público do Trello."""
    # Usar board público de exemplo
    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")

    if not api_key or not api_token:
        pytest.skip("Requires TRELLO_API_KEY and TRELLO_API_TOKEN")

    adapter = create_trello_adapter(api_key, api_token)
    try:
        result = await adapter.get_board("5e88ae2f2f103936713e7e3c")

        assert result.is_ok()
        board = result.unwrap()
        assert board.id == "5e88ae2f2f103936713e7e3c"
        assert board.external_source == "trello"
    finally:
        await adapter._close()


@pytest.mark.skip(reason="TODO: pytest-asyncio bug with skipif + async fixtures - requires manual testing")
@pytest.mark.asyncio
async def test_get_card_not_found():
    """Testa buscar card inexistente."""
    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")

    if not api_key or not api_token:
        pytest.skip("Requires TRELLO_API_KEY and TRELLO_API_TOKEN")

    adapter = create_trello_adapter(api_key, api_token)
    try:
        result = await adapter.get_card("card-inexistente-123")

        assert result.is_err()
        assert "não encontrado" in result.unwrap_err()
    finally:
        await adapter._close()


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
