# -*- coding: utf-8 -*-
"""
Testes unitários para DiscordService.

Testa a fachada da Application Layer que orquestra operações do Discord.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import discord

from src.core.discord.application.services.discord_service import (
    DiscordService,
    ButtonConfig,
    EmbedField,
    ButtonStyle,
    get_discord_service,
)


class TestDiscordService:
    """Testes para DiscordService."""

    @pytest.fixture
    def mock_client(self):
        """Cliente Discord mockado."""
        client = Mock(spec=discord.Client)
        return client

    @pytest.fixture
    def mock_channel(self):
        """Canal Discord mockado."""
        channel = AsyncMock()
        channel.send = AsyncMock(return_value=Mock(id=123))
        return channel

    @pytest.fixture
    def service(self, mock_client):
        """Instância do serviço com cliente mockado."""
        service = DiscordService(client=mock_client)
        return service

    class TestInit:
        """Testes de inicialização."""

        def test_init_without_client(self):
            """Service pode ser criado sem cliente (lazy)."""
            service = DiscordService()
            assert service._client is None

        def test_init_with_client(self, mock_client):
            """Service pode ser criado com cliente."""
            service = DiscordService(client=mock_client)
            assert service._client is mock_client

        def test_set_client(self):
            """Cliente pode ser definido depois."""
            service = DiscordService()
            client = Mock()
            service.set_client(client)
            assert service._client is client

    class TestSendMessage:
        """Testes de envio de mensagem simples."""

        @pytest.mark.asyncio
        async def test_send_message_success(self, service, mock_channel):
            """Envia mensagem simples com sucesso."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            result = await service.send_message(channel_id="123", content="Olá!")

            assert result is not None
            assert result.id == 123
            mock_channel.send.assert_called_once_with(content="Olá!", components=None)

        @pytest.mark.asyncio
        async def test_send_message_with_components(self, service, mock_channel):
            """Envia mensagem com componentes."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)
            components = [{"type": 1, "components": []}]

            await service.send_message(channel_id="123", content="Teste", components=components)

            mock_channel.send.assert_called_once_with(content="Teste", components=components)

        @pytest.mark.asyncio
        async def test_send_message_no_client(self):
            """Erro quando cliente não configurado."""
            service = DiscordService()

            with pytest.raises(RuntimeError, match="Discord client não configurado"):
                await service.send_message(channel_id="123", content="Olá!")

        @pytest.mark.asyncio
        async def test_send_message_error(self, service):
            """Trata erro ao enviar mensagem."""
            service._client.fetch_channel = AsyncMock(side_effect=Exception("Discord error"))

            result = await service.send_message(channel_id="123", content="Olá!")

            assert result is None

    class TestSendEmbed:
        """Testes de envio de embed."""

        @pytest.mark.asyncio
        async def test_send_embed_basic(self, service, mock_channel):
            """Envia embed básico."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            result = await service.send_embed(
                channel_id="123",
                title="Título",
                description="Descrição"
            )

            assert result is not None
            mock_channel.send.assert_called_once()
            call_args = mock_channel.send.call_args
            embed = call_args.kwargs.get("embed")
            assert embed is not None
            assert embed.title == "Título"
            assert embed.description == "Descrição"

        @pytest.mark.asyncio
        async def test_send_embed_with_fields(self, service, mock_channel):
            """Envia embed com campos."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            fields = [
                EmbedField(name="Campo1", value="Valor1"),
                EmbedField(name="Campo2", value="Valor2", inline=True),
            ]

            await service.send_embed(
                channel_id="123",
                title="Título",
                fields=fields
            )

            call_args = mock_channel.send.call_args
            embed = call_args.kwargs.get("embed")
            assert embed is not None

        @pytest.mark.asyncio
        async def test_send_embed_with_footer(self, service, mock_channel):
            """Envia embed com rodapé."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            await service.send_embed(
                channel_id="123",
                title="Título",
                footer="Rodapé"
            )

            call_args = mock_channel.send.call_args
            embed = call_args.kwargs.get("embed")
            assert embed is not None

    class TestCreateView:
        """Testes de criação de View."""

        def test_create_view_single_button(self, service):
            """Cria view com um botão."""
            buttons = [
                ButtonConfig(label="Confirmar", style="success", custom_id="confirm")
            ]

            view = service.create_view(buttons)

            assert isinstance(view, discord.ui.View)
            assert view.timeout is None
            assert len(view.children) == 1
            assert view.children[0].label == "Confirmar"
            assert view.children[0].custom_id == "confirm"

        def test_create_view_multiple_buttons(self, service):
            """Cria view com múltiplos botões."""
            buttons = [
                ButtonConfig(label="Confirmar", style="success", custom_id="confirm"),
                ButtonConfig(label="Cancelar", style="danger", custom_id="cancel"),
            ]

            view = service.create_view(buttons)

            assert len(view.children) == 2

        def test_create_view_with_timeout(self, service):
            """Cria view com timeout."""
            buttons = [ButtonConfig(label="OK", style="primary", custom_id="ok")]

            view = service.create_view(buttons, timeout=60)

            assert view.timeout == 60

        def test_create_view_disabled_button(self, service):
            """Cria view com botão desabilitado."""
            buttons = [
                ButtonConfig(label="Disabled", style="secondary", custom_id="disabled", disabled=True)
            ]

            view = service.create_view(buttons)

            assert view.children[0].disabled is True

        def test_button_style_mapping(self, service):
            """Mapeia corretamente os estilos de botão."""
            style_tests = [
                ("primary", discord.ButtonStyle.primary),
                ("success", discord.ButtonStyle.success),
                ("danger", discord.ButtonStyle.danger),
                ("secondary", discord.ButtonStyle.secondary),
            ]

            for style_name, expected_style in style_tests:
                buttons = [ButtonConfig(label="Test", style=style_name, custom_id="test")]
                view = service.create_view(buttons)
                assert view.children[0].style == expected_style

    class TestSendButtons:
        """Testes de envio de botões."""

        @pytest.mark.asyncio
        async def test_send_buttons_success(self, service, mock_channel):
            """Envia embed com botões."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            buttons = [
                ButtonConfig(label="Confirmar", style="success", custom_id="confirm"),
                ButtonConfig(label="Cancelar", style="danger", custom_id="cancel"),
            ]

            result = await service.send_buttons(
                channel_id="123",
                title="Confirmar Ordem",
                buttons=buttons
            )

            assert result is not None
            mock_channel.send.assert_called_once()
            call_args = mock_channel.send.call_args

            # Verifica embed
            embed = call_args.kwargs.get("embed")
            assert embed is not None
            assert embed.title == "Confirmar Ordem"

            # Verifica view
            view = call_args.kwargs.get("view")
            assert view is not None
            assert isinstance(view, discord.ui.View)

        @pytest.mark.asyncio
        async def test_send_buttons_no_buttons_error(self, service):
            """Erro quando não há botões."""
            with pytest.raises(ValueError, match="Ao menos um botão"):
                await service.send_buttons(
                    channel_id="123",
                    title="Título",
                    buttons=None
                )

        @pytest.mark.asyncio
        async def test_send_buttons_stores_view(self, service, mock_channel):
            """Armazena referência da view enviada."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)
            mock_message = Mock(id=999)
            mock_channel.send.return_value = mock_message

            buttons = [ButtonConfig(label="OK", style="success", custom_id="ok")]

            await service.send_buttons(
                channel_id="123",
                title="Título",
                buttons=buttons
            )

            assert 999 in service._views_by_message
            assert service._views_by_message[999] is not None

    class TestSendProgress:
        """Testes de envio de indicador de progresso."""

        @pytest.mark.asyncio
        async def test_send_progress_basic(self, service, mock_channel):
            """Envia indicador de progresso básico."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            result = await service.send_progress(
                channel_id="123",
                title="Processando",
                current=5,
                total=10
            )

            assert result is not None
            mock_channel.send.assert_called_once()
            call_args = mock_channel.send.call_args
            embed = call_args.kwargs.get("embed")
            assert embed is not None

        @pytest.mark.asyncio
        async def test_send_progress_with_status(self, service, mock_channel):
            """Envia progresso com status."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            await service.send_progress(
                channel_id="123",
                title="Processando",
                current=3,
                total=10,
                status="Aguarde..."
            )

            call_args = mock_channel.send.call_args
            embed = call_args.kwargs.get("embed")
            assert embed is not None

        @pytest.mark.asyncio
        async def test_send_progress_zero_division(self, service, mock_channel):
            """Trata divisão por zero."""
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            result = await service.send_progress(
                channel_id="123",
                title="Processando",
                current=0,
                total=0
            )

            assert result is not None

    class TestEditMessage:
        """Testes de edição de mensagem."""

        @pytest.mark.asyncio
        async def test_edit_message_content(self, service, mock_channel):
            """Edita conteúdo da mensagem."""
            mock_message = Mock()
            mock_message.edit = AsyncMock()
            mock_channel.fetch_message = AsyncMock(return_value=mock_message)
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            result = await service.edit_message(
                channel_id="123",
                message_id="456",
                content="Novo conteúdo"
            )

            assert result is not None
            mock_message.edit.assert_called_once_with(content="Novo conteúdo")

        @pytest.mark.asyncio
        async def test_edit_message_embed(self, service, mock_channel):
            """Edita embed da mensagem."""
            mock_message = Mock()
            mock_message.edit = AsyncMock()
            mock_channel.fetch_message = AsyncMock(return_value=mock_message)
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            embed_dict = {"title": "Novo Título", "description": "Nova Desc"}

            result = await service.edit_message(
                channel_id="123",
                message_id="456",
                embed=embed_dict
            )

            assert result is not None
            mock_message.edit.assert_called_once()

    class TestAddReaction:
        """Testes de adição de reação."""

        @pytest.mark.asyncio
        async def test_add_reaction_success(self, service, mock_channel):
            """Adiciona reação com sucesso."""
            mock_message = Mock()
            mock_message.add_reaction = AsyncMock()
            mock_channel.fetch_message = AsyncMock(return_value=mock_message)
            service._client.fetch_channel = AsyncMock(return_value=mock_channel)

            result = await service.add_reaction(
                channel_id="123",
                message_id="456",
                emoji="✅"
            )

            assert result is True
            mock_message.add_reaction.assert_called_once_with("✅")

        @pytest.mark.asyncio
        async def test_add_reaction_error(self, service):
            """Trata erro ao adicionar reação."""
            service._client.fetch_channel = AsyncMock(side_effect=Exception("Erro"))

            result = await service.add_reaction(
                channel_id="123",
                message_id="456",
                emoji="✅"
            )

            assert result is False


class TestGetDiscordService:
    """Testes para função get_discord_service."""

    def test_get_service_returns_singleton(self):
        """Retorna sempre a mesma instância."""
        service1 = get_discord_service()
        service2 = get_discord_service()
        assert service1 is service2

    def test_get_service_with_client(self):
        """Configura cliente quando fornecido."""
        client = Mock()
        service = get_discord_service(client)
        assert service._client is client


class TestDataClasses:
    """Testes para classes de dados."""

    def test_button_config(self):
        """ButtonConfig armazena dados corretamente."""
        config = ButtonConfig(
            label="Teste",
            style="success",
            custom_id="test_id",
            disabled=True
        )
        assert config.label == "Teste"
        assert config.style == "success"
        assert config.custom_id == "test_id"
        assert config.disabled is True

    def test_embed_field(self):
        """EmbedField armazena dados corretamente."""
        field = EmbedField(
            name="Campo",
            value="Valor",
            inline=True
        )
        assert field.name == "Campo"
        assert field.value == "Valor"
        assert field.inline is True

    def test_button_style_enum(self):
        """ButtonStyle enum tem valores corretos."""
        assert ButtonStyle.PRIMARY.value == "primary"
        assert ButtonStyle.SUCCESS.value == "success"
        assert ButtonStyle.DANGER.value == "danger"
        assert ButtonStyle.SECONDARY.value == "secondary"
