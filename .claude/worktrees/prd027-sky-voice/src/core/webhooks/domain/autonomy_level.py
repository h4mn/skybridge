# -*- coding: utf-8 -*-
"""
Autonomy Level Enum.

Define os níveis de autonomia para processamento de webhooks.
Cada nível representa quão autônomo o agente pode ser na execução.
"""
from __future__ import annotations

from enum import Enum


class AutonomyLevel(Enum):
    """
    Nível de autonomia para processamento de webhooks.

    Define o quão autônomo o agente pode ser ao processar um card/issue:
    - ANALYSIS: Apenas análise, sem fazer mudanças
    - DEVELOPMENT: Desenvolvimento normal (foco em implementar)
    - REVIEW: Aguardando revisão humana antes de publicar
    - PUBLISH: Commit/push/PR automático após implementação

    Mapeamento Listas Trello → AutonomyLevel:
    - "💡 Brainstorm" → ANALYSIS (apenas entender o problema)
    - "📋 A Fazer" → DEVELOPMENT (implementar a solução)
    - "🚧 Em Andamento" → DEVELOPMENT (continuar implementando)
    - "👁️ Em Revisão" → REVIEW (aguardar aprovação humana)
    - "🚀 Publicar" → PUBLISH (commit/push/PR automático)
    """

    ANALYSIS = "analysis"
    """Apenas análise, sem fazer mudanças de código."""

    DEVELOPMENT = "development"
    """Desenvolvimento normal - foco em implementar a solução."""

    REVIEW = "review"
    """Aguardando revisão humana antes de publicar."""

    PUBLISH = "publish"
    """Commit/push/PR automático após implementação."""

    def allows_code_changes(self) -> bool:
        """
        Verifica se este nível permite mudanças de código.

        Returns:
            True se o nível permite modificar código
        """
        return self in (AutonomyLevel.DEVELOPMENT, AutonomyLevel.REVIEW, AutonomyLevel.PUBLISH)

    def allows_auto_commit(self) -> bool:
        """
        Verifica se este nível permite commit/push automático.

        Returns:
            True se o nível permite commit/push automático
        """
        return self == AutonomyLevel.PUBLISH

    def requires_human_review(self) -> bool:
        """
        Verifica se este nível requer revisão humana.

        Returns:
            True se o nível requer revisão antes de publicar
        """
        return self == AutonomyLevel.REVIEW
