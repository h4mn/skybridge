"""Transcript entity e segmentos."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class TranscriptSegment:
    """Segmento da transcrição com timestamp."""
    start_time: float  # segundos
    end_time: float    # segundos
    text: str
    confidence: Optional[float] = None

    @property
    def duration(self) -> float:
        """Duração do segmento em segundos."""
        return self.end_time - self.start_time

    @property
    def timestamp_str(self) -> str:
        """Timestamp formatado como HH:MM:SS."""
        hours = int(self.start_time // 3600)
        minutes = int((self.start_time % 3600) // 60)
        seconds = int(self.start_time % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@dataclass
class Transcript:
    """Transcrição completa de um vídeo."""
    video_id: str
    segments: List[TranscriptSegment]
    language: str = "auto"
    full_text: Optional[str] = None

    def __post_init__(self):
        if self.full_text is None:
            self.full_text = " ".join(s.text for s in self.segments)

    @property
    def duration(self) -> float:
        """Duração total da transcrição."""
        if not self.segments:
            return 0.0
        return self.segments[-1].end_time

    def get_segment_at(self, timestamp: float) -> Optional[TranscriptSegment]:
        """Retorna o segmento ativo em um determinado timestamp."""
        for segment in self.segments:
            if segment.start_time <= timestamp <= segment.end_time:
                return segment
        return None

    def search_text(self, query: str) -> List[TranscriptSegment]:
        """Busca segmentos que contêm o texto."""
        query_lower = query.lower()
        return [s for s in self.segments if query_lower in s.text.lower()]
