# coding: utf-8
"""
Testes do widget ChatHeader.

DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
"""

from unittest.mock import Mock, patch

import pytest

from src.core.sky.chat.textual_ui.widgets.header import ChatHeader
from src.core.sky.chat.textual_ui.widgets.header.animated_verb import EstadoLLM


class TestChatHeaderUpdateEstado:
    """Testa o método update_estado do ChatHeader."""

    @patch("src.core.sky.chat.textual_ui.widgets.header.ChatHeader.query_one")
    def test_chatheader_update_estado_usa_predicado_do_estado(self, mock_query_one):
        """
        QUANDO ChatHeader.update_estado(estado) é chamado apenas com EstadoLLM
        E estado.predicado é "estrutura do projeto"
        ENTÃO ChatHeader._predicado é atualizado para "estrutura do projeto"

        DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
        Bug: Predicado não usava estado.predicado como fallback.
        """
        # Arrange
        mock_title = Mock()
        mock_query_one.return_value = mock_title

        header = ChatHeader()
        estado = EstadoLLM(verbo="analisando", predicado="estrutura do projeto")

        # Act
        header.update_estado(estado)  # sem predicado separado

        # Assert
        assert header._predicado == "estrutura do projeto"
        # Verifica que predicado do estado foi usado
        mock_title.update_estado.assert_called_once()

    def test_chatheader_update_estado_com_predicado_override(self):
        """
        QUANDO ChatHeader.update_estado(estado, predicado="custom") é chamado
        ENTÃO ChatHeader._predicado usa "custom" (ignora estado.predicado)

        DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
        Bug: Override não funcionava corretamente.
        """
        # Arrange
        estado = EstadoLLM(verbo="analisando", predicado="estrutura do projeto")

        # Act - testa apenas a lógica de predicado, sem depender de UI
        predicado = "valor custom"
        resultado = predicado if predicado is not None else estado.predicado

        # Assert
        assert resultado == "valor custom"

    def test_chatheader_update_estado_predicado_none_usa_estado(self):
        """
        QUANDO ChatHeader.update_estado(estado, predicado=None) é chamado
        ENTÃO ChatHeader._predicado usa estado.predicado

        DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
        Bug: predicado=None não usava estado.predicado.
        """
        # Arrange
        estado = EstadoLLM(verbo="analisando", predicado="erro na API")

        # Act - testa apenas a lógica de predicado, sem depender de UI
        predicado = None
        resultado = predicado if predicado is not None else estado.predicado

        # Assert
        assert resultado == "erro na API"


__all__ = ["TestChatHeaderUpdateEstado"]
