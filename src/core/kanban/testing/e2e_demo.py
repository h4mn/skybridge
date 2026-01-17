# -*- coding: utf-8 -*-
"""
E2E Demo — Demonstração ponta a ponta da integração completa.

Fluxo completo:
  1. Webhook GitHub chega
  2. WebhookProcessor cria card no Trello
  3. JobOrchestrator executa agente
  4. Agente atualiza card com progresso
  5. Card marcado como DONE

Este script simula TODO o fluxo que acontecerá em produção.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infra.kanban.adapters.trello_adapter import TrelloAdapter
from core.kanban.application.trello_integration_service import TrelloIntegrationService
from core.webhooks.domain.webhook_event import WebhookEvent, WebhookSource
from core.webhooks.domain.webhook_event import WebhookJob
from core.agents.mock.mock_agent import MockAgent, MockAgentConfig, MockScenario


# Webhook real do GitHub
SAMPLE_GITHUB_WEBHOOK = {
    "action": "opened",
    "issue": {
        "id": 123456789,
        "number": 42,
        "title": "[Feature] Implementar dark mode na interface do usuário",
        "body": """## Contexto
Usuários estão solicitando suporte a dark mode há meses.

## Requisitos
- Alternar entre light/dark mode
- Persistir preferência do usuário
- Aplicar em todas as páginas

## Design
- Usar CSS variables para temas
- Seguir guia de estilo do sistema
- Transições suaves entre temas

## Critérios de Aceite
- [ ] Toggle no menu de configurações
- [ ] Preferência salva em localStorage
- [ ] Dark mode segue preferência do sistema
- [ ] Testes E2E para ambos os temas""",
        "user": {
            "login": "dev-ux",
            "id": 12345,
        },
        "labels": [
            {"name": "feature"},
            {"name": "ui"},
            {"name": "good-first-issue"},
        ],
        "html_url": "https://github.com/skybridge/skybridge/issues/42",
        "state": "open",
        "created_at": "2025-01-17T00:00:00Z",
    },
    "repository": {
        "id": 987654321,
        "name": "skybridge",
        "full_name": "skybridge/skybridge",
        "owner": {
            "login": "skybridge",
        },
    },
    "sender": {
        "login": "dev-ux",
    },
}


class E2EDemo:
    """Demonstração End-to-End da integração GitHub → Trello → Agent."""

    def __init__(self, api_key: str, api_token: str, board_id: str):
        # Inicializa Trello
        trello_adapter = TrelloAdapter(api_key, api_token, board_id)
        self.trello_service = TrelloIntegrationService(trello_adapter)

        # Estado da demo
        self.card_id: str | None = None
        self.job_id: str | None = None

    def print_banner(self):
        """Imprime banner da demo."""
        print("\n" + "=" * 80)
        print("🚀 E2E DEMO - GitHub → Trello → Agent → Done")
        print("=" * 80)
        print("\nFluxo completo de integração que acontecerá em produção:")
        print("  1. 📨 Webhook GitHub chega")
        print("  2. 📋 Card criado no Trello")
        print("  3. 🤖 Agente executa")
        print("  4. 🔄 Card atualizado com progresso")
        print("  5. ✅ Card marcado como DONE")
        print()

    async def step1_receive_webhook(self) -> tuple[dict, str]:
        """Passo 1: Simula recebimento de webhook do GitHub."""
        print("=" * 80)
        print("📨 PASSO 1: Webhook GitHub Recebido")
        print("=" * 80)

        payload = SAMPLE_GITHUB_WEBHOOK
        issue_data = payload["issue"]
        issue_number = issue_data["number"]
        issue_title = issue_data["title"]
        author = issue_data["user"]["login"]

        print(f"\n📋 Issue #{issue_number}: {issue_title}")
        print(f"👤 Autor: @{author}")
        print(f"🏷️  Labels: {', '.join(l['name'] for l in issue_data['labels'])}")
        print(f"🔗 URL: {issue_data['html_url']}")

        return payload, "issues.opened"

    async def step2_create_trello_card(self, payload: dict) -> bool:
        """Passo 2: Cria card no Trello via TrelloIntegrationService."""
        print("\n" + "=" * 80)
        print("📋 PASSO 2: Criando Card no Trello")
        print("=" * 80)

        issue_data = payload["issue"]
        repository = payload["repository"]

        result = await self.trello_service.create_card_from_github_issue(
            issue_number=issue_data["number"],
            issue_title=issue_data["title"],
            issue_body=issue_data.get("body"),
            issue_url=issue_data["html_url"],
            author=issue_data["user"]["login"],
            repo_name=repository["full_name"],
            labels=[l["name"] for l in issue_data.get("labels", [])],
        )

        if result.is_err:
            print(f"❌ Erro: {result.error}")
            return False

        self.card_id = result.unwrap()
        print(f"\n✅ Card criado no Trello!")
        print(f"📋 URL: https://trello.com/c/{self.card_id}")

        return True

    async def step3_create_job(self, payload: dict) -> WebhookJob:
        """Passo 3: Cria job de processamento."""
        print("\n" + "=" * 80)
        print("⚙️  PASSO 3: Criando Job de Processamento")
        print("=" * 80)

        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id=str(payload["issue"]["number"]),
            payload=payload,
            received_at=datetime.utcnow(),
        )

        job = WebhookJob.create(event)
        job.metadata["trello_card_id"] = self.card_id

        self.job_id = job.job_id

        print(f"\n✅ Job criado: {job.job_id}")
        print(f"📋 Vinculado ao card Trello: {self.card_id}")
        print(f"📊 Status: {job.status.value}")

        return job

    async def step4_execute_agent(self, job: WebhookJob) -> bool:
        """Passo 4: Executa agente e atualiza Trello com progresso."""
        print("\n" + "=" * 80)
        print("🤖 PASSO 4: Executando Agente (com atualizações no Trello)")
        print("=" * 80)

        # Usa MockAgent para simular execução
        scenario = MockScenario.FIX_WEBHOOK_DEDUPLICATION  # Cenário realista
        config = MockAgentConfig(scenario=scenario)
        agent = MockAgent(config)

        print(f"\n📋 Cenário: {scenario.name}")
        print(f"🔄 Executando e atualizando Trello em tempo real...\n")

        try:
            async for xml in agent.execute():
                # Processa XML e atualiza Trello
                await self._update_trello_from_xml(xml)

            print("\n✅ Agente concluído!")
            return True

        except Exception as e:
            print(f"\n❌ Erro na execução: {e}")
            return False

    async def _update_trello_from_xml(self, xml: str) -> None:
        """Atualiza card no Trello baseado em XML do agente."""
        if not self.card_id:
            return

        if "<started>" in xml:
            print("  🟡 Agente iniciado...")
            await self.trello_service.adapter.add_card_comment(
                card_id=self.card_id,
                comment=f"""🟡 **Agente Iniciado**

🕐 {datetime.now().strftime('%H:%M:%S')}
📋 Job: {self.job_id}

O agente está analisando a issue e preparando implementação..."""
            )

        elif "<progress>" in xml:
            # Extrai phase e status
            phase_start = xml.find("<phase>") + 6
            phase_end = xml.find("</phase>")
            status_start = xml.find("<status>") + 7
            status_end = xml.find("</status>")

            if phase_start > 5 and phase_end > phase_start:
                phase = xml[phase_start:phase_end]
                status = xml[status_start:status_end] if status_start > 6 else "Processando..."

                print(f"  🔄 {phase}: {status}")

                await self.trello_service.adapter.add_card_comment(
                    card_id=self.card_id,
                    comment=f"""🔄 **Progresso: {phase}**

🕐 {datetime.now().strftime('%H:%M:%S')}
{status}"""
                )

        elif "<completed>" in xml:
            print("  ✅ Agente completado!")
            await self.trello_service.adapter.add_card_comment(
                card_id=self.card_id,
                comment=f"""✅ **Agente Concluído**

🕐 {datetime.now().strftime('%H:%M:%S')}

Implementação finalizada com sucesso!"""
            )

    async def step5_mark_done(self) -> bool:
        """Passo 5: Marca card como DONE no Trello."""
        print("\n" + "=" * 80)
        print("✅ PASSO 5: Marcando Card como DONE")
        print("=" * 80)

        result = await self.trello_service.mark_card_complete(
            card_id=self.card_id,
            summary="Dark mode implementado com sucesso",
            changes=[
                "DarkToggle component criado",
                "ThemeContext adicionado",
                "CSS variables para temas configuradas",
                "Preferência salva em localStorage",
                "Testes E2E adicionados",
            ],
        )

        if result.is_err:
            print(f"❌ Erro: {result.error}")
            return False

        print("\n✅ Card marcado como DONE!")
        return True

    async def run_demo(self):
        """Executa demonstração completa E2E."""
        self.print_banner()

        # Passo 1: Webhook chega
        payload, event_type = await self.step1_receive_webhook()

        # Passo 2: Cria card no Trello
        if not await self.step2_create_trello_card(payload):
            return

        # Passo 3: Cria job
        job = await self.step3_create_job(payload)

        # Passo 4: Executa agente com atualizações
        if not await self.step4_execute_agent(job):
            return

        # Passo 5: Marca como DONE
        if not await self.step5_mark_done():
            return

        # Resumo final
        print("\n" + "=" * 80)
        print("🎉 DEMONSTRAÇÃO E2E CONCLUÍDA!")
        print("=" * 80)
        print(f"\n📊 Resumo:")
        print(f"  ✅ Webhook processado: issues.opened")
        print(f"  ✅ Card criado: https://trello.com/c/{self.card_id}")
        print(f"  ✅ Job executado: {self.job_id}")
        print(f"  ✅ Card atualizado com progresso do agente")
        print(f"  ✅ Card marcado como DONE")
        print(f"\n📋 Card no Trello:")
        print(f"  🔗 https://trello.com/c/{self.card_id}")
        print("\n" + "=" * 80)
        print("💡 Em produção, este fluxo será automático:")
        print(f"   GitHub Webhook → WebhookProcessor → JobOrchestrator → Agent → Trello")
        print("=" * 80 + "\n")


async def main():
    """Função principal."""
    load_dotenv()

    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")

    if not api_key or not api_token:
        print("❌ TRELLO_API_KEY e TRELLO_API_TOKEN são obrigatórios")
        return 1

    demo = E2EDemo(api_key, api_token, board_id)
    await demo.run_demo()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
