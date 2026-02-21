# coding: utf-8
"""
ClaudeChatAdapter - Chat com Claude Agent SDK.

DOC: openspec/changes/chat-claude-sdk/specs/claude-chat-integration/spec.md
"""

import os
import time
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from core.sky.chat.personality import build_system_prompt, format_memory_context
from core.sky.memory import get_memory, PersistentMemory
from runtime.observability.logger import get_logger

# Logger estruturado para chat
logger = get_logger("sky.chat", level="INFO")


# Re-definir ChatMessage aqui para evitar import circular
# DOC: compatível com src.core.sky.chat.ChatMessage
@dataclass
class ChatMessage:
    """Uma mensagem na conversa."""
    role: str  # "user" ou "sky"
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


# Import de SkyChat será feito lazy para evitar circular import
# DOC: usado apenas em _fallback_to_legacy()


# Configurações
MAX_HISTORY_LENGTH = 20  # 10 turnos (user + sky)
TOP_K_MEMORIES = 5


def get_claude_model() -> str:
    """
    Retorna o modelo Claude configurado via environment variable.

    DOC: spec.md - Requirement: Configuração de modelo Claude

    Usa ANTHROPIC_DEFAULT_OPUS_MODEL ou CLAUDE_MODEL.

    Returns:
        Nome do modelo Claude a usar.
    """
    return os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL") or os.getenv("CLAUDE_MODEL", "glm-4.7")


# Configurações
MAX_HISTORY_LENGTH = 20  # 10 turnos (user + sky)
TOP_K_MEMORIES = 5


class ClaudeChatAdapter:
    """
    Chat com Claude Agent SDK.

    Implementa a mesma interface de SkyChat para compatibilidade.

    DOC: spec.md - Requirement: Fluxo de mensagens através do ClaudeChatAdapter
    """

    def __init__(self, memory: Optional[PersistentMemory] = None):
        """
        Inicializa o adapter.

        Args:
            memory: Instância de PersistentMemory. Se None, usa get_memory().
        """
        # DOC: spec.md - Cenário: Adapter recebe mensagem do usuário
        self._memory = memory if memory is not None else get_memory()
        self._history: List[ChatMessage] = []

        # Métricas da última resposta
        self._last_tokens_in: int = 0
        self._last_tokens_out: int = 0
        self._last_latency_ms: float = 0.0

    def receive(self, message: ChatMessage) -> None:
        """
        Recebe uma mensagem do usuário.

        DOC: spec.md - Cenário: Mensagem do usuário adicionada ao histórico

        Args:
            message: Mensagem recebida.
        """
        # DOC: "mensagem é armazenada no histórico com timestamp"
        # DOC: "role é marcado como 'user'"
        # DOC: "conteúdo é preservado exatamente como enviado"
        self._history.append(message)

        # Processar oportunidades de aprendizado (similar ao SkyChat)
        self._process_learning(message.content)

    async def respond(self, message: Optional[ChatMessage] = None) -> str:
        """
        Responde a uma mensagem.

        DOC: spec.md - Cenário: Adapter gera resposta

        NOTA: Este método é assíncrono para compatibilidade com Claude Agent SDK.
        Use asyncio.run() ou chame dentro de um contexto async.

        Args:
            message: Mensagem do usuário (opcional).

        Returns:
            Resposta gerada por Claude ou fallback para legacy.
        """
        # Se mensagem fornecida, adiciona ao histórico
        if message:
            self.receive(message)

        # Verificar se há mensagem para responder
        if not self._history:
            return ""

        # Obtém última mensagem do usuário
        user_message = self._history[-1] if self._history[-1].role == "user" else None
        if not user_message:
            # Busca última mensagem de usuário no histórico
            for msg in reversed(self._history):
                if msg.role == "user":
                    user_message = msg
                    break

        if not user_message:
            return ""

        # Tenta gerar resposta via Claude SDK
        try:
            # DOC: "adapter recupera memória relevante via RAG"
            memory_results = self._retrieve_memory(user_message.content)

            # DOC: "adapter constrói system prompt com personalidade + contexto de memória"
            system_prompt = build_system_prompt(
                format_memory_context([r["content"] for r in memory_results])
            )

            # DOC: "adapter chama Claude Agent SDK"
            response = await self._call_claude_sdk(
                user_message=user_message.content,
                system_prompt=system_prompt,
            )

            # DOC: "adapter armazena resposta no histórico"
            self._history.append(ChatMessage(role="sky", content=response))

            return response

        except Exception as e:
            # DOC: spec.md - Cenário: Falha do SDK com fallback para legacy
            logger.structured("Claude SDK falhou, usando fallback para legacy", {
                "error": str(e),
                "error_type": type(e).__name__,
                "user_message_length": len(user_message.content),
            }, level="warning")

            # Fallback para SkyChat legacy
            return self._fallback_to_legacy(user_message.content)

    def _process_learning(self, content: str) -> None:
        """
        Extrai aprendizados da mensagem do usuário.

        Args:
            content: Conteúdo da mensagem.
        """
        content_lower = content.lower()

        # Padrões de aprendizado (similar ao SkyChat)
        learning_patterns = [
            ("lembre", "lembrar"),
            ("aprenda", "aprender"),
            ("eu gosto", "gosto"),
            ("eu sou", "identidade"),
        ]

        for pattern, _category in learning_patterns:
            if pattern in content_lower:
                self._memory.learn(content)
                break

    def _retrieve_memory(self, query: str) -> List[dict]:
        """
        Recupera memórias relevantes via RAG.

        DOC: spec.md - Requirement: Integração de memória com contexto Claude

        Args:
            query: Query do usuário.

        Returns:
            Lista de memórias recuperadas.
        """
        # DOC: spec.md - Cenário: Memória recuperada e injetada
        # DOC: "sistema busca memória RAG com a query do usuário"
        # DOC: "top 5 memórias mais relevantes são recuperadas"
        return self._memory.search(query, top_k=TOP_K_MEMORIES)

    async def _call_claude_sdk(self, user_message: str, system_prompt: str) -> str:
        """
        Chama Claude Agent SDK para gerar resposta.

        Usa claude_agent_sdk (ja instalado no projeto) ao inves de anthropic direto.

        DOC: spec.md - Requirement: Integração com Claude Agent SDK

        Args:
            user_message: Mensagem do usuário.
            system_prompt: System prompt com personalidade + contexto.

        Returns:
            Resposta gerada por Claude.

        Raises:
            Exception: Se houver erro na chamada ao SDK.
        """
        from claude_agent_sdk import ClaudeSDKClient
        from claude_agent_sdk.types import ClaudeAgentOptions
        from runtime.config import get_agent_config

        agent_config = get_agent_config()
        model = get_claude_model()

        # DOC: 8.5 - Logs estruturados em JSON
        logger.structured("Claude SDK configurado", {
            "model": model,
            "has_auth_token": bool(agent_config.anthropic_auth_token),
            "base_url": agent_config.anthropic_base_url or "default",
            "system_prompt_length": len(system_prompt),
        }, level="debug")

        # Prepara environment variables
        env_vars = {}
        if agent_config.anthropic_auth_token:
            env_vars["ANTHROPIC_AUTH_TOKEN"] = agent_config.anthropic_auth_token
            # SDK também aceita ANTHROPIC_API_KEY como sinônimo
            env_vars["ANTHROPIC_API_KEY"] = agent_config.anthropic_auth_token
        if agent_config.anthropic_base_url:
            env_vars["ANTHROPIC_BASE_URL"] = agent_config.anthropic_base_url

        # Configura opções do SDK
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            permission_mode="acceptEdits",  # Mesmo modo usado no webhook
            allowed_tools=[],  # Chat não usa tools
            max_turns=1,  # Apenas uma resposta
            env=env_vars,
            setting_sources=[],  # Não ler configurações de arquivos, usar apenas env_vars
            cwd=str(Path.cwd()),  # Diretório de trabalho atual
        )

        start_time = time.time()

        async with ClaudeSDKClient(options=options) as client:
            # Envia a pergunta
            await client.query(user_message)

            # Consome a resposta
            response_text = ""
            async for msg in client.receive_response():
                if hasattr(msg, "content") and msg.content:
                    for block in msg.content:
                        if hasattr(block, "text"):
                            response_text += block.text
                # ResultMessage indica fim
                if msg.__class__.__name__ == "ResultMessage":
                    # Registra métricas
                    self._last_latency_ms = (time.time() - start_time) * 1000
                    self._last_tokens_in = getattr(msg, "input_tokens", 0)
                    self._last_tokens_out = getattr(msg, "output_tokens", 0)

                    # DOC: 8.5 - Logs estruturados em JSON
                    logger.structured("Resposta gerada com sucesso", {
                        "model": model,
                        "latency_ms": round(self._last_latency_ms, 2),
                        "tokens_in": self._last_tokens_in,
                        "tokens_out": self._last_tokens_out,
                        "response_length": len(response_text),
                    }, level="info")
                    break

            return response_text

    def _fallback_to_legacy(self, user_message: str) -> str:
        """
        Fallback para SkyChat legacy em caso de erro.

        DOC: spec.md - Cenário: Falha do SDK com fallback para legacy

        Args:
            user_message: Mensagem do usuário.

        Returns:
            Resposta do SkyChat legacy.
        """
        # Import lazy para evitar circular import
        from core.sky.chat import SkyChat

        legacy_chat = SkyChat()
        # Recria mensagem para o legacy (usando ChatMessage do módulo principal)
        from core.sky.chat import ChatMessage as MainChatMessage
        legacy_message = MainChatMessage(role="user", content=user_message)
        return legacy_chat.respond(legacy_message)

    def clear_history(self) -> None:
        """
        Limpa o histórico de mensagens.

        DOC: spec.md - Cenário: Comando /new limpa histórico
        """
        self._history.clear()

    def get_history(self) -> List[ChatMessage]:
        """
        Retorna o histórico de mensagens.

        Returns:
            Lista de mensagens no histórico.
        """
        return self._history.copy()

    def get_history_limitado(self) -> List[ChatMessage]:
        """
        Retorna o histórico limitado às últimas 20 mensagens.

        DOC: spec.md - Cenário: Histórico limitado às últimas N mensagens

        Returns:
            Lista de mensagens limitada a 20.
        """
        return self._history[-MAX_HISTORY_LENGTH:] if len(self._history) > MAX_HISTORY_LENGTH else self._history.copy()


__all__ = [
    "ClaudeChatAdapter",
    "MAX_HISTORY_LENGTH",
]
