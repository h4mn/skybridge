# -*- coding: utf-8 -*-
"""
Discord Facade Sandbox - CLI.

Execute: python -m src.core.discord.facade.sandbox
"""

import asyncio


async def main():
    """Ponto de entrada para as demonstracoes."""
    import sys

    from .demo_handlers import run_all_demos
    from .demo_integration import run_integration_demos

    print("\nDISCORD DDD - SANDBOX")
    print("=" * 40)
    print("1. Handlers Demo")
    print("2. Integration Demo")
    print("3. All Demos")
    print("=" * 40)

    choice = input("\nEscolha uma opcao (1-3): ").strip()

    if choice == "1":
        await run_all_demos()
    elif choice == "2":
        await run_integration_demos()
    elif choice == "3":
        await run_all_demos()
        print()
        await run_integration_demos()
    else:
        print("Opcao invalida!")


if __name__ == "__main__":
    asyncio.run(main())
