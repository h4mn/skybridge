# -*- coding: utf-8 -*-
"""
SendEmbedCommand.

Comando CQRS para enviar mensagem formatada (Embed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from ...domain.value_objects import ChannelId


@dataclass
class EmbedField:
    """Campo de embed."""

    name: str
    value: str
    inline: bool = False


@dataclass
class EmbedData:
    """Dados de embed Discord."""

    title: str
    description: str | None = None
    color: str = "azul"  # azul, verde, vermelho, amarelo, roxo
    fields: list[EmbedField] = field(default_factory=list)
    footer: str | None = None
    thumbnail_url: str | None = None
    image_url: str | None = None


@dataclass(frozen=True)
class SendEmbedCommand:
    """
    Command para enviar embed Discord.
    """

    channel_id: ChannelId
    embed: EmbedData

    @classmethod
    def create(
        cls,
        channel_id: str,
        title: str,
        description: str | None = None,
        color: str = "azul",
        fields: list[dict] | None = None,
        footer: str | None = None,
    ) -> Self:
        """
        Factory method.

        Args:
            channel_id: ID do canal
            title: Título do embed
            description: Descrição (opcional)
            color: Cor do embed
            fields: Lista de campos [{name, value, inline}]
            footer: Texto do rodapé (opcional)

        Returns:
            Nova instância do comando
        """
        embed_fields = []
        if fields:
            for f in fields:
                embed_fields.append(
                    EmbedField(
                        name=f["name"],
                        value=f["value"],
                        inline=f.get("inline", False),
                    )
                )

        return cls(
            channel_id=ChannelId(channel_id),
            embed=EmbedData(
                title=title,
                description=description,
                color=color,
                fields=embed_fields,
                footer=footer,
            ),
        )
