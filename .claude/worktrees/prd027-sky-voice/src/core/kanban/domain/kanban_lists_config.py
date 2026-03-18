# -*- coding: utf-8 -*-
"""
Entidades de Domínio para Configuração de Listas Kanban.

Define a FONTE ÚNICA DA VERDADE para nomes, emojis e cores das listas Kanban.

DOC: PRD024 - Kanban Cards Vivos
DOC: ADR020 - Integração Trello
DOC: ADR026 - Sincronização Trello ↔ kanban.db
"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class KanbanListDefinition:
    """
    Definição de uma lista Kanban padrão.

    Representa uma lista específica do fluxo Kanban com todos os seus atributos.

    Attributes:
        name: Nome da lista sem emoji (ex: "Brainstorm")
        name_with_emoji: Nome da lista com emoji para Trello (ex: "🧠 Brainstorm")
        slug: Alias técnico de uma palavra só (ex: "backlog", "todo")
        emoji: Emoji da lista (ex: "🧠")
        color: Cor hexadecimal da lista (ex: "#E6F7FF")
        position: Posição ordinal da lista no fluxo (0-5)

    Example:
        >>> definition = KanbanListDefinition(
        ...     name="Brainstorm",
        ...     name_with_emoji="🧠 Brainstorm",
        ...     slug="backlog",
        ...     emoji="🧠",
        ...     color="#E6F7FF",
        ...     position=1
        ... )
    """

    name: str
    name_with_emoji: str
    slug: str
    emoji: str
    color: str
    position: int


class KanbanListsConfig:
    """
    Configuração das listas Kanban Skybridge (PRD024).

    **FONTE ÚNICA DA VERDADE** para todas as operações Kanban.

    Todos os componentes que precisam das listas padrão DEVEM usar esta classe.
    Isso garante consistência entre kanban.db, Trello e frontend.

    Fluxo de listas (conforme PRD024):
        0. Issues      → Entrada de issues do GitHub
        1. Brainstorm  → Análise e ideias
        2. A Fazer     → Planejamento
        3. Em Andamento → Execução
        4. Em Revisão  → Revisão/QA
        5. Publicar   → Concluído/Publicação

    Attributes:
        _definitions: Lista de definições de listas em ordem

    Example:
        >>> config = KanbanListsConfig()
        >>> names = config.get_list_names()  # ["Issues", "Brainstorm", ...]
        >>> slugs = config.get_list_slugs()  # ["issues", "backlog", ...]
        >>> colors = config.get_list_colors()  # {"Issues": "#FFF7E6", ...}
    """

    # Definições das listas em ordem (PRD024)
    _DEFINITIONS: list[KanbanListDefinition] = [
        KanbanListDefinition(
            name="Issues",
            name_with_emoji="📥 Issues",
            slug="issues",
            emoji="📥",
            color="#FFF7E6",
            position=0,
        ),
        KanbanListDefinition(
            name="Brainstorm",
            name_with_emoji="🧠 Brainstorm",
            slug="backlog",
            emoji="🧠",
            color="#E6F7FF",
            position=1,
        ),
        KanbanListDefinition(
            name="A Fazer",
            name_with_emoji="📋 A Fazer",
            slug="todo",
            emoji="📋",
            color="#FFFBF0",
            position=2,
        ),
        KanbanListDefinition(
            name="Em Andamento",
            name_with_emoji="🚧 Em Andamento",
            slug="progress",
            emoji="🚧",
            color="#E6F7FF",
            position=3,
        ),
        KanbanListDefinition(
            name="Em Revisão",
            name_with_emoji="👀 Em Revisão",
            slug="review",
            emoji="👀",
            color="#F6FFED",
            position=4,
        ),
        KanbanListDefinition(
            name="Publicar",
            name_with_emoji="🚀 Publicar",
            slug="publish",
            emoji="🚀",
            color="#F0F5FF",
            position=5,
        ),
    ]

    def __init__(self):
        """Inicializa configuração com definições padrão."""
        self._definitions = self._DEFINITIONS

    def get_list_names(self) -> list[str]:
        """
        Retorna nomes das listas Kanban em ordem.

        Returns:
            Lista de nomes sem emoji: ["Issues", "Brainstorm", "A Fazer", ...]
        """
        return [d.name for d in self._definitions]

    def get_list_names_with_emoji(self) -> list[str]:
        """
        Retorna nomes das listas Kanban com emojis (para Trello).

        Returns:
            Lista de nomes com emoji: ["📥 Issues", "🧠 Brainstorm", ...]
        """
        return [d.name_with_emoji for d in self._definitions]

    def get_list_slugs(self) -> list[str]:
        """
        Retorna slugs técnicos das listas em ordem.

        Slugs são aliases de uma palavra só, sem espaços ou acentos.
        Úteis para URLs, IDs técnicos, e código.

        Returns:
            Lista de slugs: ["issues", "backlog", "todo", "progress", "review", "publish"]
        """
        return [d.slug for d in self._definitions]

    def get_emojis(self) -> list[str]:
        """
        Retorna emojis das listas em ordem.

        Returns:
            Lista de emojis: ["📥", "🧠", "📋", ...]
        """
        return [d.emoji for d in self._definitions]

    def get_colors(self) -> list[str]:
        """
        Retorna cores das listas em ordem.

        Returns:
            Lista de cores hex: ["#FFF7E6", "#E6F7FF", ...]
        """
        return [d.color for d in self._definitions]

    def get_list_colors(self) -> dict[str, str]:
        """
        Retorna mapeamento de nome da lista (sem emoji) para cor (hex).

        **Derivado de get_list_names()** - FONTE ÚNICA DA VERDADE.
        Usado pelo frontend/Trello.

        Returns:
            Dict: {"Issues": "#FFF7E6", "Brainstorm": "#E6F7FF", ...}
        """
        return {d.name: d.color for d in self._definitions}

    def get_list_colors_with_emoji(self) -> dict[str, str]:
        """
        Retorna mapeamento de nome da lista (com emoji) para cor (hex).

        **Derivado de get_list_names_with_emoji()** - FONTE ÚNICA DA VERDADE.
        Usado pelo TrelloService para configurar cores das listas.

        Returns:
            Dict: {"📥 Issues": "#FFF7E6", "🧠 Brainstorm": "#E6F7FF", ...}
        """
        return {d.name_with_emoji: d.color for d in self._definitions}

    def get_trello_to_kanban_mapping(self) -> dict[str, str]:
        """
        Retorna mapeamento de nomes Trello → nomes Kanban (sem emoji).

        Usado para normalizar nomes vindos de webhooks do Trello.
        SOMENTE mapeia nomes com emoji, pois é assim que o Trello foi configurado.

        Se o Trello enviar um nome que não está aqui, indica problema de configuração:
        - Alguém mudou o nome manualmente no Trello
        - O Trello não foi configurado corretamente
        - Webhook de antes da configuração de emojis

        Returns:
            Dict: {
                "📥 Issues": "Issues",
                "🧠 Brainstorm": "Brainstorm",
                "📋 A Fazer": "A Fazer",
                ...
            }
        """
        return {d.name_with_emoji: d.name for d in self._definitions}

    def get_definition_by_name(self, name: str) -> KanbanListDefinition | None:
        """
        Busca definição por nome (com ou sem emoji).

        Args:
            name: Nome da lista (com ou sem emoji)

        Returns:
            KanbanListDefinition se encontrada, None caso contrário
        """
        for d in self._definitions:
            if d.name == name or d.name_with_emoji == name:
                return d
        return None

    def get_definition_by_position(self, position: int) -> KanbanListDefinition | None:
        """
        Busca definição por posição ordinal.

        Args:
            position: Posição da lista (0-5)

        Returns:
            KanbanListDefinition se encontrada, None caso contrário
        """
        for d in self._definitions:
            if d.position == position:
                return d
        return None

    def get_definition_by_slug(self, slug: str) -> KanbanListDefinition | None:
        """
        Busca definição por slug técnico.

        Args:
            slug: Slug da lista (ex: "todo", "progress")

        Returns:
            KanbanListDefinition se encontrada, None caso contrário
        """
        for d in self._definitions:
            if d.slug == slug:
                return d
        return None

    def get_slug_by_name(self, name: str) -> str | None:
        """
        Retorna slug técnico a partir do nome da lista.

        Args:
            name: Nome da lista (com ou sem emoji)

        Returns:
            Slug se encontrado, None caso contrário

        Example:
            >>> config.get_slug_by_name("A Fazer")
            "todo"
            >>> config.get_slug_by_name("📋 A Fazer")
            "todo"
        """
        definition = self.get_definition_by_name(name)
        return definition.slug if definition else None

    def get_name_by_slug(self, slug: str) -> str | None:
        """
        Retorna nome da lista a partir do slug técnico.

        Args:
            slug: Slug da lista (ex: "todo", "progress")

        Returns:
            Nome se encontrado, None caso contrário

        Example:
            >>> config.get_name_by_slug("todo")
            "A Fazer"
        """
        definition = self.get_definition_by_slug(slug)
        return definition.name if definition else None

    def get_slug_to_name_mapping(self) -> dict[str, str]:
        """
        Retorna mapeamento de slug → nome da lista.

        Útil para converter slugs técnicos em nomes legíveis.

        Returns:
            Dict: {
                "issues": "Issues",
                "backlog": "Brainstorm",
                "todo": "A Fazer",
                "progress": "Em Andamento",
                "review": "Em Revisão",
                "publish": "Publicar",
            }
        """
        return {d.slug: d.name for d in self._definitions}

    def get_slug_to_name_with_emoji_mapping(self) -> dict[str, str]:
        """
        Retorna mapeamento de slug → nome da lista com emoji.

        Útil para frontend onde se quer mostrar nomes completos com emojis.

        Returns:
            Dict: {
                "issues": "📥 Issues",
                "backlog": "🧠 Brainstorm",
                "todo": "📋 A Fazer",
                ...
            }
        """
        return {d.slug: d.name_with_emoji for d in self._definitions}


# Mapeamento agent_type → nome da lista (conforme setup do Trello)
# Este mapeamento é derivado de KanbanListsConfig
def get_agent_type_to_list_mapping(
    config: KanbanListsConfig | None = None,
) -> dict[str, str]:
    """
    Retorna mapeamento de agent_type → nome da lista Kanban.

    Args:
        config: Configuração de listas (opcional, usa padrão se None)

    Returns:
        Dict: {
            "analyze-issue": "Brainstorm",
            "resolve-issue": "Em Andamento",
            "review-issue": "Em Revisão",
            "publish-issue": "Publicar",
            "none": "Issues",
        }
    """
    if config is None:
        config = KanbanListsConfig()

    names = config.get_list_names()

    return {
        "analyze-issue": names[1],  # Brainstorm
        "resolve-issue": names[3],  # Em Andamento
        "review-issue": names[4],   # Em Revisão
        "publish-issue": names[5],  # Publicar
        "none": names[0],           # Issues (default)
    }


# Singleton global para configuração de listas
_kanban_lists_config: KanbanListsConfig | None = None


def get_kanban_lists_config() -> KanbanListsConfig:
    """
    Retorna configuração das listas Kanban (singleton).

    Returns:
        KanbanListsConfig com definições das listas padrão
    """
    global _kanban_lists_config
    if _kanban_lists_config is None:
        _kanban_lists_config = KanbanListsConfig()
    return _kanban_lists_config
