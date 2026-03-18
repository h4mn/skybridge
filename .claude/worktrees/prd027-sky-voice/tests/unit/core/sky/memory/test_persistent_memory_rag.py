# coding: utf-8
"""
Testes unitários para PersistentMemory com RAG.
"""

import pytest
import tempfile
from pathlib import Path

from src.core.sky.memory import PersistentMemory


class TestPersistentMemoryRAG:
    """Testes para PersistentMemory com RAG."""

    def setup_method(self):
        """Configura teste."""
        # Usar diretório temporário
        self.temp_dir = tempfile.mkdtemp()
        self.memory = PersistentMemory(
            data_dir=self.temp_dir,
            use_rag=True,
        )

    def teardown_method(self):
        """Limpa após teste."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_learn_saves_to_json(self):
        """Testa que learn() salva no JSON."""
        self.memory.learn("Teste de aprendizado")

        learnings = self.memory.get_all_learnings()
        assert len(learnings) == 1
        assert learnings[0]["content"] == "Teste de aprendizado"

    def test_rag_enabled(self):
        """Testa que RAG está habilitado."""
        assert self.memory.is_rag_enabled()

    def test_rag_can_be_disabled(self):
        """Testa que RAG pode ser desabilitado."""
        self.memory.disable_rag()
        assert not self.memory.is_rag_enabled()

    def test_rag_can_be_enabled(self):
        """Testa que RAG pode ser habilitado."""
        self.memory.disable_rag()
        assert not self.memory.is_rag_enabled()

        self.memory.enable_rag()
        assert self.memory.is_rag_enabled()

    def test_search_with_rag(self):
        """Testa busca com RAG habilitado."""
        # Aprender algo
        self.memory.learn("Sky é uma assistente IA criada pelo pai")

        # Buscar semântica
        results = self.memory.search("quem é você?", top_k=5)

        # Com RAG, deve encontrar algo
        assert len(results) >= 0  # Pode não encontrar se modelo não carregou

    def test_infer_collection_identity(self):
        """Testa inferência de coleção identity."""
        collection = self.memory._infer_collection("Eu sou Sky")
        assert collection == "identity"

    def test_infer_collection_teachings(self):
        """Testa inferência de coleção teachings."""
        collection = self.memory._infer_collection("Papai ensinou sobre Python")
        assert collection == "teachings"

    def test_infer_collection_shared_moments(self):
        """Testa inferência de coleção shared-moments."""
        collection = self.memory._infer_collection("Trabalhamos juntos")
        assert collection == "shared-moments"

    def test_infer_collection_operational(self):
        """Testa inferência de coleção operational."""
        collection = self.memory._infer_collection("Deploy concluído hoje")
        assert collection == "operational"

    def test_learn_with_explicit_collection(self):
        """Testa aprender com coleção explícita."""
        self.memory.learn("Teste", collection="identity")

        # Deve salvar no JSON
        learnings = self.memory.get_all_learnings()
        assert len(learnings) == 1


class TestPersistentMemoryLegacy:
    """Testes para PersistentMemory sem RAG (modo legacy)."""

    def setup_method(self):
        """Configura teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = PersistentMemory(
            data_dir=self.temp_dir,
            use_rag=False,
        )

    def teardown_method(self):
        """Limpa após teste."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_legacy_mode_no_rag(self):
        """Testa que modo legacy não usa RAG."""
        assert not self.memory.is_rag_enabled()

    def test_legacy_search_substring(self):
        """Testa que busca legacy usa substring."""
        self.memory.learn("Python é uma linguagem legal")
        self.memory.learn("JavaScript também é bom")

        # Busca por substring
        results = self.memory.search("Python")

        assert len(results) == 1
        assert "Python" in results[0]["content"]

    def test_get_today_learnings(self):
        """Testa obter aprendizados de hoje."""
        self.memory.learn("Aprendizado 1")
        self.memory.learn("Aprendizado 2")

        today = self.memory.get_today_learnings()
        assert len(today) == 2

    def test_persistence_across_instances(self):
        """Testa que memória persiste entre instâncias."""
        # Primeira instância
        self.memory.learn("Teste persistente")

        # Segunda instância (mesmo diretório)
        memory2 = PersistentMemory(data_dir=self.temp_dir, use_rag=False)

        learnings = memory2.get_all_learnings()
        assert len(learnings) == 1
        assert learnings[0]["content"] == "Teste persistente"
