"""Testes para Domain Models do YouTube.

DOC: src/core/youtube/domain/
Metodologia: TDD Estrito (RED → GREEN → REFACTOR)
"""

import pytest
from datetime import datetime
from dataclasses import dataclass


@pytest.mark.unit
class TestVideoId:
    """Testes do Value Object VideoId."""

    def test_create_video_id(self):
        """Testa criação de VideoId."""
        from src.core.youtube import VideoId

        video_id = VideoId("abc123")
        assert video_id.value == "abc123"

    def test_video_id_equality(self):
        """Testa igualdade de VideoId."""
        from src.core.youtube import VideoId

        id1 = VideoId("abc123")
        id2 = VideoId("abc123")
        id3 = VideoId("xyz789")

        assert id1 == id2
        assert id1 != id3
        assert hash(id1) == hash(id2)

    def test_video_id_invalid_empty(self):
        """Testa que VideoId vazio levanta erro."""
        from src.core.youtube import VideoId

        with pytest.raises(ValueError, match="Video ID não pode ser vazio"):
            VideoId("")

    def test_video_id_invalid_none(self):
        """Testa que VideoId None levanta erro."""
        from src.core.youtube import VideoId

        with pytest.raises(ValueError, match="Video ID não pode ser vazio"):
            VideoId(None)


@pytest.mark.unit
class TestVideoMetadata:
    """Testes do Value Object VideoMetadata."""

    def test_create_video_metadata(self):
        """Testa criação de VideoMetadata."""
        from src.core.youtube import VideoMetadata

        metadata = VideoMetadata(
            title="Test Video",
            channel="Test Channel",
            duration_seconds=600,
            upload_date=datetime.now(),
            description="Test description"
        )

        assert metadata.title == "Test Video"
        assert metadata.channel == "Test Channel"
        assert metadata.duration_seconds == 600

    def test_video_metadata_defaults(self):
        """Testa valores padrão de VideoMetadata."""
        from src.core.youtube import VideoMetadata

        metadata = VideoMetadata(
            title="Test",
            channel="Channel",
            duration_seconds=600
        )

        assert metadata.description is None
        assert metadata.upload_date is None


@pytest.mark.unit
class TestVideo:
    """Testes da Entidade Video."""

    def test_create_video(self):
        """Testa criação de Video."""
        from src.core.youtube import Video, VideoId, VideoMetadata

        video_id = VideoId("abc123")
        metadata = VideoMetadata(
            title="Test Video",
            channel="Test Channel",
            duration_seconds=600
        )

        video = Video(
            video_id=video_id,
            url="https://youtube.com/watch?v=abc123",
            metadata=metadata,
            tags=["test", "demo"]
        )

        assert video.video_id == video_id
        assert video.url == "https://youtube.com/watch?v=abc123"
        assert video.metadata.title == "Test Video"
        assert video.tags == ["test", "demo"]
        assert video.local_path is None
        assert video.indexed is False

    def test_mark_as_indexed(self):
        """Testa marcar vídeo como indexado."""
        from src.core.youtube import Video, VideoId, VideoMetadata

        video = Video(
            video_id=VideoId("abc123"),
            url="https://youtube.com/watch?v=abc123",
            metadata=VideoMetadata(
                title="Test",
                channel="Channel",
                duration_seconds=600
            )
        )

        assert video.indexed is False

        video.mark_as_indexed()

        assert video.indexed is True


@pytest.mark.unit
class TestTranscript:
    """Testes do Value Object Transcript."""

    def test_create_transcript(self):
        """Testa criação de Transcript."""
        from src.core.youtube import Transcript

        transcript = Transcript(
            text="Este é o texto da transcrição.",
            language="pt",
            confidence=0.95
        )

        assert transcript.text == "Este é o texto da transcrição."
        assert transcript.language == "pt"
        assert transcript.confidence == 0.95

    def test_transcript_defaults(self):
        """Testa valores padrão de Transcript."""
        from src.core.youtube import Transcript

        transcript = Transcript(text="Texto")

        assert transcript.language == "unknown"
        assert transcript.confidence == 0.0


@pytest.mark.unit
class TestVideoProcessedEvent:
    """Testes do Domain Event VideoProcessedEvent."""

    def test_create_event(self):
        """Testa criação de VideoProcessedEvent."""
        from src.core.youtube import VideoProcessedEvent

        event = VideoProcessedEvent(
            video_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            title="Test Video",
            downloaded=True,
            transcribed=True
        )

        assert event.video_id == "abc123"
        assert event.url == "https://youtube.com/watch?v=abc123"
        assert event.title == "Test Video"
        assert event.downloaded is True
        assert event.transcribed is True
        assert isinstance(event.occurred_at, datetime)

    def test_event_to_dict(self):
        """Testa converter evento para dict."""
        from src.core.youtube import VideoProcessedEvent

        event = VideoProcessedEvent(
            video_id="abc123",
            url="https://youtube.com/watch?v=abc123",
            title="Test Video",
            downloaded=True,
            transcribed=False
        )

        event_dict = event.to_dict()

        assert event_dict["video_id"] == "abc123"
        assert event_dict["url"] == "https://youtube.com/watch?v=abc123"
        assert event_dict["title"] == "Test Video"
        assert "occurred_at" in event_dict
