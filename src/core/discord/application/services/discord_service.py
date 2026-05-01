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
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum

# Lazy imports para evitar colisao de namespace com tests/unit/core/discord/
# durante coleta do pytest. discord.py e importado apenas quando necessario.
if TYPE_CHECKING:
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

    def __init__(self, client=None):
        """
        Inicializa o serviço.

        Args:
            client: Instância do cliente Discord (opcional para testes)
        """
        self._client = client
        self._views_by_message: Dict[int, Any] = {}
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

    def set_client(self, client):
        """Define o cliente Discord."""
        self._client = client

    @property
    def client(self):
        """Retorna o cliente Discord (read-only)."""
        return self._client

    async def send_message(
        self,
        channel_id: str,
        content: str,
        reply_to: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Envia uma mensagem simples para um canal.

        Args:
            channel_id: ID do canal Discord
            content: Conteúdo da mensagem
            reply_to: ID da mensagem para quote-reply (opcional)

        Returns:
            Mensagem enviada ou None se erro
        """
        import discord as _discord

        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(channel_id))
            reference = None
            if reply_to:
                reference = _discord.MessageReference(
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
    ) -> Optional[Any]:
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
        from discord import Embed as _Embed

        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(channel_id))

            embed = _Embed(title=title, description=description, color=color)

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
    ) -> Any:
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
        import discord as _discord

        # View customizada com callback genérico
        class DDDView(_discord.ui.View):
            def __init__(self, timeout: Optional[float] = None):
                super().__init__(timeout=timeout)

            async def _handle_button_click(self, interaction: _discord.Interaction, button):
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
                "primary": _discord.ButtonStyle.primary,
                "success": _discord.ButtonStyle.success,
                "danger": _discord.ButtonStyle.danger,
                "secondary": _discord.ButtonStyle.secondary,
            }
            style = style_map.get(btn_config.style, _discord.ButtonStyle.primary)

            button = _discord.ui.Button(
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
    ) -> Any:
        """
        Cria uma View Discord com menu Select.

        Mesmo padrão dos botões que funcionam: classe interna + add_item.
        """
        import discord as _discord

        # View customizada (igual DDDView dos botões)
        class SelectView(_discord.ui.View):
            def __init__(self, timeout: Optional[float] = None):
                super().__init__(timeout=timeout)

            async def _handle_select(self, interaction: _discord.Interaction, select):
                """Callback genérico para Select - apenas defer."""
                try:
                    await interaction.response.defer()
                except Exception as e:
                    print(f"[SelectView] Erro no defer: {e}")

        view = SelectView(timeout=timeout)

        # Cria os SelectOptions
        select_options = [
            _discord.SelectOption(
                label=opt["label"],
                value=opt["value"],
                description=opt.get("description"),
                emoji=opt.get("emoji"),
            )
            for opt in options
        ]

        # Cria o Select
        select = _discord.ui.Select(
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
    ) -> Optional[Any]:
        """
        Envia menu suspenso (Select) para canal Discord.

        Args:
            channel_id: ID do canal
            placeholder: Texto do placeholder
            options: Lista de {label, value, description, emoji}

        Returns:
            Mensagem enviada ou None se erro
        """
        from discord import Embed as _Embed

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
            embed = _Embed(title="Selecione uma opção", description=placeholder)
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
    ) -> Optional[Any]:
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
        from discord import Embed as _Embed

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
                embed = _Embed.from_dict(embed_data)
            else:
                embed = _Embed(title=title, description=description, color=3447003)

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
    ) -> Optional[Any]:
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
        from discord import Embed as _Embed

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
            embed = _Embed(
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
    ) -> Optional[Any]:
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
        from discord import Embed as _Embed

        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))

            kwargs = {}
            if content is not None:
                kwargs["content"] = content
            if embed is not None:
                kwargs["embed"] = _Embed.from_dict(embed)

            msg = await message.edit(**kwargs)
            return msg
        except Exception as e:
            print(f"Erro ao editar mensagem: {e}")
            return None

    async def get_history(
        self,
        channel_id,
        limit: int = 20,
    ) -> List[Any]:
        """
        Busca histórico de mensagens de um canal.

        Args:
            channel_id: ID do canal (str ou ChannelId VO)
            limit: Número máximo de mensagens (1-100)

        Returns:
            Lista de mensagens em ordem cronológica reversa
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(str(channel_id)))
            messages: List[Any] = []
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

    # =============================================================================
    # FÓRUNS DISCORD
    # =============================================================================

    async def list_forum_posts(
        self,
        channel_id: str,
        limit: int = 20,
        archived: bool = False,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Lista posts de um canal de fórum com paginação.

        Args:
            channel_id: ID do canal de fórum
            limit: Máximo de posts a retornar
            archived: Incluir posts arquivados

        Returns:
            Lista de posts ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            from ..presentation.tools.dto.forum_dto import ForumPostDTO

            channel = await self._client.fetch_channel(int(channel_id))
            posts = []

            async for thread in channel.archived_threads(limit=limit) if archived else channel.threads(limit=limit):
                post_dto = ForumPostDTO.from_discord_thread(thread)
                posts.append({
                    "id": post_dto.id,
                    "title": post_dto.title,
                    "content": post_dto.content,
                    "author_id": post_dto.author_id,
                    "author_name": post_dto.author_name,
                    "created_at": post_dto.created_at.isoformat() if post_dto.created_at else None,
                    "archived": post_dto.archived,
                    "locked": post_dto.locked,
                    "total_messages": post_dto.total_messages,
                })

            return posts
        except Exception as e:
            print(f"Erro ao listar posts: {e}")
            return None

    async def create_forum_post(
        self,
        channel_id: str,
        title: str,
        content: str,
        tags: Optional[List[int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um novo post em um canal de fórum.

        Args:
            channel_id: ID do canal de fórum
            title: Título do post
            content: Conteúdo do post
            tags: Lista de IDs de tags a aplicar

        Returns:
            Dados do post criado ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            from ..presentation.tools.dto.forum_dto import ForumPostDTO

            channel = await self._client.fetch_channel(int(channel_id))

            # Criar thread (post) no fórum
            thread = await channel.create_thread(
                name=title,
                content=content,
                applied_tags=tags or [],
            )

            post_dto = ForumPostDTO.from_discord_thread(thread)

            return {
                "id": post_dto.id,
                "title": post_dto.title,
                "content": post_dto.content,
                "author_id": post_dto.author_id,
                "created_at": post_dto.created_at.isoformat() if post_dto.created_at else None,
                "url": thread.jump_url if hasattr(thread, 'jump_url') else f"https://discord.com/channels/{thread.guild.id}/{thread.id}",
                "status": "success"
            }
        except Exception as e:
            print(f"Erro ao criar post: {e}")
            return None

    async def get_forum_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes completos de um post específico.

        Args:
            post_id: ID do post (thread)

        Returns:
            Dados do post ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            from ..presentation.tools.dto.forum_dto import ForumPostDTO, ForumCommentDTO

            thread = await self._client.fetch_channel(int(post_id))
            post_dto = ForumPostDTO.from_discord_thread(thread)

            # Buscar comentários
            comments = []
            async for msg in thread.history(limit=50):
                if msg.author.id != thread.owner_id:  # Não duplicar o post principal
                    comment_dto = ForumCommentDTO.from_discord_message(msg, post_id)
                    comments.append({
                        "id": comment_dto.id,
                        "content": comment_dto.content,
                        "author_id": comment_dto.author_id,
                        "author_name": comment_dto.author_name,
                        "created_at": comment_dto.created_at.isoformat() if comment_dto.created_at else None,
                    })

            return {
                "id": post_dto.id,
                "title": post_dto.title,
                "content": post_dto.content,
                "author_id": post_dto.author_id,
                "author_name": post_dto.author_name,
                "channel_id": post_dto.channel_id,
                "created_at": post_dto.created_at.isoformat() if post_dto.created_at else None,
                "archived": post_dto.archived,
                "locked": post_dto.locked,
                "comments": comments,
                "status": "success"
            }
        except Exception as e:
            print(f"Erro ao obter post: {e}")
            return None

    async def add_forum_comment(
        self,
        post_id: str,
        content: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Adiciona um comentário a um post.

        Args:
            post_id: ID do post (thread)
            content: Conteúdo do comentário

        Returns:
            Dados do comentário criado ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            from ..presentation.tools.dto.forum_dto import ForumCommentDTO

            thread = await self._client.fetch_channel(int(post_id))
            message = await thread.send(content)
            comment_dto = ForumCommentDTO.from_discord_message(message, post_id)

            return {
                "id": comment_dto.id,
                "content": comment_dto.content,
                "author_id": comment_dto.author_id,
                "created_at": comment_dto.created_at.isoformat() if comment_dto.created_at else None,
                "status": "success"
            }
        except Exception as e:
            print(f"Erro ao adicionar comentário: {e}")
            return None

    async def list_forum_comments(
        self,
        post_id: str,
        limit: int = 50,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Lista comentários de um post.

        Args:
            post_id: ID do post (thread)
            limit: Máximo de comentários

        Returns:
            Lista de comentários ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            from ..presentation.tools.dto.forum_dto import ForumCommentDTO

            thread = await self._client.fetch_channel(int(post_id))
            comments = []

            async for msg in thread.history(limit=limit):
                if msg.author.id != thread.owner_id:  # Pular o post principal
                    comment_dto = ForumCommentDTO.from_discord_message(msg, post_id)
                    comments.append({
                        "id": comment_dto.id,
                        "content": comment_dto.content,
                        "author_id": comment_dto.author_id,
                        "author_name": comment_dto.author_name,
                        "created_at": comment_dto.created_at.isoformat() if comment_dto.created_at else None,
                    })

            return comments
        except Exception as e:
            print(f"Erro ao listar comentários: {e}")
            return None

    async def update_forum_post(
        self,
        post_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Edita um post existente.

        Args:
            post_id: ID do post (thread)
            title: Novo título
            content: Novo conteúdo

        Returns:
            Dados atualizados ou None se erro
        """
        import discord as _discord

        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            thread = await self._client.fetch_channel(int(post_id))

            kwargs = {}
            if title is not None:
                kwargs["name"] = title
            if content is not None:
                kwargs["content"] = content

            if not kwargs:
                return {"status": "error", "error": "Pelo menos um campo deve ser fornecido"}

            await thread.edit(**kwargs)

            return {
                "id": post_id,
                "edited_at": _discord.utils.utcnow().isoformat(),
                "status": "success"
            }
        except Exception as e:
            print(f"Erro ao atualizar post: {e}")
            return None

    async def close_forum_post(
        self,
        post_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fecha um post como resolvido.

        Args:
            post_id: ID do post (thread)

        Returns:
            Status da operação ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            thread = await self._client.fetch_channel(int(post_id))
            await thread.edit(locked=True)

            return {
                "id": post_id,
                "locked": True,
                "status": "success"
            }
        except Exception as e:
            print(f"Erro ao fechar post: {e}")
            return None

    async def create_forum(
        self,
        guild_id: str,
        name: str,
        layout: str = "classic",
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um novo canal de fórum na guild.

        Args:
            guild_id: ID da guild
            name: Nome do fórum
            layout: Layout ("classic" ou "list")

        Returns:
            Dados do fórum criado ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            guild = await self._client.fetch_guild(int(guild_id))
            forum_channel = await guild.create_forum(name=name, layout=layout)

            return {
                "forum_id": str(forum_channel.id),
                "forum_name": forum_channel.name,
                "guild_id": str(guild.id),
                "status": "success"
            }
        except Exception as e:
            print(f"Erro ao criar fórum: {e}")
            return None

    async def archive_forum(
        self,
        forum_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Arquiva um canal de fórum.

        Args:
            forum_id: ID do canal de fórum

        Returns:
            Status da operação ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(forum_id))
            await channel.edit(archived=True)

            return {
                "forum_id": forum_id,
                "archived": True,
                "status": "success"
            }
        except Exception as e:
            print(f"Erro ao arquivar fórum: {e}")
            return None

    async def delete_forum(
        self,
        forum_id: str,
        confirm: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Deleta um canal de fórum.

        Args:
            forum_id: ID do canal de fórum
            confirm: Confirmação obrigatória (True)

        Returns:
            Status da operação ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        if not confirm:
            return {"status": "error", "error": "confirm=True é obrigatório"}

        try:
            channel = await self._client.fetch_channel(int(forum_id))
            await channel.delete()

            return {
                "forum_id": forum_id,
                "deleted": True,
                "status": "success"
            }
        except Exception as e:
            print(f"Erro ao deletar fórum: {e}")
            return None

    async def update_forum_settings(
        self,
        forum_id: str,
        name: Optional[str] = None,
        layout: Optional[str] = None,
        default_sort_order: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Atualiza configurações de um canal de fórum.

        Args:
            forum_id: ID do canal de fórum
            name: Novo nome
            layout: Novo layout
            default_sort_order: Ordem padrão

        Returns:
            Status da operação ou None se erro
        """
        if not self._client:
            raise RuntimeError("Discord client não configurado")

        try:
            channel = await self._client.fetch_channel(int(forum_id))

            kwargs = {}
            if name is not None:
                kwargs["name"] = name
            if layout is not None:
                kwargs["layout_type"] = layout
            if default_sort_order is not None:
                kwargs["default_sort_order"] = default_sort_order

            if not kwargs:
                return {"status": "error", "error": "Pelo menos um campo deve ser fornecido"}

            await channel.edit(**kwargs)

            return {
                "forum_id": forum_id,
                "updated": list(kwargs.keys()),
                "status": "success"
            }
        except Exception as e:
            print(f"Erro ao atualizar configurações: {e}")
            return None


# Instância global do serviço (singleton)
discord_service = DiscordService()


def get_discord_service(client=None) -> DiscordService:
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
