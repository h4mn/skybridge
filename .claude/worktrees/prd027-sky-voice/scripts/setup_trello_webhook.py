# -*- coding: utf-8 -*-
"""
Script para configurar webhook do Trello.

Uso:
    python scripts/setup_trello_webhook.py [--url CALLBACK_URL]

Exemplo:
    python scripts/setup_trello_webhook.py --url http://localhost:8000/api/webhooks/trello
    python scripts/setup_trello_webhook.py --url https://abc1.ngrok-free.app/api/webhooks/trello
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Carregar variáveis do .env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # Remove comentários inline após o valor
                value = value.split("#")[0].strip()
                os.environ[key.strip()] = value


async def setup_webhook(callback_url: str, list_first: bool = False):
    """Configura webhook no Trello."""

    # Verificar credenciais
    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")

    if not api_key or not api_token:
        print("❌ Erro: Configure TRELLO_API_KEY e TRELLO_API_TOKEN")
        print("\nObtenha suas credenciais em: https://trello.com/app-key")
        return False

    if not board_id:
        print("❌ Erro: Configure TRELLO_BOARD_ID")
        return False

    print("🎯 Configurando webhook do Trello")
    print(f"   API Key: {api_key[:10]}...")
    print(f"   Token: {api_token[:20]}...")
    print(f"   Board ID: {board_id}")
    print(f"   Callback URL: {callback_url}")

    try:
        from core.kanban.application.trello_service import TrelloService
        from runtime.config.config import get_trello_kanban_lists_config
        from infra.kanban.adapters.trello_adapter import TrelloAdapter

        # Criar adapter
        adapter = TrelloAdapter(api_key, api_token, board_id)
        kanban_config = get_trello_kanban_lists_config()

        # Criar service
        service = TrelloService(trello_adapter=adapter, kanban_config=kanban_config)

        # Listar webhooks existentes
        if list_first:
            print("\n📋 Webhooks existentes:")
            list_result = await adapter.list_webhooks()
            if list_result.is_ok:
                webhooks = list_result.unwrap()
                for wh in webhooks:
                    active = "✅" if wh.get("active") else "❌"
                    print(f"   {active} {wh.get('id')}")
                    print(f"      URL: {wh.get('callbackURL')}")
                    print(f"      Desc: {wh.get('description', 'N/A')}")
            else:
                print(f"   Erro ao listar: {list_result.error}")

        # Configurar webhook
        print("\n🔧 Configurando webhook...")
        result = await service.setup_webhook(
            callback_url=callback_url,
            description="Skybridge Trello Webhook"
        )

        if result.is_ok:
            webhook = result.unwrap()
            print(f"\n✅ Webhook configurado com sucesso!")
            print(f"   ID: {webhook.get('id')}")
            print(f"   URL: {webhook.get('callbackURL')}")
            print(f"   Description: {webhook.get('description')}")
            print(f"   Active: {webhook.get('active')}")
        else:
            print(f"\n❌ Erro: {result.error}")
            return False

        # Fechar adapter
        await adapter._close()

        print("\n" + "=" * 50)
        print("✅ Setup concluído!")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"\n❌ Erro durante setup: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Configura webhook do Trello")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/webhooks/trello",
        help="URL de callback (default: http://localhost:8000/api/webhooks/trello)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar webhooks existentes antes de configurar"
    )

    args = parser.parse_args()

    success = asyncio.run(setup_webhook(args.url, args.list))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
