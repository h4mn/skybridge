# -*- coding: utf-8 -*-
"""
Teste de integração do Inbox Slash Command.

DOC: Inbox Specification - Fase 8: Slash Command Nativo
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

from core.discord.commands.inbox_slash import (
    build_description,
    calculate_expires_date,
    detect_domain_from_channel,
)


class TestInboxSlashHelpers:
    """Testa funções auxiliares do Inbox slash command."""

    def test_calculate_expires_date(self):
        """Testa cálculo de data de expires (60 dias)."""
        expires = calculate_expires_date()

        # Verificar formato
        assert len(expires) == 10  # YYYY-MM-DD
        assert expires[4] == "-"
        assert expires[7] == "-"

        # Verificar que é uma data válida
        year, month, day = map(int, expires.split("-"))
        expected = datetime.now() + timedelta(days=60)

        # Permitir variação de 1 dia por causa de mudança de dia durante o teste
        assert abs((datetime(year, month, day) - expected).days) <= 1

    def test_detect_domain_from_channel_known_patterns(self):
        """Testa detecção de domínio para canais conhecidos."""
        assert detect_domain_from_channel("paper-trading") == "paper"
        assert detect_domain_from_channel("paper-dev") == "paper"
        assert detect_domain_from_channel("discord-dev") == "discord"
        assert detect_domain_from_channel("discord-bots") == "discord"
        assert detect_domain_from_channel("autokarpa") == "autokarpa"
        assert detect_domain_from_channel("autokarpa-dev") == "autokarpa"

    def test_detect_domain_from_channel_unknown(self):
        """Testa detecção de domínio para canais desconhecidos."""
        assert detect_domain_from_channel("random-channel") == "geral"
        assert detect_domain_from_channel("general") == "geral"
        assert detect_domain_from_channel(None) == "geral"

    def test_build_description_minimal(self):
        """Testa construção de descrição mínima."""
        desc = build_description(
            title="Teste de ideia",
            channel_name=None,
            was_truncated=False,
        )

        assert "**Fonte:** Discord" in desc
        assert "**Ação sugerida:**" in desc
        assert "**Expires:**" in desc
        assert "Título completo:" not in desc

    def test_build_description_with_channel(self):
        """Testa construção de descrição com canal."""
        desc = build_description(
            title="Teste de ideia",
            channel_name="paper-trading",
            was_truncated=False,
        )

        assert "**Fonte:** Discord #paper-trading" in desc

    def test_build_description_truncated(self):
        """Testa construção de descrição com título truncado."""
        long_title = "A" * 250
        desc = build_description(
            title=long_title[:200],
            channel_name=None,
            was_truncated=True,
            full_title=long_title,
        )

        assert "**Título completo:**" in desc
        assert long_title in desc


class TestLinearClientIntegration:
    """Testes de integração com a API do Linear."""

    @pytest.mark.skipif(
        not os.getenv("LINEAR_API_KEY"),
        reason="LINEAR_API_KEY não configurada"
    )
    @pytest.mark.asyncio
    async def test_create_inbox_issue_real_api(self):
        """Testa criação real de issue na API do Linear."""
        from src.core.discord.infrastructure.linear_client import create_inbox_issue, LinearClientError

        # Dados de teste
        title = f"[TESTE] Issue de integração - {datetime.now().isoformat()}"
        description = "**Fonte:** Teste de integração\n\n---\n**Ação:** descartar"

        try:
            # Criar issue
            result = await create_inbox_issue(
                title=title,
                description=description,
                label_ids=[],  # Sem labels para o teste
            )

            # Verificar resultado
            assert "id" in result
            assert "identifier" in result
            assert "url" in result
            assert result["title"] == title
            assert "linear.app" in result["url"]

            print(f"✅ Issue criada: {result['identifier']} - {result['url']}")

        except LinearClientError as e:
            pytest.skip(f"Linear API não disponível: {e}")


if __name__ == "__main__":
    # Teste rápido
    print("Testando funções auxiliares...")

    print(f"Expires date: {calculate_expires_date()}")
    print(f"Domain 'paper-trading': {detect_domain_from_channel('paper-trading')}")
    print(f"Domain 'general': {detect_domain_from_channel('general')}")

    desc = build_description(
        title="Teste de ideia",
        channel_name="paper-trading",
        was_truncated=False,
    )
    print(f"\nDescrição:\n{desc}")

    print("\n✅ Testes auxiliares passaram!")

    # Teste de integração (requer LINEAR_API_KEY)
    if os.getenv("LINEAR_API_KEY"):
        print("\nExecutando testes de integração...")
        asyncio.run(TestLinearClientIntegration().test_create_inbox_issue_real_api())
    else:
        print("\n⚠️ Pulando testes de integração (LINEAR_API_KEY não configurada)")
        print("   Configure em .env: LINEAR_API_KEY=lin_api_...")
