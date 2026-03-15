"""
STT Service - Speech-to-Text para a Sky.

Este módulo define a interface abstrata para transcrição de áudio,
com suporte a múltiplos backends (Whisper, Whisper API, etc).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable

from core.sky.voice.audio_capture import AudioData


class STTModel(Enum):
    """Modelos de STT disponíveis."""

    WHISPER_LOCAL = "whisper-local"
    WHISPER_API = "whisper-api"
    VOSK = "vosk"


@dataclass
class TranscriptionConfig:
    """Configuração de transcrição.

    Attributes:
        language: Código do idioma (ex: "pt", "en", "auto" para detecção)
        model: Tamanho do modelo (tiny, base, small, medium, large)
        detect_language: Detectar idioma automaticamente
        streaming: Modo streaming (retorna transcrições parciais)
    """

    language: str = "pt"
    model: str = "base"
    detect_language: bool = False
    streaming: bool = False


@dataclass
class TranscriptionResult:
    """Resultado da transcrição.

    Attributes:
        text: Texto transcrito
        language: Idioma detectado
        confidence: Confiança da transcrição (0.0 a 1.0)
        duration: Duração do áudio transcrita
    """

    text: str
    language: str
    confidence: float = 0.0
    duration: float = 0.0


class STTService(ABC):
    """Interface abstrata para Speech-to-Text.

    Esta interface permite swap de implementação entre diferentes backends:
    - WhisperAdapter: Whisper local (open source)
    - WhisperAPIAdapter: Whisper API OpenAI (premium)
    - VoskAdapter: Vosk (alternativa leve)
    """

    def __init__(self, model: STTModel = STTModel.WHISPER_LOCAL):
        """Inicializa serviço STT.

        Args:
            model: Modelo de STT a ser usado
        """
        self.model = model

    @abstractmethod
    async def transcribe(
        self,
        audio: AudioData,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Transcreve áudio para texto.

        Args:
            audio: Dados de áudio para transcrever
            config: Configuração de transcrição (opcional)

        Returns:
            TranscriptionResult com texto transcrito
        """
        pass

    @abstractmethod
    async def listen(
        self,
        duration: float = 30.0,
        on_partial: Optional[Callable[[str], None]] = None,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Escuta microfone e transcreve.

        Args:
            duration: Duração máxima de gravação em segundos
            on_partial: Callback para transcrições parciais (streaming)
            config: Configuração de transcrição (opcional)

        Returns:
            TranscriptionResult com texto transcrito
        """
        pass


class WhisperAdapter(STTService):
    """Adapter para Whisper local (faster-whisper).

    Whisper é um modelo de transcrição da OpenAI
    com suporte a múltiplos idiomas, incluindo PT-BR.
    """

    def __init__(self, model_size: str = "medium", device: str = "cpu"):
        """Inicializa adapter Whisper.

        Args:
            model_size: Tamanho do modelo (tiny, base, small, medium, large)
                       CORREÇÃO: "medium" é o mínimo aceitável para PT-BR ("base" alucina muito)
            device: Dispositivo de execução (cpu, cuda)
        """
        super().__init__(model=STTModel.WHISPER_LOCAL)
        self.model_size = model_size
        self.device = device
        self._model = None
        self._hotwords = None
        self._initial_prompt = None
        self._load_biasing_context()

    def _load_model(self):
        """Carrega modelo Whisper (lazy load)."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type="int8",  # Quantização para menor uso de memória
                )
            except ImportError as e:
                raise ImportError(
                    "faster-whisper não está instalado. "
                    "Execute: pip install faster-whisper"
                ) from e

    def _load_biasing_context(self):
        """Carrega hotwords e initial prompt para melhorar transcrição PT-BR."""
        import sys
        import logging
        from pathlib import Path

        logger = logging.getLogger(__name__)

        # Detecta root do projeto
        if getattr(sys, "frozen", False):
            # Executável PyInstaller
            project_root = Path(sys.executable).parent
        else:
            # Desenvolvimento normal: sobe 5 níveis de src/core/sky/voice/
            project_root = Path(__file__).parent.parent.parent.parent.parent

        # Carrega hotwords
        hotwords_path = project_root / "stt_hotwords.txt"
        if hotwords_path.exists():
            try:
                self._hotwords = hotwords_path.read_text(encoding="utf-8").strip()
                word_count = len(self._hotwords.split())
                logger.info(f"Hotwords carregadas: {word_count} palavras técnicas")
            except Exception as e:
                logger.warning(f"Erro ao ler hotwords: {e}")
        else:
            logger.warning(f"Arquivo de hotwords não encontrado: {hotwords_path}")

        # Initial prompt contextual
        self._initial_prompt = (
            "A Sky é uma assistente de IA técnica que auxilia em engenharia de software, "
            "desenvolvimento, análise de código, deploy, testes e documentação. "
            "O usuário fala português brasileiro, mas o vocabulário técnico é rico em "
            "termos em inglês como webhook, API, job, deploy, pipeline, commit, branch, "
            "pull request, entre outros. Preserve termos técnicos em inglês."
        )

    async def transcribe(
        self,
        audio: AudioData,
        config: Optional[TranscriptionConfig] = None,
        on_partial: Optional[Callable[[str], None]] = None,
    ) -> TranscriptionResult:
        """Transcreve áudio para texto.

        Args:
            audio: Áudio para transcrever
            config: Configuração de transcrição
            on_partial: Callback para transcrições parciais (modo streaming)

        Returns:
            TranscriptionResult com texto completo
        """
        config = config or TranscriptionConfig()
        self._load_model()

        # Prepara áudio para Whisper
        import numpy as np

        audio_array = np.frombuffer(audio.samples, dtype=np.float32)

        # Transcreve
        language = None if config.detect_language else config.language

        # CORREÇÃO: Adiciona parâmetros anti-alucinação para melhor qualidade PT-BR
        segments_gen, info = self._model.transcribe(
            audio_array,
            language=language,
            beam_size=5,
            word_timestamps=True,  # Necessário para streaming preciso
            # Parâmetros anti-alucinação:
            temperature=0.0,  # Elimina aleatoriedade (reduz alucinações)
            condition_on_previous_text=False,  # Erros não contaminam segmentos seguintes
            vad_filter=True,  # Filtra silêncio e ruído - CRÍTICO para qualidade
            vad_parameters={"min_silence_duration_ms": 500},  # Silêncio mínimo 500ms
            no_speech_threshold=0.6,  # Descarta segmentos provavelmente sem fala
            # Bias de vocabulário técnico:
            hotwords=self._hotwords,  # Lista de 227 palavras técnicas
            initial_prompt=self._initial_prompt,  # Contexto PT-BR + EN mix
        )

        # Modo streaming: chama callback para cada segmento
        if config.streaming and on_partial:
            import asyncio

            # Itera pelos segmentos chamando o callback
            accumulated_text = []
            for segment in segments_gen:
                if segment.text.strip():
                    accumulated_text.append(segment.text)
                    partial = "".join(accumulated_text).strip()

                    # Chama callback com texto parcial acumulado
                    try:
                        await asyncio.get_event_loop().run_in_executor(
                            None, on_partial, partial
                        )
                    except Exception:
                        pass  # Ignora erros no callback

            # Recarrega segments para a etapa final (com mesmos parâmetros anti-alucinação)
            segments_gen, _ = self._model.transcribe(
                audio_array,
                language=language,
                beam_size=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
                no_speech_threshold=0.6,
                hotwords=self._hotwords,
                initial_prompt=self._initial_prompt,
            )

        # Combina todos os segmentos
        text_parts = []
        for segment in segments_gen:
            text_parts.append(segment.text)

        full_text = "".join(text_parts).strip()

        return TranscriptionResult(
            text=full_text,
            language=info.language,
            confidence=info.language_probability,
            duration=audio.duration,
        )

    async def listen(
        self,
        duration: float = 30.0,
        on_partial: Optional[Callable[[str], None]] = None,
        config: Optional[TranscriptionConfig] = None,
        silence_timeout: float = 2.0,
    ) -> TranscriptionResult:
        """Escuta microfone e transcreve com suporte a streaming e detecção de silêncio.

        Args:
            duration: Duração máxima de gravação em segundos
            on_partial: Callback para transcrições parciais (modo streaming)
            config: Configuração de transcrição
            silence_timeout: Segundos de silêncio antes de parar (padrão: 2.0s)

        Returns:
            TranscriptionResult com texto transcrito
        """
        from core.sky.voice.audio_capture import SoundDeviceCapture

        config = config or TranscriptionConfig()
        capture = SoundDeviceCapture()

        # Buffer para streaming
        audio_buffer = []
        partial_text_buffer = []
        last_partial_time = None

        def audio_callback(chunk: bytes) -> None:
            """Callback para cada chunk de áudio capturado."""
            audio_buffer.append(chunk)

            # Se modo streaming está ativo, transcreve parcialmente
            if config.streaming and on_partial:
                import asyncio
                import numpy as np

                # Combina buffer para transcrição parcial
                if len(audio_buffer) > 0:
                    combined = b"".join(audio_buffer)
                    audio_array = np.frombuffer(combined, dtype=np.float32)

                    # Transcreve parcial (não bloqueia)
                    try:
                        # Executa transcrição em thread separada
                        loop = asyncio.get_event_loop()
                        partial_result = loop.run_in_executor(
                            None,
                            lambda: self._transcribe_partial(audio_array, config),
                        )

                        # Nota: Não esperamos o resultado aqui para não bloquear
                        # O callback será chamado com o resultado quando disponível
                    except Exception:
                        pass  # Ignora erros em transcrições parciais

        # Inicia gravação com detecção de silêncio
        await capture.start_recording(
            on_audio_callback=audio_callback,
            silence_threshold=0.01,  # Threshold de silêncio
            silence_timeout=silence_timeout,
        )

        # Aguarda com timeout máximo
        import asyncio

        start_time = asyncio.get_event_loop().time()

        try:
            # Polling para verificar se ainda está gravando
            # (a detecção de silêncio para automaticamente)
            while capture.is_recording():
                await asyncio.sleep(0.1)

                # Verifica timeout máximo
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= duration:
                    break

        finally:
            # Sempre para a gravação
            audio = await capture.stop_recording()

        # Transcrição final completa
        result = await self.transcribe(audio, config, on_partial=on_partial)

        return result

    def _transcribe_partial(
        self,
        audio_array,
        config: TranscriptionConfig,
    ) -> str:
        """Transcreve áudio parcialmente (para streaming).

        Args:
            audio_array: Array numpy com áudio
            config: Configuração de transcrição

        Returns:
            Texto parcial transcrito
        """
        try:
            language = None if config.detect_language else config.language

            # Transcreve com beam_size menor para velocidade
            segments, _ = self._model.transcribe(
                audio_array,
                language=language,
                beam_size=1,  # Menor para streaming
                hotwords=self._hotwords,
                initial_prompt=self._initial_prompt,
            )

            # Retorna primeiro segmento (parcial)
            for segment in segments:
                if segment.text.strip():
                    return segment.text.strip()

            return ""
        except Exception:
            return ""


class WhisperAPIAdapter(STTService):
    """Adapter para Whisper API da OpenAI.

    Usa a API OpenAI para transcrição em nuvem.
    """

    def __init__(self, api_key: str):
        """Inicializa adapter Whisper API.

        Args:
            api_key: Chave de API da OpenAI
        """
        super().__init__(model=STTModel.WHISPER_API)
        self.api_key = api_key

    async def transcribe(
        self,
        audio: AudioData,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Transcreve áudio via OpenAI API."""
        # TODO: Implementar chamada à API OpenAI
        raise NotImplementedError("Whisper API não implementada ainda")

    async def listen(
        self,
        duration: float = 30.0,
        on_partial: Optional[Callable[[str], None]] = None,
        config: Optional[TranscriptionConfig] = None,
    ) -> TranscriptionResult:
        """Escuta microfone e transcreve via API."""
        # TODO: Implementar captura + API call
        raise NotImplementedError("Não implementado ainda")
