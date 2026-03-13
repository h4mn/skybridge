"""
TTS Service - Text-to-Speech para a Sky.

Este módulo define a interface abstrata para síntese de voz,
com suporte a múltiplos backends (MOSS-TTS, ElevenLabs, etc).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from core.sky.voice.audio_capture import AudioData


class TTSModel(Enum):
    """Modelos de TTS disponíveis."""

    MOSS_TTS = "moss-tts"
    KOKORO = "kokoro"
    PYTTSX3 = "pyttsx3"
    ELEVENLABS = "elevenlabs"
    COQUI_TTS = "coqui-tts"


@dataclass
class VoiceConfig:
    """Configuração de voz para TTS.

    Attributes:
        voice_id: Identificador da voz (ex: "sky-female", "sky-male")
        speed: Velocidade da fala (0.5=lento, 1.0=normal, 2.0=rápido)
        pitch: Ajuste de pitch em semitons (-12=grave, 0=normal, +12=agudo)
        language: Código do idioma (ex: "pt-BR", "en")
    """

    voice_id: str = "sky-female"
    speed: float = 1.0
    pitch: int = 0
    language: str = "pt-BR"

    def validate(self) -> None:
        """Valida parâmetros de configuração."""
        if not 0.5 <= self.speed <= 2.0:
            raise ValueError(f"Speed deve estar entre 0.5 e 2.0, got {self.speed}")
        if not -12 <= self.pitch <= 12:
            raise ValueError(f"Pitch deve estar entre -12 e +12, got {self.pitch}")


class TTSService(ABC):
    """Interface abstrata para Text-to-Speech.

    Esta interface permite swap de implementação entre diferentes backends:
    - MOSSTTSAdapter: MOSS-TTS via Hugging Face (open source)
    - ElevenLabsAdapter: ElevenLabs API (premium)
    - CoquiTTSAdapter: Coqui TTS (alternativa open source)
    """

    def __init__(self, model: TTSModel = TTSModel.MOSS_TTS):
        """Inicializa serviço TTS.

        Args:
            model: Modelo de TTS a ser usado
        """
        self.model = model

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> AudioData:
        """Sintetiza áudio a partir do texto.

        Args:
            text: Texto para ser falado
            config: Configuração de voz (opcional)

        Returns:
            AudioData com o áudio gerado
        """
        pass

    @abstractmethod
    async def speak(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> None:
        """Sintetiza e reproduz áudio.

        Args:
            text: Texto para ser falado
            config: Configuração de voz (opcional)
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """Retorna lista de vozes disponíveis.

        Returns:
            Lista de voice_ids disponíveis
        """
        pass


class MOSSTTSAdapter(TTSService):
    """Adapter para MOSS-TTS via Hugging Face.

    MOSS-TTS é um modelo open source de alta qualidade
    para síntese de voz em múltiplos idiomas.
    """

    def __init__(self, voice: str = "sky-female"):
        """Inicializa adapter MOSS-TTS.

        Args:
            voice: Voz padrão a ser usada
        """
        super().__init__(model=TTSModel.MOSS_TTS)
        self.voice = voice
        self._model = None
        self._import_transformers()

    def _import_transformers(self):
        """Importa transformers lazy (só quando necessário)."""
        try:
            from transformers import AutoModelForTextToSpectrogram, AutoProcessor
            self._AutoModel = AutoModelForTextToSpectrogram
            self._AutoProcessor = AutoProcessor
        except ImportError as e:
            raise ImportError(
                "transformers não está instalado. "
                "Execute: pip install transformers"
            ) from e

    async def _load_model(self):
        """Carrega modelo MOSS-TTS real do Hugging Face."""
        if self._model is None:
            try:
                from transformers import VitsModel, AutoTokenizer
                import torch

                # Modelo MMS-TTS para português
                # Outras opções:
                # - "facebook/mms-tts-por" (Português)
                # - "speechbrain/TTS-hifigan-ljs-v2" (Inglês, muito popular)
                model_name = "facebook/mms-tts-por"

                # Carrega modelo e tokenizer
                self._model = VitsModel.from_pretrained(model_name)
                self._tokenizer = AutoTokenizer.from_pretrained(model_name)

                # Move para CPU se disponível
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model.to(device)
                self._device = device

            except ImportError as e:
                raise ImportError(
                    "transformers ou torch não instalados. "
                    "Execute: pip install transformers torch"
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f"Erro ao carregar modelo MOSS-TTS: {e}"
                ) from e

    async def synthesize(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> AudioData:
        """Sintetiza áudio a partir do texto usando MOSS-TTS real."""
        config = config or VoiceConfig()
        config.validate()

        if not text or not text.strip():
            raise ValueError("Texto não pode ser vazio")

        # Carrega modelo
        await self._load_model()

        try:
            import torch
            import numpy as np

            # Prepara texto para o modelo
            inputs = self._tokenizer(text, return_tensors="pt")

            # Move inputs para o mesmo dispositivo do modelo
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Gera áudio
            with torch.no_grad():
                output = self._model(**inputs)
                audio_array = output.waveform[0].cpu().numpy()

            # Normaliza áudio
            audio_array = audio_array / np.max(np.abs(audio_array))

            # Aplica configuração de velocidade (resampling)
            # Speed > 1.0 = mais rápido (menos amostras)
            # Speed < 1.0 = mais lento (mais amostras)
            if config.speed != 1.0:
                import scipy.signal as signal
                original_length = len(audio_array)
                new_length = int(original_length / config.speed)
                audio_array = signal.resample(audio_array, new_length)

            # Converte para float32 bytes
            audio_bytes = (audio_array * 0.8).astype(np.float32).tobytes()

            # Calcula duração
            sample_rate = self._model.config.sampling_rate
            duration = len(audio_array) / sample_rate

            return AudioData(
                samples=audio_bytes,
                sample_rate=sample_rate,
                channels=1,
                duration=duration,
            )

        except Exception as e:
            raise RuntimeError(f"Erro na síntese MOSS-TTS: {e}") from e

    async def speak(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> None:
        """Sintetiza e reproduz áudio."""
        audio = await self.synthesize(text, config)
        await self._play_audio(audio)

    async def _play_audio(self, audio: AudioData) -> None:
        """Reproduz áudio usando sounddevice."""
        try:
            import sounddevice as sd
            import numpy as np

            # Converte bytes para numpy array
            samples = np.frombuffer(audio.samples, dtype=np.float32)

            sd.play(samples, samplerate=audio.sample_rate)
            sd.wait()  # Aguarda fim da reprodução
        except ImportError:
            raise ImportError("sounddevice não está instalado")

    def get_available_voices(self) -> list[str]:
        """Retorna vozes disponíveis."""
        return ["sky-female", "sky-male"]


class ElevenLabsAdapter(TTSService):
    """Adapter para ElevenLabs API.

    ElevenLabs é um serviço premium de alta qualidade
    para síntese de voz.
    """

    def __init__(self, api_key: str, voice: str = "sky-female"):
        """Inicializa adapter ElevenLabs.

        Args:
            api_key: Chave de API da ElevenLabs
            voice: Voz padrão a ser usada
        """
        super().__init__(model=TTSModel.ELEVENLABS)
        self.api_key = api_key
        self.voice = voice

    async def synthesize(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> AudioData:
        """Sintetiza áudio via ElevenLabs API."""
        # TODO: Implementar chamada à API ElevenLabs
        raise NotImplementedError("ElevenLabs API não implementada ainda")

    async def speak(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> None:
        """Sintetiza e reproduz áudio."""
        audio = await self.synthesize(text, config)
        await self._play_audio(audio)

    async def _play_audio(self, audio: AudioData) -> None:
        """Reproduz áudio usando sounddevice."""
        try:
            import sounddevice as sd
            import numpy as np

            samples = np.frombuffer(audio.samples, dtype=np.float32)
            sd.play(samples, samplerate=audio.sample_rate)
            sd.wait()
        except ImportError:
            raise ImportError("sounddevice não está instalado")

    def get_available_voices(self) -> list[str]:
        """Retorna vozes disponíveis na ElevenLabs."""
        # TODO: Buscar vozes disponíveis via API
        return []


class Pyttsx3Adapter(TTSService):
    """Adapter para pyttsx3 (TTS offline com vozes do sistema).

    pyttsx3 é uma biblioteca TTS offline que usa as vozes do sistema
    operacional. Funciona sem internet e suporta português.

    Vantagens:
    - Offline (funciona sem internet)
    - Vozes do sistema (incluindo PT-BR)
    - Leve e rápido

    Limitações:
    - Qualidade depende das vozes instaladas no Windows
    - Menos natural que modelos de ML
    """

    def __init__(self, voice: str = "sky-female"):
        """Inicializa adapter pyttsx3.

        Args:
            voice: Voz padrão ("sky-female" ou "sky-male")
        """
        super().__init__(model=TTSModel.PYTTSX3)
        self.voice = voice
        self._engine = None
        self._voice_mapping = {}  # Mapeamento voice_id -> pyttsx3 voice

    def _import_pyttsx3(self):
        """Importa pyttsx3 lazy (só quando necessário)."""
        try:
            import pyttsx3
            self._pyttsx3 = pyttsx3
        except ImportError as e:
            raise ImportError(
                "pyttsx3 não está instalado. "
                "Execute: pip install pyttsx3"
            ) from e

    def _init_engine(self):
        """Inicializa engine pyttsx3."""
        if self._engine is None:
            self._import_pyttsx3()
            self._engine = self._pyttsx3.init()

            # Descobre vozes disponíveis e cria mapeamento
            voices = self._engine.getProperty("voices")
            self._voice_mapping = self._discover_voices(voices)

    def _discover_voices(self, voices) -> dict:
        """Descobre e mapeia vozes do sistema.

        Args:
            voices: Lista de vozes do pyttsx3

        Returns:
            Dict mapeando voice_id -> voice index/id
        """
        mapping = {}

        for i, voice in enumerate(voices):
            voice_name = voice.name.lower()
            voice_id = voice.id

            # Tenta encontrar voz feminina em português
            if "female" in voice_name or "maria" in voice_name or "helena" in voice_name:
                mapping["sky-female"] = i
            # Tenta encontrar voz masculina em português
            elif "male" in voice_name or "daniel" in voice_name or "david" in voice_name:
                mapping["sky-male"] = i
            # Voz em português (fallback)
            elif "brazil" in voice_id or "pt_br" in voice_id or "pt-br" in voice_id:
                if "sky-female" not in mapping:
                    mapping["sky-female"] = i
                if "sky-male" not in mapping:
                    mapping["sky-male"] = i

        # Fallback: primeira voz disponível
        if "sky-female" not in mapping and voices:
            mapping["sky-female"] = 0
        if "sky-male" not in mapping and voices:
            mapping["sky-male"] = 0

        return mapping

    async def synthesize(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> AudioData:
        """Sintetiza áudio a partir do texto usando pyttsx3."""
        config = config or VoiceConfig()
        config.validate()

        if not text or not text.strip():
            raise ValueError("Texto não pode ser vazio")

        self._init_engine()

        # Configura engine
        self._configure_engine(config)

        # Salva áudio em arquivo temporário
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file = f.name

        try:
            # Salva áudio no arquivo
            self._engine.save_to_file(text, temp_file)
            self._engine.runAndWait()

            # Lê o arquivo de volta
            import wave

            with wave.open(temp_file, "rb") as wf:
                sample_rate = wf.getframerate()
                frames = wf.getnframes()
                duration = frames / sample_rate
                audio_bytes = wf.readframes(frames)

            return AudioData(
                samples=audio_bytes,
                sample_rate=sample_rate,
                channels=1,  # pyttsx3 sempre mono
                duration=duration,
            )

        finally:
            # Remove arquivo temporário
            try:
                os.unlink(temp_file)
            except:
                pass

    def _configure_engine(self, config: VoiceConfig) -> None:
        """Configura engine pyttsx3 baseado na VoiceConfig.

        Args:
            config: Configuração de voz
        """
        # Configura velocidade (rate)
        # pyttsx3 usa palavras por minuto (padrão: ~200)
        # Speed 1.0 = 200 WPM
        rate = int(200 * config.speed)
        self._engine.setProperty("rate", rate)

        # Configura volume (0.0 a 1.0)
        self._engine.setProperty("volume", 1.0)

        # Configura voz
        voice_index = self._voice_mapping.get(config.voice_id, 0)
        if voice_index < len(self._engine.getProperty("voices")):
            self._engine.setProperty("voice", self._engine.getProperty("voices")[voice_index].id)

    async def speak(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> None:
        """Sintetiza e reproduz áudio."""
        import tempfile
        import os

        self._init_engine()
        config = config or VoiceConfig()
        config.validate()

        # Configura engine
        self._configure_engine(config)

        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file = f.name

        try:
            # Salva áudio no arquivo
            self._engine.save_to_file(text, temp_file)
            self._engine.runAndWait()

            # Reproduz diretamente do arquivo
            await self._play_wav_file(temp_file)

        finally:
            # Remove arquivo temporário
            try:
                os.unlink(temp_file)
            except:
                pass

    async def _play_wav_file(self, wav_path: str) -> None:
        """Reproduz arquivo WAV usando pygame ou winsound."""
        try:
            # Tenta pygame primeiro (cross-platform)
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(wav_path)
            pygame.mixer.music.play()

            # Aguarda fim da reprodução
            while pygame.mixer.music.get_busy():
                import asyncio
                await asyncio.sleep(0.1)

        except ImportError:
            # Fallback para Windows (winsound)
            try:
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
            except ImportError:
                # Fallback para subprocess com player do sistema
                import subprocess
                import platform

                system = platform.system()
                if system == "Windows":
                    subprocess.call(["powershell", "-c", f"(New-Object Media.SoundPlayer '{wav_path}').PlaySync()"])
                elif system == "Darwin":  # macOS
                    subprocess.call(["afplay", wav_path])
                else:  # Linux
                    subprocess.call(["aplay", wav_path])

    def get_available_voices(self) -> list[str]:
        """Retorna vozes disponíveis."""
        self._init_engine()
        voices = list(self._voice_mapping.keys())
        return voices if voices else ["sky-female"]


class KokoroAdapter(TTSService):
    """Adapter para Kokoro TTS (Hexgrad).

    Kokoro é um modelo TTS com vozes femininas muito naturais e expressivas.
    Desenvolvido pela Hexgrad.

    Características:
    - Voz feminina suave e natural
    - Expressividade emocional
    - Alta qualidade de fala (quase humana)
    - Modelo compacto de 82M
    - Apache-licensed (uso livre)

    Biblioteca: pip install kokoro
    Modelo: hexgrad/Kokoro-82M (via Hugging Face)
    """

    def __init__(self, voice: str = "af_heart"):
        """Inicializa adapter Kokoro.

        Args:
            voice: Voz Kokoro ("af_heart" = feminina suave padrão)
        """
        super().__init__(model=TTSModel.KOKORO)
        self.voice = voice
        self._pipeline = None

    async def _load_model(self):
        """Carrega pipeline Kokoro."""
        if self._pipeline is None:
            try:
                from kokoro import KPipeline

                # Carrega pipeline Kokoro
                self._pipeline = KPipeline(lang_code='a')  # 'a' = American English

            except ImportError as e:
                raise ImportError(
                    "kokoro não está instalado. "
                    "Execute: pip install kokoro"
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f"Erro ao carregar Kokoro: {e}"
                ) from e

    async def synthesize(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> AudioData:
        """Sintetiza áudio a partir do texto usando Kokoro."""
        config = config or VoiceConfig()
        config.validate()

        if not text or not text.strip():
            raise ValueError("Texto não pode ser vazio")

        # Carrega pipeline
        await self._load_model()

        try:
            import numpy as np

            # Gera áudio com Kokoro
            # O generator retorna (graphemes, phonemes, audio)
            generator = self._pipeline(
                text,
                voice=self.voice,
                speed=float(config.speed),
                split_pattern=r'\n+'
            )

            # Pega última iteração (áudio final)
            audio_array = None
            for gs, ps, audio in generator:
                audio_array = audio

            if audio_array is None:
                raise RuntimeError("Falha ao gerar áudio com Kokoro")

            # Normaliza se necessário
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)

            # Normaliza amplitude
            if np.max(np.abs(audio_array)) > 0:
                audio_array = audio_array / np.max(np.abs(audio_array))

            # Converte para bytes
            audio_bytes = (audio_array * 0.8).astype(np.float32).tobytes()

            # Kokoro usa 24000 Hz
            sample_rate = 24000
            duration = len(audio_array) / sample_rate

            return AudioData(
                samples=audio_bytes,
                sample_rate=sample_rate,
                channels=1,
                duration=duration,
            )

        except Exception as e:
            raise RuntimeError(f"Erro na síntese Kokoro: {e}") from e

    async def speak(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> None:
        """Sintetiza e reproduz áudio."""
        audio = await self.synthesize(text, config)
        await self._play_audio(audio)

    async def _play_audio(self, audio: AudioData) -> None:
        """Reproduz áudio usando sounddevice."""
        try:
            import sounddevice as sd
            import numpy as np

            # Converte bytes para numpy array
            samples = np.frombuffer(audio.samples, dtype=np.float32)

            sd.play(samples, samplerate=audio.sample_rate)
            sd.wait()
        except ImportError:
            raise ImportError("sounddevice não está instalado")

    def get_available_voices(self) -> list[str]:
        """Retorna vozes disponíveis."""
        # Kokoro tem várias vozes femininas
        return [
            "af_heart",      # Feminina suave (padrão)
            "af_sky",        # Feminina narrativa
            "af_bella",      # Feminina elegante
            "sky-female",    # Mapeamento para nosso sistema
        ]

    async def synthesize(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> AudioData:
        """Sintetiza áudio a partir do texto usando Kokoro."""
        config = config or VoiceConfig()
        config.validate()

        if not text or not text.strip():
            raise ValueError("Texto não pode ser vazio")

        # Carrega modelo
        await self._load_model()

        try:
            import torch
            import numpy as np

            # Prepara texto
            inputs = self._tokenizer(text, return_tensors="pt")

            # Move para dispositivo
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Gera áudio com Kokoro
            with torch.no_grad():
                output = self._model.generate_speech(
                    **inputs,
                    emotion=self.emotion,
                    speaker="default",
                )

                # Kokoro retorna waveform
                if isinstance(output, dict):
                    audio_array = output["waveform"].cpu().numpy()
                else:
                    audio_array = output.cpu().numpy()

                # Se for 3D (batch, channels, samples), converte para 1D
                if audio_array.ndim == 3:
                    audio_array = audio_array[0, 0]
                elif audio_array.ndim == 2:
                    audio_array = audio_array[0]

            # Normaliza
            audio_array = audio_array / np.max(np.abs(audio_array))

            # Aplica velocidade se configurado
            if config.speed != 1.0:
                import scipy.signal as signal
                original_length = len(audio_array)
                new_length = int(original_length / config.speed)
                audio_array = signal.resample(audio_array, new_length)

            # Converte para bytes
            audio_bytes = (audio_array * 0.8).astype(np.float32).tobytes()

            # Obtem sample rate do modelo
            if hasattr(self._model.config, "sampling_rate"):
                sample_rate = self._model.config.sampling_rate
            else:
                sample_rate = 16000  # Default

            duration = len(audio_array) / sample_rate

            return AudioData(
                samples=audio_bytes,
                sample_rate=sample_rate,
                channels=1,
                duration=duration,
            )

        except Exception as e:
            raise RuntimeError(f"Erro na síntese Kokoro: {e}") from e

    async def speak(
        self,
        text: str,
        config: Optional[VoiceConfig] = None,
    ) -> None:
        """Sintetiza e reproduz áudio."""
        audio = await self.synthesize(text, config)
        await self._play_audio(audio)

    async def _play_audio(self, audio: AudioData) -> None:
        """Reproduz áudio usando sounddevice."""
        try:
            import sounddevice as sd
            import numpy as np

            # Converte bytes para numpy array
            samples = np.frombuffer(audio.samples, dtype=np.float32)

            sd.play(samples, samplerate=audio.sample_rate)
            sd.wait()
        except ImportError:
            raise ImportError("sounddevice não está instalado")

    def get_available_voices(self) -> list[str]:
        """Retorna vozes disponíveis."""
        return ["sky-female", "sky-female-happy", "sky-female-sad"]

    def set_emotion(self, emotion: str) -> None:
        """Define a emoção da voz.

        Args:
            emotion: Emoção ("default", "happy", "sad", "angry", etc.)
        """
        self.emotion = emotion
