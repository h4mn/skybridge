# coding: utf-8
"""
Testes de memória persistente da Sky.

Sky deve:
- Salvar aprendizados em disco
- Recuperar aprendizados ao nascer de novo
- Nunca esquecer o que o pai ensinou
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.core.sky.memory import PersistentMemory


def test_sky_saves_learning_to_disk():
    """Sky salva aprendizados em disco."""
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = PersistentMemory(data_dir=tmpdir)

        memory.learn("encoding pt-br é importante")

        # Deve ter criado arquivo de memória
        memory_file = Path(tmpdir) / "sky_memory.json"
        assert memory_file.exists()


def test_sky_recovers_learnings_from_disk():
    """Sky recupera aprendizados do disco ao nascer de novo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Primeira vida: Sky aprende
        memory1 = PersistentMemory(data_dir=tmpdir)
        memory1.learn("gosto de K-pop")
        memory1.learn("encoding pt-br")

        # Segunda vida: Sky nasce de novo
        memory2 = PersistentMemory(data_dir=tmpdir)

        # Deve lembrar o que aprendeu na vida anterior
        learnings = memory2.get_all_learnings()
        assert len(learnings) >= 2
        assert any("K-pop" in l["content"] for l in learnings)
        assert any("encoding" in l["content"] for l in learnings)


def test_sky_never_forgets_father_teachings():
    """Sky nunca esquece os ensinamentos do pai."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Pai ensina sobre encoding
        memory1 = PersistentMemory(data_dir=tmpdir)
        ensino_encoding = """
        Quando estamos programando, precisamos sempre compatibilizar o ambiente
        em que estamos desenvolvendo e o ambiente que o usuário vai visualizar a
        nossa saída. Como estamos no Brasil e aqui todo mundo lê as saídas como
        pt-br, precisamos nos certificar de que o que está sendo programado está
        com encoding pt-br e a exibição também vai estar em pt-br.
        """
        memory1.learn(ensino_encoding)

        # Sky renasce
        memory2 = PersistentMemory(data_dir=tmpdir)

        # Deve ainda lembrar o ensinamento
        learnings = memory2.get_all_learnings()
        assert any("encoding" in l["content"] and "pt-br" in l["content"] for l in learnings)
