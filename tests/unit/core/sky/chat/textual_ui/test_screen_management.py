# coding: utf-8
"""
Testes do sistema de screen management.

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Screen Management

Nota: O sistema de pilha (stack) de screens é nativo do Textual.
Estes testes verificam a integração correta com esses recursos.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.core.sky.chat.textual_ui.screens.main import MainScreen as ChatScreen
from src.core.sky.chat.textual_ui.screens.config import ConfigScreen
from src.core.sky.chat.textual_ui.screens.help import HelpScreen
from src.core.sky.chat.textual_ui.widgets.common.modal import ConfirmModal
from src.core.sky.chat.textual_ui.widgets.common.toast import ToastNotification


class TestScreenStack:
    """
    Testa sistema de pilha (stack) de screens.
    """

    def test_chat_screen_is_screen(self):
        """
        QUANDO ChatScreen é inspecionado
        ENTÃO é uma subclasse de Screen do Textual
        """
        # Assert
        from textual.screen import Screen
        assert issubclass(ChatScreen, Screen)

    def test_config_screen_is_screen(self):
        """
        QUANDO ConfigScreen é inspecionado
        ENTÃO é uma subclasse de Screen do Textual
        """
        # Assert
        from textual.screen import Screen
        assert issubclass(ConfigScreen, Screen)

    def test_help_screen_is_screen(self):
        """
        QUANDO HelpScreen é inspecionado
        ENTÃO é uma subclasse de Screen do Textual
        """
        # Assert
        from textual.screen import Screen
        assert issubclass(HelpScreen, Screen)

    def test_modal_is_screen(self):
        """
        QUANDO ConfirmModal é inspecionado
        ENTÃO é uma subclasse de Screen do Textual
        """
        # Assert
        from textual.screen import Screen
        assert issubclass(ConfirmModal, Screen)


class TestPushScreen:
    """
    Testa push_screen() - adiciona screen à pilha.
    """

    def test_chat_screen_push_help_screen(self):
        """
        QUANDO app.push_screen(HelpScreen) é chamado
        ENTÃO HelpScreen é adicionada à pilha
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()
            chat_screen.app = Mock()
            chat_screen.app.push_screen = Mock()

        # Act
        from src.core.sky.chat.textual_ui.screens.help import HelpScreen
        chat_screen.app.push_screen(HelpScreen())

        # Assert
        chat_screen.app.push_screen.assert_called_once()

    def test_execute_command_help_chama_push_screen(self):
        """
        QUANDO comando /help é executado
        ENTÃO app.push_screen() é chamado com HelpScreen
        """
        # Arrange
        from src.core.sky.chat.textual_ui.commands import Command, CommandType

        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()
            chat_screen.app = Mock()

        command = Command(type=CommandType.HELP, raw="/help")

        # Act
        chat_screen._execute_command(command)

        # Assert
        chat_screen.app.push_screen.assert_called_once()

    def test_execute_command_config_chama_push_screen(self):
        """
        QUANDO comando /config é executado
        ENTÃO app.push_screen() é chamado com ConfigScreen
        """
        # Arrange
        from src.core.sky.chat.textual_ui.commands import Command, CommandType

        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()
            chat_screen.app = Mock()

        command = Command(type=CommandType.CONFIG, raw="/config")

        # Act
        chat_screen._execute_command(command)

        # Assert
        chat_screen.app.push_screen.assert_called_once()

    def test_modal_confirmar_usa_push_screen(self):
        """
        QUANDO modal de confirmação é exibido
        ENTÃO app.push_screen() é chamado com modal
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()
            chat_screen.app = Mock()
            chat_screen.app.push_screen = Mock()

        from src.core.sky.chat.textual_ui.commands import Command, CommandType
        command = Command(type=CommandType.NEW, raw="/new")

        # Adiciona 5 mensagens para forçar modal
        from src.core.sky.chat import ChatMessage
        for i in range(5):
            chat_screen.message_history.append(ChatMessage(role="user", content=f"Msg{i}"))

        # Act
        chat_screen._execute_command(command)

        # Assert - deve ter chamado push_screen para modal
        chat_screen.app.push_screen.assert_called_once()


class TestPopScreen:
    """
    Testa pop_screen() - remove screen atual da pilha.
    """

    def test_config_screen_action_save_chama_pop_screen(self):
        """
        QUANDO action_save_and_exit() é chamado em ConfigScreen
        ENTÃO app.pop_screen() é chamado
        """
        # Arrange
        config_screen = ConfigScreen()
        config_screen.app = Mock()

        # Act
        config_screen.action_save_and_exit()

        # Assert
        config_screen.app.pop_screen.assert_called_once()

    def test_help_screen_binding_esc_chama_pop_screen(self):
        """
        QUANDO HelpScreen tem binding ESC
        ENTÃO binding está configurado para pop_screen
        """
        # Assert - bindings inclui ESC -> pop_screen
        assert any(
            binding[0] == "esc" and binding[1] == "pop_screen"
            for binding in HelpScreen.BINDINGS
        )

    def test_config_screen_binding_esc_chama_pop_screen(self):
        """
        QUANDO ConfigScreen tem binding ESC
        ENTÃO binding está configurado para pop_screen
        """
        # Assert - bindings inclui ESC -> pop_screen
        assert any(
            binding[0] == "esc" and binding[1] == "pop_screen"
            for binding in ConfigScreen.BINDINGS
        )


class TestPreservarEstado:
    """
    Testa preservação de estado ao navegar entre screens.
    """

    def test_chat_screen_preserva_historico(self):
        """
        QUANDO screen secundária é aberta
        ENTÃO ChatScreen preserva message_history
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()

        from src.core.sky.chat import ChatMessage
        chat_screen.message_history = [
            ChatMessage(role="user", content="Msg1"),
            ChatMessage(role="sky", content="Msg2"),
        ]

        # Simula abrir outra screen (histórico não deve ser afetado)
        # Arrange
        chat_screen.app = Mock()

        # Act - executa comando que abre screen
        from src.core.sky.chat.textual_ui.commands import Command, CommandType
        command = Command(type=CommandType.HELP, raw="/help")
        chat_screen._execute_command(command)

        # Assert - histórico preservado
        assert len(chat_screen.message_history) == 2

    def test_chat_screen_preserva_metricas(self):
        """
        QUANDO screen secundária é aberta
        ENTÃO ChatScreen preserva métricas
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()
            chat_screen._response_count = 5
            chat_screen._total_tokens = 1000

        # Act - abre screen
        chat_screen.app = Mock()
        from src.core.sky.chat.textual_ui.commands import Command, CommandType
        command = Command(type=CommandType.CONFIG, raw="/config")
        chat_screen._execute_command(command)

        # Assert - métricas preservadas
        assert chat_screen._response_count == 5
        assert chat_screen._total_tokens == 1000


class TestEscComoVoltar:
    """
    Testa ESC como "voltar para screen anterior".
    """

    def test_help_screen_tem_binding_esc(self):
        """
        QUANDO HelpScreen.BINDINGS é inspecionado
        ENTÃO inclui "esc" para pop_screen
        """
        # Assert
        assert any(
            binding[0] == "esc" and binding[1] == "pop_screen"
            for binding in HelpScreen.BINDINGS
        )

    def test_config_screen_tem_binding_esc(self):
        """
        QUANDO ConfigScreen.BINDINGS é inspecionado
        ENTÃO inclui "esc" para pop_screen
        """
        # Assert
        assert any(
            binding[0] == "esc" and binding[1] == "pop_screen"
            for binding in ConfigScreen.BINDINGS
        )

    def test_modal_tem_binding_esc(self):
        """
        QUANDO ConfirmModal.BINDINGS é inspecionado
        ENTÃO inclui "escape" para app.pop_screen
        """
        # Assert
        assert any(
            binding[0] == "escape" and "app.pop_screen" in str(binding[1])
            for binding in ConfirmModal.BINDINGS
        )

    def test_modal_tem_binding_n_para_cancelar(self):
        """
        QUANDO ConfirmModal.BINDINGS é inspecionado
        ENTÃO inclui "n" para app.pop_screen
        """
        # Assert
        assert any(
            binding[0] == "n" and "app.pop_screen" in str(binding[1])
            for binding in ConfirmModal.BINDINGS
        )


class TestChatScreenComoBase:
    """
    Testa que ChatScreen nunca é removida da pilha (base).
    """

    def test_chat_screen_nao_chama_pop_screen(self):
        """
        QUANDO ChatScreen é ativa
        ENTÃO não chama app.pop_screen() em operações normais
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()
            chat_screen.app = Mock()

        # Act - operações normais não devem chamar pop_screen
        from src.core.sky.chat import ChatMessage
        chat_screen.message_history.append(ChatMessage(role="user", content="Test"))

        # Assert - pop_screen não foi chamado
        chat_screen.app.pop_screen.assert_not_called()

    def test_comando_sair_exibe_summary_nao_pop_screen(self):
        """
        QUANDO comando /sair é executado
        ENTÃO exibe SessionSummaryScreen mas não chama pop_screen no ChatScreen
        """
        # Arrange
        from src.core.sky.chat.textual_ui.commands import Command, CommandType

        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()
            chat_screen.app = Mock()

        command = Command(type=CommandType.SAIR, raw="/sair")

        # Act
        chat_screen._execute_command(command)

        # Assert - push_screen foi chamado (para summary), não pop_screen
        chat_screen.app.push_screen.assert_called_once()
        chat_screen.app.pop_screen.assert_not_called()


class TestScreenNavigationCenarios:
    """
    Testa cenários reais de navegação.
    """

    def test_fluxo_chat_help_voltar(self):
        """
        QUANDO usuário navega ChatScreen → HelpScreen → ESC
        ENTÃO volta para ChatScreen com estado preservado
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()

        from src.core.sky.chat import ChatMessage
        chat_screen.message_history = [
            ChatMessage(role="user", content="Msg1"),
        ]

        # Act - abre HelpScreen
        chat_screen.app = Mock()
        from src.core.sky.chat.textual_ui.commands import Command, CommandType
        command = Command(type=CommandType.HELP, raw="/help")
        chat_screen._execute_command(command)

        # Assert - estado preservado
        assert len(chat_screen.message_history) == 1
        assert chat_screen.message_history[0].content == "Msg1"

    def test_fluxo_chat_config_voltar(self):
        """
        QUANDO usuário navega ChatScreen → ConfigScreen → ESC
        ENTÃO volta para ChatScreen com estado preservado
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()
            chat_screen._response_count = 3

        # Act - abre ConfigScreen
        chat_screen.app = Mock()
        from src.core.sky.chat.textual_ui.commands import Command, CommandType
        command = Command(type=CommandType.CONFIG, raw="/config")
        chat_screen._execute_command(command)

        # Assert - estado preservado
        assert chat_screen._response_count == 3

    def test_fluxo_chat_modal_confirmar(self):
        """
        QUANDO modal de confirmação é exibido e confirmado
        ENTÃO ação é executada e modal é fechado
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            chat_screen = ChatScreen()
            chat_screen.app = Mock()

        from src.core.sky.chat import ChatMessage
        for i in range(5):
            chat_screen.message_history.append(ChatMessage(role="user", content=f"Msg{i}"))

        # Act - executa /new que abre modal
        from src.core.sky.chat.textual_ui.commands import Command, CommandType
        command = Command(type=CommandType.NEW, raw="/new")
        chat_screen._execute_command(command)

        # Assert - modal foi aberto
        chat_screen.app.push_screen.assert_called_once()
        call_args = chat_screen.app.push_screen.call_args
        modal = call_args[0][0]
        assert isinstance(modal, ConfirmModal)


__all__ = [
    "TestScreenStack",
    "TestPushScreen",
    "TestPopScreen",
    "TestPreservarEstado",
    "TestEscComoVoltar",
    "TestChatScreenComoBase",
    "TestScreenNavigationCenarios",
]
