# coding: utf-8
"""
Testes para clipboard vendorizado.

DOC: openspec/changes/chatlog-2-0-refactor/specs/log-copier/spec.md
TDD: Red → Green → Refactor
"""

from unittest.mock import MagicMock, patch

import pytest

from core.sky.log.clipboard import copy_to_clipboard


class TestClipboard:
    """Testa o módulo clipboard vendorizado."""

    @patch("core.sky.log.clipboard._copy_windows")
    @patch("core.sky.log.clipboard._detect_platform", return_value="windows")
    def test_copy_to_clipboard_windows(self, mock_platform, mock_copy_windows):
        """
        QUANDO copy_to_clipboard é chamado no Windows
        ENTÃO chama _copy_windows
        """
        # Arrange
        mock_copy_windows.return_value = True
        text = "Teste Windows"

        # Act
        result = copy_to_clipboard(text)

        # Assert
        mock_copy_windows.assert_called_once_with(text)
        assert result is True

    @patch("core.sky.log.clipboard._copy_macos")
    @patch("core.sky.log.clipboard._detect_platform", return_value="macos")
    def test_copy_to_clipboard_macos(self, mock_platform, mock_copy_macos):
        """
        QUANDO copy_to_clipboard é chamado no macOS
        ENTÃO chama _copy_macos
        """
        # Arrange
        mock_copy_macos.return_value = True
        text = "Teste macOS"

        # Act
        result = copy_to_clipboard(text)

        # Assert
        mock_copy_macos.assert_called_once_with(text)
        assert result is True

    @patch("core.sky.log.clipboard._copy_linux")
    @patch("core.sky.log.clipboard._detect_platform", return_value="linux")
    def test_copy_to_clipboard_linux(self, mock_platform, mock_copy_linux):
        """
        QUANDO copy_to_clipboard é chamado no Linux
        ENTÃO chama _copy_linux
        """
        # Arrange
        mock_copy_linux.return_value = True
        text = "Teste Linux"

        # Act
        result = copy_to_clipboard(text)

        # Assert
        mock_copy_linux.assert_called_once_with(text)
        assert result is True

    @patch("core.sky.log.clipboard._detect_platform", return_value="windows")
    @patch("core.sky.log.clipboard._copy_windows", return_value=True)
    def test_copy_to_clipboard_retorna_true_sucesso(self, mock_copy, mock_platform):
        """
        QUANDO copy_to_clipboard tem sucesso
        ENTÃO retorna True
        """
        # Arrange & Act
        result = copy_to_clipboard("Test")

        # Assert
        assert result is True

    @patch("core.sky.log.clipboard._detect_platform", return_value="windows")
    @patch("core.sky.log.clipboard._copy_windows", return_value=False)
    def test_copy_to_clipboard_retorna_false_erro(self, mock_copy, mock_platform):
        """
        QUANDO copy_to_clipboard falha
        ENTÃO retorna False
        """
        # Arrange & Act
        result = copy_to_clipboard("Test")

        # Assert
        assert result is False

    def test_copy_to_clipboard_texto_vazio_retorna_true(self):
        """
        QUANDO copy_to_clipboard é chamado com texto vazio
        ENTÃO retorna True (nada a copiar)
        """
        # Act
        result = copy_to_clipboard("")

        # Assert
        assert result is True


__all__ = ["TestClipboard"]
