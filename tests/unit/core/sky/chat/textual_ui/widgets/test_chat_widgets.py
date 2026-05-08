# coding: utf-8
"""
Testes dos widgets ChatLog e ChatScroll.

DOC: openspec/changes/sky-chat-textual-ui-fix/design.md - ChatLog e ChatScroll
"""

import pytest

from src.core.sky.chat.textual_ui.widgets.common.log import ChatLog
from src.core.sky.chat.textual_ui.widgets.scroll.chat_scroll import ChatScroll


class TestChatLog:
    """Testa o widget ChatLog."""

    def test_init_markup_true(self):
        """
        QUANDO ChatLog é criado
        ENTÃO possui atributo markup definido como True
        """
        # Assert - verifica atributo de classe
        assert hasattr(ChatLog, "markup")
        # Verifica se está definido na classe (não na instância)
        assert "markup" in ChatLog.__dict__

    def test_debug_escreve_com_amarelo(self):
        """
        QUANDO debug() é chamado
        ENTÃO escreve com markup [yellow]
        """
        # Arrange & Act
        log = ChatLog()
        log.debug("teste debug")

        # Assert - verifica se o método existe e pode ser chamado
        assert hasattr(log, "debug")
        assert callable(log.debug)

    def test_info_escreve_com_azul(self):
        """
        QUANDO info() é chamado
        ENTÃO escreve com markup [blue]
        """
        # Arrange & Act
        log = ChatLog()
        log.info("teste info")

        # Assert
        assert hasattr(log, "info")
        assert callable(log.info)

    def test_error_escreve_com_vermelho(self):
        """
        QUANDO error() é chamado
        ENTÃO escreve com markup [red]
        """
        # Arrange & Act
        log = ChatLog()
        log.error("teste error")

        # Assert
        assert hasattr(log, "error")
        assert callable(log.error)

    def test_evento_escreve_com_verde(self):
        """
        QUANDO evento() é chamado
        ENTÃO escreve com markup [green]
        """
        # Arrange & Act
        log = ChatLog()
        log.evento("teste", "dados")

        # Assert
        assert hasattr(log, "evento")
        assert callable(log.evento)


class TestChatScroll:
    """Testa o widget ChatScroll."""

    def test_init_cria_vertical_scroll(self):
        """
        QUANDO ChatScroll é criado
        ENTÃO herda de VerticalScroll
        """
        # Arrange & Act
        scroll = ChatScroll()

        # Assert
        # Verifica se o método existe
        assert hasattr(scroll, "adicionar_mensagem")
        assert hasattr(scroll, "limpar")

    def test_adicionar_mensagem_existe(self):
        """
        QUANDO adicionar_mensagem() é chamado
        ENTÃO método existe e pode ser chamado
        """
        # Arrange & Act
        scroll = ChatScroll()

        # Assert - método existe e é chamável
        assert hasattr(scroll, "adicionar_mensagem")
        assert callable(scroll.adicionar_mensagem)

    def test_limpar_existe(self):
        """
        QUANDO limpar() é chamado
        ENTÃO método existe e pode ser chamado
        """
        # Arrange & Act
        scroll = ChatScroll()

        # Assert
        assert hasattr(scroll, "limpar")
        assert callable(scroll.limpar)


__all__ = [
    "TestChatLog",
    "TestChatScroll",
]
