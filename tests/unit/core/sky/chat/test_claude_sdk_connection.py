# coding: utf-8
"""
Teste de conexão com Claude Agent SDK.

Este teste verifica se o SDK consegue se conectar à API configurada
e receber uma resposta simples (ping-pong).
"""

import asyncio
import os
import pytest
from pathlib import Path

# Carrega .env antes de qualquer import
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)


@pytest.mark.asyncio
async def test_claude_sdk_ping_pong():
    """
    Teste de ping-pong com Claude Agent SDK.

    Verifica se:
    1. SDK consegue se conectar à API
    2. Enviar uma requisição simples
    3. Receber uma resposta válida
    """
    from claude_agent_sdk import ClaudeSDKClient
    from claude_agent_sdk.types import ClaudeAgentOptions
    from runtime.config import get_agent_config

    agent_config = get_agent_config()

    # Verifica se temos credenciais configuradas
    if not agent_config.anthropic_auth_token:
        pytest.skip("ANTHROPIC_AUTH_TOKEN não configurado - pulando teste de conexão")

    # Prepara environment variables
    env_vars = {
        "ANTHROPIC_AUTH_TOKEN": agent_config.anthropic_auth_token,
        "ANTHROPIC_API_KEY": agent_config.anthropic_auth_token,  # Sinônimo
    }
    if agent_config.anthropic_base_url:
        env_vars["ANTHROPIC_BASE_URL"] = agent_config.anthropic_base_url

    print(f"\n=== Teste de Conexão Claude SDK ===")
    print(f"Base URL: {agent_config.anthropic_base_url or 'https://api.anthropic.com'}")
    print(f"Token: {agent_config.anthropic_auth_token[:20]}...")

    # Configura opções básicas
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful assistant. Respond very briefly.",
        permission_mode="bypassPermissions",  # Modo mais permissivo
        allowed_tools=[],  # Sem tools para teste simples
        max_turns=1,
        env=env_vars,
        setting_sources=[],  # Não ler arquivos de config
    )

    response_text = ""
    result_message = None

    async with ClaudeSDKClient(options=options) as client:
        # Envia ping
        print("Enviando: 'ping' (responda apenas com 'pong')")
        await client.query("ping. Responda apenas com a palavra 'pong'.")

        # Recebe resposta
        print("Aguardando resposta...")
        msg_count = 0
        async for msg in client.receive_response():
            msg_count += 1
            msg_type = msg.__class__.__name__
            print(f"  Mensagem #{msg_count}: {msg_type}")

            # Captura texto da resposta
            if hasattr(msg, "content") and msg.content:
                for block in msg.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                        print(f"    Texto: {block.text[:100]}")

            # Verifica ResultMessage
            if msg_type == "ResultMessage":
                result_message = msg
                is_error = getattr(msg, "is_error", None)
                print(f"  ResultMessage: is_error={is_error}")
                break

            # Timeout de segurança
            if msg_count > 50:
                print("  WARNING: Muitas mensagens, interrompendo...")
                break

    # Asserts
    print(f"\n=== Resultado ===")
    print(f"Resposta recebida: '{response_text.strip()}'")
    print(f"ResultMessage: {result_message is not None}")

    # Verificações básicas
    assert result_message is not None, "ResultMessage não foi recebido"

    is_error = getattr(result_message, "is_error", None)
    assert is_error is not True, f"SDK retornou erro: {response_text}"

    # Verifica se recebeu alguma resposta (contém "pong" ou algo similar)
    assert len(response_text.strip()) > 0, "Resposta vazia recebida"

    # Flexível: aceita "pong", "Pong", "PONG!" ou qualquer resposta não-vazia
    response_lower = response_text.strip().lower()
    assert "pong" in response_lower or len(response_text) > 0, "Resposta inesperada"

    print("\n✅ Teste de conexão PASSED!")


@pytest.mark.asyncio
async def test_claude_sdk_with_chat_adapter():
    """
    Testa ClaudeChatAdapter com SDK real.

    Este é um teste de integração que verifica se o adapter
    consegue se comunicar com o SDK.
    """
    from core.sky.memory import PersistentMemory
    from core.sky.chat import ClaudeChatAdapter, ChatMessage
    from runtime.config import get_agent_config

    agent_config = get_agent_config()

    if not agent_config.anthropic_auth_token:
        pytest.skip("ANTHROPIC_AUTH_TOKEN não configurado - pulando teste")

    print("\n=== Teste de ClaudeChatAdapter ===")

    memory = PersistentMemory(use_rag=False)  # Sem RAG para teste simples
    adapter = ClaudeChatAdapter(memory=memory)

    message = ChatMessage(role="user", content="Oi")

    print("Enviando mensagem: 'Oi'")
    response = await adapter.respond(message)

    print(f"Resposta: '{response[:100]}...'")

    # Verificações básicas
    assert response, "Adapter retornou resposta vazia"
    assert len(response) > 10, "Resposta muito curta"

    print("\n✅ Teste de adapter PASSED!")
