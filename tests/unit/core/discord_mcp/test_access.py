"""
Testes unitários para access.py - TDD Estrito.

Ciclo Red-Green-Refactor:
1. RED: Escrever teste que falha
2. Verificar que falha
3. GREEN: Implementar código mínimo
4. Verificar que passa
"""

import pytest
import json
import time
from pathlib import Path


class TestDefaultAccess:
    """Testes para default_access()."""

    def test_default_access_retorna_dm_policy_pairing(self):
        """RED → GREEN: default_access() retorna Access com dm_policy='pairing'."""
        from src.core.discord.access import default_access

        access = default_access()

        assert access.dm_policy.value == "pairing"

    def test_default_access_retorna_allow_from_vazio(self):
        """RED → GREEN: default_access() retorna Access com allow_from vazio."""
        from src.core.discord.access import default_access

        access = default_access()

        assert access.allow_from == []

    def test_default_access_retorna_groups_vazio(self):
        """RED → GREEN: default_access() retorna Access com groups vazio."""
        from src.core.discord.access import default_access

        access = default_access()

        assert access.groups == {}

    def test_default_access_retorna_pending_vazio(self):
        """RED → GREEN: default_access() retorna Access com pending vazio."""
        from src.core.discord.access import default_access

        access = default_access()

        assert access.pending == {}


class TestReadAccessFile:
    """Testes para read_access_file()."""

    def test_le_arquivo_existente(self, access_file, sample_access_data):
        """RED → GREEN: read_access_file() lê access.json corretamente."""
        from src.core.discord.access import read_access_file

        access = read_access_file()

        assert access.dm_policy.value == sample_access_data["dmPolicy"]
        assert "123456789" in access.allow_from

    def test_retorna_default_se_arquivo_nao_existe(self, empty_state_dir):
        """RED → GREEN: read_access_file() retorna default se arquivo não existe."""
        from src.core.discord.access import read_access_file

        access = read_access_file()

        assert access.dm_policy.value == "pairing"
        assert access.allow_from == []

    def test_retorna_default_se_arquivo_corrompido(self, temp_state_dir):
        """RED → GREEN: read_access_file() retorna default se JSON inválido."""
        # Escreve JSON inválido
        access_file = temp_state_dir / "access.json"
        access_file.write_text("{ invalid json }", encoding="utf-8")

        from src.core.discord.access import read_access_file

        access = read_access_file()

        assert access.dm_policy.value == "pairing"


class TestSaveAccess:
    """Testes para save_access()."""

    def test_escreve_arquivo(self, temp_state_dir):
        """RED → GREEN: save_access() escreve access.json."""
        from src.core.discord.access import save_access, default_access

        access = default_access()
        access.allow_from.append("123456")

        save_access(access)

        access_file = temp_state_dir / "access.json"
        assert access_file.exists()

        data = json.loads(access_file.read_text(encoding="utf-8"))
        assert "123456" in data["allowFrom"]

    def test_escreve_atomicamente(self, temp_state_dir):
        """RED → GREEN: save_access() usa escrita atômica (tmp → rename)."""
        from src.core.discord.access import save_access, default_access

        access = default_access()
        save_access(access)

        # Verifica que arquivo .tmp não existe (foi renomeado)
        tmp_file = temp_state_dir / "access.json.tmp"
        assert not tmp_file.exists()


class TestPruneExpired:
    """Testes para prune_expired()."""

    def test_remove_entradas_expiradas(self, temp_state_dir):
        """RED → GREEN: prune_expired() remove pending expiradas."""
        from src.core.discord.access import (
            default_access,
            prune_expired,
            save_access,
        )
        from src.core.discord.models import PendingEntry

        access = default_access()
        now = int(time.time() * 1000)

        # Entrada expirada
        access.pending["abc123"] = PendingEntry(
            sender_id="999",
            chat_id="888",
            created_at=now - 7200000,
            expires_at=now - 3600000,  # Expirou 1h atrás
            replies=1,
        )

        # Entrada válida
        access.pending["def456"] = PendingEntry(
            sender_id="777",
            chat_id="666",
            created_at=now,
            expires_at=now + 3600000,  # Expira em 1h
            replies=1,
        )

        changed = prune_expired(access)

        assert changed is True
        assert "abc123" not in access.pending
        assert "def456" in access.pending

    def test_retorna_false_se_nada_expirado(self, temp_state_dir):
        """RED → GREEN: prune_expired() retorna False se nada expirou."""
        from src.core.discord.access import default_access, prune_expired
        from src.core.discord.models import PendingEntry

        access = default_access()
        now = int(time.time() * 1000)

        access.pending["valid"] = PendingEntry(
            sender_id="777",
            chat_id="666",
            created_at=now,
            expires_at=now + 3600000,
            replies=1,
        )

        changed = prune_expired(access)

        assert changed is False


class TestGateDM:
    """Testes para gate_dm()."""

    def test_usuario_autorizado_retorna_deliver(self, access_file):
        """RED → GREEN: gate_dm() retorna deliver para usuário autorizado."""
        from src.core.discord.access import gate_dm, load_access

        access = load_access()
        # 123456789 está no allow_from
        result = gate_dm(access, "123456789")

        assert result.action == "deliver"

    def test_usuario_nao_autorizado_retorna_pair(self, empty_state_dir):
        """RED → GREEN: gate_dm() retorna pair para usuário não autorizado."""
        from src.core.discord.access import gate_dm, load_access

        access = load_access()
        # dm_policy padrão é pairing
        result = gate_dm(access, "999999999")

        assert result.action == "pair"
        assert result.code is not None
        assert len(result.code) == 6  # Código de 6 chars

    def test_policy_disabled_retorna_drop(self, temp_state_dir):
        """RED → GREEN: gate_dm() retorna drop quando política é disabled."""
        from src.core.discord.access import gate_dm, default_access
        from src.core.discord.models import DMPolicy

        access = default_access()
        access.dm_policy = DMPolicy.DISABLED

        result = gate_dm(access, "123456789")

        assert result.action == "drop"

    def test_policy_allowlist_usuario_nao_autorizado_retorna_drop(self, temp_state_dir):
        """RED → GREEN: gate_dm() retorna drop em allowlist se não autorizado."""
        from src.core.discord.access import gate_dm, default_access
        from src.core.discord.models import DMPolicy

        access = default_access()
        access.dm_policy = DMPolicy.ALLOWLIST
        access.allow_from = ["111111111"]

        result = gate_dm(access, "999999999")

        assert result.action == "drop"


class TestGateGroup:
    """Testes para gate_group()."""

    def test_canal_autorizado_retorna_deliver(self, access_file):
        """RED → GREEN: gate_group() retorna deliver para canal autorizado."""
        from src.core.discord.access import gate_group, load_access

        access = load_access()
        # 987654321 está no groups
        result = gate_group(
            access=access,
            channel_id="987654321",
            sender_id="123456789",
            is_thread=False,
        )

        assert result.action == "deliver"

    def test_canal_nao_autorizado_retorna_drop(self, empty_state_dir):
        """RED → GREEN: gate_group() retorna drop para canal não autorizado."""
        from src.core.discord.access import gate_group, load_access

        access = load_access()

        result = gate_group(
            access=access,
            channel_id="999999999",
            sender_id="123456789",
            is_thread=False,
        )

        assert result.action == "drop"

    def test_thread_herda_politica_do_pai(self, empty_state_dir):
        """RED → GREEN: thread herda política do canal pai."""
        from src.core.discord.access import gate_group, default_access
        from src.core.discord.models import GroupPolicy

        access = default_access()
        access.groups["111111111"] = GroupPolicy(require_mention=False, allow_from=[])

        # Thread com parent_id no groups
        result = gate_group(
            access=access,
            channel_id="222222222",  # ID da thread
            sender_id="123456789",
            is_thread=True,
            parent_id="111111111",
        )

        assert result.action == "deliver"


class TestPairingCode:
    """Testes para códigos de pareamento."""

    def test_generate_pairing_code_gera_6_chars(self):
        """RED → GREEN: generate_pairing_code() gera código de 6 chars hex."""
        from src.core.discord.access import generate_pairing_code

        code = generate_pairing_code()

        assert len(code) == 6
        assert all(c in "0123456789abcdef" for c in code)

    def test_generate_pairing_code_gera_codigos_unicos(self):
        """RED → GREEN: generate_pairing_code() gera códigos únicos."""
        from src.core.discord.access import generate_pairing_code

        codes = {generate_pairing_code() for _ in range(100)}

        # Probabilidade de colisão é muito baixa
        assert len(codes) == 100
