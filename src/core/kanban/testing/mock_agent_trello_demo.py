# -*- coding: utf-8 -*-
"""
Mock Agent + Trello Demo — Integração completa com cenários realistas.

Demonstra o fluxo E2E:
1. Cria card no Trello com issue realista
2. Executa MockAgent com cenário Skybridge
3. Atualiza card com XML progressivo
4. Marca como DONE ao finalizar
"""

import asyncio
import os
import random
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infra.kanban.adapters.trello_adapter import TrelloAdapter
from core.agents.mock.mock_agent import MockAgent, MockAgentConfig, MockScenario


class MockAgentTrelloDemo:
    """Demonstração de MockAgent integrado com Trello."""

    def __init__(self, api_key: str, api_token: str, board_id: str):
        self.adapter = TrelloAdapter(api_key, api_token, board_id)
        self.board_id = board_id
        self.card_id: str | None = None

    async def create_card_from_scenario(self, scenario: MockScenario) -> bool:
        """Cria card no Trello a partir de um cenário."""
        print("\n📝 [1/3] Criando card no Trello...")

        # Extrai título e descrição do cenário
        description = scenario.value
        lines = description.split('\n')
        title = lines[0]

        # Adiciona cabeçalho
        full_description = f"""**[MOCK/TESTE] - Demonstração de Integração**

{description}

---
**Meta:** Este card simula a resolução de uma issue real da Skybridge.
**Início:** {datetime.now().isoformat()}
**Agente:** MockAgent v1.0
"""

        result = await self.adapter.create_card(
            title=title,
            description=full_description,
            list_name="🎯 Foco Janeiro - Março",
        )

        if result.is_ok:
            self.card_id = result.unwrap().id
            card_url = result.unwrap().url
            print(f"✅ Card criado: {card_url}")
            return True
        else:
            print(f"❌ Erro: {result.error}")
            return False

    async def run_mock_agent(self, scenario: MockScenario) -> bool:
        """Executa MockAgent e atualiza Trello com progresso."""
        print("\n🤖 [2/3] Executando MockAgent...")

        config = MockAgentConfig(scenario=scenario)
        agent = MockAgent(config)

        try:
            # Executa e processa XML
            async for xml in agent.execute():
                # Atualiza Trello com cada fase
                await self._update_trello_from_xml(xml)
                print("  📨 Progresso enviado ao Trello")

            print("✅ MockAgent concluído")
            return True

        except Exception as e:
            print(f"❌ Erro na execução: {e}")
            return False

    async def _update_trello_from_xml(self, xml: str) -> None:
        """Processa XML e atualiza card no Trello."""
        if not self.card_id:
            return

        # Parse simples do XML
        if "<started>" in xml:
            # Agente iniciou
            await self.adapter.add_card_comment(
                card_id=self.card_id,
                comment=f"""🟡 **[MOCK] Agente Iniciado**

🕐 {datetime.now().strftime('%H:%M:%S')}
O agente está analisando a issue e preparando implementação..."""
            )

        elif "<progress>" in xml:
            # Progresso intermediário
            # Extrai phase e status do XML
            phase_start = xml.find("<phase>") + 6
            phase_end = xml.find("</phase>")
            status_start = xml.find("<status>") + 7
            status_end = xml.find("</status>")

            if phase_start > 5 and phase_end > phase_start:
                phase = xml[phase_start:phase_end]
                status = xml[status_start:status_end] if status_start > 6 else "Processando..."

                await self.adapter.add_card_comment(
                    card_id=self.card_id,
                    comment=f"""🔄 **[MOCK] {phase}**

🕐 {datetime.now().strftime('%H:%M:%S')}
{status}"""
                )

        elif "<completed>" in xml:
            # Agente completou
            await self.adapter.add_card_comment(
                card_id=self.card_id,
                comment=f"""✅ **[MOCK] Concluído!**

🕐 {datetime.now().strftime('%H:%M:%S')}
Implementação finalizada com sucesso.

Ver detalhes no card para resumo completo."""
            )

    async def mark_done(self) -> bool:
        """Marca card como completo."""
        print("\n✅ [3/3] Marcando card como completo...")

        if not self.card_id:
            return False

        result = await self.adapter.add_card_comment(
            card_id=self.card_id,
            comment=f"""---
🎉 **Demonstração Concluída**

**Agente:** MockAgent
**Finalizado:** {datetime.now().isoformat()}

Este foi um teste de integração usando o MockAgent.
Em produção, o ClaudeCodeAgent executaria de forma similar.

---
*Tags: MOCK/TESTE*"""
        )

        if result.is_ok:
            print("✅ Card finalizado!")
            return True
        else:
            print(f"❌ Erro: {result.error}")
            return False

    async def run_demo(self) -> bool:
        """Executa demonstração completa."""
        print("=" * 80)
        print("🚀 MOCK AGENT + TRELLO DEMO")
        print("=" * 80)

        # Escolhe cenário aleatório
        scenario = random.choice(list(MockScenario))

        print(f"\n📋 Cenário: {scenario.name}")
        print(f"📝 {scenario.value.split(chr(10))[0]}")

        # Executa fluxo completo
        if not await self.create_card_from_scenario(scenario):
            return False

        if not await self.run_mock_agent(scenario):
            return False

        if not await self.mark_done():
            return False

        print("\n" + "=" * 80)
        print("✅ DEMONSTRAÇÃO CONCLUÍDA!")
        print("=" * 80)
        print(f"📋 Card: https://trello.com/c/{self.card_id}")
        print("=" * 80)

        return True


async def main():
    """Função principal."""
    load_dotenv()

    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")

    if not api_key or not api_token:
        print("❌ TRELLO_API_KEY e TRELLO_API_TOKEN são obrigatórios")
        return 1

    demo = MockAgentTrelloDemo(api_key, api_token, board_id)
    success = await demo.run_demo()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
