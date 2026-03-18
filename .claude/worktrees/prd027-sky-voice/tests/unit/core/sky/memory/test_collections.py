# coding: utf-8
"""
Testes unitários para CollectionManager e CollectionConfig.
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.core.sky.memory.collections import (
    CollectionConfig,
    CollectionManager,
    SourceType,
    DEFAULT_COLLECTIONS,
)


class TestCollectionConfig:
    """Testes para CollectionConfig."""

    def test_is_permanent(self):
        """Testa detecção de coleção permanente."""
        config = CollectionConfig(
            name="test",
            purpose="Test",
            retention_days=None,
        )
        assert config.is_permanent

    def test_is_not_permanent(self):
        """Testa detecção de coleção temporária."""
        config = CollectionConfig(
            name="test",
            purpose="Test",
            retention_days=30,
        )
        assert not config.is_permanent

    def test_expiration_date_permanent(self):
        """Testa data de expiração para coleção permanente."""
        config = CollectionConfig(
            name="test",
            purpose="Test",
            retention_days=None,
        )
        assert config.expiration_date(datetime.now()) is None

    def test_expiration_date_temporary(self):
        """Testa data de expiração para coleção temporária."""
        config = CollectionConfig(
            name="test",
            purpose="Test",
            retention_days=30,
        )

        now = datetime.now()
        expiration = config.expiration_date(now)

        assert expiration is not None
        expected = now + timedelta(days=30)
        assert abs((expiration - expected).total_seconds()) < 1  # < 1 segundo de diferença


class TestSourceType:
    """Testes para SourceType."""

    def test_values(self):
        """Testa valores do enum."""
        assert SourceType.CHAT.value == "chat"
        assert SourceType.CODE.value == "code"
        assert SourceType.DOCS.value == "docs"
        assert SourceType.LOGS.value == "logs"
        assert SourceType.USER.value == "user"
        assert SourceType.DEMO.value == "demo"


class TestCollectionManager:
    """Testes para CollectionManager."""

    def setup_method(self):
        """Configura teste."""
        # Usar banco em memória para testes
        import tempfile
        self.db_path = tempfile.mktemp(suffix=".db")
        self.manager = CollectionManager(db_path=Path(self.db_path))

    def teardown_method(self):
        """Limpa após teste."""
        import os
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

    def test_list_collections(self):
        """Testa listar coleções."""
        collections = self.manager.list_collections()

        # Deve ter as 4 coleções padrão
        assert len(collections) >= 4
        collection_names = {c.name for c in collections}
        assert "identity" in collection_names
        assert "shared-moments" in collection_names
        assert "teachings" in collection_names
        assert "operational" in collection_names

    def test_get_collection(self):
        """Testa obter coleção específica."""
        config = self.manager.get_collection("identity")

        assert config is not None
        assert config.name == "identity"
        assert config.is_permanent

    def test_get_collection_not_found(self):
        """Testa obter coleção inexistente."""
        config = self.manager.get_collection("inexistente")
        assert config is None

    def test_get_collection_stats(self):
        """Testa estatísticas de coleção."""
        stats = self.manager.get_collection_stats("identity")

        assert "count" in stats
        assert "oldest" in stats
        assert "newest" in stats
        assert stats["count"] >= 0


class TestDefaultCollections:
    """Testes para coleções padrão."""

    def test_default_collections_exist(self):
        """Testa que coleções padrão estão definidas."""
        assert len(DEFAULT_COLLECTIONS) >= 4

        names = {c.name for c in DEFAULT_COLLECTIONS}
        assert "identity" in names
        assert "shared-moments" in names
        assert "teachings" in names
        assert "operational" in names

    def test_identity_permanent(self):
        """Testa que coleção identity é permanente."""
        identity = next(c for c in DEFAULT_COLLECTIONS if c.name == "identity")
        assert identity.is_permanent

    def test_operational_temporary(self):
        """Testa que coleção operational é temporária."""
        operational = next(c for c in DEFAULT_COLLECTIONS if c.name == "operational")
        assert not operational.is_permanent
        assert operational.retention_days == 30
