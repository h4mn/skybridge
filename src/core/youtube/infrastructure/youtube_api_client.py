"""Cliente para YouTube Data API v3.

 Integra com YouTube Data API para:
 - Listar playlists do usuário (Favoritos, Watch Later, etc.)
 - Buscar detalhes de vídeos
 - Monitorar mudanças

 Requer:
 - google-api-python-client
 - OAuth 2.0 token com scope youtube.readonly
"""

from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class YouTubeAPIClient:
    """Cliente para YouTube Data API v3."""

    # IDs de playlists especiais do YouTube
    LL_PLAYLIST = "LL"  # Liked Videos (Favoritos)
    WL_PLAYLIST = "WL"  # Watch Later (Assistir Mais Tarde)
    HL_PLAYLIST = "HL"  # History (Histórico)

    def __init__(self, access_token: str, api_key: Optional[str] = None):
        """Inicializa cliente YouTube.

        Args:
            access_token: Token OAuth 2.0 com youtube.readonly scope
            api_key: (opcional) API key para operações públicas

        Raises:
            ValueError: Se access_token for inválido
        """
        if not access_token or not access_token.strip():
            raise ValueError("access_token é obrigatório e não pode ser vazio")

        self.access_token = access_token
        self.api_key = api_key

        # Lazy import do googleapiclient
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaUpload

            self._build = build
            self._MediaUpload = MediaUpload

        except ImportError:
            raise ImportError(
                "google-api-python-client não instalado. "
                "Instale com: pip install google-api-python-client"
            )

        self._youtube = None

    @property
    def youtube(self):
        """Lazy initialization do cliente YouTube."""
        if self._youtube is None:
            self._youtube = self._build(
                "youtube",
                "v3",
                developerKey=self.api_key,
                # Credentials para OAuth
                credentials=self._create_credentials()
            )
        return self._youtube

    def _create_credentials(self):
        """Cria credentials OAuth a partir do access_token."""
        from google.oauth2.credentials import Credentials

        return Credentials(
            token=self.access_token,
            # Scopes necessários
            scopes=["https://www.googleapis.com/auth/youtube.readonly"],
            # Token info não necessário para access token válido
            token_uri=None,
            client_id=None,
            client_secret=None
        )

    def get_my_playlists(
        self,
        max_results: int = 50,
        mine: bool = True
    ) -> List[Dict[str, Any]]:
        """Lista playlists do usuário.

        Args:
            max_results: Máximo de playlists a retornar (padrão: 50)
            mine: Se True, retorna só playlists do usuário (padrão: True)

        Returns:
            Lista de playlists com: id, title, item_count, description
        """
        try:
            response = self.youtube.playlists().list(
                part="snippet,contentDetails",
                maxResults=max_results,
                mine=mine
            ).execute()

            playlists = []

            for item in response.get("items", []):
                playlists.append({
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"].get("description", ""),
                    "item_count": int(
                        item["contentDetails"]["itemCount"]
                    ),
                    "thumbnail": item["snippet"].get("thumbnails", {}).get(
                        "default", {}
                    ).get("url")
                })

            return playlists

        except Exception as e:
            logger.error(f"Erro ao listar playlists: {e}")
            raise

    def get_playlist_items(
        self,
        playlist_id: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Lista itens de uma playlist.

        Args:
            playlist_id: ID da playlist (LL=liked, WL=watch later, ou ID custom)
            max_results: Máximo de itens a retornar (padrão: 50)

        Returns:
            Lista de vídeos com: video_id, title, channel, duration_seconds, position
        """
        try:
            response = self.youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=max_results
            ).execute()

            # Coleta video IDs para buscar durações
            video_ids = [
                item["contentDetails"]["videoId"]
                for item in response.get("items", [])
            ]

            # Busca detalhes dos vídeos (incluindo duração)
            durations = self._get_video_durations(video_ids)

            videos = []

            for item in response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                snippet = item["snippet"]
                content_details = item["contentDetails"]

                videos.append({
                    "video_id": video_id,
                    "title": snippet["title"],
                    "description": snippet.get("description", ""),
                    "channel": snippet.get("videoOwnerChannelName", "Canal desconhecido"),
                    "channel_id": snippet.get("videoOwnerChannelId", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get(
                        "default", {}
                    ).get("url"),
                    "position": content_details.get("position", 0),
                    "added_at": content_details.get("videoPublishedAt"),
                    "duration_seconds": durations.get(video_id)
                })

            return videos

        except Exception as e:
            logger.error(f"Erro ao listar itens da playlist {playlist_id}: {e}")
            raise

    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Busca detalhes de um vídeo específico.

        Args:
            video_id: ID do vídeo (11 caracteres)

        Returns:
            Dict com video details ou None se não encontrado
        """
        try:
            response = self.youtube.videos().list(
                part="snippet,contentDetails",
                id=video_id
            ).execute()

            items = response.get("items", [])

            if not items:
                return None

            item = items[0]
            snippet = item["snippet"]
            content_details = item["contentDetails"]

            # Parse duração (formato PT4M13S = 4min 13sec)
            duration_str = content_details.get("duration", "PT0S")
            duration_seconds = self._parse_duration(duration_str)

            return {
                "video_id": video_id,
                "title": snippet["title"],
                "description": snippet.get("description", ""),
                "channel": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "duration_seconds": duration_seconds,
                "duration_formatted": self._format_duration(duration_seconds),
                "thumbnail": snippet.get("thumbnails", {}).get(
                    "default", {}
                ).get("url"),
                "published_at": snippet.get("publishedAt"),
                "tags": snippet.get("tags", [])
            }

        except Exception as e:
            logger.error(f"Erro ao buscar vídeo {video_id}: {e}")
            return None

    def _get_video_durations(
        self,
        video_ids: List[str]
    ) -> Dict[str, int]:
        """Busca durações de múltiplos vídeos.

        Args:
            video_ids: Lista de video IDs

        Returns:
            Dict {video_id: duration_seconds}
        """
        if not video_ids:
            return {}

        try:
            # API limita a 50 vídeos por request
            chunk_size = 50
            durations = {}

            for i in range(0, len(video_ids), chunk_size):
                chunk = video_ids[i:i + chunk_size]

                response = self.youtube.videos().list(
                    part="contentDetails",
                    id=",".join(chunk)
                ).execute()

                for item in response.get("items", []):
                    video_id = item["id"]
                    duration_str = item["contentDetails"].get("duration", "PT0S")
                    durations[video_id] = self._parse_duration(duration_str)

            return durations

        except Exception as e:
            logger.error(f"Erro ao buscar durações: {e}")
            return {}

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """Converte duração ISO 8601 (PT4M13S) para segundos.

        Args:
            duration_str: String no formato PTnHnMnS

        Returns:
            Duração em segundos
        """
        import re

        # Remove "PT" do inicio
        duration_str = duration_str[2:] if duration_str.startswith("PT") else duration_str

        hours = 0
        minutes = 0
        seconds = 0

        # Parse horas (H)
        h_match = re.search(r"(\d+)H", duration_str)
        if h_match:
            hours = int(h_match.group(1))

        # Parse minutos (M)
        m_match = re.search(r"(\d+)M", duration_str)
        if m_match:
            minutes = int(m_match.group(1))

        # Parse segundos (S)
        s_match = re.search(r"(\d+)S", duration_str)
        if s_match:
            seconds = int(s_match.group(1))

        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Formata segundos para HH:MM:SS.

        Args:
            seconds: Duração em segundos

        Returns:
            String formatada (HH:MM:SS)
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


# Funções de conveniência para CLI
def get_favorites(access_token: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Convenience function para listar favoritos.

    Args:
        access_token: Token OAuth 2.0
        max_results: Máximo de resultados

    Returns:
        Lista de vídeos favoritos
    """
    client = YouTubeAPIClient(access_token)
    return client.get_playlist_items(
        playlist_id=YouTubeAPIClient.LL_PLAYLIST,
        max_results=max_results
    )


def get_watch_later(access_token: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Convenience function para lista Assistir Mais Tarde.

    Args:
        access_token: Token OAuth 2.0
        max_results: Máximo de resultados

    Returns:
        Lista de vídeos para assistir depois
    """
    client = YouTubeAPIClient(access_token)
    return client.get_playlist_items(
        playlist_id=YouTubeAPIClient.WL_PLAYLIST,
        max_results=max_results
    )


def get_my_playlists(access_token: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Convenience function para listar playlists do usuário.

    Args:
        access_token: Token OAuth 2.0
        max_results: Máximo de resultados

    Returns:
        Lista de playlists
    """
    client = YouTubeAPIClient(access_token)
    return client.get_my_playlists(max_results=max_results)
