"""Serviço de enciclopédia placeholder."""


class EncyclopediaService:
    """Serviço para gerenciar a enciclopédia de vídeos."""

    async def add_video(self, video_id: str, content: str, tags: list) -> None:
        """Adiciona um vídeo à enciclopédia."""
        pass

    async def search(self, query: str) -> list:
        """Busca na enciclopédia."""
        return []
