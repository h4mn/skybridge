# -*- coding: utf-8 -*-
"""
Labels do Linear - Fonte Única de Verdade

INFRASTRUCTURE LAYER: Detalhes externos (API Linear)

TODO: Implementar sync automático! Esses IDs estão hardcoded e ficam desatualizados.
      Se der erro "Entity not found: labelIds", rodar: python src/core/discord/scripts/sync_labels.py

Última atualização: 2026-04-05 (via MCP list_issue_labels)
"""

from __future__ import annotations


class LinearLabels:
    """
    Labels do time Skybridge no Linear.

    Centraliza TODOS os label IDs para evitar duplicação e facilitar sync.
    """

    # Fonte (Source)
    FONTE_DISCORD = "e75a8d97-1064-464b-92a7-f4ad371f191d"
    FONTE_CLAUDE_CODE = "546f52f0-f618-4f81-91bd-6bc77fde1fff"
    FONTE_OUTRO = "fc9f8441-3aa0-4121-917f-ba617e365cbe"
    FONTE_TWITTER = "d440d3a8-40ff-42cf-b7c1-6db9431457ee"
    FONTE_ARTIGO = "c2130d13-abcb-427f-b6e7-71cfbcb27add"
    FONTE_CONVERSA = "b746bb7a-8591-48a8-885d-e5f49182c5ef"

    # Domínios (Domains) - NOTA: No Linear são só "paper", "discord", etc. (sem prefixo)
    DOMINIO_GERAL = "871a427a-7d80-47b0-a4b8-90da50b4b0d3"
    DOMINIO_PAPER = "de2cf772-525a-4425-b38f-8e0ea5d44962"
    DOMINIO_DISCORD = "c118601f-93ad-434b-a8b5-c7ac39043087"
    DOMINIO_AUTOKARPA = "a97fbf6b-6faa-44f8-9799-b6a31c2e1aa2"

    # Ações (Actions)
    ACAO_IMPLEMENTAR = "6b8cdf2d-177f-4d86-8d4d-d66f8824c7ec"
    ACAO_PESQUISAR = "2d986af4-6c8c-4c70-9a6c-1a4e3523f8a7"
    ACAO_ARQUIVAR = "977432d4-72cf-4840-8e12-767e0adb2f9f"
    ACAO_DESCARTAR = "9b32b2cd-7964-4e82-8b00-4e13e9ac24b2"

    @classmethod
    def inbox_discord(cls) -> dict[str, str]:
        """Labels padrão para entradas via Discord /inbox."""
        return {
            "fonte:discord": cls.FONTE_DISCORD,
            "domínio:geral": cls.DOMINIO_GERAL,
            "ação:implementar": cls.ACAO_IMPLEMENTAR,
        }

    @classmethod
    def inbox_claude_code(cls) -> dict[str, str]:
        """Labels padrão para entradas via Claude Code /inbox."""
        return {
            "fonte:claude-code": cls.FONTE_CLAUDE_CODE,
            "domínio:geral": cls.DOMINIO_GERAL,
            "ação:implementar": cls.ACAO_IMPLEMENTAR,
        }

    @classmethod
    def domain_label(cls, domain: str) -> str:
        """
        Retorna o label ID para um domínio.

        Args:
            domain: 'geral', 'paper', 'discord', 'autokarpa'

        Returns:
            Label ID correspondente
        """
        mapping = {
            "geral": cls.DOMINIO_GERAL,
            "paper": cls.DOMINIO_PAPER,
            "discord": cls.DOMINIO_DISCORD,
            "autokarpa": cls.DOMINIO_AUTOKARPA,
        }
        return mapping.get(domain, cls.DOMINIO_GERAL)


# Dict para compatibilidade com código legado (será removido após refatoração)
LEGACY_LABELS = {
    "fonte:discord": LinearLabels.FONTE_DISCORD,
    "fonte:claude-code": LinearLabels.FONTE_CLAUDE_CODE,
    "domínio:paper": LinearLabels.DOMINIO_PAPER,
    "domínio:discord": LinearLabels.DOMINIO_DISCORD,
    "domínio:autokarpa": LinearLabels.DOMINIO_AUTOKARPA,
    "domínio:geral": LinearLabels.DOMINIO_GERAL,
    "ação:implementar": LinearLabels.ACAO_IMPLEMENTAR,
}
