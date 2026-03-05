# coding: utf-8
"""
Testes do widget ChatTextArea.

DOC: openspec/changes/sky-chat-textual-ui-fix/specs/chat-text-area/spec.md
"""

import pytest

from src.core.sky.chat.textual_ui.widgets.chat_text_area import ChatTextArea


class TestChatTextAreaInit:
    """Testa inicialização do ChatTextArea."""

    def test_init_cria_classe_submitted(self):
        """
        QUANDO ChatTextArea é criado
        ENTÃO possui inner class Submitted
        """
        # Assert
        assert hasattr(ChatTextArea, "Submitted")
        assert hasattr(ChatTextArea.Submitted, "__init__")

    def test_submitted_tem_atributo_value(self):
        """
        QUANDO Submitted é instanciada
        ENTÃO possui atributo value
        """
        # Arrange & Act
        msg = ChatTextArea.Submitted("teste")

        # Assert
        assert msg.value == "teste"


class TestChatTextAreaComportamento:
    """Testa comportamento de chat do ChatTextArea."""

    def test_init_com_placeholder(self):
        """
        QUANDO ChatTextArea é criado com placeholder
        ENTÃO armazena placeholder
        """
        # Arrange & Act
        textarea = ChatTextArea(placeholder="Digite aqui...")

        # Assert - TextArea suporta placeholder via propriedade
        assert textarea.placeholder == "Digite aqui..."

    def test_text_pode_ser_definido(self):
        """
        QUANDO text é definido
        ENTÃO valor é armazenado
        """
        # Arrange & Act
        textarea = ChatTextArea()
        textarea.text = "Olá mundo"

        # Assert
        assert textarea.text == "Olá mundo"

    def test_clear_limpa_texto(self):
        """
        QUANDO clear() é chamado
        ENTÃO text é limpo
        """
        # Arrange
        textarea = ChatTextArea()
        textarea.text = "Texto para limpar"

        # Act
        textarea.clear()

        # Assert
        assert textarea.text == ""


__all__ = [
    "TestChatTextAreaInit",
    "TestChatTextAreaComportamento",
]
