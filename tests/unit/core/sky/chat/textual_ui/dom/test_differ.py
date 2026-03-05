# coding: utf-8
"""
Testes unitários de State Diff.
"""

import pytest
from dataclasses import dataclass

from core.sky.chat.textual_ui.dom.differ import diff_state, format_diff, _diff_dicts, _diff_sequences


class TestDiffState:
    """Testes da função diff_state."""

    def test_valores_iguais_sem_diff(self):
        """Valores iguais não geram diff."""
        result = diff_state("a", "a")
        assert result == {}

    def test_primitivos_diferentes(self):
        """Primitivos diferentes geram diff."""
        result = diff_state("a", "b", "my_prop")
        assert result == {"my_prop": {"old": "a", "new": "b"}}

    def test_dicts_com_entrada(self):
        """Dicts com valores diferentes."""
        old = {"a": 1, "b": 2}
        new = {"a": 1, "b": 3}
        result = diff_state(old, new)
        assert "b" in result
        assert result["b"]["old"] == 2
        assert result["b"]["new"] == 3

    def test_dicts_key_removida(self):
        """Key removida aparece no diff."""
        old = {"a": 1, "b": 2}
        new = {"a": 1}
        result = diff_state(old, new)
        assert "b" in result
        assert result["b"]["new"] is None

    def test_dicts_key_adicionada(self):
        """Key adicionada aparece no diff."""
        old = {"a": 1}
        new = {"a": 1, "c": 3}
        result = diff_state(old, new)
        assert "c" in result
        assert result["c"]["old"] is None

    def test_listas_com_tamanhos_diferentes(self):
        """Listas de tamanhos diferentes."""
        old = [1, 2, 3]
        new = [1, 2, 3, 4]
        result = diff_state(old, new)
        assert "[3]" in result
        assert result["[3]"]["old"] is None

    def test_dataclasses(self):
        """Dataclasses são diffadas como dicts."""
        @dataclass
        class Data:
            x: int
            y: str

        old = Data(x=1, y="a")
        new = Data(x=2, y="a")
        result = diff_state(old, new)
        assert "x" in result
        assert result["x"]["old"] == 1
        assert result["x"]["new"] == 2


class TestFormatDiff:
    """Testes de format_diff."""

    def test_diff_vazio(self):
        """Diff vazio retorna mensagem."""
        result = format_diff({})
        assert result == "(sem mudanças)"

    def test_diff_com_mudancas(self):
        """Diff com mudanças é formatado."""
        diff = {"count": {"old": 1, "new": 2}}
        result = format_diff(diff)
        assert "~ count" in result
        assert "- 1" in result
        assert "+ 2" in result

    def test_diff_com_add_remove(self):
        """Diff com adições e remoções."""
        diff = {
            "added": {"old": None, "new": "x"},
            "removed": {"old": "y", "new": None},
        }
        result = format_diff(diff)
        assert "+ added" in result
        assert "- removed" in result
