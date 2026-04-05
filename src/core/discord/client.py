"""
Discord Client Wrapper.

Este módulo encapsula a conexão com o Discord Gateway usando discord.py.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable

from discord import (
    Client,
    Intents,
    ChannelType,
    Message,
    TextChannel,
    DMChannel,
    Thread,
    InteractionType,
    app_commands,
)

from .access import load_access

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def create_discord_client() -> Client:
    """
    Cria cliente Discord configurado com intents necessários.

    Returns:
        Client configurado com CommandTree para slash commands
    """
    intents = Intents.default()
    intents.message_content = True  # Necessário para ler conteúdo
    intents.dm_messages = True  # DMs
    intents.guild_messages = True  # Mensagens de servidor

    # Client com CommandTree para slash commands
    client = Client(
        intents=intents,
    )

    # Criar CommandTree para o client
    tree = app_commands.CommandTree(client)

    # Setup do logger para tree
    import logging
    tree.logger = logging.getLogger("discord.app_commands")

    return client


async def fetch_text_channel(client: Client, channel_id: str) -> TextChannel | DMChannel | Thread:
    """
    Busca canal por ID.

    Args:
        client: Cliente Discord
        channel_id: ID do canal

    Returns:
        Canal encontrado

    Raises:
        ValueError: Se canal não existe ou não é texto
    """
    channel = client.get_channel(int(channel_id))
    if channel is None:
        # Tenta fetch da API
        channel = await client.fetch_channel(int(channel_id))

    if channel is None:
        raise ValueError(f"Canal {channel_id} não encontrado")

    if not isinstance(channel, (TextChannel, DMChannel, Thread)):
        raise ValueError(f"Canal {channel_id} não é um canal de texto")

    return channel


async def fetch_allowed_channel(
    client: Client, channel_id: str
) -> TextChannel | DMChannel | Thread:
    """
    Busca canal validando se está autorizado no access.json.

    Args:
        client: Cliente Discord
        channel_id: ID do canal

    Returns:
        Canal autorizado

    Raises:
        ValueError: Se canal não está autorizado
    """
    channel = await fetch_text_channel(client, channel_id)
    access = load_access()

    if isinstance(channel, DMChannel):
        # DM: verifica se recipient está na allowlist
        if channel.recipient and str(channel.recipient.id) not in access.allow_from:
            raise ValueError(
                f"Canal DM não autorizado — adicione via /discord:access"
            )
    else:
        # Canal de servidor: verifica groups
        lookup_id = str(channel.parent_id) if isinstance(channel, Thread) else str(channel.id)
        if lookup_id not in access.groups:
            raise ValueError(
                f"Canal {channel_id} não está na allowlist — adicione via /discord:access"
            )

    return channel


async def fetch_message(client: Client, channel_id: str, message_id: str) -> Message:
    """
    Busca mensagem específica.

    Args:
        client: Cliente Discord
        channel_id: ID do canal
        message_id: ID da mensagem

    Returns:
        Mensagem encontrada

    Raises:
        ValueError: Se mensagem não encontrada
    """
    channel = await fetch_allowed_channel(client, channel_id)
    message = await channel.fetch_message(int(message_id))
    if message is None:
        raise ValueError(f"Mensagem {message_id} não encontrada")
    return message


def is_dm_channel(channel: TextChannel | DMChannel | Thread) -> bool:
    """Verifica se canal é DM."""
    return isinstance(channel, DMChannel)


def is_thread_channel(channel: TextChannel | DMChannel | Thread) -> bool:
    """Verifica se canal é thread."""
    return isinstance(channel, Thread)


def get_parent_channel_id(channel: TextChannel | DMChannel | Thread) -> str | None:
    """Retorna ID do canal pai se for thread, None caso contrário."""
    if isinstance(channel, Thread):
        return str(channel.parent_id)
    return None


# =============================================================================
# Event Handlers Setup
# =============================================================================


def setup_event_handlers(
    client: Client,
    on_message: Callable[[Message], None] | None = None,
    on_ready: Callable[[], None] | None = None,
) -> None:
    """
    Configura handlers de eventos do Discord client.

    Args:
        client: Cliente Discord
        on_message: Handler para mensagens recebidas
        on_ready: Handler para evento ready
    """

    @client.event
    async def on_ready():
        """Handler para quando cliente está pronto."""
        if client.user:
            logger.info(f"Discord gateway conectado como {client.user}")
        if on_ready:
            on_ready()

    @client.event
    async def on_message(message: Message):
        """Handler para mensagens recebidas."""
        # Ignora mensagens de bots
        if message.author.bot:
            return

        if on_message:
            # Executa handler de forma assíncrona
            try:
                if asyncio.iscoroutinefunction(on_message):
                    await on_message(message)
                else:
                    on_message(message)
            except Exception as e:
                logger.error(f"Erro no handler de mensagem: {e}")

    @client.event
    async def on_error(event: str, *args, **kwargs):
        """Handler para erros."""
        logger.error(f"Erro no evento Discord: {event}")


async def login_and_connect(client: Client, token: str) -> None:
    """
    Faz login e conecta ao Discord Gateway.

    Args:
        client: Cliente Discord
        token: Token do bot

    Raises:
        Exception: Se login falhar
    """
    try:
        await client.login(token)
        await client.connect()
    except Exception as e:
        logger.error(f"Falha ao conectar ao Discord: {e}")
        raise
