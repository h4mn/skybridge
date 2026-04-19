"""
YouTube Bounded Context - Fachada para submódulo sky-youtube.

Estrutura interna:
    src/core/youtube/ (submódulo sky-youtube)
    └── src/ (código aqui)
        ├── application/
        ├── domain/
        └── infrastructure/

Uso (interface compatível):
    from core.youtube import YoutubeTranscriptService
    from core.youtube.infrastructure import YouTubeStateRepository
"""

import sys
from pathlib import Path

# Configura path para o código do submódulo
# Estrutura: src/core/youtube/ (submódulo) → src/youtube/ (namespace)
youtube_src = Path(__file__).parent / "youtube" / "src"
if str(youtube_src) not in sys.path:
    sys.path.insert(0, str(youtube_src))

# Agora os imports funcionam (com namespace youtube)
from youtube.infrastructure.youtube_state_repository import YouTubeStateRepository, VideoState, PlaylistSyncState
from youtube.infrastructure.youtube_state_setup import setup_youtube_state, verify_youtube_state, get_youtube_state_path
from youtube.infrastructure.yt_dlp_adapter import YtDlpAdapter
from youtube.infrastructure.transcription_adapter import TranscriptionAdapter
from youtube.infrastructure.youtube_api_client import YouTubeAPIClient
from youtube.application.youtube_transcript_service import YoutubeTranscriptService, TranscriptResult
from youtube.infrastructure.transcription_adapter import TranscriptionAdapter, TranscriptionResult
from youtube.application.youtube_commands import (
    YouTubeCommandHandler,
    YouTubeQueryHandler,
    SyncResult,
    StatusResult,
    StatsResult,
    PlaylistListResult,
    VideoListResult,
)
from youtube.domain.video import VideoId, Video, VideoMetadata
from youtube.domain.transcript import Transcript
from youtube.domain.events import VideoProcessedEvent

__all__ = [
    "YouTubeStateRepository",
    "VideoState",
    "PlaylistSyncState",
    "setup_youtube_state",
    "verify_youtube_state",
    "get_youtube_state_path",
    "YtDlpAdapter",
    "TranscriptionAdapter",
    "TranscriptionResult",
    "YouTubeAPIClient",
    "YoutubeTranscriptService",
    "TranscriptResult",
    "YouTubeCommandHandler",
    "YouTubeQueryHandler",
    "SyncResult",
    "StatusResult",
    "StatsResult",
    "PlaylistListResult",
    "VideoListResult",
    "VideoId",
    "Video",
    "VideoMetadata",
    "Transcript",
    "VideoProcessedEvent",
]
