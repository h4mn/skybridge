# -*- coding: utf-8 -*-
"""
Attachment Entity.

Entidade para anexos de mensagem Discord.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass
class Attachment:
    """
    Entity para anexo Discord.

    Representa arquivos anexados a mensagens.
    """

    id: str
    filename: str
    content_type: str | None
    size_bytes: int
    url: str
    local_path: Path | None = None  # Path local se baixado

    def size_kb(self) -> int:
        """Retorna tamanho em KB."""
        return self.size_bytes // 1024

    def size_mb(self) -> float:
        """Retorna tamanho em MB."""
        return self.size_bytes / (1024 * 1024)

    def is_image(self) -> bool:
        """Verifica se anexo é imagem."""
        if not self.content_type:
            return False
        return self.content_type.startswith("image/")

    def is_video(self) -> bool:
        """Verifica se anexo é vídeo."""
        if not self.content_type:
            return False
        return self.content_type.startswith("video/")

    def is_audio(self) -> bool:
        """Verifica se anexo é áudio."""
        if not self.content_type:
            return False
        return self.content_type.startswith("audio/")

    def is_document(self) -> bool:
        """Verifica se anexo é documento."""
        if not self.content_type:
            return False
        return self.content_type.startswith("application/")

    def extension(self) -> str:
        """Retorna extensão do arquivo."""
        return Path(self.filename).suffix.lower()

    def is_downloaded(self) -> bool:
        """Verifica se arquivo foi baixado localmente."""
        return self.local_path is not None and self.local_path.exists()

    def mark_downloaded(self, path: Path) -> None:
        """Marca arquivo como baixado."""
        self.local_path = path

    @classmethod
    def create(
        cls,
        attachment_id: str,
        filename: str,
        content_type: str | None,
        size_bytes: int,
        url: str,
    ) -> Self:
        """
        Factory method para criar anexo.

        Args:
            attachment_id: ID do anexo Discord
            filename: Nome do arquivo
            content_type: MIME type
            size_bytes: Tamanho em bytes
            url: URL de download

        Returns:
            Nova instância de Attachment
        """
        return cls(
            id=attachment_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            url=url,
        )
