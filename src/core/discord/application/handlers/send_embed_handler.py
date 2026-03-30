# -*- coding: utf-8 -*-
"""
SendEmbedHandler.

Handler CQRS para SendEmbedCommand.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
"""

from __future__ import annotations

from ...domain.entities import Message
from ...domain.repositories import MessageRepository
from ..commands import SendEmbedCommand
from .base_handler import BaseHandler, TEMP_AUTHOR_ID, TEMP_MESSAGE_ID
from .handler_result import HandlerResult


# Mapeamento de cores nominais para valores Discord (decimal)
_COLOR_MAP: dict[str, int] = {
    "azul": 3447003,      # #3498db
    "verde": 65280,       # #00ff00
    "vermelho": 16711680, # #ff0000
    "amarelo": 16776960,  # #ffff00
    "roxo": 10181038,     # #9b59b6
    "cinza": 9807270,     # #95a5a6
}


class SendEmbedHandler(BaseHandler):
    """
    Handler para SendEmbedCommand.

    Processa comandos de envio de embed:
    1. Valida acesso ao canal (herdado de BaseHandler)
    2. Valida título do embed
    3. Cria Message com conteúdo formatado como embed
    4. Salva via MessageRepository
    5. Publica MessageSentEvent (herdado de BaseHandler)

    Args:
        channel_repository: Repositório de canais para validação de acesso
        message_repository: Repositório de mensagens para persistência
        event_publisher: Publicador de eventos de domínio (async callable)
    """

    def __init__(
        self,
        channel_repository,
        message_repository: MessageRepository,
        event_publisher,
    ) -> None:
        """Inicializa handler com dependências."""
        super().__init__(channel_repository, event_publisher)
        self._message_repo = message_repository

    async def handle(self, command: SendEmbedCommand) -> HandlerResult:
        """
        Processa comando de envio de embed.

        Args:
            command: SendEmbedCommand com dados do embed

        Returns:
            HandlerResult com sucesso e message_id

        Raises:
            PermissionError: Se canal não está autorizado
            ValueError: Se título está vazio ou cor é inválida
        """
        # 1. Validar acesso ao canal (herdado)
        await self._validate_access(command.channel_id)

        # 2. Validar embed
        self._validate_embed(command.embed)

        # 3. Criar Message com conteúdo formatado
        message = self._create_message(command)

        # 4. Salvar no repositório
        await self._message_repo.save(message)

        # 5. Publicar evento de domínio (herdado)
        await self._publish_event(message)

        return HandlerResult.success_with_message(str(message.id))

    def _validate_embed(self, embed) -> None:
        """
        Valida dados do embed.

        Args:
            embed: EmbedData a validar

        Raises:
            ValueError: Se título está vazio
        """
        if not embed.title or not embed.title.strip():
            raise ValueError("O título do embed não pode estar vazio")

    def _create_message(self, command: SendEmbedCommand) -> Message:
        """
        Cria entidade Message a partir do Command de embed.

        O embed é formatado como texto para armazenamento na Message.
        TODO: Adicionar campo embed_data à Message quando suporte disponível.

        Args:
            command: SendEmbedCommand com dados do embed

        Returns:
            Message criada com embed formatado como conteúdo
        """
        content = self._format_embed_as_text(command.embed)

        return Message.create(
            message_id=TEMP_MESSAGE_ID,
            channel_id=str(command.channel_id),
            author_id=TEMP_AUTHOR_ID,
            content=content,
            is_bot=True,
        )

    def _format_embed_as_text(self, embed) -> str:
        """
        Formata embed como texto para armazenamento.

        Args:
            embed: EmbedData a formatar

        Returns:
            String com embed formatado em Markdown
        """
        lines = [f"**{embed.title}**"]

        if embed.description:
            lines.append(embed.description)

        for field in embed.fields:
            lines.append(f"\n**{field.name}**: {field.value}")

        if embed.footer:
            lines.append(f"\n_{embed.footer}_")

        return "\n".join(lines)

    @classmethod
    def get_color_code(cls, color_name: str) -> int:
        """
        Retorna código de cor Discord para nome de cor.

        Args:
            color_name: Nome da cor (azul, verde, vermelho, etc)

        Returns:
            Código de cor Discord (decimal)

        Raises:
            ValueError: Se cor não é reconhecida
        """
        color_lower = color_name.lower()
        if color_lower not in _COLOR_MAP:
            raise ValueError(
                f"Cor '{color_name}' não reconhecida. "
                f"Use: {', '.join(_COLOR_MAP.keys())}"
            )
        return _COLOR_MAP[color_lower]
