#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste rapido do Discord MCP - valida se o modulo esta funcionando.

Uso:
    python test_discord_mcp.py
"""
import sys
from pathlib import Path

# Adiciona src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

OK = "[OK]"
ERRO = "[ERRO]"


def test_imports():
    """Testa se todos os modulos podem ser importados."""
    print("1. Testando imports...")

    try:
        from src.core.discord import models
        print(f"   {OK} models.py")
    except Exception as e:
        print(f"   {ERRO} models.py: {e}")
        return False

    try:
        from src.core.discord import access
        print(f"   {OK} access.py")
    except Exception as e:
        print(f"   {ERRO} access.py: {e}")
        return False

    try:
        from src.core.discord import utils
        print(f"   {OK} utils.py")
    except Exception as e:
        print(f"   {ERRO} utils.py: {e}")
        return False

    try:
        from src.core.discord import client
        print(f"   {OK} client.py")
    except Exception as e:
        print(f"   {ERRO} client.py: {e}")
        return False

    try:
        from src.core.discord import server
        print(f"   {OK} server.py")
    except Exception as e:
        print(f"   {ERRO} server.py: {e}")
        return False

    return True


def test_models():
    """Testa validacao de modelos Pydantic."""
    print("\n2. Testando modelos Pydantic...")

    from src.core.discord.models import (
        ReplyInput,
        FetchMessagesInput,
        CreateThreadInput,
        Access,
    )

    try:
        reply = ReplyInput(chat_id="123", text="Hello")
        print(f"   {OK} ReplyInput: {reply.chat_id}")
    except Exception as e:
        print(f"   {ERRO} ReplyInput: {e}")
        return False

    try:
        fetch = FetchMessagesInput(channel="456", limit=50)
        print(f"   {OK} FetchMessagesInput: limit={fetch.limit}")
    except Exception as e:
        print(f"   {ERRO} FetchMessagesInput: {e}")
        return False

    try:
        thread = CreateThreadInput(
            channel_id="789",
            message_id="111",
            name="Test Thread",
            auto_archive_duration=1440
        )
        print(f"   {OK} CreateThreadInput: {thread.auto_archive_duration}min")
    except Exception as e:
        print(f"   {ERRO} CreateThreadInput: {e}")
        return False

    try:
        access = Access(dm_policy="pairing", allow_from=["123"])
        print(f"   {OK} Access: policy={access.dm_policy.value}")
    except Exception as e:
        print(f"   {ERRO} Access: {e}")
        return False

    return True


def test_utils():
    """Testa funcoes uteis."""
    print("\n3. Testando utils...")

    from src.core.discord.utils import chunk, safe_attachment_name

    try:
        text = "A" * 3000
        chunks = chunk(text, limit=1000)
        assert len(chunks) == 3
        print(f"   {OK} chunk(): {len(chunks)} chunks de {len(text)} chars")
    except Exception as e:
        print(f"   {ERRO} chunk(): {e}")
        return False

    try:
        from unittest.mock import Mock
        att = Mock()
        att.filename = "file[test].png"
        att.id = 123
        name = safe_attachment_name(att)
        assert "[" not in name and "]" not in name
        print(f"   {OK} safe_attachment_name(): {name}")
    except Exception as e:
        print(f"   {ERRO} safe_attachment_name(): {e}")
        return False

    return True


def test_access_control():
    """Testa controle de acesso."""
    print("\n4. Testando controle de acesso...")

    from src.core.discord.access import default_access, gate_dm
    from src.core.discord.models import DMPolicy

    try:
        access = default_access()
        assert access.dm_policy == DMPolicy.PAIRING
        print(f"   {OK} default_access(): policy={access.dm_policy.value}")
    except Exception as e:
        print(f"   {ERRO} default_access(): {e}")
        return False

    try:
        access = default_access()
        result = gate_dm(access, sender_id="999")
        assert result.action in ["deliver", "pair", "drop"]
        print(f"   {OK} gate_dm(): action={result.action}")
    except Exception as e:
        print(f"   {ERRO} gate_dm(): {e}")
        return False

    return True


def test_token_configured():
    """Verifica se token esta configurado."""
    print("\n5. Verificando configuracao...")

    state_dir = Path.home() / ".claude" / "channels" / "discord"
    env_file = state_dir / ".env"

    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if line.startswith("DISCORD_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()
                if token and len(token) > 50:
                    print(f"   {OK} Token configurado ({len(token)} chars)")
                    return True

    print(f"   {ERRO} Token nao configurado")
    print(f"   Configure em: {env_file}")
    return False


def main():
    """Executa todos os testes."""
    print("=" * 50)
    print("Discord MCP - Teste de Validacao")
    print("=" * 50)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Modelos", test_models()))
    results.append(("Utils", test_utils()))
    results.append(("Access Control", test_access_control()))
    results.append(("Token", test_token_configured()))

    print("\n" + "=" * 50)
    print("Resultados:")
    print("-" * 50)

    all_passed = True
    for name, passed in results:
        status = "PASSOU" if passed else "FALHOU"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 50)

    if all_passed:
        print("\nTodos os testes passaram!")
        print("\nPara testar com Discord real:")
        print("  python run_discord_mcp.py")
        return 0
    else:
        print("\nAlguns testes falharam")
        return 1


if __name__ == "__main__":
    sys.exit(main())
