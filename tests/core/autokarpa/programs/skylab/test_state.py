"""
Testes para Skylab Core - State Management

Testes TDD estritos: RED → GREEN → REFACTOR

Spec: tdd-core/spec.md
- Requirement: Registrar resultados em TSV
- Scenario: Registro bem-sucedido adiciona linha ao TSV
- Scenario: Arquivo não versionado (adicionar ao .gitignore)
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.core.autokarpa.programs.skylab.core.state import (
    IterationResult,
    write_results_tsv,
    load_results_tsv,
    get_results_path,
    get_current_commit_hash,
    get_memory_usage_gb,
)


class TestIterationResult:
    """Testa IterationResult dataclass."""

    def test_iteration_result_criacao_completa(self):
        """
        DOC: spec.md - IterationResult deve armazenar 20 métricas em 6 grupos.

        Dado: dados completos de uma iteração
        Quando: IterationResult é criado
        Então: todos os campos devem ser acessíveis
        """
        result = IterationResult(
            code_health=0.85,
            mutation=0.90,
            unit=1.0,
            pbt=0.8,
            complexity=0.7,
            stagnation=False,
            decline=False,
            repetition=True,
            added_files=1,
            modified_files=2,
            removed_files=0,
            moved_files=0,
            added_dirs=0,
            removed_dirs=0,
            size_delta=1024,
            commit="abc1234",
            memory_gb=2.5,
            status="keep",
            description="implementou process()",
            diff_path="results/review/001.md",
        )

        assert result.code_health == 0.85
        assert result.mutation == 0.90
        assert result.repetition is True
        assert result.description == "implementou process()"

    def test_iteration_result_to_tsv_row(self):
        """
        DOC: spec.md - to_tsv_row() deve gerar linha com 20 valores tab-separated.

        Dado: IterationResult com valores
        Quando: to_tsv_row() é chamado
        Então: retorna string com 20 valores separados por tab
        """
        result = IterationResult(
            code_health=0.52,
            mutation=0.70,
            unit=0.90,
            pbt=0.75,
            complexity=0.70,
        )

        row = result.to_tsv_row()
        values = row.split("\t")

        assert len(values) == 20, f"Expected 20 columns, got {len(values)}"
        assert values[0] == "0.5200"  # code_health
        assert values[1] == "0.7000"  # mutation

    def test_iteration_result_from_dict(self):
        """
        DOC: spec.md - from_dict() deve criar IterationResult a partir de dict.

        Dado: dict com dados de iteração
        Quando: from_dict() é chamado
        Então: IterationResult é criado com valores do dict
        """
        data = {
            "code_health": 0.45,
            "mutation": 0.60,
            "unit": 0.80,
            "pbt": 0.70,
            "complexity": 0.75,
            "status": "discard",
            "description": "tentou recursão",
        }

        result = IterationResult.from_dict(data)

        assert result.code_health == 0.45
        assert result.status == "discard"
        assert result.description == "tentou recursão"


class TestWriteResultsTsv:
    """Testa write_results_tsv()."""

    def test_cria_arquivo_com_header_se_nao_existe(self):
        """
        DOC: spec.md - Arquivo deve ser criado com header se não existe.

        Dado: results.tsv não existe
        Quando: write_results_tsv() é chamado
        Então: arquivo é criado com header de 20 colunas
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.tsv"
            result = IterationResult(code_health=0.5, mutation=0.6, unit=0.8, pbt=0.7, complexity=0.75)

            write_results_tsv(result, results_path)

            assert results_path.exists()
            content = results_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            assert len(lines) >= 1

            # Verificar header tem 20 colunas
            header = lines[0]
            cols = header.split("\t")
            assert len(cols) == 20

    def test_adiciona_linha_ao_arquivo_existente(self):
        """
        DOC: spec.md - Linha deve ser adicionada ao final do arquivo.

        Dado: results.tsv já existe com header
        Quando: write_results_tsv() é chamado
        Então: nova linha é adicionada ao final
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.tsv"

            # Criar arquivo inicial
            result1 = IterationResult(
                code_health=0.52, mutation=0.70, unit=0.90, pbt=0.75, complexity=0.70,
                description="primeira iteração"
            )
            write_results_tsv(result1, results_path)

            # Adicionar segunda linha
            result2 = IterationResult(
                code_health=0.48, mutation=0.65, unit=0.80, pbt=0.70, complexity=0.75,
                description="segunda iteração"
            )
            write_results_tsv(result2, results_path)

            content = results_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")

            assert len(lines) == 3  # header + 2 linhas
            assert "primeira iteração" in lines[1]
            assert "segunda iteração" in lines[2]

    def test_registro_bem_sucedido_20_colunas(self):
        """
        DOC: spec.md - Registro bem-sucedido adiciona linha com 20 colunas em 6 grupos.

        Grupos:
        - Score (1): code_health
        - Components (4): mutation, unit, pbt, complexity
        - Drift (3): stagnation, decline, repetition
        - Diff (7): added_files, modified_files, removed_files, moved_files, added_dirs, removed_dirs, size_delta
        - Metadata (3): commit, memory_gb, status
        - Descritores (2): description, diff_path
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.tsv"
            result = IterationResult(
                code_health=0.45,
                mutation=0.60,
                unit=0.80,
                pbt=0.70,
                complexity=0.75,
                stagnation=True,
                decline=False,
                repetition=False,
                added_files=1,
                modified_files=2,
                removed_files=0,
                moved_files=0,
                added_dirs=0,
                removed_dirs=0,
                size_delta=1024,
                commit="a1b2c3d",
                memory_gb=2.1,
                status="keep",
                description="baseline implementation",
                diff_path="results/review/000.md",
            )

            write_results_tsv(result, results_path)

            content = results_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            data_line = lines[1]

            cols = data_line.split("\t")
            assert len(cols) == 20
            assert cols[0] == "0.4500"  # code_health
            assert cols[4] == "0.7500"  # complexity
            assert cols[5] == "1"  # stagnation (true)
            assert cols[15] == "a1b2c3d"  # commit
            assert cols[17] == "keep"  # status


class TestLoadResultsTsv:
    """Testa load_results_tsv()."""

    def test_carrega_arquivo_existente(self):
        """
        DOC: spec.md - load_results_tsv() deve retornar lista de dicts.

        Dado: results.tsv existe com dados
        Quando: load_results_tsv() é chamado
        Então: retorna lista de dicts com chaves iguais às colunas
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.tsv"

            # Criar arquivo com dados
            result = IterationResult(
                code_health=0.52, mutation=0.70, unit=0.90, pbt=0.75, complexity=0.70,
                description="teste carga"
            )
            write_results_tsv(result, results_path)

            # Carregar
            loaded = load_results_tsv(results_path)

            assert len(loaded) == 1
            assert loaded[0]["code_health"] == "0.5200"
            assert loaded[0]["description"] == "teste carga"

    def test_levanta_file_not_found_se_arquivo_nao_existe(self):
        """
        DOC: spec.md - load_results_tsv() deve levantar FileNotFoundError se não existe.

        Dado: results.tsv não existe
        Quando: load_results_tsv() é chamado
        Então: FileNotFoundError é levantado
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.tsv"

            with pytest.raises(FileNotFoundError):
                load_results_tsv(results_path)


class TestGetResultsPath:
    """Testa get_results_path()."""

    def test_retorna_caminho_results_tsv(self):
        """
        DOC: spec.md - get_results_path() deve retornar caminho para results.tsv.

        Dado: diretório skylab
        Quando: get_results_path() é chamado
        Então: retorna Path para results.tsv no diretório
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            skylab_dir = Path(tmpdir)

            path = get_results_path(skylab_dir)

            assert path == skylab_dir / "results.tsv"


class TestGetCurrentCommitHash:
    """Testa get_current_commit_hash()."""

    def test_retorna_hash_curto(self):
        """
        DOC: spec.md - get_current_commit_hash() deve retornar hash curto (7 caracteres).

        Dado: repositório git
        Quando: get_current_commit_hash() é chamado
        Então: retorna string com 7 caracteres (ou "unknown" se falhar)
        """
        hash_val = get_current_commit_hash()

        # Se git funciona, deve ter 7 chars; se falha, "unknown"
        assert isinstance(hash_val, str)
        assert len(hash_val) == 7 or hash_val == "unknown"


class TestGetMemoryUsageGb:
    """Testa get_memory_usage_gb()."""

    def test_retorna_float_gb(self):
        """
        DOC: spec.md - get_memory_usage_gb() deve retornar float com uso em GB.

        Dado: processo Python rodando
        Quando: get_memory_usage_gb() é chamado
        Então: retorna float >= 0
        """
        memory = get_memory_usage_gb()

        assert isinstance(memory, float)
        assert memory >= 0.0


__all__ = []
