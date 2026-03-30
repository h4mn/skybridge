# -*- coding: utf-8 -*-
"""
AccessRepository Interface.

Port (interface) para repositório de políticas de acesso.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self, Optional

from ..value_objects import AccessPolicy, ChannelId


class AccessRepository(ABC):
    """
    Interface para repositório de políticas de acesso.

    Define contrato para persistência e recuperação de políticas
    de acesso a canais Discord (DM e grupos).
    Implementações ficam em Infrastructure Layer.
    """

    @abstractmethod
    async def get_dm_policy(self) -> AccessPolicy:
        """
        Busca política de acesso para DMs.

        Returns:
            AccessPolicy para mensagens privadas
        """
        pass

    @abstractmethod
    async def save_dm_policy(self, policy: AccessPolicy) -> None:
        """
        Salva política de acesso para DMs.

        Args:
            policy: Política a salvar
        """
        pass

    @abstractmethod
    async def get_group_policy(self, channel_id: ChannelId) -> Optional[AccessPolicy]:
        """
        Busca política de acesso para canal de grupo.

        Args:
            channel_id: ID do canal

        Returns:
            AccessPolicy se encontrada, None caso contrário
        """
        pass

    @abstractmethod
    async def save_group_policy(
        self,
        channel_id: ChannelId,
        policy: AccessPolicy
    ) -> None:
        """
        Salva política de acesso para canal de grupo.

        Args:
            channel_id: ID do canal
            policy: Política a salvar
        """
        pass

    @abstractmethod
    async def delete_group_policy(self, channel_id: ChannelId) -> bool:
        """
        Remove política de canal de grupo.

        Args:
            channel_id: ID do canal

        Returns:
            True se removida, False se não encontrada
        """
        pass

    @abstractmethod
    async def list_group_policies(self) -> dict[ChannelId, AccessPolicy]:
        """
        Lista todas as políticas de grupo.

        Returns:
            Dicionário de channel_id -> AccessPolicy
        """
        pass

    # =========================================================================
    # Métodos para Pareamento
    # =========================================================================

    @abstractmethod
    async def create_pending_pairing(
        self,
        user_id: str,
        chat_id: str,
        expires_in_ms: int = 3600000
    ) -> str:
        """
        Cria código de pareamento pendente.

        Args:
            user_id: ID do usuário Discord
            chat_id: ID do canal DM
            expires_in_ms: Tempo até expirar (default: 1h)

        Returns:
            Código de pareamento gerado
        """
        pass

    @abstractmethod
    async def get_pending_pairing(
        self,
        code: str
    ) -> Optional[dict]:
        """
        Busca entrada de pareamento pendente.

        Args:
            code: Código de pareamento

        Returns:
            Dict com {user_id, chat_id, created_at, expires_at} ou None
        """
        pass

    @abstractmethod
    async def approve_pairing(self, code: str) -> Optional[tuple[str, str]]:
        """
        Aprova pareamento e adiciona usuário à allowlist.

        Args:
            code: Código de pareamento

        Returns:
            (user_id, chat_id) se aprovado, None se não encontrado/expirado
        """
        pass

    @abstractmethod
    async def prune_expired_pairings(self) -> int:
        """
        Remove entradas de pareamento expiradas.

        Returns:
            Número de entradas removidas
        """
        pass

    @classmethod
    @abstractmethod
    def create(cls) -> Self:
        """Factory method."""
        pass
