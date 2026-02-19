# -*- coding: utf-8 -*-
"""
Testes TDD para KanbanInitializer (PRD026 Fase 2).

Metodologia: TDD Estrito (PRD023)
- Testes escritos ANTES da implementação
- Testes falham primeiro (RED)
- Implementação mínima para passar (GREEN)
- Refatoração mantendo verde (REFACTOR)

DOC: tests/integration/kanban/test_kanban_initializer.py
DOC: core/kanban/application/kanban_initializer.py
"""

import tempfile
from pathlib import Path

import pytest

from core.kanban.application.kanban_initializer import KanbanInitializer


@pytest.fixture
def temp_db_dir():
    """Cria diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# =============================================================================
# TESTES: Auto-inicialização do kanban.db (PRD026 Fase 2)
# =============================================================================


def test_kanban_initializer_deve_criar_board_e_listas(temp_db_dir):
    """
    DOC: PRD026 RF-004/005 - KanbanInitializer deve criar board e listas padrão

    Given: kanban.db não existe
    When: KanbanInitializer.initialize() é chamado
    Then: Deve criar board-1 e 6 listas padrão (Issues, Brainstorm, A Fazer, Em Andamento, Em Revisão, Publicar)
    """
    # Given: kanban.db não existe
    db_path = temp_db_dir / "kanban.db"
    assert not db_path.exists()

    # When: KanbanInitializer é executado
    initializer = KanbanInitializer(db_path)
    initializer.initialize()

    # Then: kanban.db foi criado
    assert db_path.exists()

    # And: Board padrão existe
    boards_result = initializer.adapter.list_boards()
    assert boards_result.is_ok
    boards = boards_result.value
    assert len(boards) >= 1
    assert boards[0].name == "Skybridge"

    # And: 6 listas padrão existem
    lists_result = initializer.adapter.list_lists(boards[0].id)
    assert lists_result.is_ok
    lists = lists_result.value
    list_names = {lst.name for lst in lists}

    expected_lists = {"Issues", "Brainstorm", "A Fazer", "Em Andamento", "Em Revisão", "Publicar"}
    assert expected_lists.issubset(list_names), f"Faltam listas: {expected_lists - list_names}"

    initializer.disconnect()


def test_kanban_initializer_nao_recria_se_ja_existir(temp_db_dir):
    """
    DOC: PRD026 RF-004 - KanbanInitializer não deve recriar se já existe

    Given: kanban.db já existe com board e listas
    When: KanbanInitializer.initialize() é chamado novamente
    Then: Não deve recriar board/listas (idempotente)
    """
    # Given: kanban.db já existe
    db_path = temp_db_dir / "kanban.db"

    # Primeira inicialização
    initializer1 = KanbanInitializer(db_path)
    initializer1.initialize()

    # Guarda IDs criados ANTES de desconectar
    boards_result = initializer1.adapter.list_boards()
    original_board_id = boards_result.value[0].id
    original_board_name = boards_result.value[0].name

    initializer1.disconnect()

    # When: Segunda inicialização
    initializer2 = KanbanInitializer(db_path)
    initializer2.initialize()

    # Then: Board original ainda existe (não foi recriado)
    boards_result = initializer2.adapter.list_boards()
    assert boards_result.is_ok
    boards = boards_result.value
    assert len(boards) >= 1
    # Verifica pelo ID e nome
    assert boards[0].id == original_board_id
    assert boards[0].name == original_board_name

    initializer2.disconnect()


def test_kanban_initializer_cria_listas_com_posicoes_corretas(temp_db_dir):
    """
    DOC: PRD026 RF-005 - Listas devem ter posições 0-5

    Given: kanban.db não existe
    When: KanbanInitializer.initialize() é chamado
    Then: Listas devem ter posições 0-5 na ordem correta
    """
    # Given: kanban.db não existe
    db_path = temp_db_dir / "kanban.db"

    # When: KanbanInitializer é executado
    initializer = KanbanInitializer(db_path)
    initializer.initialize()

    # Then: Listas têm posições corretas
    boards_result = initializer.adapter.list_boards()
    board_id = boards_result.value[0].id

    lists_result = initializer.adapter.list_lists(board_id)
    lists = lists_result.value

    # Verifica posições
    expected_positions = {
        "Issues": 0,
        "Brainstorm": 1,
        "A Fazer": 2,
        "Em Andamento": 3,
        "Em Revisão": 4,
        "Publicar": 5,
    }

    for lst in lists:
        if lst.name in expected_positions:
            assert lst.position == expected_positions[lst.name], \
                f"Lista '{lst.name}' tem posição {lst.position}, esperava {expected_positions[lst.name]}"

    initializer.disconnect()
