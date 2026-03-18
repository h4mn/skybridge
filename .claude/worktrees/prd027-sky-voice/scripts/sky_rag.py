# coding: utf-8
"""
Helper para iniciar Sky com RAG habilitado.

Suporta tanto chat legacy quanto chat com Claude SDK (feature flag).
"""

import asyncio
import os
import sys
from pathlib import Path

# Caminho do projeto (usado para .env e src/)
project_root = Path(__file__).parent.parent.resolve()

# Carregar variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv não está instalado, usa variáveis de ambiente do sistema
    pass

# Habilitar RAG
os.environ["USE_RAG_MEMORY"] = "true"

# Adicionar src ao path
src_path = str(project_root / "src")
sys.path.insert(0, src_path)

from core.sky.memory import PersistentMemory, get_memory
from core.sky.identity import get_sky
from core.sky.chat import SkyChat, ChatMessage

# DOC: openspec/changes/chat-claude-sdk - Script sky_rag.py Atualizado
# Feature flag para usar Claude Chat
USE_CLAUDE_CHAT = os.getenv("USE_CLAUDE_CHAT", "false").lower() in ("true", "1", "yes")

# Feature flag para usar Textual TUI
USE_TEXTUAL_UI = os.getenv("USE_TEXTUAL_UI", "false").lower() in ("true", "1", "yes")

# Garantir que memória usa RAG
memory = PersistentMemory(use_rag=True)

# Sobrescrever singleton global
import core.sky.memory as memory_module
memory_module._persistent_memory = memory


async def main_claude_async():
    """
    Loop principal do chat Claude SDK (assíncrono).

    DOC: spec.md - Cenário: Feature flag controla integração
    """
    from core.sky.chat import ClaudeChatAdapter
    from core.sky.chat.legacy_ui import ChatUI, ChatMetrics

    chat = ClaudeChatAdapter(memory=memory)
    ui = ChatUI(verbose=os.getenv("VERBOSE", "false").lower() in ("true", "1"))

    # Exibe header inicial
    ui.render_header(rag_enabled=True, memory_count=0)

    session_metrics = []

    # Estado para operações pendentes
    pending_operation = None  # None, "new_session"

    while True:
        try:
            user_input = input("→ ").strip()

            if not user_input:
                continue

            # Comandos especiais
            # DOC: spec.md - Cenário: Comando /new limpa histórico
            if user_input.lower() == "/new":
                if len(chat.get_history()) > 5:
                    pending_operation = "new_session"
                    confirm = input("Limpar sessão? (s/N, /cancel para cancelar): ").strip().lower()
                    pending_operation = None
                    if confirm in ("cancel", "/cancel"):
                        print("Operação cancelada.")
                        continue
                    if confirm not in ("s", "y", "sim"):
                        print("Sessão mantida.")
                        continue
                chat.clear_history()
                print("✅ Nova sessão iniciada.")
                ui.render_header(rag_enabled=True, memory_count=0)
                continue

            # DOC: spec.md - Cenário: /cancel cancela operação pendente
            if user_input.lower() == "/cancel":
                if pending_operation:
                    print(f"✅ Operação '{pending_operation}' cancelada.")
                    pending_operation = None
                else:
                    print("Nenhuma operação pendente para cancelar.")
                continue

            if user_input.lower() in ("sair", "quit", "exit", "q"):
                # DOC: spec.md - Cenário: Resumo ao encerrar sessão
                ui.render_session_summary(session_metrics)
                print("\n🌌 Sky: Até logo! Foi bom conversar.\n")
                break

            # Criar mensagem e obter resposta
            message = ChatMessage(role="user", content=user_input)

            # Exibir thinking
            ui.render_thinking()

            # Obter resposta (await pois respond() é async)
            response = await chat.respond(message)

            # Criar métricas
            metrics = ChatMetrics(
                latency_ms=chat._last_latency_ms,
                tokens_in=chat._last_tokens_in,
                tokens_out=chat._last_tokens_out,
                memory_hits=0,  # TODO: obter do adapter
                model=os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL", os.getenv("CLAUDE_MODEL", "haiku")),
            )
            session_metrics.append(metrics)

            # Exibir memórias usadas (se houver)
            # ui.render_memory([])  # TODO: obter memórias do adapter

            # Exibir resposta
            ui.render_message("sky", response, metrics=metrics if ui.verbose else None)

        except KeyboardInterrupt:
            print("\n\n🌌 Sky: Interrompido. Até logo!\n")
            break
        except Exception as e:
            # DOC: spec.md - Cenário: Adicionar tratamento de exceções com fallback
            print(f"\n❌ Erro: {e}\n")
            # Fallback automático está implementado no adapter


def main():
    """Inicia o chat interativo com RAG."""
    chat_type = "Textual TUI" if USE_TEXTUAL_UI else ("Claude SDK" if USE_CLAUDE_CHAT else "Legacy")

    sky = get_sky()

    # DOC: spec.md - Cenário: Feature flag controla integração
    # DOC: "Criar instância de adapter ou SkyChat baseado na flag"

    # Prioridade: Textual TUI > Claude SDK > Legacy
    if USE_TEXTUAL_UI:
        # Chat Textual TUI
        from core.sky.chat.textual_ui import SkyApp
        app = SkyApp()
        app.run()

    elif USE_CLAUDE_CHAT:
        # Chat Claude SDK é assíncrono - usa asyncio.run()
        asyncio.run(main_claude_async())

    else:
        # Chat legacy
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
