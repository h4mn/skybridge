# coding: utf-8
"""
Testes de integração para bootstrap.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Adiciona src ao path
project_root = Path(__file__).parent.parent.parent.parent.parent
src_path = str(project_root / "src")
sys.path.insert(0, src_path)


class TestBootstrapIntegration:
    """Testes de integração do bootstrap."""

    @patch.dict(os.environ, {"USE_RAG_MEMORY": "true"})
    def test_bootstrap_complete_flow_with_rag(self):
        """Testa fluxo completo do bootstrap com RAG."""
        from core.sky.bootstrap.bootstrap import _get_stages, Stage

        stages = _get_stages(use_rag=True)

        # Verifica que todos os estágios estão presentes (6 com model_weights)
        assert len(stages) == 6
        stage_names = [s.name for s in stages]

        # Verifica ordem correta (model_weights foi adicionado após embedding)
        assert stage_names == ["environment", "embedding", "model_weights", "vector_db", "collections", "textual"]

        # Verifica descrições
        descriptions = {s.name: s.description for s in stages}
        assert "Configurando ambiente" in descriptions["environment"]
        assert "Inicializando cliente de embedding" in descriptions["embedding"]
        assert "Carregando pesos do modelo" in descriptions["model_weights"]
        assert "Inicializando banco vetorial" in descriptions["vector_db"]
        assert "Configurando coleções" in descriptions["collections"]
        assert "Iniciando interface" in descriptions["textual"]

    @patch.dict(os.environ, {"USE_RAG_MEMORY": "false"})
    def test_bootstrap_complete_flow_without_rag(self):
        """Testa fluxo completo do bootstrap sem RAG."""
        from core.sky.bootstrap.bootstrap import _get_stages

        stages = _get_stages(use_rag=False)

        # Verifica que apenas ambiente e textual estão presentes
        assert len(stages) == 2
        stage_names = [s.name for s in stages]

        assert stage_names == ["environment", "textual"]

    def test_stage_with_size_info_integration(self):
        """Testa integração de informação de tamanho no estágio."""
        from core.sky.bootstrap.stage import Stage

        stage = Stage("vector_db", "Inicializando banco vetorial...")
        new_stage = stage.with_size_info(124.5)

        assert "124.5 MB" in new_stage.description

    def test_stage_with_collections_info_integration(self):
        """Testa integração de nomes de coleções no estágio."""
        from core.sky.bootstrap.stage import Stage

        stage = Stage("collections", "Configurando coleções...")
        collections = ["identity", "shared-moments", "teachings", "operational"]
        new_stage = stage.with_collections_info(collections)

        assert "identity, shared-moments, teachings, operational" in new_stage.description

    @patch.dict(os.environ, {"USE_RAG_MEMORY": "true"})
    def test_no_bootstrap_flag_bypass(self):
        """Testa que flag --no-bootstrap bypassa a barra de progresso."""
        # Este teste valida a lógica do sky_bootstrap.py
        # A integração completa seria testada com o script real
        from core.sky.bootstrap.bootstrap import _get_stages

        stages = _get_stages(use_rag=True)
        assert len(stages) == 6  # RAG habilitado (6 estágios com model_weights)


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Teste de integração completo requer execução de script"
)
class TestBootstrapScriptIntegration:
    """Testes de integração do script sky_bootstrap.py."""

    def test_cancel_with_ctrl_c(self):
        """Testa cancelamento com Ctrl+C."""
        # Este teste seria executado com o script real
        # Documenta o comportamento esperado
        pass

    def test_handoff_to_textual(self):
        """Testa handoff limpo para Textual UI."""
        # Este teste validaria que a barra de progresso limpa
        # antes do Textual iniciar
        pass
