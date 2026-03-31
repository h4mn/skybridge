# -*- coding: utf-8 -*-
"""
MessageContent Value Object.

Conteúdo de mensagem Discord com comportamento de chunking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


class MessageTooLongError(Exception):
    """Erro quando mensagem excede limite máximo de caracteres."""

    def __init__(self, length: int, max_length: int):
        self.length = length
        self.max_length = max_length
        super().__init__(
            f"Mensagem excede limite máximo: {length} > {max_length} caracteres"
        )


@dataclass(frozen=True)
class MessageContent:
    """
    Value Object para conteúdo de mensagem Discord.

    Suporta chunking automático para respeitar limite de 2000 caracteres.
    """

    text: str
    CHUNK_LIMIT: int = 2000
    MAX_LENGTH: int = 20000

    def __post_init__(self) -> None:
        # Valida conteúdo vazio
        if not self.text or not self.text.strip():
            raise ValueError("MessageContent não pode ser vazio")

        # Valida tamanho máximo
        if len(self.text) > self.MAX_LENGTH:
            raise MessageTooLongError(len(self.text), self.MAX_LENGTH)

    def __str__(self) -> str:
        return self.text

    def __len__(self) -> int:
        return len(self.text)

    def needs_chunking(self) -> bool:
        """Verifica se mensagem precisa ser dividida."""
        return len(self.text) > self.CHUNK_LIMIT

    def chunk(self, mode: str = "length") -> list[Self]:
        """
        Divide mensagem em chunks respeitando limite.

        Args:
            mode: "length" (corte simples) ou "newline" (respeita parágrafos)

        Returns:
            Lista de MessageContent chunks
        """
        if not self.needs_chunking():
            return [self]

        chunks: list[str] = []

        if mode == "newline":
            chunks = self._chunk_by_newline()
        else:
            chunks = self._chunk_by_length()

        return [MessageContent(chunk) for chunk in chunks]

    def _chunk_by_length(self) -> list[str]:
        """Divide por comprimento fixo."""
        chunks: list[str] = []
        remaining = self.text

        while remaining:
            if len(remaining) <= self.CHUNK_LIMIT:
                chunks.append(remaining)
                break

            # Procura último espaço antes do limite
            cut_point = self.CHUNK_LIMIT
            last_space = remaining.rfind(" ", 0, self.CHUNK_LIMIT)
            if last_space > 0:
                cut_point = last_space

            chunks.append(remaining[:cut_point].strip())
            remaining = remaining[cut_point:].strip()

        return chunks

    def _chunk_by_newline(self) -> list[str]:
        """Divide respeitando quebras de parágrafo (duplo newline)."""
        chunks: list[str] = []
        paragraphs = self.text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            # Se parágrafo sozinho excede limite, divide por length
            if len(para) > self.CHUNK_LIMIT:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Divide parágrafo longo
                for sub_chunk in self._split_long_text(para):
                    chunks.append(sub_chunk)
                continue

            # Verifica se cabe no chunk atual
            test_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
            if len(test_chunk) <= self.CHUNK_LIMIT:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_long_text(self, text: str) -> list[str]:
        """Divide texto longo por comprimento."""
        chunks: list[str] = []
        remaining = text

        while remaining:
            if len(remaining) <= self.CHUNK_LIMIT:
                chunks.append(remaining)
                break

            cut_point = self.CHUNK_LIMIT
            last_space = remaining.rfind(" ", 0, self.CHUNK_LIMIT)
            if last_space > 0:
                cut_point = last_space

            chunks.append(remaining[:cut_point].strip())
            remaining = remaining[cut_point:].strip()

        return chunks

    @classmethod
    def from_text(cls, text: str) -> Self:
        """Cria MessageContent a partir de texto."""
        return cls(text)
