# -*- coding: utf-8 -*-
"""
SendMessageHandler.

Handler CQRS para SendMessageCommand.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
"""

from __future__ import annotations

from ...domain.entities import Message
from ...domain.repositories import MessageRepository
from ..commands import SendMessageCommand
from .base_handler import BaseHandler, TEMP_AUTHOR_ID, TEMP_MESSAGE_ID
from .handler_result import HandlerResult


class SendMessageHandler(BaseHandler):
    """
    Handler para SendMessageCommand.

    Processa comandos de envio de mensagem:
    1. Valida acesso ao canal (herdado de BaseHandler)
    2. Valida conteúdo
    3. Cria Message
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
        """
        Inicializa handler com dependências.

        Args:
            channel_repository: Repositório de canais
            message_repository: Repositório de mensagens
            event_publisher: Publicador de eventos
        """
        super().__init__(channel_repository, event_publisher)
        self._message_repo = message_repository

    async def handle(self, command: SendMessageCommand) -> HandlerResult:
        """
        Processa comando de envio de mensagem.

        Args:
            command: SendMessageCommand com dados da mensagem

        Returns:
            HandlerResult com sucesso e message_id

        Raises:
            PermissionError: Se canal não está autorizado
            ValueError: Se conteúdo está vazio
        """
        # 1. Validar acesso ao canal (herdado)
        await self._validate_access(command.channel_id)

        # 2. Validar conteúdo
        self._validate_content(command.content)

        # 3. Criar Message (entidade de domínio)
        message = self._create_message(command)

        # 4. Salvar no repositório
        await self._message_repo.save(message)

        # 5. Publicar evento de domínio (herdado)
        await self._publish_event(message)

        # Retornar resultado de sucesso
        return HandlerResult.success_with_message(str(message.id))

    def _validate_content(self, content) -> None:
        """
        Valida se o conteúdo não está vazio.

        Args:
            content: MessageContent a validar

        Raises:
            ValueError: Se conteúdo está vazio
        """
        if not str(content).strip():
            raise ValueError("Conteúdo da mensagem não pode estar vazio")

    def _create_message(self, command: SendMessageCommand) -> Message:
        """
        Cria entidade Message a partir do Command.

        Args:
            command: SendMessageCommand com dados da mensagem

        Returns:
            Message criada com IDs temporários

        TODO: Adicionar suporte a reply_to quando Message tiver campo
        TODO: Adicionar suporte a files quando Message tiver anexos
        """
        return Message.create(
            message_id=TEMP_MESSAGE_ID,
            channel_id=str(command.channel_id),
            author_id=TEMP_AUTHOR_ID,
            content=str(command.content),
            is_bot=True,
        )
