"""Adaptador de Transcrição com fallback.

Arquitetura:
1. faster-whisper (principal, local, rápido)
2. zai-analyze-video (fallback, análise completa)

Instalação:
    pip install faster-whisper

Modelos baixados automaticamente na primeira vez:
    - tiny (~39MB) - Mais rápido
    - base (~74MB) - Recomendado
    - small (~244MB) - Mais preciso
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

from faster_whisper import WhisperModel


@dataclass
class TranscriptionResult:
    """Resultado da transcrição."""
    text: str
    language: str
    confidence: float = 0.0
    method: str = "unknown"
    duration_seconds: float = 0.0
    segments: Optional[list] = None

    def __post_init__(self):
        if self.segments is None:
            self.segments = []


class TranscriptionAdapter:
    """
    Adaptador de transcrição com múltiplas estratégias.

    Estratégias (em ordem):
    1. faster-whisper (local, rápido)
    2. zai-analyze-video (fallback, MCP)
    """

    def __init__(
        self,
        model_size: str = "base",
        model_dir: Optional[Path] = None,
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        Inicializa adaptador de transcrição.

        Args:
            model_size: Tamanho do modelo (tiny, base, small, medium, large)
            model_dir: Diretório para modelos (opcional)
            device: Dispositivo (cpu, cuda)
            compute_type: Tipo de computação (int8, float16, float32)
        """
        self._model_size = model_size
        self._model_dir = model_dir or Path("data/whisper_models")
        self._device = device
        self._compute_type = compute_type

        # Criar diretório de modelos
        self._model_dir.mkdir(parents=True, exist_ok=True)

        # Modelo lazy (carregado sob demanda)
        self._model: Optional[WhisperModel] = None

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """
        Transcreve arquivo de áudio.

        Tenta faster-whisper primeiro, fallback para zai MCP.

        Args:
            audio_path: Caminho para arquivo de áudio

        Returns:
            TranscriptionResult com texto e metadados
        """
        # Tentar faster-whisper primeiro
        try:
            return await self._transcribe_with_whisper(audio_path)
        except Exception as e:
            print(f"⚠️  faster-whisper falhou: {e}")
            print("🔄 Tentando fallback para zai MCP...")
            return await self._transcribe_with_zai(audio_path)

    async def _transcribe_with_whisper(self, audio_path: Path) -> TranscriptionResult:
        """
        Transcreve usando faster-whisper (local).

        Args:
            audio_path: Caminho para áudio

        Returns:
            TranscriptionResult
        """
        # Carregar modelo lazy
        if self._model is None:
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
                download_root=str(self._model_dir)
            )

        # Transcrever em thread separada (Whisper é síncrono)
        loop = asyncio.get_event_loop()
        segments, info = await loop.run_in_executor(
            None,
            lambda: self._model.transcribe(
                str(audio_path),
                language=None,  # Auto-detect
                beam_size=5
            )
        )

        # Extrair texto
        text = "".join(seg.text for seg in segments)

        # Calcular confiança média
        confidence = info.language_probability if hasattr(info, 'language_probability') else 0.85

        return TranscriptionResult(
            text=text.strip(),
            language=info.language,
            confidence=confidence,
            method="faster-whisper",
            duration_seconds=getattr(info, 'duration', 0.0),
            segments=list(segments)
        )

    async def _transcribe_with_zai(self, audio_path: Path) -> TranscriptionResult:
        """
        Transcreve usando zai-analyze-video (fallback, MCP).

        Args:
            audio_path: Caminho para áudio

        Returns:
            TranscriptionResult
        """
        # TODO: Implementar integração com MCP zai-analyze-video
        # Por enquanto, retorna placeholder

        return TranscriptionResult(
            text="",
            language="unknown",
            confidence=0.0,
            method="zai-mcp",
            duration_seconds=0.0
        )

    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o modelo configurado.

        Returns:
            Dict com tamanho, dispositivo, etc.
        """
        return {
            "model_size": self._model_size,
            "device": self._device,
            "compute_type": self._compute_type,
            "model_dir": str(self._model_dir),
            "loaded": self._model is not None
        }
