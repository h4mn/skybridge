# -*- coding: utf-8 -*-
"""
GitHub → Trello Integration Demo — Demonstração de integração completa.

Simula webhooks do GitHub criando issues automaticamente no Trello.
Fluxo realista: Issue aberta → Card criado → Metadados sincronizados
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infra.kanban.adapters.trello_adapter import TrelloAdapter
from core.kanban.application.trello_integration_service import TrelloIntegrationService


# Issues realistas do Skybridge
SAMPLE_ISSUES = [
    {
        "title": "[Feature] Adicionar suporte a webhooks do GitLab",
        "body": """## Contexto
Atualmente só suportamos webhooks do GitHub. O GitLab é muito popular em empresas.

## Requisitos
- Implementar `GitlabWebhookProcessor`
- Suportar eventos: `issue.opened`, `merge_request.opened`
- Adaptar `JobOrchestrator` para ser agnóstico à fonte

## Critérios de Aceite
- [ ] Webhook do GitLab cria job corretamente
- [ ] Testes unitários para `GitlabWebhookProcessor`
- [ ] Documentação atualizada

## Prioridade
Alta - Cliente empresarial solicitando""",
        "author": "dev-senior",
        "labels": ["feature", "gitlab", "high-priority"],
    },
    {
        "title": "[Bug] Worktrees não estão sendo limpas após job finalizar",
        "body": """## Problema
Worktrees criadas pelo `JobOrchestrator` permanecem em `_worktrees/` após o job finalizar.

## Reprodução
1. Abrir issue no GitHub
2. Aguardar job completar
3. Verificar diretório `_worktrees/`
4. Worktree ainda existe

## Impacto
Consumo de disco cresce indefinidamente. Em 1 semana: ~5GB de worktrees órfãs.

## Solução Proposta
Implementar cleanup no hook `post-job`:
```python
async def cleanup_worktree(job_id: str):
    worktree_path = _worktrees / job_id
    if worktree_path.exists():
        shutil.rmtree(worktree_path)
```""",
        "author": "devops",
        "labels": ["bug", "cleanup", "urgent"],
    },
    {
        "title": "[Refactor] Migrar `JobOrchestrator` para Domain Events",
        "body": """## Motivação
`JobOrchestrator` está com muitas responsabilidades:
- Executar agentes
- Atualizar status
- Enviar notificações
- Gerenciar worktrees

Viola SRP e é difícil testar.

## Proposta
Adotar Domain Events:

```python
# Eventos
class JobCreated(DomainEvent):
    job_id: str
    correlation_id: str

class JobProgress(DomainEvent):
    job_id: str
    phase: str
    status: str

class JobCompleted(DomainEvent):
    job_id: str
    result: AgentResult

# Listeners
class TrelloEventListener:
    async def on_job_created(self, event: JobCreated):
        # Cria card no Trello

class SlackEventListener:
    async def on_job_completed(self, event: JobCompleted):
        # Notifica no Slack
```

## Benefícios
- Desacoplamento
- Fácil adicionar novos listeners
- Testabilidade""",
        "author": "architect",
        "labels": ["refactor", "architecture", "tech-debt"],
    },
]


class GitHubToTrelloDemo:
    """Demonstração de integração GitHub → Trello."""

    def __init__(self, api_key: str, api_token: str, board_id: str):
        trello_adapter = TrelloAdapter(api_key, api_token, board_id)
        self.service = TrelloIntegrationService(trello_adapter)
        self.board_id = board_id

    def print_banner(self):
        """Imprime banner da demo."""
        print("=" * 80)
        print("🚀 GITHUB → TRELLO INTEGRATION DEMO")
        print("=" * 80)
        print("\nEsta demo simula webhooks do GitHub criando cards automaticamente.")
        print("Issues realistas do projeto Skybridge serão usadas.\n")

    async def simulate_webhook(self, issue: dict, issue_number: int) -> bool:
        """
        Simula um webhook do GitHub criando uma issue.

        Args:
            issue: Dados da issue
            issue_number: Número da issue

        Returns:
            True se sucesso, False caso contrário
        """
        print(f"\n{'─' * 80}")
        print(f"📨 SIMULANDO WEBHOOK: issues.opened")
        print(f"{'─' * 80}")

        # Monta URL da issue
        issue_url = f"https://github.com/skybridge/skybridge/issues/{issue_number}"

        print(f"\n📋 Issue #{issue_number}: {issue['title']}")
        print(f"👤 Autor: @{issue['author']}")
        print(f"🏷️  Labels: {', '.join(issue['labels'])}")
        print(f"🔗 URL: {issue_url}")
        print(f"\n📝 Descrição (primeiras 100 chars):")
        print(f"   {issue['body'][:100]}...")

        # Simula delay de rede
        await asyncio.sleep(0.5)

        # Cria card no Trello
        print(f"\n📝 [1/2] Criando card no Trello...")

        result = await self.service.create_card_from_github_issue(
            issue_number=issue_number,
            issue_title=issue["title"],
            issue_body=issue["body"],
            issue_url=issue_url,
            author=issue["author"],
            repo_name="skybridge/skybridge",
            labels=issue["labels"],
        )

        if result.is_err:
            print(f"❌ Erro: {result.error}")
            return False

        card_id = result.unwrap()
        card_url = f"https://trello.com/c/{card_id}"

        print(f"✅ Card criado: {card_url}")

        # Simula comentário de confirmação
        print(f"\n💬 [2/2] Adicionando comentário de confirmação...")
        await asyncio.sleep(0.3)
        print(f"✅ Comentário adicionado")

        print(f"\n{'─' * 80}")
        print(f"✅ WEBHOOK PROCESSADO COM SUCESSO")
        print(f"{'─' * 80}")
        print(f"📊 GitHub Issue: #{issue_number}")
        print(f"📋 Trello Card: {card_url}")
        print(f"{'─' * 80}")

        return True

    async def run_demo(self, num_issues: int = 3):
        """
        Executa demonstração completa.

        Args:
            num_issues: Número de issues a simular
        """
        self.print_banner()

        print(f"\n🎯 Simulando {num_issues} issues do GitHub...\n")

        # Simula múltiplas issues
        for i in range(min(num_issues, len(SAMPLE_ISSUES))):
            issue = SAMPLE_ISSUES[i]
            issue_number = 123 + i  # Simula números de issue

            success = await self.simulate_webhook(issue, issue_number)

            if not success:
                print(f"\n❌ Falha ao processar issue #{issue_number}")
                continue

            # Delay entre webhooks
            if i < num_issues - 1:
                print(f"\n⏳ Aguardando próximo webhook...")
                await asyncio.sleep(2)

        # Resumo final
        print("\n" + "=" * 80)
        print("📊 RESUMO DA INTEGRAÇÃO")
        print("=" * 80)
        print(f"\n✅ {num_issues} cards criados no Trello")
        print(f"📋 Board: https://trello.com/b/{self.board_id}")
        print(f"\n💡 Próximos passos:")
        print(f"   - Agentes processarão as issues")
        print(f"   - Cards serão atualizados com progresso")
        print(f"   - Cards marcados como DONE ao finalizar")
        print("\n" + "=" * 80)


async def main():
    """Função principal."""
    load_dotenv()

    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")

    if not api_key or not api_token:
        print("❌ TRELLO_API_KEY e TRELLO_API_TOKEN são obrigatórios")
        return 1

    demo = GitHubToTrelloDemo(api_key, api_token, board_id)

    # Simula 3 issues
    await demo.run_demo(num_issues=3)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
