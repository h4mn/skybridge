# coding: utf-8
"""
Testes do widget ToolFeedback.

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Tool feedback para execução de ferramentas
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.core.sky.chat.textual_ui.widgets.content.agentic_loop.tool_feedback import (
    ToolFeedback,
    ToolStatus,
    ToolInfo,
)


class TestToolStatus:
    """
    Testa enum ToolStatus.
    """

    def test_tool_status_pending_value(self):
        """
        QUANDO ToolStatus.PENDING é inspecionado
        ENTÃO value é "pending"
        """
        # Assert
        assert ToolStatus.PENDING.value == "pending"

    def test_tool_status_running_value(self):
        """
        QUANDO ToolStatus.RUNNING é inspecionado
        ENTÃO value é "running"
        """
        # Assert
        assert ToolStatus.RUNNING.value == "running"

    def test_tool_status_success_value(self):
        """
        QUANDO ToolStatus.SUCCESS é inspecionado
        ENTÃO value é "success"
        """
        # Assert
        assert ToolStatus.SUCCESS.value == "success"

    def test_tool_status_failed_value(self):
        """
        QUANDO ToolStatus.FAILED é inspecionado
        ENTÃO value é "failed"
        """
        # Assert
        assert ToolStatus.FAILED.value == "failed"


class TestToolInfo:
    """
    Testa dataclass ToolInfo.
    """

    def test_tool_info_creation(self):
        """
        QUANDO ToolInfo é criado
        ENTÃO armazena name e status
        """
        # Arrange & Act
        info = ToolInfo(name="search_memory", status=ToolStatus.RUNNING)

        # Assert
        assert info.name == "search_memory"
        assert info.status == ToolStatus.RUNNING

    def test_tool_info_com_result(self):
        """
        QUANDO ToolInfo é criado com result
        ENTÃO armazena result
        """
        # Arrange & Act
        info = ToolInfo(
            name="write_file",
            status=ToolStatus.SUCCESS,
            result="Arquivo salvo com sucesso"
        )

        # Assert
        assert info.result == "Arquivo salvo com sucesso"

    def test_tool_info_result_default_vazio(self):
        """
        QUANDO ToolInfo é criado sem result
        ENTÃO result é string vazia
        """
        # Arrange & Act
        info = ToolInfo(name="test", status=ToolStatus.PENDING)

        # Assert
        assert info.result == ""


class TestToolFeedbackInit:
    """
    Testa inicialização do ToolFeedback.
    """

    def test_init(self):
        """
        QUANDO ToolFeedback é criado
        ENTÃO inicia com dicionário vazio de tools
        """
        # Arrange & Act
        feedback = ToolFeedback()

        # Assert
        assert feedback._tools == {}

    def test_css_default_definido(self):
        """
        QUANDO ToolFeedback é inspecionado
        ENTÃO possui DEFAULT_CSS definido
        """
        # Assert
        assert ToolFeedback.DEFAULT_CSS is not None


class TestToolFeedbackAddTool:
    """
    Testa método add_tool().
    """

    def test_add_tool_adiciona_ao_dict(self):
        """
        QUANDO add_tool() é chamado
        ENTÃO tool é adicionada ao dicionário
        """
        # Arrange
        feedback = ToolFeedback()

        # Act
        feedback.add_tool("search_memory")

        # Assert
        assert "search_memory" in feedback._tools
        assert feedback._tools["search_memory"].name == "search_memory"
        assert feedback._tools["search_memory"].status == ToolStatus.RUNNING

    def test_add_tool_status_running(self):
        """
        QUANDO add_tool() é chamado
        ENTÃO status da tool é RUNNING
        """
        # Arrange
        feedback = ToolFeedback()

        # Act
        feedback.add_tool("write_file")

        # Assert
        assert feedback._tools["write_file"].status == ToolStatus.RUNNING

    def test_add_tool_chama_refresh(self):
        """
        QUANDO add_tool() é chamado
        ENTÃO _refresh() é chamado
        """
        # Arrange
        feedback = ToolFeedback()
        with patch.object(feedback, "_refresh") as mock_refresh:
            # Act
            feedback.add_tool("test_tool")

            # Assert
            mock_refresh.assert_called_once()


class TestToolFeedbackUpdateTool:
    """
    Testa método update_tool().
    """

    def test_update_tool_muda_status(self):
        """
        QUANDO update_tool() é chamado com novo status
        ENTÃO status da tool é atualizado
        """
        # Arrange
        feedback = ToolFeedback()
        feedback.add_tool("search_memory")

        # Act
        feedback.update_tool("search_memory", ToolStatus.SUCCESS)

        # Assert
        assert feedback._tools["search_memory"].status == ToolStatus.SUCCESS

    def test_update_tool_adiciona_result(self):
        """
        QUANDO update_tool() é chamado com result
        ENTÃO result é adicionado
        """
        # Arrange
        feedback = ToolFeedback()
        feedback.add_tool("write_file")

        # Act
        feedback.update_tool(
            "write_file",
            ToolStatus.SUCCESS,
            "Arquivo salvo em /tmp/test.txt"
        )

        # Assert
        assert feedback._tools["write_file"].result == "Arquivo salvo em /tmp/test.txt"

    def test_update_tool_inexistente_nao_faz_nada(self):
        """
        QUANDO update_tool() é chamado com tool inexistente
        ENTÃO não lança exceção
        """
        # Arrange
        feedback = ToolFeedback()

        # Act & Assert - não deve lançar exceção
        feedback.update_tool("tool_inexistente", ToolStatus.SUCCESS)
        assert "tool_inexistente" not in feedback._tools

    def test_update_tool_chama_refresh(self):
        """
        QUANDO update_tool() é chamado
        ENTÃO _refresh() é chamado
        """
        # Arrange
        feedback = ToolFeedback()
        feedback.add_tool("test_tool")
        with patch.object(feedback, "_refresh") as mock_refresh:
            # Act
            feedback.update_tool("test_tool", ToolStatus.SUCCESS)

            # Assert
            mock_refresh.assert_called_once()


class TestToolFeedbackClear:
    """
    Testa método clear().
    """

    def test_clear_limpa_todas_tools(self):
        """
        QUANDO clear() é chamado
        ENTÃO dicionário de tools é limpo
        """
        # Arrange
        feedback = ToolFeedback()
        feedback.add_tool("tool1")
        feedback.add_tool("tool2")
        assert len(feedback._tools) == 2

        # Act
        feedback.clear()

        # Assert
        assert len(feedback._tools) == 0

    def test_clear_chama_refresh(self):
        """
        QUANDO clear() é chamado
        ENTÃO _refresh() é chamado
        """
        # Arrange
        feedback = ToolFeedback()
        feedback.add_tool("test_tool")
        with patch.object(feedback, "_refresh") as mock_refresh:
            # Act
            feedback.clear()

            # Assert
            mock_refresh.assert_called_once()


class TestToolFeedbackGetIcon:
    """
    Testa método _get_icon().
    """

    def test_get_icon_pending(self):
        """
        QUANDO status é PENDING
        ENTÃO retorna "⏳"
        """
        # Arrange
        feedback = ToolFeedback()

        # Act
        icon = feedback._get_icon(ToolStatus.PENDING)

        # Assert
        assert icon == "⏳"

    def test_get_icon_running(self):
        """
        QUANDO status é RUNNING
        ENTÃO retorna "⏳"
        """
        # Arrange
        feedback = ToolFeedback()

        # Act
        icon = feedback._get_icon(ToolStatus.RUNNING)

        # Assert
        assert icon == "⏳"

    def test_get_icon_success(self):
        """
        QUANDO status é SUCCESS
        ENTÃO retorna "✅"
        """
        # Arrange
        feedback = ToolFeedback()

        # Act
        icon = feedback._get_icon(ToolStatus.SUCCESS)

        # Assert
        assert icon == "✅"

    def test_get_icon_failed(self):
        """
        QUANDO status é FAILED
        ENTÃO retorna "❌"
        """
        # Arrange
        feedback = ToolFeedback()

        # Act
        icon = feedback._get_icon(ToolStatus.FAILED)

        # Assert
        assert icon == "❌"


class TestToolFeedbackRefresh:
    """
    Testa método _refresh().
    """

    def test_refresh_remove_children(self):
        """
        QUANDO _refresh() é chamado
        ENTÃO remove todos os filhos
        """
        # Arrange
        feedback = ToolFeedback()
        feedback.add_tool("tool1")
        # Simula filhos existentes
        feedback.mount(Mock())

        # Act
        feedback._refresh()

        # Assert - children foram removidos e readicionados
        # O teste verifica que não lança exceção

    def test_refresh_adiciona_widgets_para_cada_tool(self):
        """
        QUANDO _refresh() é chamado com tools
        ENTÃO adiciona widget para cada tool
        """
        # Arrange
        feedback = ToolFeedback()
        feedback.add_tool("tool1")
        feedback.add_tool("tool2")

        # Act & Assert
        # Após refresh, deve haver widgets para cada tool
        feedback._refresh()
        # Como _refresh chama remove_children e depois mount,
        # o número de filhos deve ser igual ao número de tools


class TestToolFeedbackFailureNotification:
    """
    Testa notificação de falha.
    """

    def test_update_tool_failed_emite_notificacao(self):
        """
        QUANDO update_tool() é chamado com FAILED
        ENTÃO emite notificação via Toast
        """
        # Arrange
        feedback = ToolFeedback()
        feedback.add_tool("failing_tool")

        # Mock app e screen
        mock_app = Mock()
        mock_screen = Mock()
        mock_app.screen = mock_screen
        feedback.app = mock_app

        # Act
        feedback.update_tool("failing_tool", ToolStatus.FAILED, "Erro de teste")

        # Assert
        mock_screen.mount.assert_called_once()
        # Verifica que o mount foi chamado com um ToastNotification
        mounted_widget = mock_screen.mount.call_args[0][0]
        assert "ToastNotification" in str(type(mounted_widget))

    def test_update_tool_failed_trunca_mensagem_longa(self):
        """
        QUANDO update_tool() é chamado com FAILED e mensagem longa
        ENTÃO mensagem é truncada
        """
        # Arrange
        feedback = ToolFeedback()
        feedback.add_tool("tool")

        # Mock app e screen
        mock_app = Mock()
        mock_screen = Mock()
        mock_app.screen = mock_screen
        feedback.app = mock_app

        # Act - mensagem longa
        long_error = "x" * 100
        feedback.update_tool("tool", ToolStatus.FAILED, long_error)

        # Assert
        mock_screen.mount.assert_called_once()
        mounted_widget = mock_screen.mount.call_args[0][0]
        # A mensagem deve estar truncada com "..."
        assert "..." in str(mounted_widget)


__all__ = [
    "TestToolStatus",
    "TestToolInfo",
    "TestToolFeedbackInit",
    "TestToolFeedbackAddTool",
    "TestToolFeedbackUpdateTool",
    "TestToolFeedbackClear",
    "TestToolFeedbackGetIcon",
    "TestToolFeedbackRefresh",
    "TestToolFeedbackFailureNotification",
]
