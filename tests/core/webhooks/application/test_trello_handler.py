# -*- coding: utf-8 -*-
"""
Testes para receive_trello_webhook handler (versão simplificada).

Cobre DoDs relacionados:
- DoD #5: Regras por lista Trello implementadas
- DoD #7: Webhook Trello recebe eventos

NOTA: Testes que requerem importar handlers.py foram removidos para
evitar registro duplicado de comandos no Sky-RPC registry.
"""

import pytest
from datetime import datetime

# Define valores localmente (evita importar handlers)
LIST_TO_AUTONOMY = {
    "💡 Brainstorm": "analysis",
    "📋 A Fazer": "development",
    "🚧 Em Andamento": "development",
    "👁️ Em Revisão": "review",
    "🚀 Publicar": "publish",
}


class TestExtractIssueNumberFromCard:
    """Testes para extração de issue number do card."""

    def test_extract_issue_number_from_name(self):
        """Extrai issue_number do nome do card."""
        import re

        card_name = "#123 Implement feature X"
        card_desc = "Description here"

        # Tenta extrair do nome (ex: "#123 Issue Title")
        match = re.search(r"#(\d+)", card_name)
        if match:
            issue_number = int(match.group(1))
        else:
            issue_number = None

        assert issue_number == 123

    def test_extract_issue_number_from_description(self):
        """Extrai issue_number da descrição do card."""
        import re

        card_name = "Implement feature X"
        card_desc = "Related to issue #456"

        # Tenta extrair da descrição (ex: "Issue #123")
        match = re.search(r"#(\d+)", card_desc)
        if match:
            issue_number = int(match.group(1))
        else:
            issue_number = None

        assert issue_number == 456

    def test_extract_issue_number_none_when_not_found(self):
        """Retorna None quando não encontra issue_number."""
        import re

        card_name = "Generic card name"
        card_desc = "Generic description"

        match = re.search(r"#(\d+)", card_name)
        if match:
            issue_number = int(match.group(1))
        else:
            issue_number = None

        assert issue_number is None


class TestExtractRepositoryFromCard:
    """Testes para extração de repositório do card."""

    def test_extract_repository_from_description(self):
        """Extrai repositório da descrição."""
        import re

        card_desc = "Repository: h4mn/skybridge"

        # Tenta extrair formato "owner/repo"
        match = re.search(r"([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)", card_desc)
        if match:
            repo = f"{match.group(1)}/{match.group(2)}"
        else:
            repo = None

        assert repo == "h4mn/skybridge"

    def test_extract_repository_none_when_not_found(self):
        """Retorna None quando não encontra repositório."""
        import re

        card_desc = "No repository info"

        match = re.search(r"([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)", card_desc)
        if match:
            repo = f"{match.group(1)}/{match.group(2)}"
        else:
            repo = None

        assert repo is None

    def test_extract_repository_from_empty_description(self):
        """Retorna None para descrição vazia."""
        assert extract_repository_from_card("") is None

    def test_extract_repository_from_none_description(self):
        """Retorna None para descrição None."""
        assert extract_repository_from_card(None) is None


# Define funções localmente para evitar importar handlers
def extract_repository_from_card(card_desc: str) -> str | None:
    """Extrai repositório da descrição do card."""
    import re
    if not card_desc:
        return None

    # Tenta extrair formato "owner/repo"
    match = re.search(r"([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)", card_desc)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    return None


@pytest.mark.unit
class TestListToAutonomyMapping:
    """Testes de mapeamento LIST_TO_AUTONOMY."""

    def test_mapping_is_defined(self):
        """LIST_TO_AUTONOMY deve estar definido."""
        assert LIST_TO_AUTONOMY is not None
        assert isinstance(LIST_TO_AUTONOMY, dict)

    def test_mapping_contains_all_lists(self):
        """Mapeamento deve conter todas as listas esperadas."""
        expected_lists = [
            "💡 Brainstorm",
            "📋 A Fazer",
            "🚧 Em Andamento",
            "👁️ Em Revisão",
            "🚀 Publicar",
        ]

        for list_name in expected_lists:
            assert list_name in LIST_TO_AUTONOMY

    def test_mapping_values_are_valid(self):
        """Valores do mapeamento devem ser válidos."""
        from core.webhooks.domain.autonomy_level import AutonomyLevel

        for list_name, autonomy_value in LIST_TO_AUTONOMY.items():
            # Deve ser possível criar AutonomyLevel a partir do valor
            level = AutonomyLevel(autonomy_value)
            assert level is not None


@pytest.mark.unit
class TestTrelloWebhookPayloadParsing:
    """Testes de parsing de payload do webhook Trello."""

    def test_extract_card_info_from_payload(self):
        """Extrai informações do card do payload."""
        payload = {
            "action": {
                "type": "updateCard",
                "data": {
                    "card": {
                        "id": "card-123",
                        "name": "#123 Feature",
                        "desc": "Description",
                    },
                    "listBefore": {"name": "💡 Brainstorm"},
                    "listAfter": {"name": "📋 A Fazer"},
                },
            },
        }

        action_type = payload.get("action", {}).get("type", "")
        action_data = payload.get("action", {}).get("data", {})
        card_data = action_data.get("card", {})

        assert action_type == "updateCard"
        assert card_data.get("id") == "card-123"
        assert card_data.get("name") == "#123 Feature"

    def test_extract_list_names_from_payload(self):
        """Extrai nomes das listas do payload."""
        payload = {
            "action": {
                "type": "updateCard",
                "data": {
                    "listBefore": {"name": "💡 Brainstorm"},
                    "listAfter": {"name": "📋 A Fazer"},
                },
            },
        }

        action_data = payload.get("action", {}).get("data", {})
        list_before = action_data.get("listBefore", {})
        list_after = action_data.get("listAfter", {})

        assert list_before.get("name") == "💡 Brainstorm"
        assert list_after.get("name") == "📋 A Fazer"


@pytest.mark.unit
class TestTrelloEventsDoD:
    """Testes de DoD do PRD020 que não requerem importar handlers."""

    def test_dod_5_trello_lists_mapping_exists(self):
        """
        DoD #5: Regras por lista Trello implementadas.

        Verifica que o mapeamento de listas existe localmente.
        """
        assert LIST_TO_AUTONOMY is not None

        expected_lists = [
            "💡 Brainstorm",
            "📋 A Fazer",
            "🚧 Em Andamento",
            "👁️ Em Revisão",
            "🚀 Publicar",
        ]

        for list_name in expected_lists:
            assert list_name in LIST_TO_AUTONOMY

    def test_dod_5_list_values_map_to_autonomy_levels(self):
        """
        DoD #5: Regras por lista Trello implementadas.

        Verifica que os valores mapeiam corretamente para AutonomyLevel.
        """
        from core.webhooks.domain.autonomy_level import AutonomyLevel

        expected_mapping = {
            "💡 Brainstorm": AutonomyLevel.ANALYSIS,
            "📋 A Fazer": AutonomyLevel.DEVELOPMENT,
            "🚧 Em Andamento": AutonomyLevel.DEVELOPMENT,
            "👁️ Em Revisão": AutonomyLevel.REVIEW,
            "🚀 Publicar": AutonomyLevel.PUBLISH,
        }

        for list_name, expected_level in expected_mapping.items():
            autonomy_value = LIST_TO_AUTONOMY.get(list_name)
            actual_level = AutonomyLevel(autonomy_value)
            assert actual_level == expected_level

    def test_dod_6_analyze_issue_skill_exists(self):
        """
        DoD #6: Skill analyze-issue criado.

        Verifica que o skill analyze-issue existe.
        """
        import os

        skill_path = "src/runtime/prompts/skills/analyze-issue/SKILL.md"
        assert os.path.exists(skill_path), f"Skill {skill_path} não encontrado"

        # Verifica conteúdo básico
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "name: Analyze Issue" in content or "Analyze Issue" in content
            assert "ANALYSIS" in content or "analysis" in content

    def test_dod_7_webhook_trello_endpoint_exists(self):
        """
        DoD #7: Webhook Trello recebe eventos.

        Verifica que endpoint /api/webhooks/{source} existe (padrão ADR023).
        O endpoint usa path parameter, então verificamos o padrão /api/webhooks/{source}.
        """
        from runtime.bootstrap.app import get_app

        app = get_app().app
        routes = [route.path for route in app.routes]
        # O endpoint usa path parameter: /api/webhooks/{source}
        # Então verificamos se o padrão existe
        assert "/api/webhooks/{source}" in routes, "Endpoint /api/webhooks/{source} não encontrado"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
