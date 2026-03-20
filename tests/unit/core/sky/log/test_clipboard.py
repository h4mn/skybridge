# coding: utf-8
"""
Testes para clipboard (lib externa + fallback vendored).

DOC: openspec/changes/chatlog-2-0-refactor/specs/log-copier/spec.md
TDD: Red → Green → Refactor

DECISÃO (2026-03-19): POC invalidou implementação 100% vendored.
Lib 'clipboard' é usada como preferência, com fallback vendored.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.sky.log.clipboard import copy_to_clipboard


class TestClipboard:
    """Testa o módulo clipboard com lib externa + fallback."""

    @patch("core.sky.log.clipboard._copy_windows_fallback", return_value=True)
    @patch("core.sky.log.clipboard._detect_platform", return_value="windows")
    def test_copy_to_clipboard_windows_fallback_usado_quando_lib_falta(
        self, mock_platform, mock_copy_windows
    ):
        """
        QUANDO copy_to_clipboard é chamado no Windows E lib clipboard não está disponível
        ENTÃO usa _copy_windows_fallback
        """
        # Arrange - simula ImportError da lib clipboard
        with patch.dict("sys.modules", {"clipboard": None}):
            text = "Teste Windows"

            # Act
            result = copy_to_clipboard(text)

            # Assert
            mock_copy_windows.assert_called_once_with(text)
            assert result is True

    @patch("core.sky.log.clipboard._copy_macos_fallback", return_value=True)
    @patch("core.sky.log.clipboard._detect_platform", return_value="macos")
    def test_copy_to_clipboard_macos_fallback_usado_quando_lib_falta(
        self, mock_platform, mock_copy_macos
    ):
        """
        QUANDO copy_to_clipboard é chamado no macOS E lib clipboard não está disponível
        ENTÃO usa _copy_macos_fallback
        """
        # Arrange - simula ImportError da lib clipboard
        with patch.dict("sys.modules", {"clipboard": None}):
            text = "Teste macOS"

            # Act
            result = copy_to_clipboard(text)

            # Assert
            mock_copy_macos.assert_called_once_with(text)
            assert result is True

    @patch("core.sky.log.clipboard._copy_linux_fallback", return_value=True)
    @patch("core.sky.log.clipboard._detect_platform", return_value="linux")
    def test_copy_to_clipboard_linux_fallback_usado_quando_lib_falta(
        self, mock_platform, mock_copy_linux
    ):
        """
        QUANDO copy_to_clipboard é chamado no Linux E lib clipboard não está disponível
        ENTÃO usa _copy_linux_fallback
        """
        # Arrange - simula ImportError da lib clipboard
        with patch.dict("sys.modules", {"clipboard": None}):
            text = "Teste Linux"

            # Act
            result = copy_to_clipboard(text)

            # Assert
            mock_copy_linux.assert_called_once_with(text)
            assert result is True

    @patch("core.sky.log.clipboard._detect_platform", return_value="windows")
    @patch("core.sky.log.clipboard._copy_windows_fallback", return_value=True)
    def test_copy_to_clipboard_retorna_true_sucesso_fallback(self, mock_copy, mock_platform):
        """
        QUANDO copy_to_clipboard tem sucesso via fallback
        ENTÃO retorna True
        """
        # Arrange - simula lib clipboard não disponível
        with patch.dict("sys.modules", {"clipboard": None}):
            # Act
            result = copy_to_clipboard("Test")

            # Assert
            assert result is True

    @patch("core.sky.log.clipboard._detect_platform", return_value="windows")
    @patch("core.sky.log.clipboard._copy_windows_fallback", return_value=False)
    def test_copy_to_clipboard_retorna_false_erro_fallback(self, mock_copy, mock_platform):
        """
        QUANDO copy_to_clipboard falha via fallback
        ENTÃO retorna False
        """
        # Arrange - simula lib clipboard não disponível
        with patch.dict("sys.modules", {"clipboard": None}):
            # Act
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
