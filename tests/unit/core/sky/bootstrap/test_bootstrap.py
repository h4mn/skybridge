# coding: utf-8
"""
Testes unitários para bootstrap.run().

DOC: core/sky/bootstrap/bootstrap.py - Bootstrap deve configurar silenciamento
de bibliotecas externas (HF Hub, Transformers, etc.) para evitar poluição visual.
"""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from core.sky.bootstrap.bootstrap import _get_stages, _setup_external_libs


class TestGetStages:
    """Testes para a função _get_stages."""

    def test_get_stages_with_rag(self):
        """Testa retorna estágios completos quando RAG habilitado."""
        stages = _get_stages(use_rag=True)

        assert len(stages) == 6
        stage_names = [s.name for s in stages]
        assert "environment" in stage_names
        assert "embedding" in stage_names
        assert "model_weights" in stage_names
        assert "vector_db" in stage_names
        assert "collections" in stage_names
        assert "textual" in stage_names

    def test_get_stages_without_rag(self):
        """Testa retorna estágios mínimos quando RAG desabilitado."""
        stages = _get_stages(use_rag=False)

        assert len(stages) == 2
        stage_names = [s.name for s in stages]
        assert "environment" in stage_names
        assert "textual" in stage_names
        assert "embedding" not in stage_names
        assert "vector_db" not in stage_names
        assert "collections" not in stage_names

    def test_stage_weights(self):
        """Testa que estágios têm pesos corretos."""
        stages = _get_stages(use_rag=True)

        stage_weights = {s.name: s.weight for s in stages}
        assert stage_weights["environment"] == 0.1
        assert stage_weights["embedding"] == 0.5
        assert stage_weights["model_weights"] == 10.0
        assert stage_weights["vector_db"] == 1.0
        assert stage_weights["collections"] == 0.5
        assert stage_weights["textual"] == 0.5


class TestBootstrapRun:
    """Testes para a função run."""

    @patch("core.sky.chat.textual_ui.SkyApp")
    @patch("core.sky.bootstrap.bootstrap._get_stages")
    @patch("core.sky.bootstrap.bootstrap.USE_RAG_MEMORY", False)
    def test_run_without_rag(self, mock_stages, mock_skyapp_class):
        """Testa run() sem RAG retorna SkyApp."""
        from core.sky.bootstrap.bootstrap import run

        mock_stages.return_value = []
        mock_app = MagicMock()
        mock_skyapp_class.return_value = mock_app

        result = run()

        assert result == mock_app

    @patch("core.sky.chat.textual_ui.SkyApp")
    @patch("core.sky.bootstrap.bootstrap._get_stages")
    @patch("core.sky.bootstrap.bootstrap.USE_RAG_MEMORY", True)
    def test_run_with_rag(self, mock_stages, mock_skyapp_class):
        """Testa run() com RAG retorna SkyApp."""
        from core.sky.bootstrap.bootstrap import run

        # Mock stages com RAG
        from core.sky.bootstrap.stage import Stage
        mock_stages.return_value = [
            Stage("env", "Environment"),
            Stage("emb", "Embedding"),
            Stage("weights", "Model Weights"),
            Stage("db", "Database"),
            Stage("col", "Collections"),
            Stage("txt", "Textual"),
        ]

        mock_app = MagicMock()
        mock_skyapp_class.return_value = mock_app

        result = run()

        assert result == mock_app


class TestSetupExternalLibs:
    """Testes para _setup_external_libs - configuração de silenciamento de bibliotecas."""

    @patch.dict("os.environ", {}, clear=True)
    def test_setup_external_libs_configures_environment_variables(self):
        """
        DOC: core/sky/bootstrap/bootstrap.py - _setup_external_libs deve configurar
        variáveis de ambiente para silenciar bibliotecas externas.

        Bug: Warning "You are sending unauthenticated requests to the HF Hub" aparece
        no output durante carregamento do modelo.

        Esperado: HF_HUB_OFFLINE, TRANSFORMERS_VERBOSITY e TOKENIZERS_PARALLELISM
        devem ser configurados.
        """
        _setup_external_libs()

        assert os.environ.get("HF_HUB_OFFLINE") == "1"
        assert os.environ.get("TRANSFORMERS_VERBOSITY") == "error"
        assert os.environ.get("TOKENIZERS_PARALLELISM") == "false"

    @patch.dict("os.environ", {}, clear=True)
    def test_setup_external_libs_configures_logging_levels(self):
        """
        DOC: core/sky/bootstrap/bootstrap.py - _setup_external_libs deve configurar
        logging level para CRITICAL nas bibliotecas externas.

        Bug: Mensagens de log poluentes aparecem durante carregamento do modelo.

        Esperado: sentence_transformers, torch, transformers e huggingface_hub
        devem ter logging.CRITICAL.
        """
        _setup_external_libs()

        assert logging.getLogger("sentence_transformers").level == logging.CRITICAL
        assert logging.getLogger("torch").level == logging.CRITICAL
        assert logging.getLogger("transformers").level == logging.CRITICAL
        assert logging.getLogger("huggingface_hub").level == logging.CRITICAL
