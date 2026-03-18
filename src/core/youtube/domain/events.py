"""Domain Events do contexto YouTube."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class VideoProcessedEvent:
    """Evento disparado quando um vídeo é processado."""
    video_id: str
    url: str
    title: str
    downloaded: bool
    transcribed: bool
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class VideoIndexedEvent:
    """Evento disparado quando um vídeo é indexado na enciclopédia."""
    video_id: str
    title: str
    tags: List[str]
    embedding_count: int
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class VideoAnalysisCompletedEvent:
    """Evento disparado quando a análise de vídeo é concluída."""
    video_id: str
    key_moments: List[Dict[str, Any]]
    summary: str
    topics: List[str]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
