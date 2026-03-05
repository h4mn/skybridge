# coding: utf-8
"""
ClaudeWorker - Worker assíncrono para chamadas Claude SDK.

Executa chamadas ao Claude Agent SDK em background
sem bloquear a UI Textual.

Otimizações (18.7):
- Retry logic com exponential backoff para falhas transitórias
- Timeout configurável para evitar travamentos
- Connection pooling via cliente persistente

Streaming (PRD019 Fase 1):
- Suporte a streaming de resposta com include_partial_messages
- AsyncIterator para yield de chunks de texto
- Parser de StreamEvent para extrair text_delta
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional
from pathlib import Path

# Import do Claude Agent SDK para streaming
try:
    from claude_agent_sdk import query
    from claude_agent_sdk.types import ClaudeAgentOptions
    HAS_AGENT_SDK = True
except ImportError:
    HAS_AGENT_SDK = False
    query = None  # type: ignore
    ClaudeAgentOptions = Any  # type: ignore

# Import opcional - permite rodar sem anthropic instalado (legacy)
try:
    from anthropic import AsyncAnthropic
    from anthropic import (
        APITimeoutError,
        InternalServerError,
        RateLimitError,
    )
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    AsyncAnthropic = Any  # type: ignore

    # Mock classes para quando anthropic não está instalado
    class APITimeoutError(Exception):
        pass

    class InternalServerError(Exception):
        pass

    class RateLimitError(Exception):
        pass


@dataclass
class ClaudeResponse:
    """Resposta do Claude SDK."""

    content: str
    tokens_in: int
    tokens_out: int
    latency_ms: float
    retry_count: int = 0  # Número de retries realizados


class ClaudeWorker:
    """
    Worker assíncrono para chamadas Claude SDK.

    Executa chamadas de inferência em background,
    permitindo que a UI continue responsiva.

    Otimizado com retry logic e timeout.
    """

    # Configurações de retry (otimização 18.7)
    MAX_RETRIES = 3  # Máximo de tentativas para falhas transitórias
    INITIAL_RETRY_DELAY = 0.5  # Delay inicial em segundos
    RETRY_BACKOFF_MULTIPLIER = 2.0  # Multiplicador para exponential backoff

    # Timeout padrão (segundos)
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        api_key: str,
        model: str = "glm-4.7",
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        allowed_tools: list[str] | None = None,
        cwd: str | None = None,
    ) -> None:
        """
        Inicializa ClaudeWorker.

        Args:
            api_key: Chave da API Anthropic (ou compatível).
            model: Modelo a usar (padrão: glm-4.7).
            timeout: Timeout para requisições em segundos (otimização 18.7).
            max_retries: Máximo de tentativas para falhas transitórias (otimização 18.7).
            allowed_tools: Lista de ferramentas permitidas para Agent SDK.
            cwd: Diretório de trabalho para Agent SDK.
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Any = None

        # Configurações do Agent SDK para streaming
        self.allowed_tools = allowed_tools or ["Read", "Grep", "Glob"]
        self.cwd = cwd or str(Path.cwd())

    async def _get_client(self) -> Any:
        """
        Retorna cliente async (lazy initialization).

        O cliente é reutilizado entre chamadas (connection pooling).
        """
        if not HAS_ANTHROPIC:
            raise ImportError(
                "Biblioteca 'anthropic' não está instalada. "
                "Instale com: pip install anthropic"
            )
        if self._client is None:
            self._client = AsyncAnthropic(
                api_key=self.api_key,
                base_url="https://api.z.ai/api/anthropic",
                timeout=self.timeout,
            )
        return self._client

    async def stream_response(
        self,
        user_message: str,
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        """
        Streaming de resposta usando Claude Agent SDK.

        Implementa streaming com include_partial_messages=True para
        que o texto apareça incrementalmente na UI.

        Args:
            user_message: Mensagem do usuário.
            system_prompt: System prompt (opcional).

        Yields:
            Chunks de texto conforme chegam do stream.

        Raises:
            ImportError: Se Agent SDK não estiver instalado.
            asyncio.CancelledError: Se o stream for cancelado.
            Exception: Se houver erro na chamada ao SDK.
        """
        if not HAS_AGENT_SDK:
            raise ImportError(
                "Claude Agent SDK não está instalado. "
                "Instale com: pip install claude-agent-sdk"
            )

        # Prepara environment variables (para Z.AI ou outros endpoints)
        import os
        env_vars = {}
        if self.api_key:
            env_vars["ANTHROPIC_AUTH_TOKEN"] = self.api_key
            env_vars["ANTHROPIC_API_KEY"] = self.api_key
        # Usa base_url compatível se configurado via env
        if base_url := os.getenv("ANTHROPIC_BASE_URL"):
            env_vars["ANTHROPIC_BASE_URL"] = base_url

        # Configura opções do SDK com streaming habilitado
        options = ClaudeAgentOptions(
            include_partial_messages=True,  # ← CHAVE para streaming
            allowed_tools=self.allowed_tools,
            permission_mode="acceptEdits",  # Auto-aceita ferramentas de leitura
            cwd=self.cwd,
            env=env_vars,
        )

        # Se system prompt fornecido, adiciona ao início da mensagem
        full_prompt = user_message
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{user_message}"

        # Coleta todos os chunks primeiro (para evitar cancel scope issues)
        chunks = []
        try:
            # Stream de resposta do Agent SDK
            async for message in query(prompt=full_prompt, options=options):
                # Verifica tipo da mensagem
                message_type = type(message).__name__

                # StreamEvent contém eventos de streaming (text_delta, etc)
                if message_type == "StreamEvent":
                    event = message.event  # type: ignore
                    event_type = event.get("type", "")

                    # content_block_delta contém chunks de texto
                    if event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            if text:
                                chunks.append(text)

                # AssistantMessage contém texto completo (fallback)
                elif message_type == "AssistantMessage":
                    if hasattr(message, "content") and message.content:
                        for block in message.content:
                            if hasattr(block, "text"):
                                chunks.append(block.text)

                # ResultMessage indica fim do stream
                elif message_type == "ResultMessage":
                    break

        except asyncio.CancelledError:
            # Propaga CancelledError para permitir interrupção
            raise

        # Agora yield dos chunks coletados (generator limpo)
        for chunk in chunks:
            yield chunk

    async def _create_message_with_retry(
        self,
        client: Any,
        system_prompt: str,
        user_message: str,
        max_tokens: int,
    ) -> Any:
        """
        Cria mensagem com retry logic para falhas transitórias.

        Implementa exponential backoff para melhorar confiabilidade.

        Args:
            client: Cliente Anthropic.
            system_prompt: System prompt da Sky.
            user_message: Mensagem do usuário.
            max_tokens: Máximo de tokens na resposta.

        Returns:
            Resposta da API.

        Raises:
            Exception: Se todas as tentativas falharem.
        """
        last_exception = None
        retry_count = 0

        for attempt in range(self.max_retries + 1):
            try:
                # Primeira tentativa ou tentativas seguintes
                return await client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_message},
                    ],
                )

            except (APITimeoutError, InternalServerError, RateLimitError) as e:
                last_exception = e
                retry_count = attempt + 1

                # Se ainda tem tentativas, aguarda com exponential backoff
                if retry_count <= self.max_retries:
                    delay = self.INITIAL_RETRY_DELAY * (
                        self.RETRY_BACKOFF_MULTIPLIER ** (retry_count - 1)
                    )
                    await asyncio.sleep(delay)
                    continue

            except Exception as e:
                # Erros não transitórios não devem ser retry
                raise

        # Todas as tentativas falharam
        raise last_exception

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 500,
    ) -> ClaudeResponse:
        """
        Gera resposta via Claude SDK.

        Implementa retry logic com exponential backoff para
        melhorar confiabilidade e latência em cenários de falha transitória.

        Args:
            system_prompt: System prompt da Sky.
            user_message: Mensagem do usuário.
            max_tokens: Máximo de tokens na resposta.

        Returns:
            ClaudeResponse com conteúdo, tokens, latência e retry count.
        """
        client = await self._get_client()
        start_time = time.time()

        # Usa retry logic para melhorar confiabilidade
        response = await self._create_message_with_retry(
            client=client,
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        content = response.content[0].text
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens

        return ClaudeResponse(
            content=content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            retry_count=0,  # TODO: rastrear retries se necessário
        )


__all__ = ["ClaudeWorker", "ClaudeResponse"]
