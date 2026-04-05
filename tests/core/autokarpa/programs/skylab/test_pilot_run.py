"""
Teste Piloto - Executa uma iteração completa do Skylab para gerar artefatos.

Este teste:
1. Executa 1 iteração do loop de evolução
2. Gera results.tsv com 20 colunas
3. Gera registros independentes (components/, drift/, review/)
4. Valida que todos os artefatos foram criados

NOTA: Para este teste piloto, desabilitamos validação de escopo pois o repositório
tem arquivos não tracked que não são do skylab. Em produção, a validação deve estar ativa.
"""

import pytest
from pathlib import Path
import sys
import os
from unittest.mock import patch, MagicMock

# Adicionar src ao path para importar skylab
project_root = Path(__file__).parent.parent.parent.parent.parent.parent  # 6 níveis até skybridge/
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

# Ir para o diretório do projeto para que git funcione corretamente
os.chdir(project_root)

from core.autokarpa.programs.skylab import run_skylab


def dummy_agent(specs, test_results):
    """Agente dummy para teste - retorna descrição simples."""
    return "test pilot iteration"


def mock_validate_scope(*args, **kwargs):
    """Mock que sempre retorna escopo válido para o teste piloto."""
    return (True, [])  # is_valid=True, no violations


class TestPilotRun:
    """Teste piloto que executa Skylab e valida artefatos gerados."""

    @patch('core.autokarpa.programs.skylab.core.evolution.validate_scope', side_effect=mock_validate_scope)
    def test_executa_uma_iteracao_completa(self, mock_scope):
        """
        Executa 1 iteração do Skylab e valida que artefatos são gerados.

        Este teste CRÍTICO valida:
        - Entry point funcional
        - results.tsv criado com 20 colunas
        - Registros components/ gerado
        - Registros review/ gerado
        """
        # Diretório skylab (usar project_root para caminho correto)
        skylab_dir = project_root / "src" / "core" / "autokarpa" / "programs" / "skylab"

        # Executar Skylab por 1 iteração
        results = run_skylab(
            change_name="autokarpa-sky-lab",
            iterations=1,
            agent_func=dummy_agent,
        )

        # Validar resultados básicos
        assert "best_code_health" in results
        assert "best_iteration" in results
        assert "total_iterations" in results
        assert "status" in results

        # Validar results.tsv
        results_path = skylab_dir / "results.tsv"
        assert results_path.exists(), "results.tsv deve ser criado"

        # Validar cabeçalho com 20 colunas
        content = results_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")

        # Header + 1 linha de dados
        assert len(lines) >= 2, "results.tsv deve ter header + pelo menos 1 linha"

        # Validar 20 colunas no header
        header = lines[0]
        columns = header.split("\t")
        assert len(columns) == 20, f"Header deve ter 20 colunas, tem {len(columns)}"

        # Validar nomes das colunas principais
        expected_cols = [
            "code_health", "mutation", "unit", "pbt", "complexity",
            "stagnation", "decline", "repetition",
            "added_files", "modified_files", "removed_files", "moved_files",
            "added_dirs", "removed_dirs", "size_delta",
            "commit", "memory_gb", "status", "description", "diff_path"
        ]
        for col in expected_cols:
            assert col in header, f"Coluna {col} deve estar no header"

        # Validar registros components/
        components_dir = skylab_dir / "results" / "components"
        assert components_dir.exists(), "results/components/ deve existir"

        # Deve ter pelo menos 1 arquivo JSON
        component_files = list(components_dir.glob("iteration_*.json"))
        assert len(component_files) >= 1, "Deve haver pelo menos 1 registro de components"

        # Validar registros review/
        review_dir = skylab_dir / "results" / "review"
        assert review_dir.exists(), "results/review/ deve existir"

        # Deve ter pelo menos 1 arquivo markdown
        review_files = list(review_dir.glob("iteration_*.md"))
        assert len(review_files) >= 1, "Deve haver pelo menos 1 registro de review"

    def test_results_tsv_tem_valores_validos(self):
        """
        Valida que results.tsv contém valores válidos (não vazios/NAN).
        """
        skylab_dir = project_root / "src" / "core" / "autokarpa" / "programs" / "skylab"
        results_path = skylab_dir / "results.tsv"

        if not results_path.exists():
            pytest.skip("results.tsv não existe - executar test_executa_uma_iteracao_completa primeiro")

        content = results_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")

        # Pegar primeira linha de dados (índice 1, após header)
        if len(lines) < 2:
            pytest.skip("results.tsv não tem linhas de dados")

        data_line = lines[1]
        values = data_line.split("\t")

        # Validar que code_health é um número válido
        code_health = values[0]
        try:
            float(code_health)
        except ValueError:
            pytest.fail(f"code_health deve ser número, got: {code_health}")

        # Validar que mutation, unit, pbt, complexity são números
        for i in [1, 2, 3, 4]:  # mutation, unit, pbt, complexity
            try:
                float(values[i])
            except ValueError:
                pytest.fail(f"Coluna {i} deve ser número, got: {values[i]}")
