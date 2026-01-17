# -*- coding: utf-8 -*-
"""
Trello Flow Demo — Demonstração do fluxo de agentes com Trello.

Este script simula o ciclo de vida de um agente executando uma tarefa,
atualizando um card no Trello em cada etapa do fluxo.

Fluxo demonstrado:
    1. Card criado (TODO)
    2. Agente inicia execução (IN_PROGRESS)
    3. Agente processa (atualiza descrição com progresso)
    4. Agente finaliza (DONE)
"""

import asyncio
import sys
from pathlib import Path

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime
from kernel import Result
from infra.kanban.adapters.trello_adapter import TrelloAdapter
from core.kanban.domain.card import Card, CardStatus


class TrelloFlowDemo:
    """Demonstração do fluxo de trabalho com Trello."""

    def __init__(self, api_key: str, api_token: str, board_id: str):
        self.adapter = TrelloAdapter(api_key, api_token, board_id)
        self.board_id = board_id
        self.card_id: str | None = None

    async def create_card(self) -> Result[Card, str]:
        """Cria um novo card no Trello."""
        print("\n📝 [1/5] Criando card no Trello...")

        title = f"[TESTE] Agente Mock - {datetime.now().strftime('%H:%M:%S')}"
        description = """**Tarefa de Teste**

Este card demonstra o fluxo de integração entre agentes e Trello.

**Status:** 🔵 Criado
**Agente:** MockAgent v1.0
**Início:** {timestamp}

---
*Este card será atualizado automaticamente durante o teste.*""".format(
            timestamp=datetime.now().isoformat()
        )

        result = await self.adapter.create_card(
            title=title,
            description=description,
            list_name="🎯 Foco Janeiro - Março",  # Lista "To Do" do board
        )

        if result.is_ok:
            self.card_id = result.unwrap().id
            card_url = result.unwrap().url
            print(f"✅ Card criado: {card_url}")
            return result
        else:
            print(f"❌ Erro ao criar card: {result.error}")
            return result

    async def start_agent(self) -> Result[None, str]:
        """Simula o início da execução do agente."""
        print("\n🤖 [2/5] Iniciando agente mock...")

        if not self.card_id:
            return Result.err("Card ID não encontrado")

        # Adiciona comentário com status atualizado
        result = await self.adapter.add_card_comment(
            card_id=self.card_id,
            comment="""🟡 **Em Progresso**

Agente: MockAgent v1.0
Passo: Inicializando ambiente de execução...""",
        )

        if result.is_ok:
            print("✅ Status atualizado no Trello")
            return Result.ok(None)
        else:
            print(f"❌ Erro ao iniciar agente: {result.error}")
            return result

    async def agent_thinking(self) -> Result[None, str]:
        """Simula o agente processando a tarefa."""
        print("\n🧠 [3/5] Agente processando...")

        if not self.card_id:
            return Result.err("Card ID não encontrado")

        # Simula tempo de processamento
        await asyncio.sleep(2)

        # Adiciona comentário com progresso
        result = await self.adapter.add_card_comment(
            card_id=self.card_id,
            comment="""🟡 **Processando**

Passo: Analisando requisitos e planejando execução...

**Progresso:**
- ✅ Ambiente inicializado
- ✅ Dependências verificadas
- 🔄 Executando análise...""",
        )

        if result.is_ok:
            print("✅ Progresso registrado no Trello")
            return Result.ok(None)
        else:
            return Result.err(result.error)

    async def agent_executing(self) -> Result[None, str]:
        """Simula o agente executando ações."""
        print("\n⚙️  [4/5] Agente executando tarefas...")

        if not self.card_id:
            return Result.err("Card ID não encontrado")

        # Simula tempo de execução
        await asyncio.sleep(2)

        # Adiciona comentário com ações executadas
        result = await self.adapter.add_card_comment(
            card_id=self.card_id,
            comment="""🟢 **Quase pronto!**

Passo: Executando implementação...

**Progresso:**
- ✅ Ambiente inicializado
- ✅ Análise concluída
- ✅ Implementação realizada
- ✅ Testes validados
- 🔄 Finalizando...

A implementação foi concluída com sucesso!""",
        )

        if result.is_ok:
            print("✅ Ações registradas no Trello")
            return Result.ok(None)
        else:
            return Result.err(result.error)

    async def complete_task(self) -> Result[None, str]:
        """Marca a tarefa como completa."""
        print("\n✅ [5/5] Finalizando tarefa...")

        if not self.card_id:
            return Result.err("Card ID não encontrado")

        # Adiciona comentário final
        result = await self.adapter.add_card_comment(
            card_id=self.card_id,
            comment=f"""✅ **Concluído!**

Agente: MockAgent v1.0
Finalizado: {datetime.now().isoformat()}

**Resumo da Execução:**
- ✅ Ambiente inicializado
- ✅ Análise concluída
- ✅ Implementação realizada
- ✅ Testes validados
- ✅ Tarefa finalizada

Fluxo de demonstração concluído com sucesso! 🎉""",
        )

        if result.is_ok:
            print("✅ Tarefa concluída no Trello")
            return Result.ok(None)
        else:
            print(f"❌ Erro ao finalizar: {result.error}")
            return result

    async def run_full_flow(self) -> Result[None, str]:
        """Executa o fluxo completo de demonstração."""
        print("=" * 60)
        print("🚀 TRELLO FLOW DEMO - Fluxo de Agentes com Trello")
        print("=" * 60)

        # Passo 1: Criar card
        card_result = await self.create_card()
        if card_result.is_err:
            return Result.err(card_result.error)

        # Passo 2: Iniciar agente
        start_result = await self.start_agent()
        if start_result.is_err:
            return Result.err(start_result.error)

        # Passo 3: Agente pensando
        thinking_result = await self.agent_thinking()
        if thinking_result.is_err:
            return Result.err(thinking_result.error)

        # Passo 4: Agente executando
        exec_result = await self.agent_executing()
        if exec_result.is_err:
            return Result.err(exec_result.error)

        # Passo 5: Finalizar
        complete_result = await self.complete_task()
        if complete_result.is_err:
            return Result.err(complete_result.error)

        print("\n" + "=" * 60)
        print("✅ FLUXO CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"📋 Card no Trello: https://trello.com/c/{self.card_id}")
        print("=" * 60)

        return Result.ok(None)


async def main():
    """Função principal."""
    import os
    from dotenv import load_dotenv

    # Carrega variáveis do .env
    load_dotenv()

    # Carrega credenciais do ambiente
    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID", "66b525c7e00c2923ad915a6c")

    if not api_key or not api_token:
        print("❌ Erro: TRELLO_API_KEY e TRELLO_API_TOKEN são obrigatórios")
        print("   Configure essas variáveis de ambiente ou no .env")
        return 1

    print(f"📊 Board ID: {board_id}")
    print(f"🔑 API Key: {api_key[:10]}...")

    demo = TrelloFlowDemo(api_key, api_token, board_id)
    result = await demo.run_full_flow()

    if result.is_err:
        print(f"\n❌ Erro na execução: {result.error}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
