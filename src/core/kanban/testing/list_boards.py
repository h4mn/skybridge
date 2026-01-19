# -*- coding: utf-8 -*-
"""
List Trello Boards — Lista todos os boards disponíveis.

Script simples para descobrir o ID dos boards do Trello.
"""

import asyncio
import os
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
from infra.kanban.adapters.trello_adapter import TrelloAdapter


async def main():
    load_dotenv()

    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")

    if not api_key or not api_token:
        print("❌ TRELLO_API_KEY e TRELLO_API_TOKEN são obrigatórios")
        return 1

    adapter = TrelloAdapter(api_key, api_token)
    result = await adapter.list_boards()

    if result.is_ok:
        boards = result.unwrap()
        print(f"\n📋 {len(boards)} BOARDS DISPONÍVEIS:")
        print("=" * 80)

        for b in boards:
            print(f"\nNome: {b.get('name', 'N/A')}")
            print(f"ID:   {b.get('id', 'N/A')}")
            print(f"URL:  {b.get('url', 'N/A')}")
            print("-" * 80)

        # Mostra como usar
        print("\n💡 Para usar um board no .env:")
        print(f"   TRELLO_BOARD_ID={boards[0]['id']}")
    else:
        print(f"❌ Erro: {result.error}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
