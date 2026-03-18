# -*- coding: utf-8 -*-
"""
Script de teste para integração Kanban + Trello.

Uso:
    export TRELLO_API_KEY="sua_api_key"
    export TRELLO_API_TOKEN="seu_token"
    python scripts/test_kanban_trello.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Carregar variáveis do .env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

from infra.kanban.adapters.trello_adapter import create_trello_adapter


async def main():
    """Testa integração com Trello."""

    # Verificar credenciais
    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")

    if not api_key or not api_token:
        print("❌ Erro: Configure TRELLO_API_KEY e TRELLO_API_TOKEN")
        print("\nObtenha suas credenciais em: https://trello.com/app-key")
        print("\nExemplo:")
        print('  export TRELLO_API_KEY="sua_api_key"')
        print('  export TRELLO_API_TOKEN="seu_token"')
        sys.exit(1)

    print("🎯 Testando integração Kanban + Trello")
    print(f"   API Key: {api_key[:10]}...")
    print(f"   Token: {api_token[:20]}...")

    try:
        # Criar adapter
        adapter = create_trello_adapter(api_key, api_token)
        print("\n✅ Adapter criado com sucesso!")

        # Test 1: Buscar board público de exemplo
        print("\n📋 Teste 1: Buscar board público...")
        result = await adapter.get_board("5e88ae2f2f103936713e7e3c")

        if result.is_ok:
            board = result.unwrap()
            print(f"   ✅ Board encontrado: {board.name}")
            print(f"   📎 URL: {board.url}")
        else:
            print(f"   ❌ Erro: {result.error}")

        # Test 2: Listar cards do board
        print("\n📋 Teste 2: Listar cards do board...")
        result = await adapter.list_cards(board_id="5e88ae2f2f103936713e7e3c")

        if result.is_ok:
            cards = result.unwrap()
            print(f"   ✅ Encontrados {len(cards)} cards")
            for card in cards[:5]:  # Mostrar primeiros 5
                print(f"   - {card.title[:40]}... [{card.status.value}]")
        else:
            print(f"   ❌ Erro: {result.error}")

        # Test 3: Listar boards do usuário
        print("\n📋 Teste 3: Listar seus boards Skybridge...")
        result = await adapter.list_cards(board_id="65439d2c57a4d14b94f3c239")  # SkyBridge-01

        if result.is_ok:
            cards = result.unwrap()
            print(f"   ✅ Encontrados {len(cards)} cards no board SkyBridge-01")
            for card in cards[:5]:
                print(f"   - {card.title[:40]}... [{card.status.value}]")
        else:
            print(f"   ❌ Erro: {result.error}")

        # Fechar adapter
        await adapter._close()

        print("\n" + "=" * 50)
        print("✅ Testes concluídos com sucesso!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Erro durante testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
