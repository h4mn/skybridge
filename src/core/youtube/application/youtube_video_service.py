"""Serviço principal para processamento de vídeos YouTube."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..domain import Video, VideoId, VideoMetadata, VideoProcessedEvent
from ..domain.transcript import Transcript
from ..infrastructure import YtDlpAdapter, VideoAnalyzerAdapter, RAGVideoRepository


class YouTubeVideoService:
    """
    Serviço que orquestra o processamento completo de vídeos YouTube.

    Fluxo:
        1. Download (yt-dlp)
        2. Transcrição/Análise (MCP Analyzer)
        3. Indexação (RAG na coleção skypedia)
    """

    def __init__(
        self,
        download_path: Path = Path("data/youtube"),
        yt_dlp_adapter: Optional[YtDlpAdapter] = None,
        analyzer_adapter: Optional[VideoAnalyzerAdapter] = None,
        rag_repository: Optional[RAGVideoRepository] = None,
    ):
        self._download_path = download_path
        self._download_path.mkdir(parents=True, exist_ok=True)

        self._yt_dlp = yt_dlp_adapter or YtDlpAdapter(self._download_path)
        self._analyzer = analyzer_adapter or VideoAnalyzerAdapter()
        self._rag = rag_repository or RAGVideoRepository()

    async def process_video(
        self,
        url: str,
        tags: Optional[List[str]] = None,
        download_video: bool = False,
    ) -> Video:
        """
        Processa um vídeo YouTube completo.

        Args:
            url: URL do vídeo YouTube
            tags: Tags para categorização na skypedia
            download_video: Se True, baixa o vídeo MP4. Se False, só legendas.

        Returns:
            Video com metadados e transcrição
        """
        # 1. Extrair metadados
        video_id = await self._yt_dlp.extract_video_id(url)
        metadata = await self._yt_dlp.get_metadata(url)

        # 2. Download (vídeo e/ou legendas)
        local_path = None
        if download_video:
            local_path = await self._yt_dlp.download_video(url)
        else:
            # Baixar formato leve para análise (360p < 8MB)
            local_path = await self._yt_dlp.download_lightweight(url)

        # 3. Transcrição/Análise
        transcript = await self._analyzer.transcribe(local_path or url)

        # 4. Criar entidade
        video = Video(
            video_id=VideoId(video_id),
            url=url,
            metadata=metadata,
            local_path=local_path,
            tags=tags or [],
        )

        # 5. Emitir evento
        event = VideoProcessedEvent(
            video_id=video_id,
            url=url,
            title=metadata.title,
            downloaded=local_path is not None,
            transcribed=transcript is not None,
        )
        # TODO: Emitir via EventBus quando integrado

        return video

    async def index_to_skypedia(
        self,
        video: Video,
        transcript: str,
        analysis: Optional[dict] = None,
    ) -> int:
        """
        Indexa o vídeo na coleção skypedia do RAG da Sky.

        Args:
            video: Video com metadados
            transcript: Transcrição completa
            analysis: Análise opcional com insights, topics, etc

        Returns:
            ID da memória inserida
        """
        # Preparar metadados
        metadata = {
            "channel": video.metadata.channel,
            "duration_seconds": video.metadata.duration_seconds,
            "tags": video.tags,
            "upload_date": video.metadata.upload_date.isoformat() if video.metadata.upload_date else None,
            "url": video.url,
        }

        if analysis:
            metadata.update({
                "topics": analysis.get("topics", []),
                "key_moments": analysis.get("key_moments", []),
                "summary": analysis.get("summary", ""),
            })

        # Indexar
        memory_id = await self._rag.index_video(
            video_id=video.video_id.value,
            title=video.metadata.title,
            transcript=transcript,
            metadata=metadata,
        )

        video.mark_as_indexed()
        return memory_id

    async def search_skypedia(self, query: str, limit: int = 5) -> List[dict]:
        """
        Busca vídeos na skypedia por similaridade semântica.

        Args:
            query: Query de busca em linguagem natural
            limit: Máximo de resultados

        Returns:
            Lista de resultados ordenados por relevância
        """
        return self._rag.search(query, limit)

    async def get_skypedia_stats(self) -> dict:
        """Retorna estatísticas da coleção skypedia."""
        return self._rag.get_stats()

    async def process_and_index(
        self,
        url: str,
        tags: Optional[List[str]] = None,
    ) -> dict:
        """
        Atalho: processa e indexa em uma única chamada.

        Args:
            url: URL do vídeo YouTube
            tags: Tags para categorização

        Returns:
            Dict com {video, memory_id, analysis}
        """
        # 1. Processar vídeo
        video = await self.process_video(url, tags, download_video=False)

        # 2. Analisar conteúdo
        analysis = await self._analyzer.analyze(video.local_path or url)

        # 3. Extrair transcrição da análise
        transcript = analysis.get("transcription", "")
        if not transcript:
            transcript = analysis.get("full_text", "")

        # 4. Indexar na skypedia
        memory_id = await self.index_to_skypedia(video, transcript, analysis)

        return {
            "video": video,
            "memory_id": memory_id,
            "analysis": analysis,
        }
