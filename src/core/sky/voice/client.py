"""Voice API Client - Cliente HTTP assíncrono para consumir a Voice API."""

import asyncio

import httpx

from core.sky.voice.api.models import HealthResponse, StartupStatus


class VoiceAPITimeoutError(TimeoutError):
    """Timeout ao aguardar resposta da Voice API."""

class VoiceAPIUnavailableError(ConnectionError):
    """Voice API não está disponível."""

class VoiceAPIRequestError(Exception):
    """Erro na request à Voice API."""


class VoiceAPIClient:
    """Cliente HTTP assíncrono para Voice API."""

    DEFAULT_BASE_URL = "http://127.0.0.1:8765"
    DEFAULT_TIMEOUT = 30.0
    MAX_RETRIES = 3

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT
    ):
        """Inicializa o cliente.

        Args:
            base_url: URL base da Voice API
            timeout: Timeout padrão para requests (segundos)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Fecha o cliente HTTP."""
        await self._client.aclose()

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """Faz request com retry automático para erros 5xx."""
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.request(
                    method,
                    f"{self.base_url}{path}",
                    **kwargs
                )

                # Sucesso ou erro 4xx (não retry)
                if response.status_code < 500:
                    return response

                # Erro 5xx - retry com backoff
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # 1s, 2s, 3s
                    continue

                return response

            except httpx.TimeoutException as e:
                last_error = VoiceAPITimeoutError(f"Timeout after {self.timeout}s")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                raise last_error

            except httpx.ConnectError as e:
                raise VoiceAPIUnavailableError(f"Cannot connect to {self.base_url}") from e

        raise VoiceAPIRequestError(f"Request failed after {self.MAX_RETRIES} retries")

    async def health(self) -> HealthResponse:
        """Verifica status da Voice API.

        Returns:
            HealthResponse com status atual

        Raises:
            VoiceAPIUnavailableError: Se API não responde
        """
        response = await self._request_with_retry("GET", "/health")
        data = response.json()

        return HealthResponse(
            status=StartupStatus(data["status"]),
            progress=data["progress"],
            message=data["message"],
            stage=data.get("stage")
        )

    async def wait_until_ready(self, timeout: float = 60.0) -> None:
        """Aguarda até que a Voice API esteja ready.

        Args:
            timeout: Tempo máximo de espera (segundos)

        Raises:
            VoiceAPITimeoutError: Se timeout
            VoiceAPIUnavailableError: Se API não responde
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            try:
                status = await self.health()

                if status.status == StartupStatus.READY:
                    return

                if status.status == StartupStatus.ERROR:
                    raise VoiceAPIRequestError(f"API error: {status.message}")

            except VoiceAPIUnavailableError:
                pass  # API ainda não está up, tentar de novo

            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise VoiceAPITimeoutError(f"API not ready after {timeout}s")

            await asyncio.sleep(0.1)

    async def stt(self, audio_bytes: bytes) -> str:
        """Transcreve áudio para texto.

        Args:
            audio_bytes: Áudio em formato WAV (bytes)

        Returns:
            Texto transcrito

        Raises:
            VoiceAPIRequestError: Se request falhar
        """
        import base64

        # Para POC: envia em base64
        # Implementação completa usaria multipart/form-data
        response = await self._request_with_retry(
            "POST",
            "/voice/stt",
            json={"audio": base64.b64encode(audio_bytes).decode()}
        )

        if response.status_code != 200:
            raise VoiceAPIRequestError(f"STT failed: {response.text}")

        data = response.json()
        return data["text"]

    async def tts(
        self,
        text: str,
        mode: str = "normal"
    ) -> bytes:
        """Sintetiza texto em áudio.

        Args:
            text: Texto para sintetizar
            mode: Modo de voz ("normal" ou "thinking")

        Returns:
            Bytes de áudio (float32 @ 24000Hz)

        Raises:
            VoiceAPIRequestError: Se request falhar
        """
        response = await self._request_with_retry(
            "POST",
            "/voice/tts",
            json={"text": text, "mode": mode}
        )

        if response.status_code != 200:
            raise VoiceAPIRequestError(f"TTS failed: {response.text}")

        return response.content

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
