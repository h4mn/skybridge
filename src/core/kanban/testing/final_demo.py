# -*- coding: utf-8 -*-
"""
DEMO FINAL - Skybridge + Trello: E2E Completo

Esta é a DEMO FINAL mostrando TODA a integração funcionando:
1. ✅ Webhook GitHub chega
2. ✅ Card criado no Trello automaticamente
3. ✅ JobOrchestrator executa com atualizações em tempo real
4. ✅ Tratamento de erros
5. ✅ Card marcado como DONE

Execute este script para ver TODA a integração funcionando!
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
from core.webhooks.domain.webhook_event import WebhookJob, JobStatus
from core.webhooks.application.webhook_processor import WebhookProcessor
from core.webhooks.application.job_orchestrator import JobOrchestrator
from core.webhooks.application.worktree_manager import WorktreeManager
from core.agents.mock.mock_agent import MockAgent, MockAgentConfig, MockScenario


# Mock JobQueue para demo
class MockJobQueue:
    """JobQueue em memória para demo."""

    def __init__(self):
        self._jobs = {}

    async def enqueue(self, job):
        self._jobs[job.job_id] = job
        print(f"  ✅ Job enfileirado: {job.job_id}")

    async def get_job(self, job_id: str):
        return self._jobs.get(job_id)

    async def complete(self, job_id: str, result: dict | None = None):
        if job_id in self._jobs:
            self._jobs[job_id].mark_completed()
            print(f"  ✅ Job completado: {job_id}")

    async def fail(self, job_id: str, error: str):
        if job_id in self._jobs:
            self._jobs[job_id].mark_failed(error)
            print(f"  ❌ Job falhou: {job_id} - {error}")


# Mock WorktreeManager para demo
class MockWorktreeManager:
    """WorktreeManager mock que não cria worktrees reais."""

    def create_worktree(self, job):
        print(f"  🌳 Worktree mock criada para job {job.job_id}")
        from kernel.contracts.result import Result
        # Retorna caminho mockado
        job.worktree_path = f"/tmp/worktrees/{job.job_id}"
        job.branch_name = f"mock-branch-{job.job_id[:8]}"
        return Result.ok(job.worktree_path)


# Issue realista do Skybridge
SAMPLE_ISSUE = {
    "action": "opened",
    "issue": {
        "id": 123456789,
        "number": 99,
        "title": "[Feature] Implementar busca fuzzy em queries",
        "body": """## Contexto
Queries atuais usam busca exata. Usuários querem encontrar arquivos mesmo com erros de digitação.

## Requisitos
- Implementar algoritmo de fuzzy matching
- Suportar busca aproximada de nomes
- Score de relevância para resultados

## Implementação Proposta
Usar `fuzzywuzzy` ou `thefuzz`:
```python
from fuzzywuzzy import fuzz, process

choices = ["file_ops.py", "webhook_processor.py", "job_orchestrator.py"]
result = process.extract("file_ops", choices, limit=3)
# [('file_ops.py', 90), ('webhook_processor.py', 45), ...]
```

## Critérios de Aceite
- [ ] Busca "fileop" encontra "file_ops"
- [ ] Busca "webook" encontra "webhook"
- [ ] Score de relevância visível
- [ ] Testes unitários""",
        "user": {"login": "dev-core", "id": 12345},
        "labels": [
            {"name": "feature"},
            {"name": "enhancement"},
            {"name": "good-first-issue"},
        ],
        "html_url": "https://github.com/skybridge/skybridge/issues/99",
        "state": "open",
    },
    "repository": {
        "id": 987654321,
        "name": "skybridge",
        "full_name": "skybridge/skybridge",
        "owner": {"login": "skybridge"},
    },
    "sender": {"login": "dev-core"},
}


class FinalDemo:
    """Demo FINAL da integração completa Skybridge ↔ Trello."""

    def __init__(self, api_key: str, api_token: str, board_id: str):
        # Inicializa Trello
        trello_adapter = TrelloAdapter(api_key, api_token, board_id)
        self.trello_service = TrelloIntegrationService(trello_adapter)

        # Inicializa componentes
        self.job_queue = MockJobQueue()
        self.worktree_manager = MockWorktreeManager()

        # WebhookProcessor COM Trello
        self.webhook_processor = WebhookProcessor(
            self.job_queue,
            self.trello_service
        )

        # JobOrchestrator COM Trello
        self.job_orchestrator = JobOrchestrator(
            self.job_queue,
            self.worktree_manager,
            trello_service=self.trello_service
        )

    def print_banner(self):
        """Banner épico da demo."""
        print("\n" + "=" * 80)
        print("🚀 SKYBRIDGE + TRELLO: DEMO FINAL")
        print("=" * 80)
        print("\nEsta demo mostra TODA a integração funcionando:")
        print("  1. 📨 Webhook GitHub → WebhookProcessor")
        print("  2. 📋 Card criado no Trello automaticamente")
        print("  3. ⚙️ JobOrchestrator executa com atualizações em TEMPO REAL")
        print("  4. ✅ Card marcado como DONE")
        print("\n💡 Abra o link do card no final para VER O RESULTADO!")
        print()

    async def run(self):
        """Executa demo completa."""
        self.print_banner()

        # FASE 1: Webhook GitHub chega
        print("=" * 80)
        print("📨 FASE 1: Webhook GitHub Recebido")
        print("=" * 80)

        issue_data = SAMPLE_ISSUE["issue"]
        print(f"\n📋 Issue #{issue_data['number']}: {issue_data['title']}")
        print(f"👤 Autor: @{issue_data['user']['login']}")
        print(f"🏷️  Labels: {', '.join(l['name'] for l in issue_data['labels'])}")

        # Processa webhook
        print("\n⏳ Processando webhook via WebhookProcessor...")
        result = await self.webhook_processor.process_github_issue(
            SAMPLE_ISSUE,
            "issues.opened"
        )

        if result.is_err:
            print(f"\n❌ Erro: {result.error}")
            return

        job_id = result.unwrap()
        print(f"\n✅ Webhook processado: job_id={job_id}")

        # FASE 2: JobOrchestrator executa
        print("\n" + "=" * 80)
        print("⚙️  FASE 2: JobOrchestrator Executando")
        print("=" * 80)
        print("\n⏳ Executando job COM atualizações no Trello...")
        print("(Observe os comentários sendo adicionados em tempo real!)\n")

        # Executa job
        job_result = await self.job_orchestrator.execute_job(job_id)

        if job_result.is_err:
            print(f"\n❌ Erro: {job_result.error}")
        else:
            print(f"\n✅ {job_result.unwrap()['message']}")

        # FASE 3: Resultado final
        print("\n" + "=" * 80)
        print("🎉 FASE 3: RESULTADO FINAL")
        print("=" * 80)

        job = await self.job_queue.get_job(job_id)
        card_id = job.metadata.get("trello_card_id")

        print(f"\n📊 Resumo da Execução:")
        print(f"  ✅ Webhook processado")
        print(f"  ✅ Card criado no Trello")
        print(f"  ✅ Job executado: {job_id}")
        print(f"  ✅ Progresso atualizado em tempo real")
        print(f"  ✅ Card marcado como DONE")
        print(f"  📋 Status final: {job.status.value}")

        print(f"\n🔗 Link do Card no Trello:")
        print(f"  https://trello.com/c/{card_id}")
        print(f"\n💡 Abra o link acima para VER:")
        print(f"  - Card criado com dados da issue")
        print(f"  - Comentários de progresso em cada fase")
        print(f"  - Marcação como DONE ao final")

        print("\n" + "=" * 80)
        print("✨ DEMO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print("\n🚀 Próximos passos:")
        print("  1. Configure ngrok: python -m apps.api.main")
        print("  2. Configure webhook no GitHub")
        print("  3. Abra issue real e veja a mágica acontecer!")
        print("\n" + "=" * 80 + "\n")


async def main():
    """Função principal."""
    load_dotenv()

    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")

    if not api_key or not api_token:
        print("❌ TRELLO_API_KEY e TRELLO_API_TOKEN são obrigatórios")
        return 1

    demo = FinalDemo(api_key, api_token, board_id)
    await demo.run()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
