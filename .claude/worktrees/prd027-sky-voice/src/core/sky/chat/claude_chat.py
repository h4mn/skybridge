# coding: utf-8
"""
ClaudeChatAdapter - Chat com Claude Agent SDK.

DOC: openspec/changes/chat-claude-sdk/specs/claude-chat-integration/spec.md
"""

import asyncio
import os
import time
from pathlib import Path
from typing import List, Optional, AsyncIterator, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

from core.sky.chat.personality import build_system_prompt, format_memory_context
from core.sky.chat.session_history import SessionHistory
from core.sky.memory import get_memory, PersistentMemory


# =============================================================================
# Tipos para Stream com Thinking (PRD019 Fase 2)
# =============================================================================

class StreamEventType(Enum):
    """Tipo de evento do stream."""
    TEXT = auto()           # Chunk de texto normal
    THOUGHT = auto()        # Pensamento da IA
    TOOL_START = auto()     # Início de uso de ferramenta
    TOOL_RESULT = auto()    # Resultado de ferramenta
    ERROR = auto()          # Erro durante processamento


@dataclass
class StreamEvent:
    """
    Evento do stream que pode ser texto ou metadado de thinking.

    Usado para passar tanto chunks de texto quanto entradas de raciocínio
    para a UI Textual.
    """
    type: StreamEventType
    content: str
    metadata: dict | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


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

    #: Sentinela para indicar "sem memória" — distinto de None acidental
    _SEM_MEMORIA = object()

    def __init__(self, memory: Optional[PersistentMemory] = None, _isolated: bool = False):
        """
        Inicializa o adapter.

        Args:
            memory: Instância de PersistentMemory. Se None, usa get_memory().
            _isolated: Se True, não usa nenhuma memória (para workers temporários).
        """
        # DOC: spec.md - Cenário: Adapter recebe mensagem do usuário
        if _isolated:
            self._memory = None  # type: ignore  # sem memory — workers isolados
        else:
            self._memory = memory if memory is not None else get_memory()
        self._history: List[ChatMessage] = []

        # Sessão única para manter contexto da conversa
        self._session_id = f"sky_chat_{id(self)}"

        # Métricas da última resposta
        self._last_tokens_in: int = 0
        self._last_tokens_out: int = 0
        self._last_latency_ms: float = 0.0

        # Cliente SDK persistente (lazy initialization)
        self._sdk_client = None  # type: ignore | ClaudeSDKClient

        # Histórico de sessão para debug
        self._history_collector = SessionHistory(
            session_id=self._session_id,
            model=get_claude_model(),
        )

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

        # Registra no histórico de debug
        self._history_collector.add_message(message.role, message.content)

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

        # FAST PATH: Respostas simples sem IA (saudações, etc)
        fast_response = self._fast_path_response(user_message.content)
        if fast_response:
            self._history.append(ChatMessage(role="sky", content=fast_response))
            return fast_response

        # Tenta gerar resposta via Claude SDK
        try:
            # DOC: "adapter recupera memória relevante via RAG"
            memory_results = self._retrieve_memory(user_message.content)

            # DOC: "adapter constrói system prompt com personalidade + contexto de memória"
            system_prompt = build_system_prompt(
                format_memory_context([r["content"] for r in memory_results])
            )

            # Constrói contexto da conversa (histórico como contexto)
            conversation_context = self._format_conversation_context()

            # DOC: "adapter chama Claude Agent SDK"
            response = await self._call_claude_sdk(
                user_message=user_message.content,
                system_prompt=system_prompt,
                conversation_context=conversation_context,
            )

            # DOC: "adapter armazena resposta no histórico"
            self._history.append(ChatMessage(role="sky", content=response))

            # Registra resposta no histórico de debug
            self._history_collector.add_message("sky", response)
            self._history_collector.increment_turns()

            return response

        except Exception as e:
            # DOC: spec.md - Cenário: Falha do SDK com fallback para legacy
# logger.structured("Claude SDK falhou, usando fallback para legacy", {
#     "error": str(e),
#     "error_type": type(e).__name__,
#     "user_message_length": len(user_message.content),
# }, level="warning")

            # Fallback para SkyChat legacy
            return self._fallback_to_legacy(user_message.content)

    async def stream_response(
        self,
        message: Optional[ChatMessage] = None,
    ) -> AsyncIterator[StreamEvent]:
        """
        Streaming de resposta usando Claude Agent SDK.

        Similar a respond() mas retorna AsyncIterator de StreamEvent
        para atualização incremental da UI (PRD019 Fase 1 + Fase 2).

        Args:
            message: Mensagem do usuário (opcional).

        Yields:
            StreamEvent com texto ou metadados de thinking.
        """
        # Se mensagem fornecida, adiciona ao histórico
        if message:
            self.receive(message)

        # Verificar se há mensagem para responder
        if not self._history:
            return

        # Obtém última mensagem do usuário
        user_message = self._history[-1] if self._history[-1].role == "user" else None
        if not user_message:
            # Busca última mensagem de usuário no histórico
            for msg in reversed(self._history):
                if msg.role == "user":
                    user_message = msg
                    break

        if not user_message:
            return

        # FAST PATH: Respostas simples sem IA (saudações, etc)
        fast_response = self._fast_path_response(user_message.content)
        if fast_response:
            self._history.append(ChatMessage(role="sky", content=fast_response))
            yield StreamEvent(type=StreamEventType.TEXT, content=fast_response)
            return

        # Tenta gerar resposta via streaming Claude SDK
        try:
            # Recupera memória relevante via RAG
            memory_results = self._retrieve_memory(user_message.content)

            # Constrói system prompt com personalidade + contexto de memória
            system_prompt = build_system_prompt(
                format_memory_context([r["content"] for r in memory_results])
            )

            # Constrói contexto da conversa (histórico como contexto)
            conversation_context = self._format_conversation_context()

            # Coleta texto para histórico
            response_text = ""

            # Streaming via Claude SDK
            async for event in self._stream_claude_sdk(
                user_message=user_message.content,
                system_prompt=system_prompt,
                conversation_context=conversation_context,
            ):
                # Coleta apenas texto para o histórico
                if event.type == StreamEventType.TEXT:
                    response_text += event.content

                # Yield todos os eventos para a UI
                yield event

            # Armazena resposta completa no histórico
            self._history.append(ChatMessage(role="sky", content=response_text))

            # Registra resposta no histórico de debug
            self._history_collector.add_message("sky", response_text)
            self._history_collector.increment_turns()

        except Exception as e:
# logger.structured("Claude SDK streaming falhou", {
#     "error": str(e),
#     "error_type": type(e).__name__,
# }, level="warning")
            # Fallback: yield resposta completa de uma vez
            try:
                response = self._fallback_to_legacy(user_message.content)
                yield StreamEvent(type=StreamEventType.TEXT, content=response)
            except Exception as fallback_error:
                # Se até o fallback falhar, yield mensagem genérica
# logger.structured("Fallback também falhou", {
#     "original_error": str(e),
#     "fallback_error": str(fallback_error),
# }, level="error")
                yield StreamEvent(
                    type=StreamEventType.ERROR,
                    content=f"[Erro ao gerar resposta: {type(e).__name__}]"
                )

    def _format_conversation_context(self) -> str:
        """
        Formata o histórico da conversa como contexto para o Claude.

        Returns:
            String com o histórico formatado.
        """
        if not self._history:
            return ""

        # Formata as últimas MAX_HISTORY_LENGTH mensagens
        recent_history = self._history[-MAX_HISTORY_LENGTH:]
        context_parts = []
        for msg in recent_history:
            if msg.role == "user":
                context_parts.append(f"Você: {msg.content}")
            else:
                context_parts.append(f"Sky: {msg.content}")

        return "\n\n".join(context_parts)

    def _fast_path_response(self, content: str) -> str | None:
        """
        Respostas instantâneas sem chamar IA.

        Para saudações e mensagens simples, retorna resposta imediata.
        Evita chamadas custosas à API para casos triviais.

        Args:
            content: Conteúdo da mensagem do usuário.

        Returns:
            Resposta ou None se deve usar IA.
        """
        content_lower = content.strip().lower()

        # Saudações simples
        greetings = {
            "oi": "Olá! 😊 Como posso ajudar?",
            "olá": "Olá! 👋 Tudo bem?",
            "ola": "Olá! 👋 Tudo bem?",
            "hey": "Hey! 😊 O que precisa?",
            "hi": "Oi! Como posso ajudar?",
        }

        # Verifica saudação exata
        if content_lower in greetings:
            return greetings[content_lower]

        # Saudações com nome
        if content_lower in ["oi sky", "olá sky", "ola sky", "hey sky"]:
            return "Olá! 👋 Sou a Sky, sua assistente. Como posso ajudar hoje?"

        # Perguntas sobre identidade (resposta rápida)
        if any(kw in content_lower for kw in ["quem é você", "quem e voce", "o que é sky"]):
            return "Sou a Sky, sua assistente de IA criada para ajudar! 🚀"

        # Perguntas sobre como estou
        if any(kw in content_lower for kw in ["tudo bem", "como vc está", "como voce está", "como você está"]):
            return "Tudo ótimo! 💚 Pronta para ajudar!"

        return None

    def _process_learning(self, content: str) -> None:
        """
        Extrai aprendizados da mensagem do usuário.

        Args:
            content: Conteúdo da mensagem.
        """
        if self._memory is None:
            return  # modo isolado — sem gravação em memória

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
        if self._memory is None:
            return []  # modo isolado — sem acesso ao RAG

        # DOC: spec.md - Cenário: Memória recuperada e injetada
        return self._memory.search(query, top_k=TOP_K_MEMORIES)

    async def _ensure_client(self) -> None:
        """
        Garante que o cliente SDK está inicializado (lazy initialization).

        Cria o cliente na primeira chamada e o mantém para reutilização
        em mensagens subsequentes da mesma sessão.

        Raises:
            Exception: Se houver erro ao inicializar o cliente SDK.
        """
        if self._sdk_client is None:
            from claude_agent_sdk import ClaudeSDKClient
            from claude_agent_sdk.types import ClaudeAgentOptions
            from runtime.config import get_agent_config

            agent_config = get_agent_config()

            # Prepara environment variables
            env_vars = {}
            if agent_config.anthropic_auth_token:
                env_vars["ANTHROPIC_AUTH_TOKEN"] = agent_config.anthropic_auth_token
                env_vars["ANTHROPIC_API_KEY"] = agent_config.anthropic_auth_token
            if agent_config.anthropic_base_url:
                env_vars["ANTHROPIC_BASE_URL"] = agent_config.anthropic_base_url

            # Configura opções do SDK
            options = ClaudeAgentOptions(
                system_prompt="",  # Será definido por mensagem
                permission_mode="acceptEdits",
                allowed_tools=["Read", "Glob", "Grep"],  # Ferramentas de leitura habilitadas
                max_turns=None,  # Multi-turno sem limite
                env=env_vars,
                setting_sources=[],
                cwd=str(Path.cwd()),
            )

            try:
                self._sdk_client = ClaudeSDKClient(options=options)
                await self._sdk_client.__aenter__()
# logger.structured("Cliente SDK inicializado", {
#     "session_id": self._session_id,
# }, level="debug")
            except Exception:
                self._sdk_client = None  # Reset para tentar novamente
                raise

    async def _call_claude_sdk(self, user_message: str, system_prompt: str, conversation_context: str = "") -> str:
        """
        Chama Claude Agent SDK para gerar resposta.

        Usa cliente SDK persistente (reutilizado entre mensagens).

        DOC: spec.md - Requirement: Integração com Claude Agent SDK

        Args:
            user_message: Mensagem do usuário.
            system_prompt: System prompt com personalidade + contexto.
            conversation_context: Histórico da conversa atual.

        Returns:
            Resposta gerada por Claude.

        Raises:
            Exception: Se houver erro na chamada ao SDK.
        """
        # Garante que o cliente está inicializado
        await self._ensure_client()

        model = get_claude_model()
        start_time = time.time()

        # Atualiza system prompt do cliente (pode mudar por mensagem)
        # NOTA: SDK pode não suportar mudança de system prompt após inicialização
        # Nesse caso, passamos no prompt da mensagem

        # Constrói prompt completo com contexto da conversa
        full_prompt = user_message
        if conversation_context:
            full_prompt = f"""Aqui está o histórico da nossa conversa até agora:

{conversation_context}

---

Agora responda à seguinte mensagem: {user_message}"""

        # Se o SDK suportar, atualizamos o system prompt
        # Caso contrário, incluímos no prompt da mensagem
        if system_prompt:
            full_prompt = f"""{system_prompt}

{full_prompt}"""

        # Envia a pergunta com contexto (reutilizando cliente existente)
        await self._sdk_client.query(full_prompt)

        # Consome a resposta
        response_text = ""
        async for msg in self._sdk_client.receive_response():
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

# logger.structured("Resposta gerada com sucesso", {
#     "model": model,
#     "latency_ms": round(self._last_latency_ms, 2),
#     "tokens_in": self._last_tokens_in,
#     "tokens_out": self._last_tokens_out,
#     "response_length": len(response_text),
# }, level="info")
                break

        return response_text

    async def _stream_claude_sdk(
        self,
        user_message: str,
        system_prompt: str,
        conversation_context: str = "",
    ) -> AsyncIterator[StreamEvent]:
        """
        Streaming de resposta via Claude Agent SDK.

        Similar a _call_claude_sdk() mas usa include_partial_messages=True
        para yield de chunks incrementalmente (PRD019 Fase 1 + Fase 2).

        Args:
            user_message: Mensagem do usuário.
            system_prompt: System prompt com personalidade + contexto.
            conversation_context: Histórico da conversa atual.

        Yields:
            StreamEvent com texto ou metadados de thinking.
        """
        from claude_agent_sdk import query
        from claude_agent_sdk.types import ClaudeAgentOptions
        from runtime.config import get_agent_config

        agent_config = get_agent_config()

        # Prepara environment variables
        env_vars = {}
        if agent_config.anthropic_auth_token:
            env_vars["ANTHROPIC_AUTH_TOKEN"] = agent_config.anthropic_auth_token
            env_vars["ANTHROPIC_API_KEY"] = agent_config.anthropic_auth_token
        if agent_config.anthropic_base_url:
            env_vars["ANTHROPIC_BASE_URL"] = agent_config.anthropic_base_url

        # Configura opções do SDK com streaming habilitado
        options = ClaudeAgentOptions(
            include_partial_messages=True,  # ← CHAVE para streaming
            allowed_tools=["Read", "Grep", "Glob", "Bash", "Edit", "Write"],
            permission_mode="acceptEdits",
            env=env_vars,
            cwd=str(Path.cwd()),
        )

        # Constrói prompt completo com contexto da conversa
        full_prompt = user_message
        if conversation_context:
            full_prompt = f"""Aqui está o histórico da nossa conversa até agora:

{conversation_context}

---

Agora responda à seguinte mensagem: {user_message}"""

        # Se o SDK suportar, atualizamos o system prompt
        # Caso contrário, incluímos no prompt da mensagem
        if system_prompt:
            full_prompt = f"""{system_prompt}

{full_prompt}"""

        start_time = time.time()
        message_count = 0
        received_streaming_chunks = False

        # PRD-REACT-001: Event Router com buffer + lookahead
        # A ordem dos eventos é: text_block → text_delta → text_block_stop → tool_use_block_start
        # Precisamos armazenar o texto quando text_block_stop chega e emitir no próximo block_start
        pending_thought: str = ""  # Acumula texto durante text_delta
        last_text_block_content: str = ""  # Texto completo do último text_block_stop
        last_block_index: int = -1  # Index do último block processado
        last_tool_result_received = False  # Flag para heurística de fallback

        # Rastreamenta ferramentas em uso
        pending_tool: dict | None = None
        last_tool_command: str = ""  # Armazena comando do TOOL_START para usar no TOOL_RESULT

# logger.structured("Iniciando streaming SDK", {
#     "prompt_length": len(full_prompt),
# }, level="debug")

        # Cria o query generator SDK
        query_gen = query(prompt=full_prompt, options=options)

        # Caminho absoluto do log de diagnóstico
        import pathlib as _pl
        _SKY_LOG = _pl.Path("B:/sky_debug.log")

        try:
            # Yield eventos conforme chegam (evita cancel scope issue)
            async for message in query_gen:
                message_count += 1
                message_type = type(message).__name__

                # DIAGNÓSTICO COMPLETO: loga tudo sem filtro
                try:
                    import datetime as _dt
                    if message_type == "StreamEvent":
                        _ev = getattr(message, "event", {})
                        _line = f"{_dt.datetime.now().isoformat()} StreamEvent type={_ev.get('type','?')!r} keys={list(_ev.keys())}\n"
                    else:
                        _attrs = {a: repr(getattr(message, a, '?'))[:100]
                                  for a in dir(message) if not a.startswith('_')}
                        _line = f"{_dt.datetime.now().isoformat()} {message_type} {_attrs}\n"
                    _SKY_LOG.open("a", encoding="utf-8").write(_line)
                except Exception:
                    pass

                # StreamEvent contém eventos de streaming (text_delta, etc)
                if message_type == "StreamEvent":
                    event = message.event  # type: ignore
                    event_type = event.get("type", "")

                    # content_block_start - início de um content block
                    if event_type == "content_block_start":
                        index = event.get("index", -1)
                        content_block = event.get("content_block", {})
                        block_type = content_block.get("type", "")

                        # PRD-REACT-001: Lookahead - se há texto acumulado do bloco anterior
                        if last_text_block_content:
                            if block_type == "tool_use":
                                # Texto seguido de tool = THOUGHT (com ou sem 🔧)
                                yield StreamEvent(
                                    type=StreamEventType.THOUGHT,
                                    content=last_text_block_content,
                                )
                            elif block_type == "text":
                                # Texto seguido de texto = Final Answer
                                yield StreamEvent(
                                    type=StreamEventType.TEXT,
                                    content=last_text_block_content,
                                )
                            # Limpa o buffer após emitir
                            last_text_block_content = ""
                            received_streaming_chunks = True

                        # PRD-REACT-001: Se for tool use SEM thought anterior, usa padrão
                        if block_type == "tool_use":
                            tool_name = content_block.get("name", "unknown")
                            pending_tool = {
                                "name": tool_name,
                                "index": index,
                                "input": {},  # Será preenchido nos content_block_delta
                            }
# logger.structured("Tool use detectado", {
#     "tool": tool_name,
#     "index": index,
# }, level="debug")

                        last_block_index = index

                    # content_block_delta contém chunks de texto ou tool input
                    elif event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        delta_type = delta.get("type", "")

                        if delta_type == "text_delta":
                            # PRD-REACT-001: Acumula em pending_thought em vez de yield imediato
                            text = delta.get("text", "")
                            if text:
                                # Heurística: após ToolResult, texto é Final Answer
                                if last_tool_result_received:
                                    yield StreamEvent(
                                        type=StreamEventType.TEXT,
                                        content=text
                                    )
                                else:
                                    # Antes de tool, acumula como Thought
                                    pending_thought += text
                                received_streaming_chunks = True

                        elif delta_type == "input_json_delta":
                            # Input JSON para tool use - acumula
                            if pending_tool:
                                partial_input = delta.get("partial_json", "")
                                if not pending_tool.get("input"):
                                    pending_tool["input"] = ""
                                pending_tool["input"] += partial_input

                    # content_block_stop - fim de um content block
                    elif event_type == "content_block_stop":
                        index = event.get("index", -1)

                        # PRD-REACT-001: Se era um text block e há pending_thought,
                        # armazena para lookahead (será emitido no próximo content_block_start)
                        if pending_thought and index == last_block_index:
                            last_text_block_content = pending_thought
                            pending_thought = ""  # Limpa após armazenar

                        # Se era uma tool use, yield evento de tool_start
                        if pending_tool and pending_tool.get("index") == index:
                            tool_name = pending_tool["name"]
                            tool_input_str = pending_tool.get("input", "{}")

                            # Tenta extrair parâmetro principal do JSON de input
                            import json
                            tool_input_json = {}
                            try:
                                tool_input_json = json.loads(tool_input_str) if tool_input_str else {}
                                param = (
                                    tool_input_json.get("file_path")
                                    or tool_input_json.get("pattern")
                                    or tool_input_json.get("command")
                                    or tool_input_json.get("query")
                                    or tool_input_json.get("path")
                                )
                                if param:
                                    display_content = f"{tool_name}: {param}"
                                else:
                                    display_content = f"Usando {tool_name}"
                            except Exception:
                                display_content = f"Usando {tool_name}"

                            yield StreamEvent(
                                type=StreamEventType.TOOL_START,
                                content=display_content,
                                metadata={
                                    "tool": tool_name,
                                    "input": tool_input_str,
                                }
                            )
                            # Armazena comando para usar no TOOL_RESULT (especialmente Bash)
                            last_tool_command = tool_input_json.get("command", "") if tool_name == "Bash" else ""
                            pending_tool = None

                # AssistantMessage contém texto completo (fallback)
                elif message_type == "AssistantMessage" and not received_streaming_chunks:
                    if hasattr(message, "content") and message.content:
                        for block in message.content:
                            if hasattr(block, "text"):
                                yield StreamEvent(
                                    type=StreamEventType.TEXT,
                                    content=block.text
                                )

                # ToolUseMessage - ferramenta sendo usada
                elif message_type == "ToolUseMessage":
                    if hasattr(message, "name"):
                        tool_name = message.name  # type: ignore
                        tool_input = getattr(message, "input", {})
                        yield StreamEvent(
                            type=StreamEventType.TOOL_START,
                            content=f"Usando {tool_name}...",
                            metadata={
                                "tool": tool_name,
                                "input": str(tool_input),
                            }
                        )
                        # Armazena comando para usar no TOOL_RESULT (caminho alternativo)
                        if tool_name == "Bash" and isinstance(tool_input, dict):
                            last_tool_command = tool_input.get("command", "")
                        else:
                            last_tool_command = ""

                # ToolResultMessage - resultado da ferramenta
                elif message_type == "ToolResultMessage":
                    # PRD-REACT-001: Marca que recebeu ToolResult para heurística de fallback
                    last_tool_result_received = True

                    # Log de diagnóstico em arquivo (Windows-compatível)
                    try:
                        import pathlib, datetime as _dt
                        _log_path = pathlib.Path(os.environ.get("TEMP", ".")) / "sky_tool_result.log"
                        _attrs = {a: repr(getattr(message, a, "<ERR>"))[:200]
                                  for a in dir(message) if not a.startswith("_")}
                        _dump = (
                            f"\n{'='*60}\n"
                            f"{_dt.datetime.now().isoformat()}\n"
                            f"type={message_type}\n"
                            + "\n".join(f"  {k}: {v}" for k, v in _attrs.items())
                            + "\n"
                        )
                        _log_path.open("a", encoding="utf-8").write(_dump)
                    except Exception:
                        pass

                    # Tenta extrair conteúdo de qualquer atributo possível
                    # (SDK pode usar 'content', 'output', 'result', 'text'...)
                    raw = (
                        getattr(message, "content", None)
                        or getattr(message, "output",  None)
                        or getattr(message, "result",  None)
                        or getattr(message, "text",    None)
                    )

                    if raw is not None:
                        # Extrai texto real independente do formato
                        # SDK pode retornar: str, list[TextBlock], list[dict], etc.
                        if isinstance(raw, str):
                            result_content = raw
                        elif isinstance(raw, list):
                            # Lista de blocos: [{"type": "text", "text": "..."}, ...]
                            # ou [TextBlock(text="..."), ...]
                            parts = []
                            for block in raw:
                                if isinstance(block, str):
                                    parts.append(block)
                                elif isinstance(block, dict):
                                    parts.append(block.get("text", ""))
                                elif hasattr(block, "text"):
                                    parts.append(block.text)
                                else:
                                    parts.append(str(block))
                            result_content = "\n".join(p for p in parts if p)
                        else:
                            result_content = str(raw)
                        tool_name = getattr(message, "name", "tool")

                        # Detecta exit code do Bash no conteúdo
                        # O SDK injeta "Exit code: N" no final do output
                        exit_code: int | None = None
                        output_lines = result_content.strip().splitlines()
                        for ln in reversed(output_lines[-3:]):
                            ln_s = ln.strip().lower()
                            if ln_s.startswith("exit code:"):
                                try:
                                    exit_code = int(ln_s.split(":", 1)[1].strip())
                                except ValueError:
                                    pass
                                break

                        # Resumo compacto para a ActionLine
                        n_lines = len(output_lines)
                        if exit_code is not None:
                            status = "✓" if exit_code == 0 else "✗"
                            result_summary = f"{status} exit {exit_code} · {n_lines} linhas"
                        elif n_lines > 1:
                            result_summary = f"{n_lines} linhas"
                        elif output_lines:
                            result_summary = output_lines[0][:60]
                        else:
                            result_summary = "ok"

                        yield StreamEvent(
                            type=StreamEventType.TOOL_RESULT,
                            content=result_summary,
                            metadata={
                                "tool": tool_name,
                                "result": result_content,  # output COMPLETO — sem truncar
                                "exit_code": exit_code,
                                "command": last_tool_command,  # Comando executado (especialmente Bash)
                            }
                        )

                # ResultMessage indica fim do stream
                elif message_type == "ResultMessage":
                    # PRD-REACT-001: Se ainda tem conteúdo pendente, emite como Final Answer
                    # Prioridade: pending_thought → last_text_block_content
                    remaining_content = pending_thought or last_text_block_content
                    if remaining_content:
                        yield StreamEvent(
                            type=StreamEventType.TEXT,
                            content=remaining_content
                        )
                        pending_thought = ""
                        last_text_block_content = ""

                    # Registra métricas
                    self._last_latency_ms = (time.time() - start_time) * 1000
                    self._last_tokens_in = getattr(message, "input_tokens", 0)
                    self._last_tokens_out = getattr(message, "output_tokens", 0)

# logger.structured("Streaming completado", {
#     "model": get_claude_model(),
#     "latency_ms": round(self._last_latency_ms, 2),
#     "tokens_in": self._last_tokens_in,
#     "tokens_out": self._last_tokens_out,
#     "messages_processed": message_count,
# }, level="info")
                    break

        except asyncio.CancelledError:
            # PRD-REACT-001: Cancelamento pelo usuário (Ctrl+C)
# logger.structured("Streaming cancelado pelo usuário", {
#     "messages_processed": message_count,
# }, level="info")
            # Silenciosamente propaga CancelledError para limpeza graciosa
            raise
        except Exception as e:
# logger.structured("Erro no streaming SDK", {
#     "error": str(e),
#     "error_type": type(e).__name__,
#     "messages_processed": message_count,
# }, level="warning")
            raise
        finally:
            # PRD-REACT-001: Garante limpeza do generator SDK
            # Isso evita "Event loop is closed" quando subprocessos tentam limpar
            if hasattr(query_gen, 'aclose'):
                try:
                    await query_gen.aclose()
                except Exception:
                    # Ignora erros na limpeza do generator
                    pass

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

    async def close(self) -> None:
        """
        Encerra a sessão do cliente SDK e libera recursos.

        Este método é idempotente - pode ser chamado múltiplas vezes sem erro.
        Após close(), uma nova mensagem criará um novo cliente SDK.

        Salva o histórico de sessão para debug antes de encerrar.

        DOC: spec.md - Requirement: Gerenciamento de ciclo de vida da sessão
        """
        # Salva histórico de debug antes de encerrar
        try:
            await self._history_collector.save()
        except Exception as e:
            # logger.structured("Erro ao salvar histórico de debug", {
            #     "error": str(e),
            #     "session_id": self._session_id,
            # }, level="warning")
            pass  # Silencioso - erro ao salvar histórico não quebra a aplicação

        # Encerra cliente SDK
        if self._sdk_client is not None:
            try:
                await self._sdk_client.__aexit__(None, None, None)
                # logger.structured("Cliente SDK encerrado", {
                #     "session_id": self._session_id,
                # }, level="debug")
            except Exception as e:
                # logger.structured("Erro ao encerrar cliente SDK", {
                #     "error": str(e),
                #     "session_id": self._session_id,
                # }, level="warning")
                pass  # Silencioso - erro ao encerrar cliente SDK não quebra a aplicação
            finally:
                self._sdk_client = None


__all__ = [
    "ClaudeChatAdapter",
    "MAX_HISTORY_LENGTH",
    "ChatMessage",
    "StreamEvent",
    "StreamEventType",
]
