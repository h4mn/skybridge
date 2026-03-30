# -*- coding: utf-8 -*-
"""
HandleButtonClickCommand

Command para processar clique de botão no Discord.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.core.discord.domain.events.button_clicked import ButtonClickedEvent


@dataclass(frozen=True)
class HandleButtonClickCommand:
    """
    Command para processar clique de botão Discord.

    Este command é criado quando um usuário clica em um botão interativo
    e precisa ser processado pelo sistema.

    Attributes:
        interaction_id: ID único da interação Discord
        channel_id: ID do canal onde ocorreu o clique
        message_id: ID da mensagem que continha o botão
        user_id: ID do usuário que clicou
        user_name: Nome do usuário que clicou
        button_label: Texto visível do botão clicado
        button_custom_id: ID customizado do botão (usado para roteamento)
    """

    interaction_id: str
    channel_id: str
    message_id: str
    user_id: str
    user_name: str
    button_label: str
    button_custom_id: str

    def to_event(self) -> ButtonClickedEvent:
        """
        Converte command para Domain Event.

        Returns:
            ButtonClickedEvent pronto para publicação
        """
        return ButtonClickedEvent.create(
            interaction_id=self.interaction_id,
            channel_id=self.channel_id,
            message_id=self.message_id,
            user_id=self.user_id,
            user_name=self.user_name,
            button_label=self.button_label,
            button_custom_id=self.button_custom_id,
        )

    @classmethod
    def from_discord_interaction(cls, interaction) -> HandleButtonClickCommand:
        """
        Cria command a partir de interação Discord.

        Args:
            interaction: Interação Discord (discord.Interaction)

        Returns:
            HandleButtonClickCommand populado
        """
        # NOTA: interaction.data é um DICT, não objeto!
        data = interaction.data if hasattr(interaction, 'data') else {}
        custom_id = data.get('custom_id') if isinstance(data, dict) else None

        if not custom_id:
            raise ValueError("Interação não possui custom_id")

        # Extrair label do botão (se disponível)
        button_label = custom_id  # Fallback
        if isinstance(data, dict) and data.get('values'):
            # Select menu
            values = data.get('values', [])
            button_label = values[0] if values else custom_id

        return cls(
            interaction_id=str(interaction.id),
            channel_id=str(interaction.channel_id),
            message_id=str(interaction.message.id) if interaction.message else "",
            user_id=str(interaction.user.id),
            user_name=interaction.user.name,
            button_label=button_label,
            button_custom_id=custom_id,
        )
