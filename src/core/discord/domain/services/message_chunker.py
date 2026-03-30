# -*- coding: utf-8 -*-
"""
MessageChunker - Domain Service.

Serviço de domínio para dividir mensagens longas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ..value_objects import MessageContent


@dataclass
class ChunkResult:
    """Resultado de chunking."""

    chunks: list[MessageContent]
    total: int
    truncated: bool = False


class MessageChunker:
    """
    Domain Service para chunking de mensagens.

    Divide mensagens longas em chunks respeitando limite Discord.
    """

    CHUNK_LIMIT: int = 2000

    def chunk(
        self,
        content: MessageContent,
        mode: str = "length",
    ) -> ChunkResult:
        """
        Divide mensagem em chunks.

        Args:
            content: Conteúdo da mensagem
            mode: "length" (corte simples) ou "newline" (respeita parágrafos)

        Returns:
            ChunkResult com lista de chunks
        """
        chunks = content.chunk(mode)
        return ChunkResult(
            chunks=chunks,
            total=len(chunks),
            truncated=False,
        )

    def chunk_text(
        self,
        text: str,
        mode: str = "length",
    ) -> list[str]:
        """
        Divide texto diretamente em strings.

        Método de conveniência para uso direto.

        Args:
            text: Texto a dividir
            mode: Modo de chunking

        Returns:
            Lista de strings
        """
        if len(text) <= self.CHUNK_LIMIT:
            return [text]

        content = MessageContent(text)
        result = self.chunk(content, mode)
        return [c.text for c in result.chunks]

    def estimate_chunks(self, text: str) -> int:
        """
        Estima número de chunks necessários.

        Args:
            text: Texto a estimar

        Returns:
            Número estimado de chunks
        """
        return (len(text) + self.CHUNK_LIMIT - 1) // self.CHUNK_LIMIT

    @classmethod
    def create(cls) -> Self:
        """Factory method."""
        return cls()
