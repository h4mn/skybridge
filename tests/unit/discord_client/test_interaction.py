# -*- coding: utf-8 -*-
"""
Testes para on_interaction_create no Discord client.

NOTA: Arquivo fora da árvore discord/ para evitar conflito de import
com a biblioteca discord.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import discord
from discord import Interaction, InteractionType

from src.core.discord.client import setup_event_handlers


class TestInteractionHandler:
    """
    Testa o handler de interação do Discord client.

    Verifica que cliques de botão são processados e respondidos corretamente.
    """

    @pytest.fixture
    def mock_client(self):
        """Mock do cliente Discord."""
        client = MagicMock()

        # Mock do decorator event que registra e retorna a função
        def event_decorator(func):
            # Registrar o método no client
            setattr(client, func.__name__, func)
            return func

        client.event = event_decorator
        client.user = MagicMock()
        client.user.name = "TestBot"
        return client

    @pytest.fixture
    def mock_interaction(self):
        """Mock de uma interação de botão."""
        interaction = MagicMock(spec=Interaction)
        interaction.type = InteractionType.component
        interaction.data = MagicMock()
        interaction.data.custom_id = "ordem_confirm"
        interaction.data.component_type = 2  # Button

        # Mock do canal
        interaction.channel_id = "123456789"
        interaction.channel = MagicMock()
        interaction.channel.name = "test-channel"
        interaction.channel.id = 123456789

        # Mock da mensagem
        interaction.message = MagicMock()
        interaction.message.id = 987654321

        # Mock do usuário
        interaction.user = MagicMock()
        interaction.user.id = 111222333
        interaction.user.name = "TestUser"
        interaction.user.display_name = "TestUser"

        # Mock do guild
        interaction.guild = MagicMock()
        interaction.guild_id = 555666777

        # Response methods
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        interaction.response.defer = AsyncMock()
        interaction.response.acknowledge = AsyncMock()

        return interaction

    def test_setup_event_handlers_registra_on_interaction_create(
        self,
        mock_client,
    ):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Registrar handler de interação

        WHEN setup_event_handlers é chamado
        THEN SHALL registrar handler on_interaction_create
        """
        # Act
        setup_event_handlers(mock_client)

        # Assert - verificar que o handler foi registrado
        assert hasattr(mock_client, 'on_interaction_create')
        assert callable(mock_client.on_interaction_create)

    @pytest.mark.asyncio
    async def test_on_interaction_create_responde_botao_clique(
        self,
        mock_client,
        mock_interaction,
    ):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Responder clique de botão

        WHEN usuário clica em botão
        THEN SHALL fazer acknowledge da interação
        """
        # Arrange
        setup_event_handlers(mock_client)
        handler = mock_client.on_interaction_create

        # Act
        await handler(mock_interaction)

        # Assert - interação foi respondida
        mock_interaction.response.acknowledge.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_interaction_create_ignora_outras_tipos(
        self,
        mock_client,
        mock_interaction,
    ):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Ignorar interações que não são botões

        WHEN interação não é de componente (botão)
        THEN SHALL ignorar
        """
        # Arrange - mudar tipo para modal
        mock_interaction.type = InteractionType.modal_submit

        setup_event_handlers(mock_client)
        handler = mock_client.on_interaction_create

        # Act
        await handler(mock_interaction)

        # Assert - não respondeu
        mock_interaction.response.acknowledge.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_interaction_create_trata_erro_graciosamente(
        self,
        mock_client,
        mock_interaction,
    ):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Tratamento de erro no handler

        WHEN handler lança exceção
        THEN SHALL logar erro sem crashar
        """
        # Arrange - simulate error no acknowledge
        mock_interaction.response.acknowledge.side_effect = Exception("Test error")
        mock_interaction.response.defer.side_effect = Exception("Defer also failed")

        setup_event_handlers(mock_client)
        handler = mock_client.on_interaction_create

        # Act - não deve crashar
        await handler(mock_interaction)

        # Assert - não crashou (chegamos aqui sem exceção)
        # O erro foi logado mas o teste apenas verifica que não crashou
