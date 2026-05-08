# coding: utf-8
"""
Testes do ChatScreen.

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - ChatScreen (principal)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.core.sky.chat.textual_ui.screens.main import MainScreen as ChatScreen
from src.core.sky.chat import ChatMessage


class TestChatScreenInit:
    """
    Testa inicialização do ChatScreen.
    """

    def test_init_sem_mensagem_inicial(self):
        """
        QUANDO ChatScreen é criado sem mensagem inicial
        ENTÃO inicializa com estados vazios
        """
        # Arrange & Act
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        # Assert
        assert screen.initial_message is None
        assert screen.message_history == []
        assert screen._pending_task is None
        assert screen._thinking_indicator is None
        assert screen._response_count == 0
        assert screen._total_tokens == 0

    def test_init_com_mensagem_inicial(self):
        """
        QUANDO ChatScreen é criado com mensagem inicial
        ENTÃO armazena mensagem inicial
        """
        # Arrange & Act
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen(initial_message="Olá Sky!")

        # Assert
        assert screen.initial_message == "Olá Sky!"

    def test_init_inicializa_workers(self):
        """
        QUANDO ChatScreen é criado
        ENTÃO inicializa ClaudeWorker e RAGWorker
        """
        # Arrange & Act
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        # Assert
        assert screen.claude_worker is not None
        assert screen.rag_worker is not None
        assert screen.worker_queue is not None

    def test_init_inicializa_metricas(self):
        """
        QUANDO ChatScreen é criado
        ENTÃO inicializa métricas da sessão
        """
        # Arrange & Act
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        # Assert
        assert screen._session_start is not None
        assert screen._total_latency == 0.0
        assert screen._memories_used_total == 0


class TestChatScreenCompose:
    """
    Testa método compose().
    """

    def test_compose_retorna_header_content_footer(self):
        """
        QUANDO compose() é chamado
        ENTÃO retorna Header, ScrollView com content-area, e Footer
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        # Act
        children = list(screen.compose())

        # Assert - deve ter ChatHeader, Vertical com content-area, Footer
        assert len(children) == 3

    def test_compose_inclui_chat_header(self):
        """
        QUANDO compose() é chamado
        ENTÃO inclui ChatHeader
        """
        # Arrange
        from src.core.sky.chat.textual_ui.widgets.header import ChatHeader

        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        # Act
        children = list(screen.compose())

        # Assert
        assert any(isinstance(c, ChatHeader) for c in children)

    def test_compose_inclui_scroll_view_com_id(self):
        """
        QUANDO compose() é chamado
        ENTÃO inclui ScrollView com id="messages-scroll"
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        # Act
        children = list(screen.compose())

        # Assert - Vertical contém ScrollView
        vertical = children[1]
        vertical_children = list(vertical.compose())
        scroll_view = vertical_children[0]
        assert scroll_view.id == "messages-scroll"

    def test_compose_inclui_footer(self):
        """
        QUANDO compose() é chamado
        ENTÃO inclui Footer
        """
        # Arrange
        from textual.widgets import Footer

        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        # Act
        children = list(screen.compose())

        # Assert
        assert any(isinstance(c, Footer) for c in children)


class TestChatScreenCss:
    """
    Testa CSS do ChatScreen.
    """

    def test_possui_css_default_definido(self):
        """
        QUANDO ChatScreen é inspecionado
        ENTÃO possui DEFAULT_CSS definido
        """
        # Assert
        assert ChatScreen.DEFAULT_CSS is not None

    def test_css_inclui_layout_vertical(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui layout: vertical
        """
        # Assert
        assert "layout: vertical" in ChatScreen.DEFAULT_CSS

    def test_css_inclui_content_area_height(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define height: 1fr para #content-area
        """
        # Assert
        assert "#content-area" in ChatScreen.DEFAULT_CSS
        assert "height: 1fr" in ChatScreen.DEFAULT_CSS

    def test_css_inclui_messages_scroll_overflow(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define overflow-y: auto para #messages-scroll
        """
        # Assert
        assert "#messages-scroll" in ChatScreen.DEFAULT_CSS
        assert "overflow-y: auto" in ChatScreen.DEFAULT_CSS

    def test_css_inclui_turn_separator(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define estilo para .turn-separator
        """
        # Assert
        assert ".turn-separator" in ChatScreen.DEFAULT_CSS


class TestChatScreenOnInputSubmitted:
    """
    Testa on_input_submitted().
    """

    def test_on_input_submitted_vazio_nao_faz_nada(self):
        """
        QUANDO input vazio é submetido
        ENTÃO não processa mensagem
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        mock_event = Mock()
        mock_event.value = "   "

        # Act
        screen.on_input_submitted(mock_event)

        # Assert - histórico vazio
        assert len(screen.message_history) == 0

    def test_on_input_submitted_com_mensagem_processa(self):
        """
        QUANDO input com mensagem é submetido
        ENTÃO processa mensagem
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        mock_event = Mock()
        mock_event.value = "Olá Sky!"

        with patch.object(screen, "process_message") as mock_process:
            # Act
            screen.on_input_submitted(mock_event)

            # Assert
            mock_process.assert_called_once_with("Olá Sky!")

    def test_on_input_submitted_comando_detecta(self):
        """
        QUANDO input com comando é submetido
        ENTÃO executa comando em vez de processar mensagem
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        mock_event = Mock()
        mock_event.value = "/help"

        with patch.object(screen, "_execute_command") as mock_execute:
            # Act
            screen.on_input_submitted(mock_event)

            # Assert
            mock_execute.assert_called_once()


class TestChatScreenProcessMessage:
    """
    Testa process_message().
    """

    def test_process_message_cria_chat_message_user(self):
        """
        QUANDO process_message() é chamado
        ENTÃO cria ChatMessage com role="user"
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        with patch.object(screen, "_add_user_bubble"), \
             patch.object(screen, "mount"), \
             patch("asyncio.create_task"):
            # Act
            screen.process_message("Test message")

            # Assert
            assert len(screen.message_history) == 1
            assert screen.message_history[0].role == "user"
            assert screen.message_history[0].content == "Test message"

    def test_process_message_adiciona_user_bubble(self):
        """
        QUANDO process_message() é chamado
        ENTÃO adiciona UserBubble ao scroll view
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        with patch.object(screen, "_add_user_bubble") as mock_add, \
             patch.object(screen, "mount"), \
             patch("asyncio.create_task"):
            # Act
            screen.process_message("Test message")

            # Assert
            mock_add.assert_called_once_with("Test message")

    def test_process_message_exibe_thinking_indicator(self):
        """
        QUANDO process_message() é chamado
        ENTÃO exibe ThinkingIndicator
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        with patch.object(screen, "_add_user_bubble"), \
             patch.object(screen, "mount") as mock_mount, \
             patch("asyncio.create_task"):
            # Act
            screen.process_message("Test message")

            # Assert
            assert mock_mount.call_count >= 1
            # Primeira chamada deve ser ThinkingIndicator


class TestChatScreenAddBubbles:
    """
    Testa métodos de adição de bubbles.
    """

    def test_add_user_bubble_cria_widget(self):
        """
        QUANDO _add_user_bubble() é chamado
        ENTÃO cria UserBubble e monta no scroll view
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        mock_scroll = Mock()
        screen.query_one = Mock(return_value=mock_scroll)

        # Act
        screen._add_user_bubble("User message")

        # Assert
        mock_scroll.mount.assert_called_once()
        args = mock_scroll.mount.call_args[0]
        from src.core.sky.chat.textual_ui.widgets import UserBubble
        assert isinstance(args[0], UserBubble)

    def test_add_sky_bubble_cria_widget_com_separador(self):
        """
        QUANDO _add_sky_bubble() é chamado
        ENTÃO cria SkyBubble e separador
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        mock_scroll = Mock()
        screen.query_one = Mock(return_value=mock_scroll)

        # Act
        screen._add_sky_bubble("Sky response")

        # Assert
        assert mock_scroll.mount.call_count == 2  # bubble + separador


class TestChatScreenClearSession:
    """
    Testa _clear_session().
    """

    def test_clear_session_limpa_historico(self):
        """
        QUANDO _clear_session() é chamado
        ENTÃO limpa message_history
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()
            screen.message_history = [
                ChatMessage(role="user", content="Msg1"),
                ChatMessage(role="sky", content="Msg2"),
            ]

        mock_scroll = Mock()
        screen.query_one = Mock(return_value=mock_scroll)
        mock_header = Mock()
        screen.query_one = Mock(return_value=mock_header)

        # Act
        screen._clear_session()

        # Assert
        assert len(screen.message_history) == 0
        mock_scroll.remove_children.assert_called_once()

    def test_clear_session_reseta_header(self):
        """
        QUANDO _clear_session() é chamado
        ENTÃO reseta título e contexto do header
        """
        # Arrange
        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        mock_header = Mock()
        screen.query_one = Mock(return_value=mock_header)

        # Act
        screen._clear_session()

        # Assert
        mock_header.update_title.assert_called_once_with("SkyBridge", "aguardando")
        mock_header.update_context.assert_called_once_with(0)


class TestChatScreenExecuteCommand:
    """
    Testa _execute_command().
    """

    def test_execute_command_help_abre_help_screen(self):
        """
        QUANDO comando /help é executado
        ENTÃO abre HelpScreen
        """
        # Arrange
        from src.core.sky.chat.textual_ui.commands import Command, CommandType

        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()

        command = Command(type=CommandType.HELP, raw="/help")
        screen.app = Mock()

        # Act
        screen._execute_command(command)

        # Assert
        screen.app.push_screen.assert_called_once()

    def test_execute_command_new_sem_mensagens_limpa_direto(self):
        """
        QUANDO comando /new é executado com menos de 5 mensagens
        ENTÃO limpa sessão diretamente (sem modal)
        """
        # Arrange
        from src.core.sky.chat.textual_ui.commands import Command, CommandType

        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()
            screen.message_history = [
                ChatMessage(role="user", content="Msg1"),
            ]

        command = Command(type=CommandType.NEW, raw="/new")

        with patch.object(screen, "_clear_session") as mock_clear:
            # Act
            screen._execute_command(command)

            # Assert
            mock_clear.assert_called_once()

    def test_execute_command_cancel_sem_pending(self):
        """
        QUANDO comando /cancel é executado sem operação pendente
        ENTÃO exibe mensagem informativa
        """
        # Arrange
        from src.core.sky.chat.textual_ui.commands import Command, CommandType

        with patch("src.core.sky.chat.textual_ui.screens.main.get_memory"):
            screen = ChatScreen()
            screen._pending_task = None

        command = Command(type=CommandType.CANCEL, raw="/cancel")

        with patch.object(screen, "_add_info_bubble") as mock_info:
            # Act
            screen._execute_command(command)

            # Assert
            mock_info.assert_called_once()


__all__ = [
    "TestChatScreenInit",
    "TestChatScreenCompose",
    "TestChatScreenCss",
    "TestChatScreenOnInputSubmitted",
    "TestChatScreenProcessMessage",
    "TestChatScreenAddBubbles",
    "TestChatScreenClearSession",
    "TestChatScreenExecuteCommand",
]
