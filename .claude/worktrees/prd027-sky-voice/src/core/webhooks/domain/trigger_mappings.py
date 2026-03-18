# -*- coding: utf-8 -*-
"""
Trigger Mappings - Configuração de quais eventos disparam agentes.

DOC: PRD013 - Webhook Autonomous Agents
DOC: PRD020 - Fluxo Bidirecional GitHub ↔ Trello
DOC: PRD024 - Kanban Cards Vivos

Define mapeamento de eventos (GitHub/Trello) para skills/agente.
Usa slugs do KanbanListsConfig (PRD024) para evitar problemas com emojis.
"""

from dataclasses import dataclass
from typing import Final

# Importa slugs do KanbanListsConfig (PRD024)
from core.kanban.domain.kanban_lists_config import KanbanListsConfig

# ============================================================================
# SLUGS DAS LISTAS TRELLO (PRD024)
# ============================================================================
# Usar slugs evita problemas com emojis em:
# - Nomes de branches Git
# - Nomes de arquivos
# - Logs e mensagens
class TrelloListSlug:
    """Slugs das listas Trello (conforme PRD024 KanbanListsConfig)."""

    # Slugs das listas (PRD024)
    ISSUES: Final[str] = KanbanListsConfig()._DEFINITIONS[0].slug  # "issues"
    BRAINSTORM: Final[str] = KanbanListsConfig()._DEFINITIONS[1].slug  # "backlog"
    TODO: Final[str] = KanbanListsConfig()._DEFINITIONS[2].slug  # "todo"
    PROGRESS: Final[str] = KanbanListsConfig()._DEFINITIONS[3].slug  # "progress"
    REVIEW: Final[str] = KanbanListsConfig()._DEFINITIONS[4].slug  # "review"
    PUBLISH: Final[str] = KanbanListsConfig()._DEFINITIONS[5].slug  # "publish"

    # Mapeamento reverso: slug → nome completo (sem emoji)
    SLUG_TO_NAME = {
        ISSUES: KanbanListsConfig()._DEFINITIONS[0].name,      # "Issues"
        BRAINSTORM: KanbanListsConfig()._DEFINITIONS[1].name,    # "Brainstorm"
        TODO: KanbanListsConfig()._DEFINITIONS[2].name,          # "A Fazer"
        PROGRESS: KanbanListsConfig()._DEFINITIONS[3].name,      # "Em Andamento"
        REVIEW: KanbanListsConfig()._DEFINITIONS[4].name,         # "Em Revisão"
        PUBLISH: KanbanListsConfig()._DEFINITIONS[5].name,        # "Publicar"
    }

    # Mapeamento: slug → nome com emoji (para debug/exibição)
    SLUG_TO_NAME_WITH_EMOJI = {
        ISSUES: KanbanListsConfig()._DEFINITIONS[0].name_with_emoji,  # "📥 Issues"
        BRAINSTORM: KanbanListsConfig()._DEFINITIONS[1].name_with_emoji,  # "🧠 Brainstorm"
        TODO: KanbanListsConfig()._DEFINITIONS[2].name_with_emoji,      # "📋 A Fazer"
        PROGRESS: KanbanListsConfig()._DEFINITIONS[3].name_with_emoji,   # "🚧 Em Andamento"
        REVIEW: KanbanListsConfig()._DEFINITIONS[4].name_with_emoji,      # "👁️ Em Revisão"
        PUBLISH: KanbanListsConfig()._DEFINITIONS[5].name_with_emoji,     # "🚀 Publicar"
    }


# ============================================================================
# EVENT_TYPE TO SKILL - Mapeamento de eventos para skills
# ============================================================================
# DOC: PRD020 - Apenas Brainstorm, A Fazer e Publicar devem disparar agentes
# DOC: Em Andamento e Em Revisão são estados intermediários, não triggers

@dataclass(frozen=True)
class TriggerMapping:
    """
    Mapeamento de evento para skill.

    Attributes:
        event_type: Identificador do evento (ex: "card.moved.todo")
        skill: Skill a executar (None se não deve disparar agente)
        description: Descrição do que dispara
    """

    event_type: str
    skill: str | None
    description: str


# Lista de mapeamentos (imutável)
#
# PRD026: Fluxo ajustado - Issue aberta NÃO executa agente
# Apenas movimento para "📋 A Fazer" dispara agente resolve-issue
#
# Racional:
# - Issue aberta → Card criado para triagem (aguardando decisão humana)
# - Mover para "A Fazer" → Decisão tomada, agente deve executar
TRIGGER_MAPPINGS: tuple[TriggerMapping, ...] = (
    # GitHub Events - NÃO disparam agentes diretamente
    # O agente só é disparado quando o card é movido para "📋 A Fazer"
    TriggerMapping(
        event_type="issues.opened",
        skill=None,
        description="Issue aberta no GitHub - cria card, NÃO executa agente"
    ),
    TriggerMapping(
        event_type="issues.reopened",
        skill=None,
        description="Issue reaberta no GitHub - cria card, NÃO executa agente"
    ),
    TriggerMapping(
        event_type="issues.edited",
        skill=None,
        description="Issue editada - NÃO executa agente"
    ),
    TriggerMapping(
        event_type="issues.closed",
        skill=None,
        description="Issue fechada - não dispara agente"
    ),
    TriggerMapping(
        event_type="issues.deleted",
        skill=None,
        description="Issue deletada - não dispara agente"
    ),
    TriggerMapping(
        event_type="issues.labeled",
        skill=None,
        description="Label adicionada - não dispara agente"
    ),
    TriggerMapping(
        event_type="issues.unlabeled",
        skill=None,
        description="Label removida - não dispara agente"
    ),
    TriggerMapping(
        event_type="issue_comment.created",
        skill="respond-discord",
        description="Comentário criado - responder via Discord (TODO)"
    ),

    # Pull Requests
    TriggerMapping(
        event_type="pull_request.opened",
        skill=None,
        description="PR aberta - não dispara agente (TODO)"
    ),
    TriggerMapping(
        event_type="pull_request.closed",
        skill=None,
        description="PR fechada - não dispara agente (TODO)"
    ),
    TriggerMapping(
        event_type="pull_request.edited",
        skill=None,
        description="PR editada - não dispara agente (TODO)"
    ),

    # Trello Events - PRD020
    # Apenas Brainstorm, A Fazer e Publicar devem disparar agentes
    # Em Andamento (progress) e Em Revisão (review) são estados intermediários do trabalho

    TriggerMapping(
        event_type=f"card.moved.{TrelloListSlug.BRAINSTORM}",
        skill="analyze-issue",
        description="Card movido para Brainstorm → ANALYSIS (agente lê e comenta, sem código)"
    ),
    TriggerMapping(
        event_type=f"card.moved.{TrelloListSlug.TODO}",
        skill="resolve-issue",
        description="Card movido para A Fazer → DEVELOPMENT (move p/ Em Andamento + desenvolve)"
    ),
    # Em Andamento (progress) NÃO dispara agente - já está trabalhando
    # Em Revisão (review) NÃO dispara agente - é revisão humana
    TriggerMapping(
        event_type=f"card.moved.{TrelloListSlug.PUBLISH}",
        skill="publish-issue",
        description="Card movido para Publicar → commit/push/PR"
    ),
)


# Dicionário para lookup rápido (usado pelo JobOrchestrator)
EVENT_TYPE_TO_SKILL: dict[str, str | None] = {
    m.event_type: m.skill for m in TRIGGER_MAPPINGS
}


# ============================================================================
# AUTONOMY LEVEL TO SKILL - Mapeamento de nível de autonomia para skills
# ============================================================================
# DOC: PRD020 - Mapeia AutonomyLevel para skill baseado na lista Trello
# DOC: Usado como fallback quando event_type não está em EVENT_TYPE_TO_SKILL
AUTONOMY_LEVEL_TO_SKILL: dict[str, str | None] = {
    "analysis": "analyze-issue",   # Brainstorm, Issues
    "development": "resolve-issue",  # A Fazer (Em Andamento não dispara)
    "review": None,                # Em Revisão - revisão humana, não dispara agente
    "publish": "publish-issue",    # Publicar
}


# Helper functions
def get_skill_for_event(event_type: str) -> str | None:
    """Retorna o skill para um evento, ou None se não deve disparar agente."""
    return EVENT_TYPE_TO_SKILL.get(event_type)


def get_trello_list_slug(trello_list_name: str) -> str | None:
    """
    Converte nome de lista Trello para slug.

    Usa KanbanListsConfig para encontrar o slug correspondente.

    Args:
        trello_list_name: Nome da lista no Trello (ex: "🧠 Brainstorm", "Brainstorm")

    Returns:
        Slug da lista (ex: "backlog") ou None se não encontrado
    """
    from core.kanban.domain.kanban_lists_config import get_kanban_lists_config

    config = get_kanban_lists_config()
    definition = config.get_definition_by_name(trello_list_name)

    if definition:
        return definition.slug
    return None


def build_card_moved_event_type(trello_list_slug: str) -> str:
    """
    Constrói event_type para movimento de card usando slug.

    Args:
        trello_list_slug: Slug da lista destino (ex: "backlog", "todo")

    Returns:
        event_type (ex: "card.moved.backlog", "card.moved.todo")
    """
    return f"card.moved.{trello_list_slug}"
