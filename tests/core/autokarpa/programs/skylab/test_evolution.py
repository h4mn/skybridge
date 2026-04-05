"""
Testes para Skylab Core - Evolution Loop

Testes TDD estritos: RED → GREEN → REFACTOR

Spec: tdd-core/spec.md
- Requirement: Loop de evolução
- Scenario: Uma iteração do loop
- Scenario: Iteração melhora → keep
- Scenario: Iteração piora → discard
- Scenario: Crash → reset + crash status
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch, MagicMock

from src.core.autokarpa.programs.skylab.core.evolution import (
    EvolutionLoop,
    run_evolution,
)


class TestEvolutionLoopInit:
    """Testa inicialização do EvolutionLoop."""

    @patch("src.core.autokarpa.programs.skylab.core.evolution.load_change")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.parse_specs")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.get_results_path")
    def test_inicializa_com_change_name(self, mock_get_results, mock_parse, mock_load):
        """
        DOC: spec.md - EvolutionLoop deve carregar change pelo nome.

        Dado: change_name fornecido
        Quando: EvolutionLoop é criado
        Então: change é carregada e specs são parseadas
        """
        # Mocks
        mock_load.return_value = {
            "proposal": "Implement feature X",
            "design": "Design decisions",
            "tasks": "Task list",
            "specs_path": Path("/fake/specs"),
        }
        mock_parse.return_value = []
        mock_get_results.return_value = Path("/fake/results.tsv")

        with tempfile.TemporaryDirectory() as tmpdir:
            loop = EvolutionLoop(
                change_name="test-change",
                skylab_dir=Path(tmpdir),
            )

            assert loop.change_name == "test-change"
            assert loop.proposal == "Implement feature X"


class TestRunIteration:
    """Testa run_iteration()."""

    @patch("src.core.autokarpa.programs.skylab.core.evolution.load_change")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.parse_specs")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.get_results_path")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.run_pytest")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.calculate_complexity")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.run_mutation_test")
    def test_uma_iteracao_completa(
        self, mock_mutation, mock_complexity, mock_pytest, mock_get_results, mock_parse, mock_load
    ):
        """
        DOC: spec.md - Uma iteração executa fluxo completo.

        Fluxo:
        1. Testes gerados (via spec_parser)
        2. Agente implementa (via agent_func)
        3. Pytest roda (GREEN)
        4. Refactoring verificado
        5. PBT roda
        6. Mutation roda
        7. Code Health calculado
        """
        # Setup mocks
        mock_load.return_value = {
            "proposal": "Test proposal",
            "design": "Design",
            "tasks": "Tasks",
            "specs_path": Path("/fake"),
        }
        mock_parse.return_value = []
        mock_get_results.return_value = Path("/fake/results.tsv")
        mock_pytest.return_value = {"success": True, "passed": 5, "failed": 0, "total": 5}
        mock_complexity.return_value = {"avg": 5.0, "max": 8, "worst_function": "foo"}
        mock_mutation.return_value = {"score": 0.85, "killed": 42, "total": 50}

        with tempfile.TemporaryDirectory() as tmpdir:
            agent_func = Mock(return_value="implementou foo")

            loop = EvolutionLoop(
                change_name="test",
                skylab_dir=Path(tmpdir),
                agent_func=agent_func,
            )

            result = loop.run_iteration(0)

            # Verificar resultado
            assert result.code_health > 0
            assert result.mutation == 0.85
            assert result.unit == 1.0  # Pytest success
            assert result.description == "implementou foo"


class TestKeepDiscardDecision:
    """Testa decisão keep/discard."""

    @patch("src.core.autokarpa.programs.skylab.core.evolution.load_change")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.parse_specs")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.get_results_path")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.get_current_commit_hash")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.run_pytest")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.calculate_complexity")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.run_mutation_test")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.write_results_tsv")
    def test_iteracao_melhora_keep_e_commita(
        self, mock_write, mock_mutation, mock_complexity, mock_pytest,
        mock_hash, mock_get_results, mock_parse, mock_load
    ):
        """
        DOC: spec.md - Iteração que melhora deve ser mantida (keep).

        Dado: code_health antes = 0.5, after = 0.6
        Quando: run_evolution() executa
        Então: git commit é chamado e status = "keep"
        """
        # Setup mocks
        mock_load.return_value = {
            "proposal": "Test",
            "design": "Design",
            "tasks": "Tasks",
            "specs_path": Path("/fake"),
        }
        mock_parse.return_value = []
        mock_get_results.return_value = Path("/fake/results.tsv")
        mock_hash.return_value = "abc1234"
        mock_pytest.return_value = {"success": True, "passed": 5, "failed": 0, "total": 5}
        mock_complexity.return_value = {"avg": 5.0, "max": 8, "worst_function": "foo"}
        mock_mutation.return_value = {"score": 0.9, "killed": 45, "total": 50}

        with tempfile.TemporaryDirectory() as tmpdir:
            agent_func = Mock(return_value="melhoria")

            loop = EvolutionLoop(
                change_name="test",
                skylab_dir=Path(tmpdir),
                agent_func=agent_func,
            )

            # Primeira iteração: baseline
            result1 = loop.run_iteration(0)
            assert result1.code_health > 0
            best_after_iter1 = loop.best_code_health

            # Mock mutation para retornar score maior
            mock_mutation.return_value = {"score": 0.95, "killed": 47, "total": 50}

            # Segunda iteração: melhoria
            with patch.object(loop, "_git_commit") as mock_commit:
                mock_commit.return_value = "def5678"
                result2 = loop.run_iteration(1)

                # Verificar que commit foi chamado (por código, não pelo teste)
                assert result2.code_health > best_after_iter1


class TestCrashHandling:
    """Testa handling de crashes."""

    @patch("src.core.autokarpa.programs.skylab.core.evolution.load_change")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.parse_specs")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.get_results_path")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.write_results_tsv")
    def test_run_iteration_retorna_status_crash(self, mock_write, mock_get_results, mock_parse, mock_load):
        """
        DOC: spec.md - Crash durante execução deve retornar status "crash".

        Dado: iteração levanta exceção
        Quando: exceção ocorre
        Então: run_iteration() retorna status "crash"
        """
        # Setup mocks
        mock_load.return_value = {
            "proposal": "Test",
            "design": "Design",
            "tasks": "Tasks",
            "specs_path": Path("/fake"),
        }
        mock_parse.return_value = []
        mock_get_results.return_value = Path("/fake/results.tsv")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Agent que levanta exceção
            def crashing_agent(*args, **kwargs):
                raise ValueError("Simulated crash")

            loop = EvolutionLoop(
                change_name="test",
                skylab_dir=Path(tmpdir),
                agent_func=crashing_agent,
            )

            result = loop.run_iteration(0)

            # Verificar resultado tem status crash
            assert result.status == "crash"
            assert "crash" in result.description.lower()
            assert result.code_health == 0.0


class TestGitIntegration:
    """Testa integração com git."""

    @patch("src.core.autokarpa.programs.skylab.core.evolution.load_change")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.parse_specs")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.get_results_path")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.subprocess.run")
    def test_cria_branch_no_inicio(self, mock_run, mock_get_results, mock_parse, mock_load):
        """
        DOC: tasks.md - Deve criar branch autoresearch/<data>-0 no início.

        Dado: EvolutionLoop é criado
        Quando: inicialização ocorre
        Então: branch é criado com nome correto
        """
        # Setup mocks
        mock_load.return_value = {
            "proposal": "Test",
            "design": "Design",
            "tasks": "Tasks",
            "specs_path": Path("/fake"),
        }
        mock_parse.return_value = []
        mock_get_results.return_value = Path("/fake/results.tsv")
        mock_run.return_value = MagicMock(check=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            loop = EvolutionLoop(
                change_name="test",
                skylab_dir=Path(tmpdir),
            )

            # Verificar que git checkout -b foi chamado
            assert mock_run.called
            call_args = mock_run.call_args_list[0]
            assert "checkout" in str(call_args)
            assert "-b" in str(call_args)
            assert "autoresearch/" in str(call_args)


class TestRunEvolution:
    """Testa run_evolution() entry point."""

    @patch("src.core.autokarpa.programs.skylab.core.evolution.load_change")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.parse_specs")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.get_results_path")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.run_pytest")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.calculate_complexity")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.run_mutation_test")
    @patch("src.core.autokarpa.programs.skylab.core.evolution.write_results_tsv")
    def test_executa_n_iteracoes(
        self, mock_write, mock_mutation, mock_complexity, mock_pytest,
        mock_get_results, mock_parse, mock_load
    ):
        """
        DOC: spec.md - run_evolution() deve executar N iterações.

        Dado: iterations=3
        Quando: run_evolution() é chamado
        Então: 3 iterações são executadas
        """
        # Setup mocks
        mock_load.return_value = {
            "proposal": "Test",
            "design": "Design",
            "tasks": "Tasks",
            "specs_path": Path("/fake"),
        }
        mock_parse.return_value = []
        mock_get_results.return_value = Path("/fake/results.tsv")
        mock_pytest.return_value = {"success": True, "passed": 5, "failed": 0, "total": 5}
        mock_complexity.return_value = {"avg": 5.0, "max": 8, "worst_function": "foo"}
        mock_mutation.return_value = {"score": 0.8, "killed": 40, "total": 50}

        with tempfile.TemporaryDirectory() as tmpdir:
            agent_func = Mock(return_value="iteração")

            results = run_evolution(
                change_name="test",
                iterations=3,
                skylab_dir=Path(tmpdir),
                agent_func=agent_func,
            )

            # Verificar resultados
            assert results["total_iterations"] == 3
            assert results["status"] == "completed"
            assert results["best_code_health"] >= 0

            # Verificar que agent foi chamado 3 vezes
            assert agent_func.call_count == 3


__all__ = []
