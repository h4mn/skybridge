# coding: utf-8
"""
Voice API Stage - Estágio de bootstrap para inicializar a Voice API.

DOC: openspec/changes/voice-api-isolation/tasks.md - Seções 12 e 13
Feature flag: SKYBRIDGE_VOICE_API_ENABLED (default: 0)
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from typing import Optional

import httpx

from core.sky.voice.feature_toggle import is_voice_api_enabled, get_voice_api_url


logger = logging.getLogger(__name__)


# Configurações
STARTUP_TIMEOUT = 120.0  # segundos
HEALTH_POLL_INTERVAL = 0.1  # 100ms
MAX_RETRIES = 2
RETRY_DELAY = 2.0  # segundos
SHUTDOWN_TIMEOUT = 5.0  # segundos


class VoiceAPIStage:
    """
    Gerencia inicialização e lifecycle da Voice API como subprocess.

    Responsabilidades:
    - Iniciar subprocess da Voice API
    - Aguardar via health check até ficar ready
    - Fazer retry em caso de crash no startup
    - Fazer cleanup gracioso no shutdown
    """

    def __init__(self):
        """Inicializa o stage."""
        self._process: Optional[subprocess.Popen] = None
        self._base_url: Optional[str] = None
        self._ready = False

    def is_enabled(self) -> bool:
        """
        Verifica se a Voice API está habilitada via feature toggle.

        Returns:
            True se SKYBRIDGE_VOICE_API_ENABLED=1, False caso contrário
        """
        return is_voice_api_enabled()

    def execute(
        self,
        progress_update_callback: Optional[callable] = None,
        progress_context: Optional[Any] = None
    ) -> str:
        """
        Executa o estágio de inicialização da Voice API.

        Args:
            progress_update_callback: Callback para atualizar progresso visualmente
            progress_context: Contexto de progresso do bootstrap

        Returns:
            URL base da Voice API (ex: "http://127.0.0.1:8765")

        Raises:
            RuntimeError: Se falhar após todas as tentativas
        """
        if not self.is_enabled():
            logger.info("Voice API desabilitada via feature flag")
            return ""

        # Obtém URL configurada
        self._base_url = get_voice_api_url()

        # Tenta iniciar com retry
        for attempt in range(MAX_RETRIES + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry {attempt}/{MAX_RETRIES} após crash...")
                    time.sleep(RETRY_DELAY)

                self._start_and_wait(progress_update_callback, progress_context)
                return self._base_url

            except Exception as e:
                logger.error(f"Tentativa {attempt + 1} falhou: {e}")
                self._cleanup()

                if attempt >= MAX_RETRIES:
                    raise RuntimeError(
                        f"Voice API falhou após {MAX_RETRIES + 1} tentativas: {e}"
                    ) from e

        # Nunca deve chegar aqui
        raise RuntimeError("Voice API: estado inesperado no execute()")

    def _start_and_wait(
        self,
        progress_update_callback: Optional[callable] = None,
        progress_context: Optional[Any] = None
    ) -> None:
        """
        Inicia subprocess e aguarda until ready.

        Args:
            progress_update_callback: Callback para atualizar progresso
            progress_context: Contexto de progresso do bootstrap

        Raises:
            RuntimeError: Se timeout ou crash
        """
        # Inicia subprocess
        self._process = self._start_subprocess()
        logger.info(f"Voice API subprocess iniciado (pid: {self._process.pid})")

        # Aguarda ready com health check
        self._wait_until_ready(progress_update_callback, progress_context)

        self._ready = True
        logger.info(f"Voice API ready em {self._base_url}")

    def _start_subprocess(self) -> subprocess.Popen:
        """
        Inicia subprocess da Voice API.

        Returns:
            Processo iniciado
        """
        # Usa mesmo Python interpreter
        python_exe = sys.executable

        # Module path
        module = "src.core.sky.voice.api.main"

        # Build command
        cmd = [
            python_exe,
            "-m",
            module,
            "--port", "8765",  # Porta fixa por enquanto
            "--log-level", "info"
        ]

        # Log
        logger.info(f"Iniciando Voice API: {' '.join(cmd)}")

        # Inicia subprocess
        # - stdout/stderr redirecionados para logs (pipe)
        # - sem janela no Windows (CREATE_NO_WINDOW)
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW  # type: ignore

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creation_flags,
            text=False  # bytes para UTF-8 correto
        )

        return process

    def _wait_until_ready(
        self,
        progress_update_callback: Optional[callable] = None,
        progress_context: Optional[Any] = None
    ) -> None:
        """
        Aguarda Voice API ficar ready via polling de /health.

        Args:
            progress_update_callback: Callback para atualizar progresso
            progress_context: Contexto de progresso do bootstrap

        Raises:
            RuntimeError: Se timeout ou processo crashar
        """
        start_time = time.time()
        client = httpx.Client(timeout=5.0)

        try:
            while True:
                # Verifica timeout
                elapsed = time.time() - start_time
                if elapsed > STARTUP_TIMEOUT:
                    raise RuntimeError(
                        f"Timeout após {STARTUP_TIMEOUT}s aguardando Voice API ready"
                    )

                # Verifica se processo ainda está rodando
                if self._process and self._process.poll() is not None:
                    # Processo terminou (crash)
                    stderr = self._process.stderr.read() if self._process else b""
                    raise RuntimeError(
                        f"Voice API crashou (exit code: {self._process.returncode})"
                        f"{stderr.decode('utf-8', errors='replace') if stderr else ''}"
                    )

                # Tenta health check
                try:
                    response = client.get(f"{self._base_url}/health")
                    response.raise_for_status()

                    data = response.json()
                    status = data.get("status")
                    progress = data.get("progress", 0.0)
                    message = data.get("message", "")
                    stage = data.get("stage")

                    # Atualiza progresso visualmente
                    if progress_update_callback and progress_context:
                        self._update_progress(
                            progress_context,
                            status,
                            progress,
                            message,
                            stage
                        )

                    # Verifica se está ready
                    if status == "ready":
                        return

                    # Se está em erro, levanta exceção
                    if status == "error":
                        raise RuntimeError(f"Voice API reportou erro: {message}")

                except httpx.HTTPError:
                    # API ainda não está respondendo (normal durante startup)
                    pass

                # Aguarda antes do próximo poll
                time.sleep(HEALTH_POLL_INTERVAL)

        finally:
            client.close()

    def _update_progress(
        self,
        progress_context: Any,
        status: str,
        progress: float,
        message: str,
        stage: Optional[str]
    ) -> None:
        """
        Atualiza progresso visualmente no bootstrap.

        Args:
            progress_context: Contexto de progresso do bootstrap
            status: Status atual (STARTING, LOADING_MODELS, READY, ERROR)
            progress: Progresso (0.0 a 1.0)
            message: Mensagem descritiva
            stage: Estágio atual (stt, tts, etc)
        """
        # Monta descrição com porcentagem
        percent = int(progress * 100)
        if stage:
            desc = f"Carregando Voice API... [{message} {percent}%]"
        else:
            desc = f"Carregando Voice API... [{message} {percent}%]"

        # Atualiza descrição do stage
        if hasattr(progress_context, "update_stage_description"):
            progress_context.update_stage_description("voice_api", desc)

    def shutdown(self, timeout: float = SHUTDOWN_TIMEOUT) -> None:
        """
        Encerra Voice API graciosamente.

        Args:
            timeout: Tempo em segundos para aguardar shutdown graciosos
        """
        if self._process is None:
            return

        logger.info("Encerrando Voice API...")

        try:
            # SIGTERM (shutdown graciosos)
            self._process.terminate()

            # Aguarda até timeout
            try:
                self._process.wait(timeout=timeout)
                logger.info("Voice API encerrada graciosamente")
                return
            except subprocess.TimeoutExpired:
                pass

            # SIGKILL (forçado)
            logger.warning("Voice API não respondeu ao SIGTERM, enviando SIGKILL...")
            self._process.kill()
            self._process.wait(timeout=1.0)
            logger.info("Voice API encerrada forçadamente")

        except Exception as e:
            logger.error(f"Erro ao encerrar Voice API: {e}")

        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Limpa recursos."""
        if self._process:
            try:
                # Fecha pipes
                if self._process.stdout:
                    self._process.stdout.close()
                if self._process.stderr:
                    self._process.stderr.close()
            except Exception:
                pass

        self._process = None
        self._ready = False

    def is_ready(self) -> bool:
        """
        Verifica se Voice API está ready.

        Returns:
            True se está ready e rodando
        """
        if not self._ready or not self._process:
            return False

        # Verifica se processo ainda está rodando
        return self._process.poll() is None

    def get_url(self) -> Optional[str]:
        """
        Retorna URL da Voice API.

        Returns:
            URL base ou None se não inicializada
        """
        return self._base_url


# Singleton instance
_instance: Optional[VoiceAPIStage] = None


def get_voice_api_stage() -> VoiceAPIStage:
    """
    Retorna instância singleton do VoiceAPIStage.

    Returns:
        Instância do stage
    """
    global _instance
    if _instance is None:
        _instance = VoiceAPIStage()
    return _instance


# Função compatível com o padrão de stages do bootstrap
def _stage_voice_api(progress: Any, ctx: Optional[Any] = None) -> str:
    """
    Estágio de bootstrap: Inicialização da Voice API.

    Esta função segue o padrão dos outros estágios (_stage_environment, etc)
    e pode ser adicionada ao pipeline do bootstrap.

    Args:
        progress: Instância de Progress
        ctx: Contexto de progresso (_ProgressContext)

    Returns:
        URL base da Voice API

    Raises:
        RuntimeError: Se falhar após todas as tentativas
    """
    stage = get_voice_api_stage()

    # Só executa se feature flag enabled
    if not stage.is_enabled():
        logger.info("Voice API está desabilitada, pulando estágio")
        return ""

    # Executa e retorna URL
    return stage.execute(
        progress_update_callback=None,
        progress_context=ctx
    )
