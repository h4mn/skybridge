# -*- coding: utf-8 -*-
"""
DEMO FLUXO COMPLETO - GitHub REAL + Webhook Server + Trello REAL

Estratégia Inteligente da Dupla:
1. FakeGitHubAgent cria issues REAIS no GitHub (realed source)
2. GitHub dispara webhook REAL para nosso servidor
3. WebhookProcessor processa e cria card no Trello REAL
4. JobOrchestrator executa e atualiza Trello em tempo real

Status Taxonomy:
- realed: Componente 100% real, dados reais (GitHub, Trello, WebhookProcessor)
- mocked: Componente mockado (FakeGitHubAgent, MockAgent)
- paused: Componente real mas desativado temporariamente

Fluxo:
    ┌─────────────────────────────────────────────────────────────┐
    │                                                              │
    │  FakeGitHubAgent ──► Issue REAL no GitHub ──► Webhook REAL  │
    │       (realed source)         (realed source)    (realed)    │
    │                                                              │
    │           ▼                                                  │
    │  Webhook Server (localhost:8000 via ngrok)                  │
    │           (realed)                                            │
    │                                                              │
    │           ▼                                                  │
    │  WebhookProcessor ──► JobQueue ──► JobOrchestrator         │
    │       (realed)           (paused)         (realed)          │
    │                                                              │
    │           ▼                                                  │
    │  TrelloIntegrationService ──► Card REAL no Trello           │
    │           (realed)                  (realed source)         │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.agents.mock.mock_github_agent import (
    FakeGitHubAgent,
    RealisticIssueTemplates,
    ComponentStatus,
)
from dotenv import load_dotenv


class FlowOrchestrator:
    """
    Orquestra o fluxo completo de testes.

    Responsabilidades:
    - Criar issues reais via FakeGitHubAgent
    - Aguardar webhooks serem processados
    - Verificar cards no Trello
    - Cleanup (fechar issues de teste)
    """

    def __init__(
        self,
        github_token: str,
        github_repo: str,
        trello_api_key: str,
        trello_api_token: str,
        trello_board_id: str,
    ):
        """
        Inicializa orquestrador.

        Args:
            github_token: Token do GitHub para criar issues
            github_repo: Repositório (owner/repo)
            trello_api_key: API key do Trello
            trello_api_token: Token do Trello
            trello_board_id: ID do board Trello
        """
        owner, name = github_repo.split("/", 1)
        self.github_agent = FakeGitHubAgent(owner, name, github_token)
        self.github_repo = github_repo

        # Trello integration (opcional para demo, apenas verificação)
        self.trello_api_key = trello_api_key
        self.trello_api_token = trello_api_token
        self.trello_board_id = trello_board_id

    def print_banner(self):
        """Banner épico do fluxo completo."""
        print("\n" + "=" * 80)
        print("🚀 FLUXO COMPLETO - Dupla Inteligente Sky + Você")
        print("=" * 80)
        print("\n💡 Estratégia:")
        print("   1. FakeGitHubAgent cria issues REAIS no GitHub")
        print("   2. GitHub dispara webhook REAL para ngrok → localhost")
        print("   3. WebhookProcessor processa e cria card no Trello")
        print("   4. JobOrchestrator executa e atualiza Trello")
        print("\n📊 Status Taxonomy:")
        print(f"   • FakeGitHubAgent: {ComponentStatus.MOCKED.value} (cria issues reais)")
        print(f"   • GitHub source: {ComponentStatus.REALED.value} (issues de verdade)")
        print(f"   • Webhook Server: {ComponentStatus.REALED.value} (FastAPI real)")
        print(f"   • WebhookProcessor: {ComponentStatus.REALED.value} (pronto)")
        print(f"   • JobQueue: {ComponentStatus.PAUSED.value} (InMemory)")
        print(f"   • JobOrchestrator: {ComponentStatus.REALED.value} (com Trello)")
        print(f"   • Trello source: {ComponentStatus.REALED.value} (cards de verdade)")
        print("\n" + "=" * 80)

    def print_prerequisites(self):
        """Imprime pré-requisitos."""
        print("\n📋 PRÉ-REQUISITOS:")
        print("\n1️⃣  Configurar ngrok:")
        print("   ngrok http 8000")
        print("   → Copie a URL HTTPS (ex: https://abc1.ngrok-free.app)")
        print("\n2️⃣  Iniciar Webhook Server:")
        print("   cd B:\\_repositorios\\skybridge-worktrees\\kanban")
        print("   python src/core/webhooks/infrastructure/github_webhook_server.py")
        print("\n3️⃣  Configurar Webhook no GitHub:")
        print(f"   Repository: {self.github_repo}")
        print("   Settings → Webhooks → Add webhook")
        print("   Payload URL: https://SEU-NGROK-URL.ngrok-free.app/webhook/github")
        print("   Content type: application/json")
        print("   Events: Issues → Issues only (opened, edited, closed)")
        print("\n4️⃣  Configurar Variáveis de Ambiente:")
        print("   GITHUB_TOKEN=seu_token_aqui")
        print("   GITHUB_REPO=owner/repo")
        print("   TRELLO_API_KEY=sua_key")
        print("   TRELLO_API_TOKEN=seu_token")
        print("   TRELLO_BOARD_ID=seu_board_id")
        print("\n" + "=" * 80)

    async def run_demo(
        self,
        num_issues: int = 1,
        delay_between_issues: float = 5.0,
    ):
        """
        Executa demo do fluxo completo.

        Args:
            num_issues: Número de issues para criar (padrão: 1)
            delay_between_issues: Delay entre issues (padrão: 5s)

        Fluxo:
            1. Mostra pré-requisitos
            2. Aguarda confirmação do usuário
            3. Cria issues reais no GitHub
            4. Aguarda webhooks serem processados
            5. Mostra resultado
        """
        self.print_banner()
        self.print_prerequisites()

        # Aguarda confirmação
        print("\n⚠️  VERIFIQUE:")
        print("   [ ] ngrok rodando")
        print("   [ ] Webhook server rodando")
        print("   [ ] Webhook configurado no GitHub")
        print("\nPressione ENTER quando tudo estiver pronto...")
        input()

        # Templates de issues
        templates = RealisticIssueTemplates()
        available_issues = [
            templates.fuzzy_search_feature(),
            templates.webhook_deduplication_bug(),
            templates.trello_integration_feature(),
            templates.agent_orchestrator_refactor(),
            templates.rate_limiting_feature(),
        ]

        # Seleciona issues
        issues_to_create = available_issues[:num_issues]

        print(f"\n📝 Criando {len(issues_to_create)} issue(s) de teste...")
        print(f"📦 Repositório: {self.github_repo}")
        print(f"⏱️  Delay entre issues: {delay_between_issues}s\n")

        # Cria issues
        results = await self.github_agent.create_multiple_issues(
            issues_to_create,
            delay=delay_between_issues,
        )

        # Resultado
        created = sum(1 for r in results if r)
        print(f"\n✅ {created}/{len(issues_to_create)} issues criadas com sucesso!")

        # Extrai informações das issues criadas
        print("\n📊 Issues Criadas:")
        for i, response in enumerate(results):
            if response:
                issue_data = response.json()
                print(f"\n  {i+1}. Issue #{issue_data['number']}: {issue_data['title']}")
                print(f"     URL: {issue_data['html_url']}")
                print(f"     Labels: {', '.join(l['name'] for l in issue_data['labels'])}")

        print("\n" + "=" * 80)
        print("🎉 FLUXO INICIADO!")
        print("=" * 80)
        print("\n💡 O que acontece AGORA:")
        print("   1. GitHub envia webhook para seu servidor via ngrok")
        print("   2. WebhookProcessor recebe e processa")
        print("   3. Trello card é criado automaticamente")
        print("   4. JobOrchestrator executa (se configurado)")
        print("   5. Trello card é atualizado em tempo real")
        print("\n💡 Acompanhe:")
        print("   • Logs do webhook server (terminal onde está rodando)")
        print("   • Board do Trello (cards devem aparecer)")
        print(f"   • Issues no GitHub: https://github.com/{self.github_repo}/issues")
        print("\n" + "=" * 80)

        # Menu de cleanup
        print("\n🧹 CLEANUP:")
        print("   Deseja fechar as issues de teste? (s/n)")
        choice = input("> ").strip().lower()

        if choice == 's':
            print("\n🔒 Fechando issues de teste...")
            closed = await self.github_agent.close_all_test_issues()
            print(f"✅ {len(closed)} issue(s) fechada(s)")

        await self.github_agent.close()

    async def cleanup_test_issues(self):
        """Apenas fecha issues de teste existentes."""
        print("\n🧹 Limpando issues de teste...")
        closed = await self.github_agent.close_all_test_issues()
        print(f"✅ {len(closed)} issue(s) fechada(s)")
        await self.github_agent.close()


async def main():
    """Função principal."""
    load_dotenv()

    # GitHub
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO", "skybridge/skybridge")

    # Trello
    trello_api_key = os.getenv("TRELLO_API_KEY")
    trello_api_token = os.getenv("TRELLO_API_TOKEN")
    trello_board_id = os.getenv("TRELLO_BOARD_ID")

    # Validação
    if not github_token:
        print("❌ GITHUB_TOKEN não configurado")
        print("💡 Crie um token em: https://github.com/settings/tokens")
        print("💡 Escopo necessário: repo (full repo access)")
        return 1

    if not trello_api_key or not trello_api_token:
        print("⚠️  Trello não configurado - cards não serão criados")
        print("💡 Configure TRELLO_API_KEY e TRELLO_API_TOKEN no .env")

    # Orquestrador
    orchestrator = FlowOrchestrator(
        github_token=github_token,
        github_repo=github_repo,
        trello_api_key=trello_api_key or "",
        trello_api_token=trello_api_token or "",
        trello_board_id=trello_board_id or "",
    )

    # Menu
    print("\n" + "=" * 80)
    print("🎯 SKYBRIDGE - FLUXO COMPLETO")
    print("=" * 80)
    print("\nEscolha uma opção:")
    print("  1. Executar demo (criar issues e testar fluxo)")
    print("  2. Limpar issues de teste")
    print("  3. Sair")

    choice = input("\n> ").strip()

    if choice == "1":
        print("\n🔢 Quantas issues criar? (1-5, padrão: 1)")
        num = input("> ").strip()
        num_issues = int(num) if num.isdigit() else 1

        await orchestrator.run_demo(num_issues=num_issues)
    elif choice == "2":
        await orchestrator.cleanup_test_issues()
    else:
        print("\n👋 Até logo!")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
