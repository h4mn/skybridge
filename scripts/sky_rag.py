# coding: utf-8
"""
Helper para iniciar Sky com RAG habilitado.
"""

import os
import sys
from pathlib import Path

# Habilitar RAG
os.environ["USE_RAG_MEMORY"] = "true"

# Adicionar src ao path
src_path = str(Path(__file__).parent.parent.resolve())
sys.path.insert(0, src_path)

from src.core.sky.memory import PersistentMemory, get_memory
from src.core.sky.identity import get_sky
from src.core.sky.chat import SkyChat, ChatMessage

# Garantir que memória usa RAG
memory = PersistentMemory(use_rag=True)

# Sobrescrever singleton global
import src.core.sky.memory as memory_module
memory_module._persistent_memory = memory


def main():
    """Inicia o chat interativo com RAG."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🌌 SKY - CONVERSE (RAG habilitado)              ║
╠════════════════════════════════════════════════════════════╣
║  Memória semântica ATIVADA!                               ║
║  Use: "o que eu te ensinei" para ver a diferença           ║
║  'sair' ou 'quit' para encerrar                             ║
╚════════════════════════════════════════════════════════════╝
    """)

    sky = get_sky()
    chat = SkyChat()

    while True:
        try:
            user_input = input("→ ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("sair", "quit", "exit", "q"):
                print("\n🌌 Sky: Até logo! Foi bom conversar.\n")
                break

            # Criar mensagem e obter resposta
            message = ChatMessage(role="user", content=user_input)
            response = chat.respond(message)

            print(f"\n🌌 Sky: {response}\n")

        except KeyboardInterrupt:
            print("\n\n🌌 Sky: Interrompido. Até logo!\n")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}\n")


if __name__ == "__main__":
    main()
