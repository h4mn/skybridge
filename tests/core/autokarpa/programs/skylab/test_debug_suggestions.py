"""
Teste para validar debug suggestions

Testa que as sugestões de teste para mutants sobreviventes funcionam.
"""

import pytest
from pathlib import Path
import tempfile

from src.core.autokarpa.programs.skylab.testing.debug import (
    classify_mutant,
    suggest_test,
    generate_test_code,
    analyze_survivors,
    filter_critical_survivors,
    get_debug_summary,
)
from src.core.autokarpa.programs.skylab.testing.mutation import (
    Mutant,
    MutantType,
)


class TestDebugSuggestions:
    """Testa que debug suggestions funcionam."""

    def test_classify_boundary_mutant(self):
        """
        DOC: debug.py - classify_mutant classifica corretamente mutants Boundary.

        Dado: Mutant do tipo Boundary
        Quando: classify_mutant é chamado
        Então: retorna type='boundary', category='limit_check', severity='high'
        """
        mutant = Mutant(
            id="test:1",
            type=MutantType.BOUNDARY,
            filename="test.py",
            lineno=10,
            original="x = 0",
            mutated="x = 1",
            description="Boundary: 0 -> 1",
        )

        result = classify_mutant(mutant)

        assert result["type"] == "boundary"
        assert result["category"] == "limit_check"
        assert result["severity"] == "high"

    def test_suggest_test_generates_suggestion(self):
        """
        DOC: debug.py - suggest_test gera sugestão específica.

        Dado: Mutant sobrevivente
        Quando: suggest_test é chamado
        Então: retorna string com sugestão específica para o tipo
        """
        mutant = Mutant(
            id="test:2",
            type=MutantType.LOGICAL,
            filename="logic.py",
            lineno=5,
            original="if a and b",
            mutated="if a or b",
            description="Logical: and -> or",
        )

        suggestion = suggest_test(mutant)

        assert "Cubra ambos os branches" in suggestion
        assert "and" in suggestion
        assert "or" in suggestion

    def test_generate_test_code_produces_valid_code(self):
        """
        DOC: debug.py - generate_test_code gera código Python válido.

        Dado: Mutant de qualquer tipo
        Quando: generate_test_code é chamado
        Então: retorna string com código de teste Python válido
        """
        mutant = Mutant(
            id="test:3",
            type=MutantType.BOUNDARY,
            filename="boundary.py",
            lineno=1,
            original="return x > 0",
            mutated="return x >= 0",
            description="Boundary: > -> >=",
        )

        test_code = generate_test_code(mutant)

        # Verificar que contém elementos de teste válido
        assert "def test_" in test_code
        assert "assert" in test_code
        assert "boundary.py" in test_code

    def test_analyze_survivors_generates_complete_report(self):
        """
        DOC: debug.py - analyze_survivors gera relatório completo.

        Dado: Lista de mutants sobreviventes
        Quando: analyze_survivors é chamado
        Então: retorna lista com análise completa (suggestion, pattern, test_code)
        """
        survivors = [
            Mutant(
                id="s1",
                type=MutantType.BOUNDARY,
                filename="test.py",
                lineno=10,
                original="x == 0",
                mutated="x == 1",
                description="Boundary: 0 -> 1",
            ),
            Mutant(
                id="s2",
                type=MutantType.LOGICAL,
                filename="logic.py",
                lineno=5,
                original="a and b",
                mutated="a or b",
                description="Logical: and -> or",
            ),
        ]

        report = analyze_survivors(survivors)

        assert len(report) == 2
        assert all("suggestion" in r for r in report)
        assert all("pattern" in r for r in report)
        assert all("test_code" in r for r in report)
        assert all("severity" in r for r in report)

    def test_filter_critical_survivors_boundary_and_logical(self):
        """
        DOC: debug.py - filter_critical_survivors filtra apenas Boundary e Logical.

        Dado: Lista com diferentes tipos de mutants
        Quando: filter_critical_survivors é chamado
        Então: retorna apenas Boundary e Logical
        """
        survivors = [
            Mutant("s1", MutantType.BOUNDARY, "f1", 1, "", "", ""),
            Mutant("s2", MutantType.LOGICAL, "f2", 2, "", "", ""),
            Mutant("s3", MutantType.ARITHMETIC, "f3", 3, "", "", ""),
            Mutant("s4", MutantType.COMPARISON, "f4", 4, "", "", ""),
        ]

        critical = filter_critical_survivors(survivors)

        assert len(critical) == 2
        assert all(s.type in [MutantType.BOUNDARY, MutantType.LOGICAL] for s in critical)

    def test_get_debug_summary_formats_correctly(self):
        """
        DOC: debug.py - get_debug_summary formata resumo corretamente.

        Dado: Lista de survivors
        Quando: get_debug_summary é chamado
        Então: retorna string formatada com seções CRITICAL e Non-Critical
        """
        survivors = [
            Mutant("s1", MutantType.BOUNDARY, "f1", 1, "", "", "desc1"),
            Mutant("s2", MutantType.ARITHMETIC, "f2", 2, "", "", "desc2"),
        ]

        summary = get_debug_summary(survivors)

        assert "Debug Summary" in summary
        assert "CRITICAL" in summary
        assert "s1" in summary


__all__ = []
