"""
Audio Cache - Cache de áudio gerado pelo TTS.

Este módulo implementa um cache LRU de áudio em disco
para evitar reprocessamento de textos repetidos.
"""

import hashlib
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.core.sky.voice.audio_capture import AudioData


@dataclass
class CacheEntry:
    """Entrada do cache de áudio.

    Attributes:
        text_hash: Hash MD5 do texto
        voice_id: Identificador da voz usada
        file_path: Caminho do arquivo em disco
        created_at: Timestamp de criação
        size_bytes: Tamanho do arquivo em bytes
    """

    text_hash: str
    voice_id: str
    file_path: str
    created_at: float
    size_bytes: int

    @property
    def age_seconds(self) -> float:
        """Retorna idade da entrada em segundos."""
        return time.time() - self.created_at

    def is_expired(self, ttl_seconds: float = 86400.0) -> bool:
        """Verifica se entrada expirou.

        Args:
            ttl_seconds: TTL em segundos (padrão: 24h)

        Returns:
            True se entrada expirou
        """
        return self.age_seconds > ttl_seconds


class AudioCache:
    """Cache de áudio em disco com LRU.

    Cacheia áudios gerados pelo TTS para evitar reprocessamento.
    Usa hash MD5 do texto + voice_id como chave.
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl_seconds: float = 86400.0,  # 24 horas
        max_size_mb: float = 500.0,
    ):
        """Inicializa cache de áudio.

        Args:
            cache_dir: Diretório para cache (padrão: ~/.cache/sky-voice)
            ttl_seconds: TTL em segundos (padrão: 24h)
            max_size_mb: Tamanho máximo do cache em MB
        """
        self.cache_dir = Path(cache_dir or self._default_cache_dir())
        self.ttl_seconds = ttl_seconds
        self.max_size_bytes = max_size_mb * 1024 * 1024

        # Cria diretório se não existe
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Índice em memória
        self._index: dict[str, CacheEntry] = {}
        self._load_index()

    def _default_cache_dir(self) -> str:
        """Retorna diretório padrão de cache."""
        home = os.path.expanduser("~")
        return os.path.join(home, ".cache", "sky-voice")

    def _load_index(self) -> None:
        """Carrega índice do disco."""
        index_file = self.cache_dir / "index.json"

        if not index_file.exists():
            return

        # TODO: Carregar índice de JSON
        pass

    def _save_index(self) -> None:
        """Salva índice em disco."""
        # TODO: Salvar índice em JSON
        pass

    def _get_key(self, text: str, voice_id: str) -> str:
        """Gera chave de cache.

        Args:
            text: Texto a ser cacheado
            voice_id: Voz usada

        Returns:
            Chave de cache (hash MD5)
        """
        combined = f"{text}:{voice_id}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, text: str, voice_id: str) -> Optional[AudioData]:
        """Retorna áudio cacheado se disponível.

        Args:
            text: Texto buscando
            voice_id: Voz usada

        Returns:
            AudioData se encontrado e válido, None caso contrário
        """
        key = self._get_key(text, voice_id)

        if key not in self._index:
            return None

        entry = self._index[key]

        # Verifica se expirou
        if entry.is_expired(self.ttl_seconds):
            self.delete(key)
            return None

        # Verifica se arquivo existe
        if not Path(entry.file_path).exists():
            del self._index[key]
            return None

        # Carrega áudio do disco
        try:
            with open(entry.file_path, "rb") as f:
                samples = f.read()

            return AudioData(
                samples=samples,
                sample_rate=16000,  # TODO: Salvar sample_rate no cache
                channels=1,
            )
        except IOError:
            del self._index[key]
            return None

    def put(self, text: str, voice_id: str, audio: AudioData) -> None:
        """Adiciona áudio ao cache.

        Args:
            text: Texto cacheado
            voice_id: Voz usada
            audio: Dados de áudio
        """
        key = self._get_key(text, voice_id)

        # Gera nome de arquivo
        filename = f"{key}.wav"
        file_path = self.cache_dir / filename

        # Salva áudio em disco
        try:
            with open(file_path, "wb") as f:
                f.write(audio.samples)
        except IOError as e:
            # Falha silenciosa - cache não é crítico
            return

        # Cria entrada
        entry = CacheEntry(
            text_hash=key,
            voice_id=voice_id,
            file_path=str(file_path),
            created_at=time.time(),
            size_bytes=len(audio.samples),
        )

        self._index[key] = entry

        # Limpa cache se necessário
        self._cleanup_if_needed()

    def delete(self, key: str) -> None:
        """Remove entrada do cache.

        Args:
            key: Chave da entrada
        """
        if key not in self._index:
            return

        entry = self._index[key]

        # Remove arquivo
        try:
            Path(entry.file_path).unlink(missing_ok=True)
        except IOError:
            pass

        # Remove do índice
        del self._index[key]

    def clear(self) -> None:
        """Limpa todo o cache."""
        for key in list(self._index.keys()):
            self.delete(key)

    def _cleanup_if_needed(self) -> None:
        """Limpa cache se exceder tamanho máximo."""
        total_size = sum(e.size_bytes for e in self._index.values())

        if total_size <= self.max_size_bytes:
            return

        # Ordena por criação (mais antigos primeiro)
        entries_by_age = sorted(
            self._index.values(),
            key=lambda e: e.created_at,
        )

        # Remove entradas até ficar abaixo do limite
        for entry in entries_by_age:
            if total_size <= self.max_size_bytes * 0.8:  # 80% do limite
                break

            key = entry.text_hash
            total_size -= entry.size_bytes
            self.delete(key)

    def get_stats(self) -> dict:
        """Retorna estatísticas do cache.

        Returns:
            Dict com estatísticas
        """
        total_size = sum(e.size_bytes for e in self._index.values())
        entry_count = len(self._index)

        return {
            "entry_count": entry_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
            "ttl_seconds": self.ttl_seconds,
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
        }
