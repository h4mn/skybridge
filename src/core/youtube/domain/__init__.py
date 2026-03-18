"""Domain Layer - Entidades e eventos do domínio YouTube."""

from .video import Video, VideoId, VideoMetadata
from .transcript import Transcript, TranscriptSegment
from .events import VideoProcessedEvent, VideoIndexedEvent

__all__ = [
    "Video",
    "VideoId",
    "VideoMetadata",
    "Transcript",
    "TranscriptSegment",
    "VideoProcessedEvent",
    "VideoIndexedEvent",
]
