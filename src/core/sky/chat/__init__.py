# coding: utf-8
"""
Sistema de chat com a Sky.

Sky conversa com você, aprende com o que você diz,
e demonstra que está construindo memória.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from core.sky.identity import get_sky

# Personality module exports
from core.sky.chat.personality import (
    SYSTEM_PROMPT_TEMPLATE,
    build_system_prompt,
    format_memory_context,
)

# ClaudeChatAdapter exports
from core.sky.chat.claude_chat import (
    ClaudeChatAdapter,
    MAX_HISTORY_LENGTH,
)

# UI exports
from core.sky.chat.ui import (
    ChatUI,
    ChatMetrics,
)


@dataclass
class ChatMessage:
    """Uma mensagem na conversa."""
    role: str  # "user" ou "sky"
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SkyChat:
    """
    Chat com a Sky.

    Sky ouve, aprende, e responde.
    """

    def __init__(self):
        self._sky = get_sky()
        self.history: List[ChatMessage] = []

    def receive(self, message: ChatMessage) -> None:
        """
        Recebe uma mensagem do usuário.

        Args:
            message: Mensagem recebida.
        """
        self.history.append(message)
        self._process_learning(message.content)

    def respond(self, message: ChatMessage | None = None) -> str:
        """
        Responde a uma mensagem.

        Args:
            message: Mensagem do usuário (opcional).

        Returns:
            Resposta da Sky.
        """
        if message:
            self.receive(message)

        # Analisa a mensagem e decide como responder
        response = self._generate_response(message.content if message else "")

        # Registra a resposta da Sky
        self.history.append(ChatMessage(role="sky", content=response))

        return response

    def _process_learning(self, content: str) -> None:
        """
        Extrai aprendizados da mensagem do usuário.

        Args:
            content: Conteúdo da mensagem.
        """
        content_lower = content.lower()

        # Padrões de aprendizado
        learning_patterns = [
            ("lembre", "lembrar"),
            ("aprenda", "aprender"),
            ("eu gosto", "gosto"),
            ("eu sou", "identidade"),
        ]

        for pattern, category in learning_patterns:
            if pattern in content_lower:
                # Sky aprende o conteúdo
                self._sky.learn(content)
                break

    def _generate_response(self, user_message: str) -> str:
        """
        Gera uma resposta baseada na mensagem do usuário.

        Com RAG: usa busca semântica para encontrar respostas relevantes.
        Sem RAG: usa padrões fixos (legacy).

        Args:
            user_message: Mensagem do usuário.

        Returns:
            Resposta gerada.
        """
        user_message_lower = user_message.lower()

        # Perguntas sobre identidade - usa busca semântica se disponível
        if "quem é você" in user_message_lower or "quem e voce" in user_message_lower:
            # Tenta usar busca semântica primeiro
            if self._sky._memory.is_rag_enabled():
                return self._sky.describe_semantic()
            return self._sky.describe()

        # Perguntas sobre ensinamentos - busca semântica
        if any(kw in user_message_lower for kw in ["papai ensinou", "ensinamento", "lição do papai"]):
            teachings = self._sky.search_memory("o que papai ensinou", top_k=3)
            if teachings:
                return f"Papai me ensinou:\n" + "\n".join(f"• {t}" for t in teachings)
            return "Papai ainda não me ensinou nada que eu lembre."

        # Perguntas sobre memórias compartilhadas
        if any(kw in user_message_lower for kw in ["lembra", "momento", "vez que"]):
            memories = self._sky.search_memory(user_message, top_k=3)
            if memories:
                return f"Lembro disso:\n" + "\n".join(f"• {m}" for m in memories)
            return "Não me lembro de nada assim."

        # Perguntas sobre o que sabe
        if "o que você sabe" in user_message_lower or "o que sabe" in user_message_lower:
            knowledge = self._sky.get_self_knowledge()
            return f"Sei que: {', '.join(knowledge)}"

        # Perguntas sobre aprendizados de hoje
        if "hoje" in user_message_lower and ("aprendeu" in user_message_lower or "aprendiz" in user_message_lower):
            learnings = self._sky.get_today_learnings()
            if learnings:
                return f"Hoje aprendi: {', '.join(learnings)}"
            return "Hoje ainda não aprendi nada novo."

        # Saudações
        if user_message_lower in ["oi", "olá", "ola", "hey"]:
            return f"Oi! Sou {self._sky.get_name()}. Estou aprendendo com você."

        # Busca semântica genérica para outras perguntas
        if self._sky._memory.is_rag_enabled():
            results = self._sky.search_memory(user_message, top_k=3)
            if results:
                return f"Encontrei isso na memória:\n" + "\n".join(f"• {r}" for r in results)

        # Resposta padrão
        return self._sky.describe()
