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

# Testes de integração que requerem credenciais foram movidos para
# tests/integration/kanban/test_trello_integration.py com implementação TDD completa.

class TestTrelloAdapterUnit:
    """Testes unitários sem chamar API."""

    def test_factory_function(self):
        """Testa factory create_trello_adapter."""
        adapter = create_trello_adapter("test-key", "test-token")

        assert adapter.api_key == "test-key"
        assert adapter.api_token == "test-token"

    def test_parse_card_status_from_list_name(self):
        """
        Testa que _parse_card determina status baseado no nome da lista.

        REGRA DE OURO: NÃO EXISTE PADRÃO.
        - Lista reconhecida → CardStatus correspondente
        - Lista NÃO reconhecida → CardStatus.UNKNOWN (requer atenção manual)

        UNKNOWN é usado para marcar cards que precisam de correção manual,
        evitando padrões silenciosos que mascaram problemas de configuração.
        """
        adapter = create_trello_adapter("key", "token")

        # Dados simulados da API do Trello com diferentes nomes de lista
        # Inclui todos os campos necessários para evitar KeyError
        test_cases = [
            # Casos normais - lista reconhecida
            ({"name": "Card 1", "id": "1", "url": "http://trello.com/c1", "list": {"name": "🧠 Brainstorm"}}, CardStatus.BACKLOG),
            ({"name": "Card 2", "id": "2", "url": "http://trello.com/c2", "list": {"name": "📋 A Fazer"}}, CardStatus.TODO),
            ({"name": "Card 3", "id": "3", "url": "http://trello.com/c3", "list": {"name": "🚧 Em Andamento"}}, CardStatus.IN_PROGRESS),
            ({"name": "Card 4", "id": "4", "url": "http://trello.com/c4", "list": {"name": "👀 Em Revisão"}}, CardStatus.REVIEW),
            ({"name": "Card 5", "id": "5", "url": "http://trello.com/c5", "list": {"name": "🚀 Publicar"}}, CardStatus.DONE),
            # Casos de lista não reconhecida ou ausente → UNKNOWN (requer atenção manual)
            ({"name": "Card 6 - Sem lista", "id": "6", "url": "http://trello.com/c6"}, CardStatus.UNKNOWN),
            ({"name": "Card 7 - Lista não reconhecida", "id": "7", "url": "http://trello.com/c7", "list": {"name": "Lista Desconhecida"}}, CardStatus.UNKNOWN),
        ]

        for data, expected_status in test_cases:
            card = adapter._parse_card(data)
            assert card.status == expected_status, f"Card {data['name']} should have status {expected_status}"

