# -*- coding: utf-8 -*-
"""
Testes unitários para DiscordAdapter.

DOC: openspec/changes/discord-ddd-migration/specs/discord-infrastructure/spec.md
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.discord.infrastructure.adapters import discord_adapter


class TestDiscordAdapter:
    """
    Testa DiscordAdapter.

    O adapter encapsula discord.py para enviar mensagens.
    """

    @pytest.fixture
    def mock_discord_client(self):
        """Mock do cliente discord.py."""
        client = MagicMock()
        return client

    @pytest.fixture
    def adapter(self, mock_discord_client):
        """Cria adapter com client mockado."""
        return discord_adapter.DiscordAdapter(client=mock_discord_client)

    @pytest.mark.asyncio
    async def test_send_message_envia_texto_para_canal(
        self,
        adapter,
        mock_discord_client,
    ):
        """
        DOC: specs/discord-infrastructure/spec.md
        Scenario: Enviar mensagem via adapter

        WHEN adapter.send_message(channel_id, content) é chamado
        THEN SHALL usar discord.py client para enviar mensagem
        """
        # Setup - mock do canal
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock(return_value=MagicMock(id="123"))

        mock_discord_client.fetch_channel = AsyncMock(return_value=mock_channel)

        # Act
        result = await adapter.send_message(
            channel_id="123456789",
            content="Mensagem de teste",
        )

        # Assert
        mock_channel.send.assert_called_once_with("Mensagem de teste")
        assert result == "123"

    @pytest.mark.asyncio
    async def test_send_message_com_embed(
        self,
        adapter,
        mock_discord_client,
    ):
        """
        DOC: specs/discord-infrastructure/spec.md
        Scenario: Enviar embed via adapter

        WHEN adapter.send_embed() é chamado com dados de embed
        THEN SHALL enviar Discord Embed com título, descrição e cor
        """
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock(return_value=MagicMock(id="456"))
        mock_discord_client.fetch_channel = AsyncMock(return_value=mock_channel)

        # Act
        result = await adapter.send_embed(
            channel_id="123456789",
            title="Titulo Teste",
            description="Descrição Teste",
            color=3447003,  # Azul
            fields=[],
        )

        # Assert - embed foi enviado
        assert mock_channel.send.called
        call_args = mock_channel.send.call_args
        embed = call_args[0][0]

        assert embed.title.value == "Titulo Teste"
        assert embed.description == "Descrição Teste"
        assert embed.color.value == 3447003
        assert result == "456"

    @pytest.mark.asyncio
    async def test_send_buttons(
        self,
        adapter,
        mock_discord_client,
    ):
        """
        DOC: specs/discord-infrastructure/spec.md
        Scenario: Enviar botões via adapter

        WHEN adapter.send_buttons() é chamado
        THEN SHALL enviar View com botões
        """
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock(return_value=MagicMock(id="789"))
        mock_discord_client.fetch_channel = AsyncMock(return_value=mock_channel)

        buttons = [
            {"id": "btn1", "label": "Botão 1", "style": "primary"},
            {"id": "btn2", "label": "Botão 2", "style": "danger"},
        ]

        # Act
        result = await adapter.send_buttons(
            channel_id="123456789",
            text="Escolha:",
            buttons=buttons,
        )

        # Assert - View com botões foi enviada
        assert mock_channel.send.called
        assert result == "789"

    @pytest.mark.asyncio
    async def test_fetch_messages_retorna_historico(
        self,
        adapter,
        mock_discord_client,
    ):
        """
        DOC: specs/discord-infrastructure/spec.md
        Scenario: Buscar histórico via adapter

        WHEN adapter.fetch_messages(channel_id, limit) é chamado
        THEN SHALL retornar lista de mensagens do Discord API
        """
        # Setup - mensagens mockadas
        mock_msg1 = MagicMock()
        mock_msg1.id = "111"
        mock_msg1.content = "Msg 1"
        mock_msg1.author = MagicMock()
        mock_msg1.author.id = "user1"
        mock_msg1.author.bot = False

        mock_msg2 = MagicMock()
        mock_msg2.id = "222"
        mock_msg2.content = "Msg 2"
        mock_msg2.author = MagicMock()
        mock_msg2.author.id = "user2"
        mock_msg2.author.bot = False

        mock_channel = MagicMock()
        mock_channel.history = AsyncMock(return_value=[mock_msg1, mock_msg2])
        mock_discord_client.fetch_channel = AsyncMock(return_value=mock_channel)

        # Act
        messages = await adapter.fetch_messages(
            channel_id="123456789",
            limit=10,
        )

        # Assert
        assert len(messages) == 2
        assert messages[0].id == "111"
        assert messages[1].id == "222"
