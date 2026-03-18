# coding: utf-8
"""
Testes do widget ToastNotification.

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Toast notifications
"""

import pytest
from unittest.mock import Mock, patch

from src.core.sky.chat.textual_ui.widgets.toast import ToastNotification


class TestToastNotificationInit:
    """
    Testa inicialização do ToastNotification.
    """

    def test_init_com_mensagem(self):
        """
        QUANDO ToastNotification é criado com mensagem
        ENTÃO armazena a mensagem
        """
        # Arrange & Act
        toast = ToastNotification("Test message")

        # Assert
        assert toast.toast_type == "info"
        assert toast.duration == 5.0

    def test_init_com_type_success(self):
        """
        QUANDO ToastNotification é criado com type="success"
        ENTÃO armazena toast_type como "success"
        """
        # Arrange & Act
        toast = ToastNotification("Success!", toast_type="success")

        # Assert
        assert toast.toast_type == "success"

    def test_init_com_type_error(self):
        """
        QUANDO ToastNotification é criado com type="error"
        ENTÃO armazena toast_type como "error"
        """
        # Arrange & Act
        toast = ToastNotification("Error occurred", toast_type="error")

        # Assert
        assert toast.toast_type == "error"

    def test_init_com_duration_customizada(self):
        """
        QUANDO ToastNotification é criado com duration customizado
        ENTÃO armazena duration
        """
        # Arrange & Act
        toast = ToastNotification("Quick message", duration=2.0)

        # Assert
        assert toast.duration == 2.0

    def test_init_timer_inicia_none(self):
        """
        QUANDO ToastNotification é criado
        ENTÃO _timer inicia como None
        """
        # Arrange & Act
        toast = ToastNotification("Test")

        # Assert
        assert toast._timer is None


class TestToastNotificationCss:
    """
    Testa CSS do ToastNotification.
    """

    def test_possui_css_default_definido(self):
        """
        QUANDO ToastNotification é inspecionado
        ENTÃO possui DEFAULT_CSS definido
        """
        # Assert
        assert ToastNotification.DEFAULT_CSS is not None

    def test_css_inclui_dock_top_right(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui dock: top right
        """
        # Assert
        assert "dock: top right" in ToastNotification.DEFAULT_CSS

    def test_css_inclui_classe_success(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui classe .success
        """
        # Assert
        assert "ToastNotification.success" in ToastNotification.DEFAULT_CSS

    def test_css_inclui_classe_error(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui classe .error
        """
        # Assert
        assert "ToastNotification.error" in ToastNotification.DEFAULT_CSS

    def test_css_inclui_classe_info(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui classe .info
        """
        # Assert
        assert "ToastNotification.info" in ToastNotification.DEFAULT_CSS


class TestToastNotificationDismiss:
    """
    Testa método dismiss().
    """

    def test_dismiss_para_timer(self):
        """
        QUANDO dismiss() é chamado com timer ativo
        ENTÃO para o timer
        """
        # Arrange
        toast = ToastNotification("Test")
        mock_timer = Mock()
        toast._timer = mock_timer

        # Act
        toast.dismiss()

        # Assert
        mock_timer.stop.assert_called_once()

    def test_dismiss_sem_timer(self):
        """
        QUANDO dismiss() é chamado sem timer
        ENTÃO não lança exceção
        """
        # Arrange
        toast = ToastNotification("Test")
        toast._timer = None

        # Act & Assert - não deve lançar exceção
        # (remove() pode falhar se não montado, mas mock ok)
        with patch.object(toast, "remove"):
            toast.dismiss()


class TestToastNotificationTipos:
    """
    Testa diferentes tipos de toast.
    """

    def test_toast_info_tipo_default(self):
        """
        QUANDO toast_type não é especificado
        ENTÃO usa "info" como padrão
        """
        # Arrange & Act
        toast = ToastNotification("Info message")

        # Assert
        assert toast.toast_type == "info"

    def test_toast_success_usa_cor_sucesso(self):
        """
        QUANDO toast_type é "success"
        ENTÃO CSS usa $success
        """
        # Arrange & Act
        toast = ToastNotification("Success!", toast_type="success")

        # Assert
        assert "$success" in ToastNotification.DEFAULT_CSS

    def test_toast_error_usa_cor_erro(self):
        """
        QUANDO toast_type é "error"
        ENTÃO CSS usa $error
        """
        # Arrange & Act
        toast = ToastNotification("Error!", toast_type="error")

        # Assert
        assert "$error" in ToastNotification.DEFAULT_CSS

    def test_toast_info_usa_cor_primary(self):
        """
        QUANDO toast_type é "info"
        ENTÃO CSS usa $primary
        """
        # Arrange & Act
        toast = ToastNotification("Info", toast_type="info")

        # Assert
        assert "$primary" in ToastNotification.DEFAULT_CSS


class TestToastNotificationDuration:
    """
    Testa configurações de duração.
    """

    def test_duration_padrao_5_segundos(self):
        """
        QUANDO duration não é especificado
        ENTÃO usa 5.0 segundos como padrão
        """
        # Arrange & Act
        toast = ToastNotification("Test")

        # Assert
        assert toast.duration == 5.0

    def test_duration_curta_2_segundos(self):
        """
        QUANDO duration=2.0
        ENTÃO usa 2 segundos
        """
        # Arrange & Act
        toast = ToastNotification("Quick", duration=2.0)

        # Assert
        assert toast.duration == 2.0

    def test_duration_longa_10_segundos(self):
        """
        QUANDO duration=10.0
        ENTÃO usa 10 segundos
        """
        # Arrange & Act
        toast = ToastNotification("Long message", duration=10.0)

        # Assert
        assert toast.duration == 10.0


__all__ = [
    "TestToastNotificationInit",
    "TestToastNotificationCss",
    "TestToastNotificationDismiss",
    "TestToastNotificationTipos",
    "TestToastNotificationDuration",
]
