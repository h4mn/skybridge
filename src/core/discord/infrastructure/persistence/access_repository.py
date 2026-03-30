# -*- coding: utf-8 -*-
"""
AccessRepository Implementation.

Implementação do repositório de acesso usando access.json.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
from pathlib import Path
from typing import Optional

import discord

from ...domain.repositories import AccessRepository
from ...domain.value_objects import AccessPolicy, ChannelId, DMPolicy


class JsonAccessRepository(AccessRepository):
    """
    Implementação de AccessRepository usando JSON.

    Persiste políticas em access.json, compatível com sistema existente.
    """

    # Diretório de estado padrão
    DEFAULT_STATE_DIR = Path(
        os.environ.get(
            "DISCORD_STATE_DIR",
            Path.home() / ".claude" / "channels" / "discord"
        )
    )

    def __init__(self, state_dir: Optional[Path] = None):
        """
        Inicializa repositório.

        Args:
            state_dir: Diretório para armazenamento (opcional, para testes)
        """
        self._state_dir = state_dir or self.DEFAULT_STATE_DIR
        self._access_file = self._state_dir / "access.json"
        self._approved_dir = self._state_dir / "approved"
        self._cache: Optional[dict] = None

    async def _load_data(self) -> dict:
        """Carrega dados do access.json."""
        if self._cache is not None:
            return self._cache

        try:
            if not self._access_file.exists():
                self._cache = self._default_data()
                return self._cache

            raw = self._access_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            self._cache = data
            return data
        except (json.JSONDecodeError, IOError):
            # Arquivo corrompido - retorna default
            self._cache = self._default_data()
            return self._cache

    def _default_data(self) -> dict:
        """Retorna estrutura padrão de dados."""
        return {
            "dm_policy": "pairing",
            "allow_from": [],
            "groups": {},
            "pending": {},
        }

    async def _save_data(self, data: dict) -> None:
        """Salva dados para access.json atomicamente."""
        # Modo estático não salva
        if os.environ.get("DISCORD_ACCESS_MODE") == "static":
            return

        # Garante diretório existe
        self._state_dir.mkdir(parents=True, exist_ok=True)

        # Escrita atômica: tmp → rename
        tmp_file = self._access_file.with_suffix(".tmp")

        tmp_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        shutil.move(str(tmp_file), str(self._access_file))

        # Atualiza cache
        self._cache = data

    # =========================================================================
    # DM Policy
    # =========================================================================

    async def get_dm_policy(self) -> AccessPolicy:
        """Busca política de acesso para DMs."""
        data = await self._load_data()

        dm_policy_str = data.get("dm_policy", "pairing")
        dm_policy = DMPolicy(dm_policy_str) if dm_policy_str in DMPolicy._value2member_map_ else DMPolicy.PAIRING

        allow_from = frozenset(data.get("allow_from", []))

        return AccessPolicy(
            dm_policy=dm_policy,
            allow_from=allow_from,
        )

    async def save_dm_policy(self, policy: AccessPolicy) -> None:
        """Salva política de acesso para DMs."""
        data = await self._load_data()

        data["dm_policy"] = policy.dm_policy.value
        data["allow_from"] = list(policy.allow_from)

        await self._save_data(data)

    # =========================================================================
    # Group Policy
    # =========================================================================

    async def get_group_policy(self, channel_id: ChannelId) -> Optional[AccessPolicy]:
        """Busca política de acesso para canal de grupo."""
        data = await self._load_data()

        channel_id_str = str(channel_id)
        group_data = data.get("groups", {}).get(channel_id_str)

        if not group_data:
            return None

        return self._dict_to_policy(group_data)

    async def save_group_policy(
        self,
        channel_id: ChannelId,
        policy: AccessPolicy
    ) -> None:
        """Salva política de acesso para canal de grupo."""
        data = await self._load_data()

        if "groups" not in data:
            data["groups"] = {}

        channel_id_str = str(channel_id)
        data["groups"][channel_id_str] = self._policy_to_dict(policy)

        await self._save_data(data)

    async def delete_group_policy(self, channel_id: ChannelId) -> bool:
        """Remove política de canal de grupo."""
        data = await self._load_data()

        channel_id_str = str(channel_id)
        groups = data.get("groups", {})

        if channel_id_str not in groups:
            return False

        del groups[channel_id_str]
        await self._save_data(data)
        return True

    async def list_group_policies(self) -> dict[ChannelId, AccessPolicy]:
        """Lista todas as políticas de grupo."""
        data = await self._load_data()
        groups_data = data.get("groups", {})

        result = {}
        for channel_id_str, policy_data in groups_data.items():
            try:
                channel_id = ChannelId(channel_id_str)
                policy = self._dict_to_policy(policy_data)
                result[channel_id] = policy
            except Exception:
                # Skip inválidos
                pass

        return result

    # =========================================================================
    # Pairing
    # =========================================================================

    async def create_pending_pairing(
        self,
        user_id: str,
        chat_id: str,
        expires_in_ms: int = 3600000
    ) -> str:
        """Cria código de pareamento pendente."""
        import time

        data = await self._load_data()

        if "pending" not in data:
            data["pending"] = {}

        # Cap de pendings
        if len(data["pending"]) >= 3:
            raise ValueError("Limite de pareamentos pendentes atingido")

        code = secrets.token_hex(3)
        now = int(time.time() * 1000)

        data["pending"][code] = {
            "sender_id": user_id,
            "chat_id": chat_id,
            "created_at": now,
            "expires_at": now + expires_in_ms,
            "replies": 1,
        }

        await self._save_data(data)
        return code

    async def get_pending_pairing(self, code: str) -> Optional[dict]:
        """Busca entrada de pareamento pendente."""
        import time

        data = await self._load_data()
        pending = data.get("pending", {})

        entry = pending.get(code)
        if not entry:
            return None

        # Verifica expiração
        now = int(time.time() * 1000)
        if entry["expires_at"] < now:
            # Remove expirado
            del pending[code]
            await self._save_data(data)
            return None

        return entry

    async def approve_pairing(self, code: str) -> Optional[tuple[str, str]]:
        """Aprova pareamento e adiciona usuário à allowlist."""
        import time

        data = await self._load_data()
        pending = data.get("pending", {})

        entry = pending.get(code)
        if not entry:
            return None

        # Verifica expiração
        now = int(time.time() * 1000)
        if entry["expires_at"] < now:
            del pending[code]
            await self._save_data(data)
            return None

        user_id = entry["sender_id"]
        chat_id = entry["chat_id"]

        # Adiciona à allowlist
        allow_from = data.get("allow_from", [])
        if user_id not in allow_from:
            allow_from.append(user_id)
            data["allow_from"] = allow_from

        # Remove do pending
        del pending[code]
        await self._save_data(data)

        # Escreve arquivo de aprovação
        self._write_approval(user_id, chat_id)

        return user_id, chat_id

    async def prune_expired_pairings(self) -> int:
        """Remove entradas de pareamento expiradas."""
        import time

        data = await self._load_data()
        pending = data.get("pending", {})

        now = int(time.time() * 1000)
        expired_codes = [
            code for code, entry in pending.items()
            if entry["expires_at"] < now
        ]

        for code in expired_codes:
            del pending[code]

        if expired_codes:
            await self._save_data(data)

        return len(expired_codes)

    def _write_approval(self, user_id: str, chat_id: str) -> None:
        """Escreve arquivo de aprovação para poll do servidor."""
        self._approved_dir.mkdir(parents=True, exist_ok=True)
        approval_file = self._approved_dir / user_id
        approval_file.write_text(chat_id, encoding="utf-8")

    # =========================================================================
    # Helpers
    # =========================================================================

    def _policy_to_dict(self, policy: AccessPolicy) -> dict:
        """Converte AccessPolicy para dict."""
        return {
            "require_mention": policy.require_mention,
            "allow_from": list(policy.allow_from) if policy.allow_from else [],
        }

    def _dict_to_policy(self, data: dict) -> AccessPolicy:
        """Converte dict para AccessPolicy."""
        return AccessPolicy(
            require_mention=data.get("require_mention", True),
            allow_from=frozenset(data.get("allow_from", [])),
        )

    @classmethod
    def create(cls) -> "JsonAccessRepository":
        """Factory method."""
        return cls()


# Instância padrão
_default_repository: Optional[JsonAccessRepository] = None


def get_access_repository() -> JsonAccessRepository:
    """Retorna instância singleton do repositório."""
    global _default_repository
    if _default_repository is None:
        _default_repository = JsonAccessRepository.create()
    return _default_repository
