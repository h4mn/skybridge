# coding: utf-8
"""
Testes unitários para Stage.
"""

import pytest

from core.sky.bootstrap.stage import Stage


class TestStage:
    """Testes para a classe Stage."""

    def test_stage_creation(self):
        """Testa criação de Stage com valores padrão."""
        stage = Stage("test", "Test Stage")

        assert stage.name == "test"
        assert stage.description == "Test Stage"
        assert stage.weight == 1.0

    def test_stage_with_custom_weight(self):
        """Testa criação de Stage com peso customizado."""
        stage = Stage("test", "Test Stage", weight=5.0)

        assert stage.weight == 5.0

    def test_with_size_info_with_size(self):
        """Testa with_size_info com tamanho específico."""
        stage = Stage("test", "Test Stage")
        new_stage = stage.with_size_info(10.5)

        assert new_stage.name == "test"
        assert "(10.5 MB)" in new_stage.description
        assert new_stage.weight == 1.0

    def test_with_size_info_none(self):
        """Testa with_size_info com None (novo)."""
        stage = Stage("test", "Test Stage")
        new_stage = stage.with_size_info(None)

        assert "(novo)" in new_stage.description

    def test_with_size_info_zero(self):
        """Testa with_size_info com tamanho zero."""
        stage = Stage("test", "Test Stage")
        new_stage = stage.with_size_info(0.0)

        assert "(0 MB)" in new_stage.description

    def test_with_collections_info_with_collections(self):
        """Testa with_collections_info com coleções."""
        stage = Stage("test", "Test Stage")
        collections = ["identity", "shared-moments", "teachings", "operational"]
        new_stage = stage.with_collections_info(collections)

        assert "(identity, shared-moments, teachings, operational)" in new_stage.description

    def test_with_collections_info_empty(self):
        """Testa with_collections_info com lista vazia."""
        stage = Stage("test", "Test Stage")
        new_stage = stage.with_collections_info([])

        assert "(criando defaults)" in new_stage.description
