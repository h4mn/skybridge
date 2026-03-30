# -*- coding: utf-8 -*-
"""
SendButtonsHandler.

Handler CQRS para SendButtonsCommand.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
"""

from __future__ import annotations

from ...domain.entities import Message
from ...domain.repositories import MessageRepository
from ..commands import SendButtonsCommand
from .base_handler import BaseHandler, TEMP_AUTHOR_ID, TEMP_MESSAGE_ID
from .handler_result import HandlerResult


class SendButtonsHandler(BaseHandler):
    """
    Handler para SendButtonsCommand.

    Processa comandos de envio de mensagem com botões:
    1. Valida acesso ao canal (herdado de BaseHandler)
    2. Valida texto e botões
    3. Cria Message com conteúdo formatado
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

    async def handle(self, command: SendButtonsCommand) -> HandlerResult:
        """
        Processa comando de envio de botões.

        Args:
            command: SendButtonsCommand com texto e botões

        Returns:
            HandlerResult com sucesso e message_id

        Raises:
            PermissionError: Se canal não está autorizado
            ValueError: Se texto está vazio
        """
        # 1. Validar acesso ao canal (herdado)
        await self._validate_access(command.channel_id)

        # 2. Validar comando
        self._validate_command(command)

        # 3. Criar Message com conteúdo formatado
        message = self._create_message(command)

        # 4. Salvar no repositório
        await self._message_repo.save(message)

        # 5. Publicar evento de domínio (herdado)
        await self._publish_event(message)

        return HandlerResult.success_with_message(str(message.id))

    def _validate_command(self, command: SendButtonsCommand) -> None:
        """
        Valida dados do comando.

        Args:
            command: SendButtonsCommand a validar

        Raises:
            ValueError: Se texto está vazio ou sem botões
        """
        if not command.text or not command.text.strip():
            raise ValueError("O texto da mensagem não pode estar vazio")

        if not command.buttons:
            raise ValueError("Pelo menos um botão deve ser fornecido")

    def _create_message(self, command: SendButtonsCommand) -> Message:
        """
        Cria entidade Message a partir do Command de botões.

        Os botões são formatados como texto para armazenamento na Message.
        TODO: Adicionar campo buttons_data à Message quando suporte disponível.

        Args:
            command: SendButtonsCommand com dados dos botões

        Returns:
            Message criada com botões formatados como conteúdo
        """
        content = self._format_buttons_as_text(command)

        return Message.create(
            message_id=TEMP_MESSAGE_ID,
            channel_id=str(command.channel_id),
            author_id=TEMP_AUTHOR_ID,
            content=content,
            is_bot=True,
        )

    def _format_buttons_as_text(self, command: SendButtonsCommand) -> str:
        """
        Formata botões como texto para armazenamento.

        Args:
            command: SendButtonsCommand a formatar

        Returns:
            String com botões formatados em Markdown
        """
        lines = [command.text]

        for button in command.buttons:
            # Formata: [emoji] Label (style)
            parts = []

            if button.emoji:
                parts.append(f"{button.emoji}")

            parts.append(f"**{button.label}**")

            if button.style != "primary":
                parts.append(f"({button.style})")

            if button.disabled:
                parts.append("[DISABLED]")

            lines.append(f"  `btn:{button.id}` - {' '.join(parts)}")

        return "\n".join(lines)
