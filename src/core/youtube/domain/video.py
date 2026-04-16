"""Video entity e value objects."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class VideoId:
    """Value Object para ID de vídeo YouTube."""
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Video ID não pode ser vazio")

    def __eq__(self, other):
        if not isinstance(other, VideoId):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)


@dataclass(frozen=True)
class VideoMetadata:
    """Metadados do vídeo."""
    title: str
    channel: str
    duration_seconds: int
    upload_date: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Video:
    """Entidade principal Video."""
    video_id: VideoId
    url: str
    metadata: VideoMetadata
    local_path: Optional[Path] = None
    tags: List[str] = None
    created_at: datetime = None
    indexed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()

    def mark_as_indexed(self) -> None:
        """Marca o vídeo como indexado na enciclopédia."""
        self.indexed_at = datetime.now()

    @property
    def indexed(self) -> bool:
        """Retorna se o vídeo está indexado."""
        return self.indexed_at is not None

    def add_tag(self, tag: str) -> None:
        """Adiciona uma tag ao vídeo."""
        if tag and tag not in self.tags:
            self.tags.append(tag)
