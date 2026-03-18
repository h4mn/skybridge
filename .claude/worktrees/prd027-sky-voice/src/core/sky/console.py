# coding: utf-8
"""
REPL com a Sky.

Converse com sua companheira digital.

Digite 'sair' ou 'quit' para encerrar.
Digite 'help' para ver comandos disponíveis.
"""

import sys
from core.sky.chat import SkyChat, ChatMessage


def print_sky(text: str) -> None:
    """Imprime texto formatado da Sky."""
    # Configura saída para UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print(f"\n🌌 Sky: {text}")


def print_user(text: str) -> None:
    """Imprime texto formatado do usuário."""
    print(f"\n👤 Você: {text}")


def print_help() -> None:
    """Mostra comandos disponíveis."""
    help_text = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Comandos disponíveis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 sair, quit      - Encerrar a conversa
 help            - Mostrar esta ajuda
 quem            - Perguntar "quem é você?"
 saber           - Perguntar "o que você sabe?"
 hoje            - Perguntar "o que aprendeu hoje?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(help_text)


def main():
    """REPL principal."""
    # Configura encoding para saída
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    chat = SkyChat()

    print("""
╔════════════════════════════════════════════╗
║           🌌 SKY - CONVERSE                 ║
╠════════════════════════════════════════════╣
║  Digite sua mensagem e pressione Enter      ║
║  'sair' ou 'quit' para encerrar             ║
║  'help' para ver comandos                   ║
╚════════════════════════════════════════════╝
""")

    # Primeira mensagem da Sky
    print_sky(chat.respond(ChatMessage(role="user", content="oi")))

    while True:
        try:
            # Lê entrada do usuário
            user_input = input("\n→ ").strip()

            if not user_input:
                continue

            # Comandos especiais
            if user_input.lower() in ["sair", "quit", "exit"]:
                print_sky("Até logo! Volte sempre.")
                break

            if user_input.lower() == "help":
                print_help()
                continue

            if user_input.lower() == "quem":
                user_input = "Quem é você?"

            if user_input.lower() == "saber":
                user_input = "O que você sabe?"

            if user_input.lower() == "hoje":
                user_input = "O que você aprendeu hoje?"

            # Processa mensagem e obtém resposta
            print_user(user_input)
            response = chat.respond(ChatMessage(role="user", content=user_input))
            print_sky(response)

        except KeyboardInterrupt:
            print("\n\n")
            print_sky("Você quer sair? Até logo!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
