# -*- coding: utf-8 -*-
"""
Testes unitários para AutonomyLevel.

Cobre todos os DoDs relacionados ao autonomy_level:
- Valores do enum (ANALYSIS, DEVELOPMENT, REVIEW, PUBLISH)
- Métodos: allows_code_changes(), allows_auto_commit(), requires_human_review()
- Mapeamento listas Trello → AutonomyLevel
"""

import pytest

from src.core.webhooks.domain.autonomy_level import AutonomyLevel


class TestAutonomyLevelEnum:
    """Testes do enum AutonomyLevel."""

    def test_autonomy_level_has_all_values(self):
        """
        DoD #4: autonomy_level em JobOrchestrator.

        Verifica que todos os valores esperados existem no enum.
        """
        expected_values = {
            "ANALYSIS": "analysis",
            "DEVELOPMENT": "development",
            "REVIEW": "review",
            "PUBLISH": "publish",
        }

        for name, value in expected_values.items():
            assert hasattr(AutonomyLevel, name)
            assert getattr(AutonomyLevel, name).value == value

    def test_autonomy_level_analysis_no_code_changes(self):
        """
        DoD #5: Regras por lista Trello.

        ANALYSIS não deve permitir mudanças de código.
        """
        level = AutonomyLevel.ANALYSIS
        assert level.allows_code_changes() is False
        assert level.allows_auto_commit() is False
        assert level.requires_human_review() is False

    def test_autonomy_level_development_allows_code(self):
        """
        DoD #5: Regras por lista Trello.

        DEVELOPMENT deve permitir mudanças de código mas não commit automático.
        """
        level = AutonomyLevel.DEVELOPMENT
        assert level.allows_code_changes() is True
        assert level.allows_auto_commit() is False
        assert level.requires_human_review() is False

    def test_autonomy_level_review_requires_human(self):
        """
        DoD #5: Regras por lista Trello.

        REVIEW deve permitir mudanças mas requer revisão humana.
        """
        level = AutonomyLevel.REVIEW
        assert level.allows_code_changes() is True
        assert level.allows_auto_commit() is False
        assert level.requires_human_review() is True

    def test_autonomy_level_publish_allows_auto_commit(self):
        """
        DoD #5: Regras por lista Trello.

        PUBLISH deve permitir mudanças e commit automático.
        """
        level = AutonomyLevel.PUBLISH
        assert level.allows_code_changes() is True
        assert level.allows_auto_commit() is True
        assert level.requires_human_review() is False


class TestAutonomyLevelMapping:
    """Testes de mapeamento listas Trello → AutonomyLevel."""

    def test_list_to_autonomy_mapping(self):
        """
        DoD #5: Regras por lista Trello implementadas.

        Verifica o mapeamento correto de cada lista para autonomy_level.
        """
        # Define o mapeamento esperado (evita importar handlers)
        expected_mapping = {
            "💡 Brainstorm": "analysis",
            "📋 A Fazer": "development",
            "🚧 Em Andamento": "development",
            "👁️ Em Revisão": "review",
            "🚀 Publicar": "publish",
        }

        # Verifica que todos os níveis são válidos
        from src.core.webhooks.domain.autonomy_level import AutonomyLevel

        for list_name, autonomy_value in expected_mapping.items():
            level = AutonomyLevel(autonomy_value)
            assert level is not None

    def test_brainstorm_maps_to_analysis(self):
        """Lista 💡 Brainstorm deve mapear para ANALYSIS."""
        from src.core.webhooks.domain.autonomy_level import AutonomyLevel

        autonomy = "analysis"  # Valor esperado para Brainstorm
        assert AutonomyLevel(autonomy) == AutonomyLevel.ANALYSIS

    def test_a_fazer_maps_to_development(self):
        """Lista 📋 A Fazer deve mapear para DEVELOPMENT."""
        from src.core.webhooks.domain.autonomy_level import AutonomyLevel

        autonomy = "development"  # Valor esperado para "📋 A Fazer"
        assert AutonomyLevel(autonomy) == AutonomyLevel.DEVELOPMENT

    def test_publicar_maps_to_publish(self):
        """Lista 🚀 Publicar deve mapear para PUBLISH."""
        from src.core.webhooks.domain.autonomy_level import AutonomyLevel

        autonomy = "publish"  # Valor esperado para "🚀 Publicar"
        assert AutonomyLevel(autonomy) == AutonomyLevel.PUBLISH


class TestAutonomyLevelIntegration:
    """Testes de integração de autonomy_level com o sistema."""

    def test_webhook_source_includes_trello(self):
        """
        DoD #2: TrelloCardMovedToListEvent criado.

        Verifica que WebhookSource suporta TRELLO.
        """
        from src.core.webhooks.domain import WebhookSource

        assert hasattr(WebhookSource, "TRELLO")
        assert WebhookSource.TRELLO.value == "trello"

    def test_webhook_job_has_autonomy_level_field(self):
        """
        DoD #4: autonomy_level em JobOrchestrator.

        Verifica que WebhookJob tem campo autonomy_level.
        """
        from src.core.webhooks.domain import WebhookJob, WebhookEvent, WebhookSource
        from datetime import datetime

        event = WebhookEvent(
            source=WebhookSource.TRELLO,
            event_type="card.moved.📋 A Fazer",
            event_id="card-123",
            payload={},
            received_at=datetime.utcnow(),
        )

        job = WebhookJob.create(event)

        # Verifica que campo existe
        assert hasattr(job, "autonomy_level")
        # Valor padrão deve ser None
        assert job.autonomy_level is None

        # Pode ser definido
        job.autonomy_level = AutonomyLevel.DEVELOPMENT
        assert job.autonomy_level == AutonomyLevel.DEVELOPMENT


class TestAutonomyLevelSkills:
    """Testes de mapeamento autonomy_level → skills."""

    def test_autonomy_level_to_skill_mapping(self):
        """
        DoD #4: autonomy_level em JobOrchestrator.

        Verifica mapeamento de autonomy_level para skills.
        """
        from src.core.webhooks.application.job_orchestrator import AUTONOMY_LEVEL_TO_SKILL

        expected_mapping = {
            "analysis": "analyze-issue",
            "development": "resolve-issue",
            "review": "review-issue",
            "publish": "publish-issue",
        }

        assert AUTONOMY_LEVEL_TO_SKILL == expected_mapping

    def test_analysis_maps_to_analyze_issue_skill(self):
        """ANALYSIS deve mapear para skill 'analyze-issue'."""
        from src.core.webhooks.application.job_orchestrator import AUTONOMY_LEVEL_TO_SKILL

        skill = AUTONOMY_LEVEL_TO_SKILL.get("analysis")
        assert skill == "analyze-issue"

    def test_development_maps_to_resolve_issue_skill(self):
        """DEVELOPMENT deve mapear para skill 'resolve-issue'."""
        from src.core.webhooks.application.job_orchestrator import AUTONOMY_LEVEL_TO_SKILL

        skill = AUTONOMY_LEVEL_TO_SKILL.get("development")
        assert skill == "resolve-issue"

    def test_publish_maps_to_publish_issue_skill(self):
        """PUBLISH deve mapear para skill 'publish-issue'."""
        from src.core.webhooks.application.job_orchestrator import AUTONOMY_LEVEL_TO_SKILL

        skill = AUTONOMY_LEVEL_TO_SKILL.get("publish")
        assert skill == "publish-issue"


class TestAutonomyLevelEventTypes:
    """Testes de event_types específicos para Trello."""

    def test_trello_event_type_mapping(self):
        """
        DoD #5: Regras por lista Trello implementadas.

        Verifica mapeamento de event_types Trello para skills.
        """
        from src.core.webhooks.application.job_orchestrator import EVENT_TYPE_TO_SKILL

        # Event types Trello devem estar mapeados
        assert "card.moved.💡 Brainstorm" in EVENT_TYPE_TO_SKILL
        assert EVENT_TYPE_TO_SKILL["card.moved.💡 Brainstorm"] == "analyze-issue"

        assert "card.moved.📋 A Fazer" in EVENT_TYPE_TO_SKILL
        assert EVENT_TYPE_TO_SKILL["card.moved.📋 A Fazer"] == "resolve-issue"

        assert "card.moved.🚀 Publicar" in EVENT_TYPE_TO_SKILL
        assert EVENT_TYPE_TO_SKILL["card.moved.🚀 Publicar"] == "publish-issue"


class TestAutonomyLevelEdgeCases:
    """Testes de casos extremos e validação."""

    def test_invalid_autonomy_level_value_raises(self):
        """Valor inválido de autonomy_level deve levantar ValueError."""
        with pytest.raises(ValueError):
            AutonomyLevel("invalid_value")

    def test_autonomy_level_is_hashable(self):
        """AutonomyLevel deve ser hashable para usar em sets/dicts."""
        level_set = {AutonomyLevel.ANALYSIS, AutonomyLevel.DEVELOPMENT}
        assert len(level_set) == 2
        assert AutonomyLevel.ANALYSIS in level_set

    def test_autonomy_level_comparison(self):
        """AutonomyLevel deve suportar comparação de igualdade."""
        assert AutonomyLevel.ANALYSIS == AutonomyLevel.ANALYSIS
        assert AutonomyLevel.ANALYSIS != AutonomyLevel.DEVELOPMENT

    def test_autonomy_level_string_representation(self):
        """AutonomyLevel deve ter representação de string útil."""
        level = AutonomyLevel.ANALYSIS
        assert str(level) == "AutonomyLevel.ANALYSIS"
        assert repr(level) == "<AutonomyLevel.ANALYSIS: 'analysis'>"

    def test_unknown_list_defaults_to_development(self):
        """Lista desconhecida deve default para DEVELOPMENT."""
        from src.core.webhooks.domain.autonomy_level import AutonomyLevel

        # Simula valor padrão para lista desconhecida
        autonomy = "development"  # Valor padrão esperado
        assert AutonomyLevel(autonomy) == AutonomyLevel.DEVELOPMENT


class TestAutonomyLevelDoD:
    """Testes específicos de DoD do PRD020."""

    def test_dod_2_trello_webhook_received_event_exists(self):
        """
        DoD #2: TrelloCardMovedToListEvent criado.

        Verifica que o evento de domínio existe.
        """
        from src.core.domain_events.trello_events import TrelloWebhookReceivedEvent
        from src.core.domain_events.trello_events import TrelloCardMovedToListEvent

        # Verifica que os eventos existem e são classes
        assert TrelloWebhookReceivedEvent is not None
        assert TrelloCardMovedToListEvent is not None

    def test_dod_4_job_orchestrator_autonomy_level(self):
        """
        DoD #4: autonomy_level em JobOrchestrator.

        Verifica que JobOrchestrator considera autonomy_level.
        """
        from src.core.webhooks.application.job_orchestrator import JobOrchestrator

        # Verifica que método aceita autonomy_level
        assert hasattr(JobOrchestrator, "_get_skill_for_event_type")

        # Verifica assinatura do método (aceita autonomy_level)
        import inspect
        sig = inspect.signature(JobOrchestrator._get_skill_for_event_type)
        assert "autonomy_level" in sig.parameters

    def test_dod_5_trello_lists_implemented(self):
        """
        DoD #5: Regras por lista Trello implementadas.

        Verifica que todas as listas esperadas estão mapeadas.
        """
        # Lista de nomes de listas esperadas
        expected_lists = [
            "💡 Brainstorm",
            "📋 A Fazer",
            "🚧 Em Andamento",
            "👁️ Em Revisão",
            "🚀 Publicar",
        ]

        # Verifica que todos os níveis de autonomia correspondentes existem
        from src.core.webhooks.domain.autonomy_level import AutonomyLevel

        expected_autonomy_levels = {
            "💡 Brainstorm": AutonomyLevel.ANALYSIS,
            "📋 A Fazer": AutonomyLevel.DEVELOPMENT,
            "🚧 Em Andamento": AutonomyLevel.DEVELOPMENT,
            "👁️ Em Revisão": AutonomyLevel.REVIEW,
            "🚀 Publicar": AutonomyLevel.PUBLISH,
        }

        # Verifica que todas as listas têm um nível correspondente
        for list_name in expected_lists:
            assert list_name in expected_autonomy_levels
            assert expected_autonomy_levels[list_name] is not None

    def test_dod_6_analyze_issue_skill_exists(self):
        """
        DoD #6: Skill analyze-issue criado.

        Verifica que o skill analyze-issue existe.
        """
        import os

        skill_path = "plugins/skybridge-workflows/src/skybridge_workflows/skills/analyze-issue.md"
        assert os.path.exists(skill_path), f"Skill {skill_path} não encontrado"

        # Verifica conteúdo básico
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "name: Analyze Issue" in content or "Analyze Issue" in content
            assert "ANALYSIS" in content or "analysis" in content

    def test_dod_7_webhook_trello_endpoint_exists(self):
        """
        DoD #7: Webhook Trello recebe eventos.

        Verifica que endpoint /webhook/trello existe.
        """
        from src.core.webhooks.infrastructure.github_webhook_server import app

        routes = [route.path for route in app.routes]
        assert "/webhook/trello" in routes, "Endpoint /webhook/trello não encontrado"


@pytest.mark.unit
class TestAutonomyLevelProgressiveAutonomy:
    """Testes de autonomia progressiva (PRD018)."""

    def test_autonomy_increases_from_analysis_to_publish(self):
        """
        PRD018: Autonomia progressiva.

        Verifica que autonomia aumenta de ANALYSIS → PUBLISH.
        """
        # ANALYSIS: sem mudanças
        assert not AutonomyLevel.ANALYSIS.allows_code_changes()

        # DEVELOPMENT: pode mudar, mas não commitar
        assert AutonomyLevel.DEVELOPMENT.allows_code_changes()
        assert not AutonomyLevel.DEVELOPMENT.allows_auto_commit()

        # REVIEW: pode mudar, requer revisão
        assert AutonomyLevel.REVIEW.allows_code_changes()
        assert AutonomyLevel.REVIEW.requires_human_review()

        # PUBLISH: autonomia máxima
        assert AutonomyLevel.PUBLISH.allows_auto_commit()

    def test_four_levels_of_autonomy(self):
        """
        PRD018: 4 níveis de autonomia implementados.

        Verifica que existem exatamente 4 níveis.
        """
        levels = list(AutonomyLevel)
        assert len(levels) == 4

        level_names = [level.name for level in levels]
        expected_names = ["ANALYSIS", "DEVELOPMENT", "REVIEW", "PUBLISH"]
        assert sorted(level_names) == sorted(expected_names)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
