# -*- coding: utf-8 -*-
"""
AccessPolicy Value Object.

Política de controle de acesso para canais Discord.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Self


class DMPolicy(str, Enum):
    """Política de acesso para mensagens privadas (DM)."""

    PAIRING = "pairing"  # Requer código de pareamento
    ALLOWLIST = "allowlist"  # Apenas usuários na lista
    DISABLED = "disabled"  # Bloqueia todas


class GroupPolicyType(str, Enum):
    """Tipo de política para canais de grupo."""

    OPEN = "open"  # Qualquer um pode enviar
    MENTION_ONLY = "mention_only"  # Apenas com menção
    RESTRICTED = "restricted"  # Apenas usuários autorizados


@dataclass(frozen=True)
class AccessPolicy:
    """
    Value Object para política de acesso Discord.

    Define quem pode interagir com o bot em cada tipo de canal.
    """

    dm_policy: DMPolicy = DMPolicy.PAIRING
    allow_from: frozenset[str] = field(default_factory=frozenset)
    mention_patterns: frozenset[str] = field(default_factory=frozenset)
    require_mention: bool = True

    def is_allowed(self, user_id: str, is_paired: bool = False) -> bool:
        """
        Verifica se usuário tem permissão de acesso.

        Args:
            user_id: ID do usuário Discord
            is_paired: Se usuário já foi pareado (para PAIRING policy)

        Returns:
            True se usuário tem acesso
        """
        if self.dm_policy == DMPolicy.DISABLED:
            return False

        if self.dm_policy == DMPolicy.ALLOWLIST:
            return user_id in self.allow_from

        if self.dm_policy == DMPolicy.PAIRING:
            return is_paired or user_id in self.allow_from

        return False

    def requires_pairing(self, user_id: str) -> bool:
        """
        Verifica se usuário precisa de pareamento.

        Args:
            user_id: ID do usuário Discord

        Returns:
            True se precisa parear
        """
        if self.dm_policy != DMPolicy.PAIRING:
            return False
        return user_id not in self.allow_from

    def matches_mention_pattern(self, text: str) -> bool:
        """
        Verifica se texto matches algum padrão de menção.

        Args:
            text: Texto da mensagem

        Returns:
            True se matches algum padrão
        """
        import re

        for pattern in self.mention_patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                pass
        return False

    @classmethod
    def disabled(cls) -> Self:
        """Cria política que bloqueia tudo."""
        return cls(dm_policy=DMPolicy.DISABLED)

    @classmethod
    def allowlist(cls, user_ids: list[str]) -> Self:
        """Cria política de allowlist."""
        return cls(
            dm_policy=DMPolicy.ALLOWLIST,
            allow_from=frozenset(user_ids),
        )

    @classmethod
    def pairing(cls, pre_approved: list[str] | None = None) -> Self:
        """Cria política de pareamento."""
        return cls(
            dm_policy=DMPolicy.PAIRING,
            allow_from=frozenset(pre_approved or []),
        )
