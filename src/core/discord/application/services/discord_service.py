# -*- coding: utf-8 -*-
"""
Discord Service - Fachada da Application Layer.

Este serviço fornece uma API unificada para operações do Discord,
delegando para os handlers apropriados.

Uso:
    from src.core.discord.application.services.discord_service import discord_service

    # Enviar mensagem simples
    await discord_service.send_message(channel_id="123", content="Olá!")

    # Enviar embed com botões
    await discord_service.send_embed(
        channel_id="123",
        title="Portfolio",
        fields=[...]
    )

    # Enviar botões de confirmação
    await discord_service.send_buttons(
        channel_id="123",
        title="Confirmar Ordem",
        buttons=[
            {"label": "Confirmar", "style": "success", "custom_id": "confirm"},
            {"label": "Cancelar", "style": "danger", "custom_id": "cancel"}
        ]
    )
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

import discord
from discord import Embed, Color

# Adicionar caminho do projeto
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class ButtonStyle(Enum):
    """Estilos de botão Discord."""
    PRIMARY = "primary"
    SUCCESS = "success"
    DANGER = "danger"
    SECONDARY = "secondary"


@dataclass
class ButtonConfig:
    """Configuração de um botão."""
    label: str
    style: str
    custom_id: str
    disabled: bool = False


@dataclass
class EmbedField:
    """Campo de embed Discord."""
    name: str
    value: str
    inline: bool = False


@dataclass
class MessageOptions:
    """Opções para envio de mensagem."""
    content: Optional[str] = None
    embed: Optional[dict] = None
    buttons: Optional[List[ButtonConfig]] = None
    components: Optional[List[dict]] = None


class DiscordService:
    """
    Fachada para operações do Discord.

    Este serviço simplifica a interação com o Discord, fornecendo
    métodos de alto nível que abstraem a complexidade do discord.py.
    """

    def __init__(self, client: Optional[discord.Client] = None):
        """
        Inicializa o serviço.

        Args:
            client: Instância do cliente Discord (opcional para testes)
        """
        self._client = client
        self._views_by_message: Dict[int, discord.ui.View] = {}
        self._progress_trackers: Dict[str, str] = {}  # tracking_id -> message_id

    def is_ready(self) -> bool:
        """Verifica se o Discord client está pronto."""
        if not self._client:
            return False
        return self._client.is_ready()

    async def ensure_ready(self, timeout: float = 5.0) -> bool:
        """
        Aguarda o Discord client estar pronto.

        Args:
            timeout: Tempo máximo de espera em segundos

        Returns:
            True se ficou pronto, False se timeout
        """
        if not self._client:
            return False

        if self._client.is_ready():
            return True

        try:
            import asyncio
            await asyncio.wait_for(self._client.wait_until_ready(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def set_client(self, client: discord.Client):
        """Define o cliente Discord."""
        self._client = client

    async def send_message(
        self,
        channel_id: str,
        content: str,
        reply_to: Optional[str] = None,
    ) -> Optional[discord.Message]:
        """
        Envia uma mensagem simples para um canal.

        Args:
            channel_id: ID do canal Discord
            content: Conteúdo da mensagem
            reply_to: ID da mensagem para quote-reply (opcional)

        Returns:
            Mensagem enviada ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(channel_id))
            reference = None
            if reply_to:
                reference = discord.MessageReference(
                    message_id=int(reply_to),
                    channel_id=int(channel_id),
                    fail_if_not_exists=False,
                )
            msg = await channel.send(content=content, reference=reference)
            return msg
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return None

    async def send_embed(
        self,
        channel_id: str,
        title: str,
        description: Optional[str] = None,
        color: int = 3447003,  # Azul padrão
        fields: Optional[List[EmbedField]] = None,
        footer: Optional[str] = None
    ) -> Optional[discord.Message]:
        """
        Envia um embed para um canal.

        Args:
            channel_id: ID do canal Discord
            title: Título do embed
            description: Descrição do embed
            color: Cor do embed (decimal)
            fields: Lista de campos do embed
            footer: Texto do rodapé

        Returns:
            Mensagem enviada ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(channel_id))

            embed = Embed(title=title, description=description, color=color)

            if fields:
                for field in fields:
                    embed.add_field(
                        name=field.name,
                        value=field.value,
                        inline=field.inline
                    )

            if footer:
                embed.set_footer(text=footer)

            msg = await channel.send(embed=embed)
            return msg
        except Exception as e:
            print(f"Erro ao enviar embed: {e}")
            return None

    def create_view(
        self,
        buttons: List[ButtonConfig],
        timeout: Optional[float] = None
    ) -> discord.ui.View:
        """
        Cria uma View Discord com botões.

        CORREÇÃO 3: Adiciona callbacks aos botões para evitar "Esta interação falhou".
        Os callbacks apenas fazem defer() - o processamento real é feito pelo
        on_interaction_create global via MCPButtonAdapter.

        Args:
            buttons: Lista de configurações de botão
            timeout: Timeout da View (None = nunca expira)

        Returns:
            View configurada com botões e callbacks
        """
        # View customizada com callback genérico
        class DDDView(discord.ui.View):
            def __init__(self, timeout: Optional[float] = None):
                super().__init__(timeout=timeout)

            async def _handle_button_click(self, interaction: discord.Interaction, button):
                """
                Callback genérico para todos os botões.

                Apenas faz defer para evitar timeout.
                O processamento real é feito pelo on_interaction_create global.

                NOTA: O parâmetro `button` é obrigatório mesmo que não usado,
                caso contrário o callback não é chamado (discord.py requirement).
                """
                import sys
                sys.stderr.write(f"[DDDView._handle_button_click] CHAMADO! custom_id={interaction.data.get('custom_id') if interaction.data else 'none'}\n")
                sys.stderr.flush()
                try:
                    await interaction.response.defer()
                    sys.stderr.write(f"[DDDView._handle_button_click] Defer OK!\n")
                    sys.stderr.flush()
                except Exception as e:
                    sys.stderr.write(f"[DDDView] Erro no defer: {e}\n")
                    sys.stderr.flush()

        view = DDDView(timeout=timeout)

        for btn_config in buttons:
            style_map = {
                "primary": discord.ButtonStyle.primary,
                "success": discord.ButtonStyle.success,
                "danger": discord.ButtonStyle.danger,
                "secondary": discord.ButtonStyle.secondary,
            }
            style = style_map.get(btn_config.style, discord.ButtonStyle.primary)

            button = discord.ui.Button(
                label=btn_config.label,
                style=style,
                custom_id=btn_config.custom_id,
                disabled=btn_config.disabled,
            )
            # Adiciona callback genérico
            button.callback = view._handle_button_click
            view.add_item(button)

        return view

    def create_select_view(
        self,
        placeholder: str,
        options: List[dict],
        timeout: Optional[float] = None
    ) -> discord.ui.View:
        """
        Cria uma View Discord com menu Select.

        Mesmo padrão dos botões que funcionam: classe interna + add_item.
        """
        # View customizada (igual DDDView dos botões)
        class SelectView(discord.ui.View):
            def __init__(self, timeout: Optional[float] = None):
                super().__init__(timeout=timeout)

            async def _handle_select(self, interaction: discord.Interaction, select):
                """Callback genérico para Select - apenas defer."""
                try:
                    await interaction.response.defer()
                except Exception as e:
                    print(f"[SelectView] Erro no defer: {e}")

        view = SelectView(timeout=timeout)

        # Cria os SelectOptions
        select_options = [
            discord.SelectOption(
                label=opt["label"],
                value=opt["value"],
                description=opt.get("description"),
                emoji=opt.get("emoji"),
            )
            for opt in options
        ]

        # Cria o Select
        select = discord.ui.Select(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=select_options
        )

        # Callback genérico (igual botões)
        select.callback = view._handle_select

        # Adiciona à View
        view.add_item(select)

        return view

    async def send_menu(
        self,
        channel_id: str,
        placeholder: str,
        options: List[dict],
    ) -> Optional[discord.Message]:
        """
        Envia menu suspenso (Select) para canal Discord.

        Args:
            channel_id: ID do canal
            placeholder: Texto do placeholder
            options: Lista de {label, value, description, emoji}

        Returns:
            Mensagem enviada ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        # Aguarda Discord estar pronto
        if not self._client.is_ready():
            if not await self.ensure_ready(timeout=5.0):
                raise RuntimeError("Discord client não está pronto")

        try:
            channel = await self._client.fetch_channel(int(channel_id))
            view = self.create_select_view(placeholder, options, timeout=None)

            # Envia com embed (como send_buttons que funciona)
            embed = Embed(title="Selecione uma opção", description=placeholder)
            msg = await channel.send(embed=embed, view=view)

            self._views_by_message[msg.id] = view
            return msg
        except Exception as e:
            print(f"Erro ao enviar menu: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def send_buttons(
        self,
        channel_id: str,
        title: str,
        description: Optional[str] = None,
        buttons: Optional[List[ButtonConfig]] = None,
        embed_data: Optional[dict] = None
    ) -> Optional[discord.Message]:
        """
        Envia um embed com botões interativos.

        Args:
            channel_id: ID do canal Discord
            title: Título do embed
            description: Descrição do embed
            buttons: Lista de configurações de botão
            embed_data: Dados completos do embed (sobrescreve title/description)

        Returns:
            Mensagem enviada ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        # Aguarda Discord estar pronto (até 5 segundos)
        if not self._client.is_ready():
            if not await self.ensure_ready(timeout=5.0):
                raise RuntimeError("Discord client não está pronto. Tente novamente em instantes.")

        if not buttons:
            raise ValueError("Ao menos um botão é necessário")

        try:
            channel = await self._client.fetch_channel(int(channel_id))

            # Criar embed
            if embed_data:
                embed = Embed.from_dict(embed_data)
            else:
                embed = Embed(title=title, description=description, color=3447003)

            # Criar view com botões
            view = self.create_view(buttons, timeout=None)

            msg = await channel.send(embed=embed, view=view)

            # Guardar referência da view
            self._views_by_message[msg.id] = view

            return msg
        except Exception as e:
            print(f"Erro ao enviar botões: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def send_progress(
        self,
        channel_id: str,
        title: str,
        current: int,
        total: int,
        status: Optional[str] = None,
        tracking_id: Optional[str] = None
    ) -> Optional[discord.Message]:
        """
        Envia ou atualiza indicador de progresso.

        Args:
            channel_id: ID do canal Discord
            title: Título do progresso
            current: Valor atual
            total: Valor total
            status: Status adicional
            tracking_id: ID de tracking (se fornecido, atualiza mensagem existente)

        Returns:
            Mensagem enviada/editada ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            percentage = int((current / total) * 100) if total > 0 else 0
            bar_length = 20
            filled = int((current / total) * bar_length) if total > 0 else 0
            bar = "█" * filled + "░" * (bar_length - filled)

            description = f"```\n{bar} {percentage}%\n```"
            if status:
                description += f"\n{status}"

            channel = await self._client.fetch_channel(int(channel_id))
            embed = Embed(
                title=f"⏳ {title}",
                description=description,
                color=16776960  # Amarelo
            )
            embed.add_field(name="Progresso", value=f"{current}/{total}", inline=True)

            # Se tem tracking_id e mensagem existe, atualiza
            if tracking_id and tracking_id in self._progress_trackers:
                message_id = self._progress_trackers[tracking_id]
                try:
                    message = await channel.fetch_message(int(message_id))
                    await message.edit(embed=embed)
                    return message
                except Exception:
                    # Mensagem foi deletada ou erro, criar nova
                    pass

            # Cria nova mensagem
            msg = await channel.send(embed=embed)

            # Salva tracking se fornecido
            if tracking_id:
                self._progress_trackers[tracking_id] = str(msg.id)

            return msg
        except Exception as e:
            print(f"Erro ao enviar progresso: {e}")
            return None

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        embed: Optional[dict] = None
    ) -> Optional[discord.Message]:
        """
        Edita uma mensagem existente.

        Args:
            channel_id: ID do canal
            message_id: ID da mensagem
            content: Novo conteúdo
            embed: Novo embed (dict)

        Returns:
            Mensagem editada ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))

            kwargs = {}
            if content is not None:
                kwargs["content"] = content
            if embed is not None:
                kwargs["embed"] = Embed.from_dict(embed)

            msg = await message.edit(**kwargs)
            return msg
        except Exception as e:
            print(f"Erro ao editar mensagem: {e}")
            return None

    async def get_history(
        self,
        channel_id,
        limit: int = 20,
    ) -> List[discord.Message]:
        """
        Busca histórico de mensagens de um canal.

        Args:
            channel_id: ID do canal (str ou ChannelId VO)
            limit: Número máximo de mensagens (1-100)

        Returns:
            Lista de discord.Message em ordem cronológica reversa
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(str(channel_id)))
            messages: List[discord.Message] = []
            async for msg in channel.history(limit=limit):
                messages.append(msg)
            return messages
        except Exception as e:
            print(f"Erro ao buscar histórico: {e}")
            return []

    async def add_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji: str
    ) -> bool:
        """
        Adiciona uma reação a uma mensagem.

        Args:
            channel_id: ID do canal
            message_id: ID da mensagem
            emoji: Emoji a adicionar

        Returns:
            True se sucesso, False se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            await message.add_reaction(emoji)
            return True
        except Exception as e:
            print(f"Erro ao adicionar reação: {e}")
            return False


# Instância global do serviço (singleton)
discord_service = DiscordService()


def get_discord_service(client: Optional[discord.Client] = None) -> DiscordService:
    """
    Retorna a instância do Discord Service.

    Args:
        client: Cliente Discord para configurar (opcional)

    Returns:
        Instância de DiscordService
    """
    if client:
        discord_service.set_client(client)
    return discord_service
