# -*- coding: utf-8 -*-
"""
AccessService - Domain Service.

Serviço de domínio para controle de acesso Discord.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ..value_objects import AccessPolicy, DMPolicy, UserId


@dataclass
class AccessResult:
    """Resultado de verificação de acesso."""

    allowed: bool
    reason: str
    requires_pairing: bool = False
    pairing_code: str | None = None


class AccessService:
    """
    Domain Service para controle de acesso.

    Centraliza lógica de autorização para canais Discord.
    Não tem estado - apenas opera sobre Value Objects e Entities.
    """

    def check_dm_access(
        self,
        policy: AccessPolicy,
        user_id: UserId,
        is_paired: bool = False,
    ) -> AccessResult:
        """
        Verifica acesso a DM.

        Args:
            policy: Política de acesso
            user_id: ID do usuário
            is_paired: Se usuário já foi pareado

        Returns:
            AccessResult com decisão e motivo
        """
        if policy.dm_policy == DMPolicy.DISABLED:
            return AccessResult(
                allowed=False,
                reason="DMs desabilitados por política",
            )

        if policy.dm_policy == DMPolicy.ALLOWLIST:
            if user_id.value in policy.allow_from:
                return AccessResult(
                    allowed=True,
                    reason="Usuário na allowlist",
                )
            return AccessResult(
                allowed=False,
                reason="Usuário não autorizado (fora da allowlist)",
            )

        if policy.dm_policy == DMPolicy.PAIRING:
            if is_paired or user_id.value in policy.allow_from:
                return AccessResult(
                    allowed=True,
                    reason="Usuário autorizado",
                )
            return AccessResult(
                allowed=False,
                reason="Pareamento requerido",
                requires_pairing=True,
            )

        # Fallback - não deveria chegar aqui
        return AccessResult(
            allowed=False,
            reason="Política desconhecida",
        )

    def check_group_access(
        self,
        policy: AccessPolicy,
        user_id: UserId,
        is_mentioned: bool = False,
    ) -> AccessResult:
        """
        Verifica acesso a canal de grupo.

        Args:
            policy: Política de acesso
            user_id: ID do usuário
            is_mentioned: Se bot foi mencionado

        Returns:
            AccessResult com decisão e motivo
        """
        # Grupos geralmente têm require_mention
        if policy.require_mention and not is_mentioned:
            return AccessResult(
                allowed=False,
                reason="Bot não foi mencionado",
            )

        # Se há allowlist, verifica
        if policy.allow_from and user_id.value not in policy.allow_from:
            return AccessResult(
                allowed=False,
                reason="Usuário não autorizado neste canal",
            )

        return AccessResult(
            allowed=True,
            reason="Acesso permitido",
        )

    def is_mentioned(
        self,
        text: str,
        mention_patterns: frozenset[str],
        bot_mention: str | None = None,
    ) -> bool:
        """
        Verifica se bot foi mencionado.

        Args:
            text: Texto da mensagem
            mention_patterns: Padrões regex de menção
            bot_mention: Menção direta ao bot (<@bot_id>)

        Returns:
            True se mencionado
        """
        import re

        # Menção direta
        if bot_mention and bot_mention in text:
            return True

        # Padrões customizados
        for pattern in mention_patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                pass

        return False

    @classmethod
    def create(cls) -> Self:
        """Factory method."""
        return cls()
