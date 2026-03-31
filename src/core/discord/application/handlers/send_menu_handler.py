# -*- coding: utf-8 -*-
"""
SendMenuHandler.

Handler CQRS para SendMenuCommand.

DOC: openspec/changes/discord-ddd-migration/specs/discord-application/spec.md
"""

from __future__ import annotations

from ...domain.entities import Message
from ...domain.repositories import MessageRepository
from ..commands import SendMenuCommand
from .base_handler import BaseHandler, TEMP_AUTHOR_ID, TEMP_MESSAGE_ID
from .handler_result import HandlerResult


class SendMenuHandler(BaseHandler):
    """
    Handler para SendMenuCommand.

    Processa comandos de envio de mensagem com menu dropdown:
    1. Valida acesso ao canal (herdado de BaseHandler)
    2. Valida texto e opções
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

    async def handle(self, command: SendMenuCommand) -> HandlerResult:
        """
        Processa comando de envio de menu.

        Args:
            command: SendMenuCommand com texto e opções

        Returns:
            HandlerResult com sucesso e message_id

        Raises:
            PermissionError: Se canal não está autorizado
            ValueError: Se texto está vazio ou sem opções
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

    def _validate_command(self, command: SendMenuCommand) -> None:
        """
        Valida dados do comando.

        Args:
            command: SendMenuCommand a validar

        Raises:
            ValueError: Se texto está vazio, placeholder vazio ou sem opções
        """
        if not command.text or not command.text.strip():
            raise ValueError("O texto da mensagem não pode estar vazio")

        if not command.placeholder or not command.placeholder.strip():
            raise ValueError("O placeholder não pode estar vazio")

        if not command.options:
            raise ValueError("Ao menos uma opção deve ser fornecida")

    def _create_message(self, command: SendMenuCommand) -> Message:
        """
        Cria entidade Message a partir do Command de menu.

        As opções são formatadas como texto para armazenamento na Message.
        TODO: Adicionar campo menu_data à Message quando suporte disponível.

        Args:
            command: SendMenuCommand com dados do menu

        Returns:
            Message criada com opções formatadas como conteúdo
        """
        content = self._format_menu_as_text(command)

        return Message.create(
            message_id=TEMP_MESSAGE_ID,
            channel_id=str(command.channel_id),
            author_id=TEMP_AUTHOR_ID,
            content=content,
            is_bot=True,
        )

    def _format_menu_as_text(self, command: SendMenuCommand) -> str:
        """
        Formata menu como texto para armazenamento.

        Args:
            command: SendMenuCommand a formatar

        Returns:
            String com opções formatadas em Markdown
        """
        lines = [command.text]
        lines.append(f"_Placeholder: {command.placeholder}_")

        for option in command.options:
            # Formata: [emoji] Label - description (value)
            parts = []

            if option.emoji:
                parts.append(f"{option.emoji}")

            parts.append(f"**{option.label}**")

            if option.description:
                parts.append(f"- {option.description}")

            parts.append(f"(`{option.value}`)")

            if option.default:
                parts.append("[DEFAULT]")

            lines.append(f"  - {' '.join(parts)}")

        return "\n".join(lines)
