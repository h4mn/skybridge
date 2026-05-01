# coding: utf-8
"""
Testes do módulo chat.py (ChatScreen e _VERBOS_TESTE).

DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
"""

import pytest

from src.core.sky.chat.textual_ui.widgets.header.animated_verb import EstadoLLM
from src.core.sky.chat.textual_ui.screens.main import _VERBOS_TESTE


class TestVerbosTeste:
    """Testa a lista _VERBOS_TESTE usada para validação visual."""

    def test_verbos_teste_possuem_predicados_completos(self):
        """
        QUANDO _VERBOS_TESTE é inspecionada
        ENTÃO cada entrada tem campo predicado com 2+ palavras

        DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
        Bug: _VERBOS_TESTE não tinha predicados, apenas verbos isolados.
        """
        # Arrange & Act
        entradas_sem_predicado = []
        for rotulo, estado in _VERBOS_TESTE:
            # predicado padrão "conversa" não é válido para teste
            if estado.predicado == "conversa":
                entradas_sem_predicado.append(rotulo)
            elif len(estado.predicado.split()) < 2:
                entradas_sem_predicado.append(f"{rotulo} (predicado: '{estado.predicado}')")

        # Assert
        assert not entradas_sem_predicado, (
            f"Entradas sem predicado completo (2+ palavras): {entradas_sem_predicado}"
        )

    def test_verbos_teste_titulo_completo_formado(self):
        """
        QUANDO _VERBOS_TESTE é inspecionada
        ENTÃO cada entrada forma título completo "Sky verbo predicado"

        DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
        Bug: Títulos mostravam apenas "Sky verbo conversa".
        """
        # Arrange & Act
        for rotulo, estado in _VERBOS_TESTE:
            titulo_completo = f"Sky {estado.verbo} {estado.predicado}"
            palavras = titulo_completo.split()

            # Assert
            # Título completo deve ter no mínimo 4 palavras: "Sky" + verbo + predicado(2+)
            assert len(palavras) >= 4, (
                f"Título '{titulo_completo}' tem menos de 4 palavras "
                f"(rotulo={rotulo}, verbo={estado.verbo}, predicado={estado.predicado})"
            )
            # Predicado não pode ser "conversa" (valor padrão genérico)
            assert estado.predicado != "conversa", (
                f"rotulo={rotulo} usa predicado padrão genérico 'conversa'"
            )


__all__ = ["TestVerbosTeste"]
