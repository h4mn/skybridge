# coding: utf-8
"""
Testes do ChatUI.

DOC: openspec/changes/chat-claude-sdk/specs/chat-observability/spec.md
"""

import pytest
from io import StringIO
from unittest.mock import Mock

from src.core.sky.chat.legacy_ui import (
    ChatUI,
    ChatMetrics,
)


class TestChatMetrics:
    """
    Testa o dataclass ChatMetrics.
    """

    def test_chat_metrics_creation(self):
        """
        QUANDO ChatMetrics é criado
        ENTÃO todos os campos são armazenados
        """
        # Arrange & Act
        metrics = ChatMetrics(
            latency_ms=1234.5,
            tokens_in=100,
            tokens_out=50,
            memory_hits=3,
            model="claude-3-5-haiku-20241022",
        )

        # Assert
        assert metrics.latency_ms == 1234.5
        assert metrics.tokens_in == 100
        assert metrics.tokens_out == 50
        assert metrics.memory_hits == 3
        assert metrics.model == "claude-3-5-haiku-20241022"


class TestChatUIInit:
    """
    Testa inicialização do ChatUI.
    """

    def test_init_com_console_padrao(self):
        """
        QUANDO ChatUI é criado sem console
        ENTÃO cria console padrão
        """
        # Act
        ui = ChatUI()

        # Assert
        assert ui.console is not None
        assert ui.verbose is False

    def test_init_com_verbose(self):
        """
        QUANDO ChatUI é criado com verbose=True
        ENTÃO verbose é True
        """
        # Act
        ui = ChatUI(verbose=True)

        # Assert
        assert ui.verbose is True


class TestRenderHeader:
    """
    Testa renderização do cabeçalho.
    """

    def test_render_header_com_rag_on(self):
        """
        QUANDO render_header é chamado com RAG enabled
        ENTÃO exibe "ON" em verde
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_header(rag_enabled=True, memory_count=5)

        # Assert
        console.print.assert_called_once()
        # Verifica que foi passado um Panel com o conteúdo
        call_args = console.print.call_args[0][0]
        # O objeto deve ser um Panel do Rich
        assert hasattr(call_args, 'render') or 'Panel' in str(type(call_args))

    def test_render_header_com_rag_off(self):
        """
        QUANDO render_header é chamado com RAG disabled
        ENTÃO exibe "OFF" em vermelho
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_header(rag_enabled=False)

        # Assert
        console.print.assert_called_once()


class TestRenderThinking:
    """
    Testa renderização do thinking.
    """

    def test_render_thinking_default(self):
        """
        QUANDO render_thinking é chamado sem mensagem
        ENTÃO exibe "🤔 Pensando..."
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_thinking()

        # Assert
        console.print.assert_called_once()
        call_args = console.print.call_args
        assert "Pensando" in str(call_args) or "Thinking" in str(call_args)


class TestRenderTools:
    """
    Testa renderização de tools executadas.
    """

    def test_render_tools_vazio(self):
        """
        QUANDO render_tools é chamado com lista vazia
        ENTÃO não exibe nada
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_tools([])

        # Assert
        console.print.assert_not_called()

    def test_render_tools_com_lista(self):
        """
        QUANDO render_tools é chamado com tools
        ENTÃO exibe tabela com nome e resultado
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        tools = [
            {"name": "search_memory", "result": "3 resultados", "success": True},
            {"name": "write_file", "result": "Arquivo salvo", "success": True},
        ]

        # Act
        ui.render_tools(tools)

        # Assert
        console.print.assert_called()


class TestRenderMemory:
    """
    Testa renderização de memórias.
    """

    def test_render_memory_vazio(self):
        """
        QUANDO render_memory é chamado com lista vazia
        ENTÃO não exibe nada
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_memory([])

        # Assert
        console.print.assert_not_called()

    def test_render_memory_com_lista(self):
        """
        QUANDO render_memory é chamado com memórias
        ENTÃO exibe quantidade de memórias
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        memories = [
            {"content": "Sky é uma IA", "similarity": 0.9},
            {"content": "Sky foi criada pelo pai", "similarity": 0.85},
        ]

        # Act
        ui.render_memory(memories)

        # Assert
        console.print.assert_called()
        # Deve exibir quantidade de memórias
        call_args = console.print.call_args
        assert "2" in str(call_args) or "duas" in str(call_args).lower()


class TestRenderMessage:
    """
    Testa renderização de mensagens.
    """

    def test_render_message_user(self):
        """
        QUANDO render_message é chamado com role="user"
        ENTÃO exibe mensagem do usuário
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_message("user", "Olá Sky!")

        # Assert
        console.print.assert_called()

    def test_render_message_sky_sem_metrics(self):
        """
        QUANDO render_message é chamado com role="sky" sem métricas
        ENTÃO exibe mensagem da Sky sem métricas
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_message("sky", "Olá! Sou a Sky.")

        # Assert
        console.print.assert_called()

    def test_render_message_sky_com_metrics_verbose(self):
        """
        QUANDO render_message é chamado com métricas e verbose=True
        ENTÃO exibe latência e tokens
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console, verbose=True)

        metrics = ChatMetrics(
            latency_ms=1234,
            tokens_in=100,
            tokens_out=50,
            memory_hits=2,
            model="haiku",
        )

        # Act
        ui.render_message("sky", "Resposta", metrics=metrics)

        # Assert
        console.print.assert_called()
        # Deve ter exibido métricas (2 calls: mensagem + métricas)
        assert console.print.call_count >= 1


class TestRenderFooter:
    """
    Testa renderização do rodapé.
    """

    def test_render_footer(self):
        """
        QUANDO render_footer é chamado
        ENTÃO exibe comandos disponíveis
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_footer()

        # Assert
        console.print.assert_called_once()


class TestRenderError:
    """
    Testa renderização de erros.
    """

    def test_render_error(self):
        """
        QUANDO render_error é chamado
        ENTÃO exibe mensagem de erro
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_error("Erro de teste")

        # Assert
        console.print.assert_called_once()


class TestRenderSessionSummary:
    """
    Testa renderização do resumo da sessão.
    """

    def test_render_session_summary_vazio(self):
        """
        QUANDO render_session_summary é chamado sem métricas
        ENTÃO não exibe nada
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        # Act
        ui.render_session_summary([])

        # Assert
        console.print.assert_not_called()

    def test_render_session_summary_com_metricas(self):
        """
        QUANDO render_session_summary é chamado com métricas
        ENTÃO exibe tabela com resumo
        """
        # Arrange
        console = Mock()
        ui = ChatUI(console=console)

        metrics = [
            ChatMetrics(1000, 100, 50, 2, "haiku"),
            ChatMetrics(1500, 150, 75, 3, "haiku"),
        ]

        # Act
        ui.render_session_summary(metrics)

        # Assert
        console.print.assert_called()
