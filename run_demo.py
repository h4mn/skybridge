# -*- coding: utf-8 -*-
"""Script para executar a demo SPEC009 com carregamento do .env."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from runtime.demo.scenarios.spec009_e2e_demo import SPEC009InteractiveDemo
from runtime.demo.base import DemoContext


async def main():
    # Carrega .env
    load_dotenv()

    # Cria demo
    demo = SPEC009InteractiveDemo()

    # Cria contexto
    context = DemoContext(
        demo_id="spec009-interactive",
        params={"branch": "refactor/system-prompt-pt-br"},
    )

    # Executa demo
    result = await demo.run(context)

    # Exibe resultado
    if result.success:
        print(f"\n✅ {result.message}")
    else:
        print(f"\n❌ {result.message}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
