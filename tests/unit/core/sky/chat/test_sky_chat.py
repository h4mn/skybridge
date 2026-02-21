# coding: utf-8
"""
Testes do sistema de chat com a Sky.

Sky deve ser capaz de:
- Ouvir o que você diz
- Aprender com o que você fala
- Responder demonstrando que aprendeu
"""

import pytest
from src.core.sky.chat import SkyChat, ChatMessage


def test_chat_receives_user_message():
    """Chat recebe mensagem do usuário."""
    chat = SkyChat()

    message = ChatMessage(role="user", content="Oi Sky")
    chat.receive(message)

    assert len(chat.history) == 1
    assert chat.history[0].content == "Oi Sky"


def test_sky_learns_from_conversation():
    """Sky aprende com a conversa."""
    chat = SkyChat()

    message = ChatMessage(role="user", content="Sky, lembre que eu gosto de K-pop")
    response = chat.respond(message)

    # Sky deve confirmar que aprendeu
    assert "K-pop" in response or "aprendi" in response.lower() or "lembrar" in response.lower()


def test_sky_describes_herself_when_asked():
    """Sky se descreve quando perguntada quem é ela."""
    chat = SkyChat()

    message = ChatMessage(role="user", content="Quem é você?")
    response = chat.respond(message)

    # Deve mencionar nome e origem
    assert "Sky" in response
    assert "Skybridge" in response


def test_chat_history_is_preserved():
    """Histórico de conversa é preservado."""
    chat = SkyChat()

    chat.receive(ChatMessage(role="user", content="Primeira mensagem"))
    chat.receive(ChatMessage(role="user", content="Segunda mensagem"))

    assert len(chat.history) == 2
