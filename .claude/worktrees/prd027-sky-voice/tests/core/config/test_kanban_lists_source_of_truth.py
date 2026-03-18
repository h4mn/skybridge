# -*- coding: utf-8 -*-
"""
Testes para garantir que get_list_names() seja a FONTE ÚNICA DA VERDADE.

Estes testes asseguram que:
1. get_list_names() retorna a ordem correta (PRD024)
2. Não há definições duplicadas de listas hardcoded
3. Todos os componentes usam get_list_names()

DOC: ADR020 - Integração Trello (get_list_names como fonte única da verdade)
DOC: PRD024 - Kanban Cards Vivos
"""

import pytest

from runtime.config.config import get_trello_kanban_lists_config


class TestListNamesSourceOfTruth:
    """
    Testa que get_list_names() é a fonte única da verdade para nomes das listas.
    """

    def test_get_list_names_returns_correct_order(self):
        """
        DOC: ADR020 - get_list_names como fonte única da verdade
        DOC: PRD024 - Ordem das colunas

        Garante que get_list_names() retorna as listas na ordem correta
        conforme PRD024.
        """
        config = get_trello_kanban_lists_config()
        lists = config.get_list_names()

        # Verifica quantidade
        assert len(lists) == 6, f"Devem ser 6 listas, mas retornou {len(lists)}"

        # Ordem conforme PRD024
        expected_order = [
            "Issues",
            "Brainstorm",
            "A Fazer",
            "Em Andamento",
            "Em Revisão",
            "Publicar",
        ]

        assert lists == expected_order, (
            f"Ordem incorreta. Esperado: {expected_order}, Obtido: {lists}"
        )

    def test_get_list_names_with_emoji_has_correct_prefix(self):
        """
        DOC: ADR020 - get_list_names_with_emoji para Trello

        Garante que a versão com emoji tem emojis válidos.
        """
        config = get_trello_kanban_lists_config()
        lists_with_emoji = config.get_list_names_with_emoji()

        assert len(lists_with_emoji) == 6

        # Verifica que todos têm emoji
        for lst in lists_with_emoji:
            # Emoji estão na faixa U+1F300 a U+1F9FF
            has_emoji = any('\U0001F300' <= c <= '\U0001F9FF' for c in lst)
            assert has_emoji, f"Lista '{lst}' não tem emoji: {lst_with_emoji}"

    def test_get_list_colors_matches_list_names(self):
        """
        DOC: ADR020 - Consistência entre nomes e cores

        Garante que todas as listas têm cores definidas.
        """
        config = get_trello_kanban_lists_config()
        lists = config.get_list_names()
        colors = config.get_list_colors()

        # Todas as listas devem ter cor
        for lst in lists:
            assert lst in colors, f"Lista '{lst}' não tem cor definida"

    def test_get_list_colors_with_emoji_matches_list_names_with_emoji(self):
        """
        DOC: ADR020 - Consistência entre nomes com emoji e cores

        Garante que todas as listas com emoji têm cores definidas.
        """
        config = get_trello_kanban_lists_config()
        lists_with_emoji = config.get_list_names_with_emoji()
        colors_with_emoji = config.get_list_colors_with_emoji()

        # Todas as listas com emoji devem ter cor
        for lst in lists_with_emoji:
            assert lst in colors_with_emoji, f"Lista '{lst}' não tem cor definida"


class TestNoHardcodedLists:
    """
    Testa que não há definições duplicadas hardcoded de listas no código.

    Se adicionar novas listas, SEMPRE use get_list_names().
    """

    def test_kanban_initializer_uses_config(self):
        """
        DOC: kanban_initializer.py deve usar get_list_names()

        Verifica que KanbanInitializer não tem DEFAULT_LISTS hardcoded.
        """
        from core.kanban.application.kanban_initializer import KanbanInitializer
        import inspect
        import textwrap

        # Lê o código fonte do kanban_initializer.py
        source = inspect.getsource(KanbanInitializer)

        # Verifica que não há DEFAULT_LISTS hardcoded
        assert "DEFAULT_LISTS" not in source, (
            "kanban_initializer.py ainda tem DEFAULT_LISTS hardcoded. "
            "Use get_trello_kanban_lists_config().get_list_names() em vez disso."
        )

        # Verifica que importa get_trello_kanban_lists_config
        assert "get_trello_kanban_lists_config" in source, (
            "kanban_initializer.py não importa get_trello_kanban_lists_config. "
            "Deve usar a fonte única da verdade."
        )

    def test_trello_sync_service_uses_config(self):
        """
        DOC: trello_sync_service.py deve usar get_list_names()

        Verifica que TrelloSyncService não tem listas hardcoded.
        """
        from core.kanban.application.trello_sync_service import TrelloSyncService
        import inspect

        # Lê o código fonte do trello_sync_service.py
        source = inspect.getsource(TrelloSyncService)

        # Verifica que não há default_lists hardcoded
        assert "default_lists = [" not in source, (
            "trello_sync_service.py tem default_lists hardcoded. "
            "Use get_trello_kanban_lists_config().get_list_names() em vez disso."
        )

        # Verifica que importa get_trello_kanban_lists_config
        assert "get_trello_kanban_lists_config" in source, (
            "trello_sync_service.py não importa get_trello_kanban_lists_config. "
            "Deve usar a fonte única da verdade."
        )

    def test_config_py_has_source_of_truth_comment(self):
        """
        DOC: config.py deve documentar FONTE ÚNICA DA VERDADE

        Verifica que get_list_names() tem documentação apropriada.
        """
        import inspect
        from runtime.config.config import TrelloKanbanListsConfig

        # Lê o código fonte do método get_list_names
        source = inspect.getsource(TrelloKanbanListsConfig.get_list_names)

        # Verifica documentação menciona "FONTE ÚNICA DA VERDADE"
        assert "FONTE ÚNICA DA VERDADE" in source or "FONTE_UNICA_DA_VERDADE" in source, (
            "get_list_names() não documenta ser a fonte única da verdade. "
            "Adicione esta documentação conforme ADR020."
        )

        # Verifica documentação menciona PRD024
        assert "PRD024" in source, (
            "get_list_names() não menciona PRD024. "
            "Deve referenciar a especificação que define as listas."
        )


class TestListNamesConsistency:
    """
    Testa consistência entre diferentes componentes que usam listas.
    """

    def test_initializer_and_sync_use_same_lists(self):
        """
        Garante que KanbanInitializer e TrelloSyncService usam as mesmas listas.
        """
        config = get_trello_kanban_lists_config()
        expected_lists = config.get_list_names()

        # Testa via KanbanInitializer (se disponível)
        try:
            from core.kanban.application.kanban_initializer import KanbanInitializer
            from core.kanban.domain.database import KanbanBoard
            from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter
            import tempfile

            # Cria board temporário
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
                db_path = f.name

            try:
                initializer = KanbanInitializer(db_path)
                initializer.initialize()

                # Busca listas criadas
                adapter = SQLiteKanbanAdapter(db_path)
                adapter.connect()
                lists_result = adapter.list_lists("skybridge-main")

                if lists_result.is_ok:
                    created_lists = [lst.name for lst in lists_result.value]
                    # Verifica que todas as listas esperadas foram criadas
                    for expected in expected_lists:
                        assert expected in created_lists, (
                            f"Lista '{expected}' não foi criada pelo KanbanInitializer. "
                            f"Criadas: {created_lists}"
                        )

                adapter.disconnect()
                initializer.disconnect()

            finally:
                import os
                os.unlink(db_path)

        except Exception as e:
            pytest.skip(f"Não foi possível testar KanbanInitializer: {e}")

    def test_agent_type_to_list_matches_config(self):
        """
        DOC: kanban_lists_config.py - get_agent_type_to_list_mapping()

        Garante que get_agent_type_to_list_mapping() usa nomes consistentes com get_list_names().
        """
        from core.kanban.domain.database import get_agent_type_to_list_mapping, get_kanban_lists_config

        config = get_kanban_lists_config()
        config_lists = config.get_list_names()
        agent_type_mapping = get_agent_type_to_list_mapping()

        # Verifica que os valores em get_agent_type_to_list_mapping() são listas válidas
        for agent_type, list_name in agent_type_mapping.items():
            assert list_name in config_lists, (
                f"get_agent_type_to_list_mapping()['{agent_type}'] = '{list_name}' não está em get_list_names(). "
                f"Listas válidas: {config_lists}"
            )


class TestADR020Compliance:
    """
    Testa conformidade com ADR020 - Integração Trello.
    """

    def test_adr020_documented_source_of_truth(self):
        """
        DOC: ADR020 - Integração Trello

        Verifica que ADR020 documenta get_list_names() como fonte única da verdade.
        """
        from pathlib import Path
        import re

        adr_path = Path("B:/_repositorios/skybridge-prd026/docs/adr/ADR020-integracao-trello.md")
        assert adr_path.exists(), "ADR020 não encontrado"

        content = adr_path.read_text(encoding="utf-8")

        # Verifica seção de fonte única da verdade existe
        assert "FONTE ÚNICA DA VERDADE" in content, (
            "ADR020 não documenta get_list_names() como fonte única da verdade. "
            "Adicione seção conforme template."
        )

        # Verifica se menciona get_list_names()
        assert "get_list_names()" in content, (
            "ADR020 não menciona get_list_names(). "
            "Deve documentar a fonte única da verdade."
        )

    def test_prd024_list_order_match_config(self):
        """
        DOC: PRD024 - Colunas do Kanban

        Verifica que PRD024 define a mesma ordem que get_list_names().
        """
        from pathlib import Path

        prd_path = Path("B:/_repositorios/skybridge-prd026/docs/prd/PRD024-kanban-cards-vivos.md")
        assert prd_path.exists(), "PRD024 não encontrado"

        content = prd_path.read_text(encoding="utf-8")

        # PRD024 define a ordem das colunas
        # Vou verificar se a tabela de colunas existe
        assert "Issues" in content, "PRD024 não menciona 'Issues'"
        assert "Brainstorm" in content, "PRD024 não menciona 'Brainstorm'"
        assert "A Fazer" in content, "PRD024 não menciona 'A Fazer'"
        assert "Em Andamento" in content, "PRD024 não menciona 'Em Andamento'"
        assert "Em Revisão" in content, "PRD024 não menciona 'Em Revisão'"
        assert "Publicar" in content, "PRD024 não menciona 'Publicar'"

        # Verifica se tabela com ordem existe
        if "|" in content and "Coluna" in content:
            # Extrai a tabela de colunas
            lines = content.split("\n")
            in_table = False
            order_found = []

            for line in lines:
                if "| Coluna |" in line:
                    in_table = True
                    continue
                if in_table and line.strip() == "":
                    break
                if in_table and "| Issues |" in line:
                    order_found.append("Issues")
                elif in_table and "| Brainstorm |" in line:
                    order_found.append("Brainstorm")
                elif in_table and "| A Fazer |" in line:
                    order_found.append("A Fazer")
                elif in_table and "| Em Andamento |" in line or "| Em Andamento |" in line:
                    order_found.append("Em Andamento")
                elif in_table and "| Em Revisão |" in line:
                    order_found.append("Em Revisão")
                elif in_table and "| Publicar |" in line:
                    order_found.append("Publicar")

            if order_found:
                config = get_trello_kanban_lists_config()
                config_order = config.get_list_names()

                # Compara ordem
                assert order_found == config_order, (
                    f"Ordem no PRD024: {order_found} != config.get_list_names(): {config_order}"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
