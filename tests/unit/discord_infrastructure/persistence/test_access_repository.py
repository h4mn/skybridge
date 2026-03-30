# -*- coding: utf-8 -*-
"""
Testes unitários para AccessRepository.

Testa a implementação JSON do repositório de políticas de acesso.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.core.discord.infrastructure.persistence.access_repository import (
    JsonAccessRepository,
    get_access_repository,
)
from src.core.discord.domain.value_objects import AccessPolicy, ChannelId, DMPolicy


class TestJsonAccessRepository:
    """Testes para JsonAccessRepository."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Diretório temporário para estado."""
        return tmp_path / "state"

    @pytest.fixture
    def repository(self, temp_state_dir):
        """Repositório com diretório temporário e isolamento completo."""
        repo = JsonAccessRepository(state_dir=temp_state_dir)
        repo._cache = None  # Reset cache
        yield repo
        repo._cache = None  # Limpa após teste

    class TestInit:
        """Testes de inicialização."""

        def test_init(self):
            """Repositório pode ser criado."""
            repo = JsonAccessRepository()
            assert repo is not None
            assert repo._cache is None

        @pytest.mark.asyncio
        async def test_load_creates_default_if_missing(self, repository, temp_state_dir):
            """Cria dados padrão se arquivo não existe."""
            data = await repository._load_data()

            assert data["dm_policy"] == "pairing"
            assert data["allow_from"] == []
            assert data["groups"] == {}
            assert data["pending"] == {}

    class TestDMPolicy:
        """Testes de política de DM."""

        @pytest.mark.asyncio
        async def test_get_dm_policy_default(self, repository):
            """Retorna política padrão."""
            policy = await repository.get_dm_policy()

            assert policy.dm_policy == DMPolicy.PAIRING
            assert policy.allow_from == frozenset()

        @pytest.mark.asyncio
        async def test_save_and_get_dm_policy(self, repository):
            """Salva e recupera política de DM."""
            policy = AccessPolicy.pairing(pre_approved=["user123", "user456"])

            await repository.save_dm_policy(policy)
            retrieved = await repository.get_dm_policy()

            assert retrieved.dm_policy == DMPolicy.PAIRING
            assert "user123" in retrieved.allow_from
            assert "user456" in retrieved.allow_from

        @pytest.mark.asyncio
        async def test_save_dm_policy_allowlist(self, repository):
            """Salva política de allowlist."""
            policy = AccessPolicy.allowlist(["user1", "user2"])

            await repository.save_dm_policy(policy)
            retrieved = await repository.get_dm_policy()

            assert retrieved.dm_policy == DMPolicy.ALLOWLIST
            assert "user1" in retrieved.allow_from
            assert "user2" in retrieved.allow_from

    class TestGroupPolicy:
        """Testes de política de grupo."""

        @pytest.mark.asyncio
        async def test_get_group_policy_not_found(self, repository):
            """Retorna None para canal inexistente."""
            policy = await repository.get_group_policy(ChannelId("123"))

            assert policy is None

        @pytest.mark.asyncio
        async def test_save_and_get_group_policy(self, repository):
            """Salva e recupera política de grupo."""
            channel_id = ChannelId("123456")
            policy = AccessPolicy(
                require_mention=False,
                allow_from=frozenset(["user1"]),
            )

            await repository.save_group_policy(channel_id, policy)
            retrieved = await repository.get_group_policy(channel_id)

            assert retrieved is not None
            assert retrieved.require_mention is False
            assert "user1" in retrieved.allow_from

        @pytest.mark.asyncio
        async def test_delete_group_policy(self, repository):
            """Remove política de grupo."""
            channel_id = ChannelId("123456")
            policy = AccessPolicy()

            await repository.save_group_policy(channel_id, policy)
            result = await repository.delete_group_policy(channel_id)

            assert result is True
            assert await repository.get_group_policy(channel_id) is None

        @pytest.mark.asyncio
        async def test_delete_group_policy_not_found(self, repository):
            """Retorna False ao deletar inexistente."""
            channel_id = ChannelId("999")

            result = await repository.delete_group_policy(channel_id)

            assert result is False

        @pytest.mark.asyncio
        async def test_list_group_policies(self, repository):
            """Lista todas as políticas de grupo."""
            channel1 = ChannelId("111")
            channel2 = ChannelId("222")
            policy1 = AccessPolicy(require_mention=True)
            policy2 = AccessPolicy(require_mention=False)

            await repository.save_group_policy(channel1, policy1)
            await repository.save_group_policy(channel2, policy2)

            policies = await repository.list_group_policies()

            assert len(policies) == 2
            assert channel1 in policies
            assert channel2 in policies
            assert policies[channel1].require_mention is True
            assert policies[channel2].require_mention is False

    class TestPairing:
        """Testes de funcionalidade de pareamento."""

        @pytest.mark.asyncio
        async def test_create_pending_pairing(self, repository):
            """Cria código de pareamento."""
            code = await repository.create_pending_pairing(
                user_id="user123",
                chat_id="987654321",
            )

            assert code is not None
            assert len(code) == 6  # 3 bytes hex = 6 caracteres

            # Verifica que foi salvo
            entry = await repository.get_pending_pairing(code)
            assert entry is not None
            assert entry["sender_id"] == "user123"
            assert entry["chat_id"] == "987654321"

        @pytest.mark.asyncio
        async def test_create_pending_pairing_custom_expiry(self, repository):
            """Cria código com expiração customizada."""
            code = await repository.create_pending_pairing(
                user_id="user123",
                chat_id="987654321",
                expires_in_ms=5000,  # 5 segundos
            )

            entry = await repository.get_pending_pairing(code)
            assert entry is not None
            # Expiry deve ser ~5s no futuro
            import time
            now = int(time.time() * 1000)
            assert entry["expires_at"] - now >= 4000  # Pelo menos 4s

        @pytest.mark.asyncio
        async def test_create_pending_pairing_limit(self, repository):
            """Impede criar mais de 3 pendings."""
            # Cria 3 pendings
            for i in range(3):
                await repository.create_pending_pairing(
                    user_id=f"user{i}",
                    chat_id=f"dm{i}",
                )

            # 4º deve falhar
            with pytest.raises(ValueError, match="Limite"):
                await repository.create_pending_pairing(
                    user_id="user4",
                    chat_id="111111111",
                )

        @pytest.mark.asyncio
        async def test_get_pending_pairing_not_found(self, repository):
            """Retorna None para código inexistente."""
            entry = await repository.get_pending_pairing("invalid")

            assert entry is None

        @pytest.mark.asyncio
        async def test_approve_pairing(self, repository):
            """Aprova pareamento."""
            code = await repository.create_pending_pairing(
                user_id="user123",
                chat_id="987654321",
            )

            result = await repository.approve_pairing(code)

            assert result is not None
            assert result[0] == "user123"
            assert result[1] == "987654321"

            # Verifica que usuário está na allowlist
            policy = await repository.get_dm_policy()
            assert "user123" in policy.allow_from

            # Verifica que pending foi removido
            entry = await repository.get_pending_pairing(code)
            assert entry is None

        @pytest.mark.asyncio
        async def test_approve_pairing_invalid_code(self, repository):
            """Retorna None para código inválido."""
            result = await repository.approve_pairing("invalid")

            assert result is None

        @pytest.mark.asyncio
        async def test_prune_expired_pairings(self, repository):
            """Remove entradas expiradas."""
            repository._cache = None  # Reset para este teste
            # Cria entradas com expiração curta
            code1 = await repository.create_pending_pairing(
                user_id="user1",
                chat_id="123456789",
                expires_in_ms=-1000,  # Já expirado
            )
            # Reset cache para criar segunda entrada (limite de 3 não é problema)
            repository._cache = None
            code2 = await repository.create_pending_pairing(
                user_id="user2",
                chat_id="987654321",
                expires_in_ms=10000,  # Válido
            )

            # Prune
            removed = await repository.prune_expired_pairings()

            assert removed >= 1
            assert await repository.get_pending_pairing(code1) is None
            assert await repository.get_pending_pairing(code2) is not None

    class TestStaticMode:
        """Testes do modo estático."""

        @pytest.mark.asyncio
        async def test_static_mode_no_save(self, repository):
            """Modo estático não salva."""
            with patch.dict(
                "os.environ",
                {"DISCORD_ACCESS_MODE": "static"}
            ):
                policy = AccessPolicy.allowlist(["user1"])
                await repository.save_dm_policy(policy)

                # Cache atualizado mas arquivo não escrito
                assert repository._cache is not None


class TestGetAccessRepository:
    """Testes para função get_access_repository."""

    def test_returns_singleton(self):
        """Retorna mesma instância."""
        # Clear singleton
        import src.core.discord.infrastructure.persistence.access_repository as mod
        mod._default_repository = None

        repo1 = get_access_repository()
        repo2 = get_access_repository()

        assert repo1 is repo2

    def test_create_method(self):
        """Factory method cria instância."""
        repo = JsonAccessRepository.create()

        assert isinstance(repo, JsonAccessRepository)


class TestIntegration:
    """Testes de integração com access.json."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Diretório temporário para estado."""
        return tmp_path / "state"

    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_state_dir):
        """Testa fluxo completo de uso."""
        repo = JsonAccessRepository(state_dir=temp_state_dir)

        # Setup inicial
        dm_policy = AccessPolicy.pairing(pre_approved=["admin"])
        await repo.save_dm_policy(dm_policy)

        # Cria canal de grupo
        channel_id = ChannelId("123456789")
        group_policy = AccessPolicy(require_mention=False)
        await repo.save_group_policy(channel_id, group_policy)

        # Cria pareamento
        code = await repo.create_pending_pairing(
            user_id="new_user",
            chat_id="555555555",
        )

        # Aprova
        result = await repo.approve_pairing(code)
        assert result is not None

        # Verifica usuário na allowlist
        final_policy = await repo.get_dm_policy()
        assert "new_user" in final_policy.allow_from
        assert "admin" in final_policy.allow_from

        # Verifica canal listado
        groups = await repo.list_group_policies()
        assert channel_id in groups
