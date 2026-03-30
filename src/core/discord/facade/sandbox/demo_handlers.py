# -*- coding: utf-8 -*-
"""
Demonstrações dos Handlers Discord.

Exemplos de uso dos Command/Query Handlers implementados.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

from ...application.commands import (
    SendButtonsCommand,
    SendEmbedCommand,
    SendMessageCommand,
)
from ...application.handlers import (
    FetchMessagesHandler,
    ListThreadsHandler,
    SendButtonsHandler,
    SendEmbedHandler,
    SendMessageHandler,
)
from ...application.queries import FetchMessagesQuery, ListThreadsQuery
from ...domain.repositories import ChannelRepository, MessageRepository


async def demo_send_message():
    """
    Demonstração: SendMessageHandler.

    Envia uma mensagem de texto simples.
    """
    print("[DEMO] Demo: SendMessageHandler")
    print("-" * 50)

    # Setup - mocks para demonstração
    mock_channel_repo = AsyncMock(spec=ChannelRepository)
    mock_channel_repo.is_authorized = AsyncMock(return_value=True)

    mock_message_repo = AsyncMock(spec=MessageRepository)
    mock_message_repo.save = AsyncMock()

    mock_event_publisher = AsyncMock()

    # Criar handler
    handler = SendMessageHandler(
        channel_repository=mock_channel_repo,
        message_repository=mock_message_repo,
        event_publisher=mock_event_publisher,
    )

    # Criar comando
    command = SendMessageCommand.create(
        channel_id="123456789",
        text="Olá! Esta é uma demonstração do SendMessageHandler.",
    )

    # Executar
    result = await handler.handle(command)

    print(f"[OK] Mensagem enviada!")
    print(f"   Message ID: {result.message_id}")
    print(f"   Success: {result.success}")
    print()


async def demo_send_embed():
    """
    Demonstração: SendEmbedHandler.

    Envia uma mensagem formatada com embed.
    """
    print("[DEMO] Demo: SendEmbedHandler")
    print("-" * 50)

    # Setup
    mock_channel_repo = AsyncMock(spec=ChannelRepository)
    mock_channel_repo.is_authorized = AsyncMock(return_value=True)

    mock_message_repo = AsyncMock(spec=MessageRepository)
    mock_message_repo.save = AsyncMock()

    mock_event_publisher = AsyncMock()

    # Criar handler
    handler = SendEmbedHandler(
        channel_repository=mock_channel_repo,
        message_repository=mock_message_repo,
        event_publisher=mock_event_publisher,
    )

    # Criar comando com embed colorido
    command = SendEmbedCommand.create(
        channel_id="123456789",
        title="[ROCKET] Embed de Demonstração",
        description="Este é um exemplo de embed com múltiplos campos.",
        color="verde",
        fields=[
            {"name": "Campo 1", "value": "Valor 1"},
            {"name": "Campo 2", "value": "Valor 2", "inline": True},
            {"name": "Campo 3", "value": "Valor 3", "inline": True},
        ],
        footer="Enviado via Discord DDD",
    )

    # Executar
    result = await handler.handle(command)

    print(f"[OK] Embed enviado!")
    print(f"   Title: {command.embed.title}")
    print(f"   Color: {command.embed.color}")
    print(f"   Fields: {len(command.embed.fields)} campos")
    print(f"   Message ID: {result.message_id}")
    print()


async def demo_send_buttons():
    """
    Demonstração: SendButtonsHandler.

    Envia uma mensagem com botões interativos.
    """
    print("[DEMO] Demo: SendButtonsHandler")
    print("-" * 50)

    # Setup
    mock_channel_repo = AsyncMock(spec=ChannelRepository)
    mock_channel_repo.is_authorized = AsyncMock(return_value=True)

    mock_message_repo = AsyncMock(spec=MessageRepository)
    mock_message_repo.save = AsyncMock()

    mock_event_publisher = AsyncMock()

    # Criar handler
    handler = SendButtonsHandler(
        channel_repository=mock_channel_repo,
        message_repository=mock_message_repo,
        event_publisher=mock_event_publisher,
    )

    # Criar comando com botões
    command = SendButtonsCommand.create(
        channel_id="123456789",
        text="Selecione uma ação:",
        buttons=[
            {"id": "confirm", "label": "[OK] Confirmar", "style": "success"},
            {"id": "cancel", "label": "[X] Cancelar", "style": "danger"},
            {"id": "info", "label": "[INFO] Informações", "style": "primary"},
        ],
    )

    # Executar
    result = await handler.handle(command)

    print(f"[OK] Botões enviados!")
    print(f"   Buttons: {len(command.buttons)} botões")
    for btn in command.buttons:
        print(f"      - {btn.label} ({btn.style})")
    print(f"   Message ID: {result.message_id}")
    print()


async def demo_fetch_messages():
    """
    Demonstração: FetchMessagesHandler.

    Busca histórico de mensagens de um canal.
    """
    print("[DEMO] Demo: FetchMessagesHandler")
    print("-" * 50)

    # Setup
    mock_channel_repo = AsyncMock(spec=ChannelRepository)
    mock_channel_repo.is_authorized = AsyncMock(return_value=True)

    mock_message_repo = AsyncMock(spec=MessageRepository)
    # Mock retorna lista vazia (demo)
    from ...domain.entities import Message

    mock_messages = [
        Message.create(
            message_id="1",
            channel_id="123456789",
            author_id="123456",
            content="Mensagem 1",
            is_bot=False,
        ),
        Message.create(
            message_id="2",
            channel_id="123456789",
            author_id="789012",
            content="Mensagem 2",
            is_bot=False,
        ),
    ]
    mock_message_repo.get_history = AsyncMock(return_value=mock_messages)

    # Criar handler
    handler = FetchMessagesHandler(
        channel_repository=mock_channel_repo,
        message_repository=mock_message_repo,
    )

    # Criar query
    query = FetchMessagesQuery.create(
        channel_id="123456789",
        limit=10,
    )

    # Executar
    result = await handler.handle(query)

    print(f"[OK] Mensagens recuperadas!")
    print(f"   Total: {result.total} mensagens")
    for msg in result.messages:
        print(f"      - {msg.id}: {str(msg.content)[:40]}...")
    print()


async def demo_list_threads():
    """
    Demonstração: ListThreadsHandler.

    Lista threads de um canal.
    """
    print("[DEMO] Demo: ListThreadsHandler")
    print("-" * 50)

    # Setup
    mock_channel_repo = AsyncMock(spec=ChannelRepository)
    mock_channel_repo.is_authorized = AsyncMock(return_value=True)

    mock_thread_repo = AsyncMock()
    from ...domain.entities import Thread

    mock_threads = [
        Thread.create(
            thread_id="1",
            name="Thread Discussão",
            parent_channel_id="123456789",
            root_message_id="111111",
            guild_id="999999999",
        ),
        Thread.create(
            thread_id="2",
            name="Thread Dúvidas",
            parent_channel_id="123456789",
            root_message_id="222222",
            guild_id="999999999",
        ),
    ]
    mock_thread_repo.list_threads = AsyncMock(return_value=mock_threads)

    # Criar handler
    handler = ListThreadsHandler(
        channel_repository=mock_channel_repo,
        thread_repository=mock_thread_repo,
    )

    # Criar query
    query = ListThreadsQuery.create(
        channel_id="123456789",
        include_archived=False,
    )

    # Executar
    result = await handler.handle(query)

    print(f"[OK] Threads listadas!")
    print(f"   Total: {result.total} threads")
    for thread in result.threads:
        print(f"      - {thread.name} (ativo: {thread.is_active()})")
    print()


async def run_all_demos():
    """
    Executa todas as demonstrações em sequencia.
    """
    print("\n" + "=" * 60)
    print("DISCORD DDD - SANDBOX DEMONSTRATIONS")
    print("=" * 60)
    print()

    await demo_send_message()
    await demo_send_embed()
    await demo_send_buttons()
    await demo_fetch_messages()
    await demo_list_threads()

    print("=" * 60)
    print("TODAS AS DEMONSTRACOES CONCLUIDAS!")
    print("=" * 60)


# Para executar as demos:
# python -m src.core.discord.facade.sandbox
