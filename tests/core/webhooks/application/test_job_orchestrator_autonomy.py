# -*- coding: utf-8 -*-
"""
Testes para JobOrchestrator com autonomy_level.

Cobre DoDs relacionados:
- DoD #4: autonomy_level em JobOrchestrator
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.webhooks.application.job_orchestrator import (
    JobOrchestrator,
)
from core.webhooks.domain.trigger_mappings import (
    EVENT_TYPE_TO_SKILL,
    AUTONOMY_LEVEL_TO_SKILL,
)
from core.webhooks.domain import (
    WebhookJob,
    WebhookEvent,
    WebhookSource,
    AutonomyLevel,
    JobStatus,
)


class TestAutonomyLevelToSkillMapping:
    """Testes de mapeamento autonomy_level → skills."""

    def test_mapping_exists(self):
        """AUTONOMY_LEVEL_TO_SKILL deve estar definido."""
        assert AUTONOMY_LEVEL_TO_SKILL is not None
        assert isinstance(AUTONOMY_LEVEL_TO_SKILL, dict)

    def test_mapping_contains_all_levels(self):
        """Mapeamento deve conter todos os níveis de autonomia."""
        expected_levels = ["analysis", "development", "review", "publish"]

        for level in expected_levels:
            assert level in AUTONOMY_LEVEL_TO_SKILL

    def test_analysis_maps_to_analyze_issue(self):
        """ANALYSIS deve mapear para 'analyze-issue'."""
        assert AUTONOMY_LEVEL_TO_SKILL.get("analysis") == "analyze-issue"

    def test_development_maps_to_resolve_issue(self):
        """DEVELOPMENT deve mapear para 'resolve-issue'."""
        assert AUTONOMY_LEVEL_TO_SKILL.get("development") == "resolve-issue"

    def test_review_maps_to_none(self):
        """
        REVIEW deve mapear para None.

        PRD020: Em Revisão é revisão humana, não dispara agente.
        """
        assert AUTONOMY_LEVEL_TO_SKILL.get("review") is None

    def test_publish_maps_to_publish_issue(self):
        """PUBLISH deve mapear para 'publish-issue'."""
        assert AUTONOMY_LEVEL_TO_SKILL.get("publish") == "publish-issue"


class TestJobOrchestratorAutonomyLevel:
    """Testes de JobOrchestrator com autonomy_level."""

    @pytest.fixture
    def mock_orchestrator(self):
        """JobOrchestrator mockado."""
        job_queue = Mock()
        worktree_manager = Mock()
        event_bus = Mock()
        event_bus.publish = AsyncMock()

        return JobOrchestrator(
            job_queue=job_queue,
            worktree_manager=worktree_manager,
            event_bus=event_bus,
            enable_auto_commit=False,
            enable_auto_pr=False,
        )

    def test_get_skill_for_event_type_considers_autonomy_level(self, mock_orchestrator):
        """
        DoD #4: autonomy_level em JobOrchestrator.
        PRD026: issues.opened NÃO dispara agente diretamente.

        _get_skill_for_event_type deve considerar autonomy_level.
        """
        # PRD026: Sem autonomy_level, issues.opened retorna None (não dispara agente)
        skill = JobOrchestrator._get_skill_for_event_type("issues.opened")
        assert skill is None  # PRD026: issue aberta só cria card, não executa agente

        # Com autonomy_level, usa mapeamento específico
        skill = JobOrchestrator._get_skill_for_event_type(
            "issues.opened",
            AutonomyLevel.ANALYSIS
        )
        assert skill == "analyze-issue"

    def test_get_skill_for_event_type_with_analysis(self, mock_orchestrator):
        """ANALYSIS deve retornar 'analyze-issue'."""
        skill = JobOrchestrator._get_skill_for_event_type(
            "issues.opened",
            AutonomyLevel.ANALYSIS
        )
        assert skill == "analyze-issue"

    def test_get_skill_for_event_type_with_development(self, mock_orchestrator):
        """DEVELOPMENT deve retornar 'resolve-issue'."""
        skill = JobOrchestrator._get_skill_for_event_type(
            "issues.opened",
            AutonomyLevel.DEVELOPMENT
        )
        assert skill == "resolve-issue"

    def test_get_skill_for_event_type_with_review(self, mock_orchestrator):
        """
        REVIEW deve retornar None.

        PRD020: Em Revisão é revisão humana, não dispara agente.
        """
        skill = JobOrchestrator._get_skill_for_event_type(
            "issues.opened",
            AutonomyLevel.REVIEW
        )
        assert skill is None

    def test_get_skill_for_event_type_with_publish(self, mock_orchestrator):
        """PUBLISH deve retornar 'publish-issue'."""
        skill = JobOrchestrator._get_skill_for_event_type(
            "issues.opened",
            AutonomyLevel.PUBLISH
        )
        assert skill == "publish-issue"

    def test_get_skill_for_event_type_autonomy_overrides_default(self, mock_orchestrator):
        """
        autonomy_level deve sobrescrever mapeamento padrão.
        PRD026: issues.opened tem padrão None, autonomy_level sobrescreve.
        """
        # PRD026: Padrão para issues.opened é None (não dispara agente)
        default_skill = JobOrchestrator._get_skill_for_event_type("issues.opened")
        assert default_skill is None

        # Com autonomy_level=ANALYSIS, deve sobrescrever para analyze-issue
        override_skill = JobOrchestrator._get_skill_for_event_type(
            "issues.opened",
            AutonomyLevel.ANALYSIS
        )
        assert override_skill == "analyze-issue"
        assert override_skill != default_skill


class TestJobOrchestratorExecuteJobWithAutonomy:
    """Testes de execute_job com autonomy_level."""

    @pytest.fixture
    def sample_job(self):
        """Job de exemplo com autonomy_level."""
        event = WebhookEvent(
            source=WebhookSource.TRELLO,
            event_type="card.moved.📋 A Fazer",
            event_id="card-123",
            payload={},
            received_at=datetime.utcnow(),
        )

        job = WebhookJob.create(event)
        job.autonomy_level = AutonomyLevel.DEVELOPMENT
        return job

    def test_job_has_autonomy_level_field(self, sample_job):
        """Job deve ter campo autonomy_level."""
        assert hasattr(sample_job, "autonomy_level")
        assert sample_job.autonomy_level == AutonomyLevel.DEVELOPMENT

    def test_job_autonomy_level_can_be_none(self):
        """Job pode ter autonomy_level=None."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="issue-123",
            payload={},
            received_at=datetime.utcnow(),
        )

        job = WebhookJob.create(event)
        # autonomy_level padrão é None
        assert job.autonomy_level is None

    def test_job_autonomy_level_can_be_set(self):
        """autonomy_level pode ser definido."""
        event = WebhookEvent(
            source=WebhookSource.TRELLO,
            event_type="card.moved.🚀 Publicar",
            event_id="card-123",
            payload={},
            received_at=datetime.utcnow(),
        )

        job = WebhookJob.create(event)
        job.autonomy_level = AutonomyLevel.PUBLISH
        assert job.autonomy_level == AutonomyLevel.PUBLISH


@pytest.mark.unit
class TestEventTypeToSkillMapping:
    """Testes de mapeamento event_type → skills."""

    def test_mapping_includes_trello_events(self):
        """
        Mapeamento deve incluir eventos do Trello.

        PRD024: Usa slugs do KanbanListsConfig (evita problemas com emojis).
        PRD020: Apenas Brainstorm, A Fazer e Publicar devem disparar agentes.
        """
        # Eventos que devem disparar agentes (mapear para skills não-None)
        trello_trigger_events = [
            "card.moved.backlog",   # Brainstorm → analyze-issue
            "card.moved.todo",      # A Fazer → resolve-issue
            "card.moved.publish",   # Publicar → publish-issue
        ]

        for event_type in trello_trigger_events:
            assert event_type in EVENT_TYPE_TO_SKILL, f"Evento {event_type} não mapeado"
            # Verifica que o skill não é None (realmente dispara agente)
            assert EVENT_TYPE_TO_SKILL[event_type] is not None

    def test_trello_brainstorm_maps_to_analyze_issue(self):
        """
        Evento 'card.moved.backlog' deve mapear para 'analyze-issue'.

        PRD024: Usa slug 'backlog' para Brainstorm.
        """
        assert EVENT_TYPE_TO_SKILL.get("card.moved.backlog") == "analyze-issue"

    def test_trello_a_fazer_maps_to_resolve_issue(self):
        """
        Evento 'card.moved.todo' deve mapear para 'resolve-issue'.

        PRD024: Usa slug 'todo' para A Fazer.
        """
        assert EVENT_TYPE_TO_SKILL.get("card.moved.todo") == "resolve-issue"

    def test_trello_publicar_maps_to_publish_issue(self):
        """
        Evento 'card.moved.publish' deve mapear para 'publish-issue'.

        PRD024: Usa slug 'publish' para Publicar.
        """
        assert EVENT_TYPE_TO_SKILL.get("card.moved.publish") == "publish-issue"

    def test_trello_em_andamento_nao_dispara(self):
        """
        Evento 'card.moved.progress' não deve disparar agente.

        PRD020: Em Andamento é estado intermediário, não trigger.
        """
        skill = EVENT_TYPE_TO_SKILL.get("card.moved.progress")
        assert skill is None

    def test_trello_em_revisao_nao_dispara(self):
        """
        Evento 'card.moved.review' não deve disparar agente.

        PRD020: Em Revisão é revisão humana, não trigger.
        """
        skill = EVENT_TYPE_TO_SKILL.get("card.moved.review")
        assert skill is None


@pytest.mark.integration
class TestJobOrchestratorDoD:
    """Testes de DoD do PRD020 para JobOrchestrator."""

    def test_dod_4_orchestrator_has_autonomy_support(self):
        """
        DoD #4: autonomy_level em JobOrchestrator.

        Verifica que JobOrchestrator suporta autonomy_level.
        """
        import inspect
        from core.webhooks.application.job_orchestrator import JobOrchestrator

        # Verifica método existe
        assert hasattr(JobOrchestrator, "_get_skill_for_event_type")

        # Verifica assinatura
        sig = inspect.signature(JobOrchestrator._get_skill_for_event_type)
        assert "autonomy_level" in sig.parameters

    def test_dod_4_job_has_autonomy_field(self):
        """
        DoD #4: autonomy_level em JobOrchestrator.

        Verifica que WebhookJob tem campo autonomy_level.
        """
        from core.webhooks.domain import WebhookJob, WebhookEvent, WebhookSource
        from datetime import datetime

        event = WebhookEvent(
            source=WebhookSource.TRELLO,
            event_type="card.moved.📋 A Fazer",
            event_id="card-123",
            payload={},
            received_at=datetime.utcnow(),
        )

        job = WebhookJob.create(event)

        # Campo deve existir
        assert hasattr(job, "autonomy_level")

        # Pode ser definido
        job.autonomy_level = AutonomyLevel.DEVELOPMENT
        assert job.autonomy_level == AutonomyLevel.DEVELOPMENT


@pytest.mark.unit
class TestAutonomyLevelProgressiveAutonomy:
    """Testes de autonomia progressiva."""

    def test_autonomy_levels_in_order(self):
        """Níveis de autonomia devem estar em ordem crescente."""
        levels = list(AutonomyLevel)

        # Verifica ordem esperada
        assert levels[0] == AutonomyLevel.ANALYSIS
        assert levels[1] == AutonomyLevel.DEVELOPMENT
        assert levels[2] == AutonomyLevel.REVIEW
        assert levels[3] == AutonomyLevel.PUBLISH

    def test_each_level_increases_autonomy(self):
        """Cada nível deve aumentar autonomia."""
        # ANALYSIS: sem mudanças
        assert not AutonomyLevel.ANALYSIS.allows_code_changes()

        # DEVELOPMENT: pode mudar
        assert AutonomyLevel.DEVELOPMENT.allows_code_changes()

        # REVIEW: requer revisão (mais conservador)
        assert AutonomyLevel.REVIEW.requires_human_review()

        # PUBLISH: autonomia máxima
        assert AutonomyLevel.PUBLISH.allows_auto_commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
