# -*- coding: utf-8 -*-
"""
DEMO SIMPLES - GitHub → Trello (Fluxo Completo)

Este demo cria uma issue REAL no GitHub e observa:
1. Issue criada no GitHub
2. Webhook enviado para nosso servidor
3. Card criado no Trello
4. Link do card para verificar

Pré-requisitos:
- Servidor webhook rodando: python github_webhook_server.py
- Webhook configurado no GitHub: https://cunning-dear-primate.ngrok-free.app/webhook/github
"""

import asyncio
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.agents.mock.fake_github_agent import (
    FakeGitHubAgent,
    RealisticIssueTemplates,
)
from dotenv import load_dotenv
import os


async def main():
    """Executa demo simples."""
    load_dotenv()

    # Credenciais
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO", "h4mn/skybridge")

    if not github_token:
        print("❌ GITHUB_TOKEN não configurado")
        return 1

    owner, name = github_repo.split("/", 1)

    # Banner
    print("\n" + "=" * 80)
    print("🚀 DEMO: GitHub → Trello (Fluxo Completo)")
    print("=" * 80)
    print("\nEste demo cria uma issue REAL no GitHub.")
    print("O webhook configurado vai enviar para nosso servidor.")
    print("Nosso servidor cria o card no Trello automaticamente.")
    print("\n📋 Pré-requisitos:")
    print("  ✅ Webhook configurado no GitHub")
    print("  ✅ Servidor webhook rodando em localhost:8000")
    print("  ✅ Trello configurado")
    print("\n" + "=" * 80)

    # Seleciona template
    templates = RealisticIssueTemplates()

    print("\n📝 Issues disponíveis:")
    print("  1. [Feature] Implementar busca fuzzy em queries")
    print("  2. [Bug] Webhooks being processed multiple times")
    print("  3. [Feature] Integrar com Trello para visibilidade de jobs")
    print("  4. [Refactor] Simplificar JobOrchestrator com Domain Events")
    print("  5. [Feature] Rate limiting para API do Claude")

    print("\n🔢 Qual issue criar? (1-5, padrão: 1)")
    choice = input("> ").strip() or "1"

    issues_map = {
        "1": templates.fuzzy_search_feature(),
        "2": templates.webhook_deduplication_bug(),
        "3": templates.trello_integration_feature(),
        "4": templates.agent_orchestrator_refactor(),
        "5": templates.rate_limiting_feature(),
    }

    issue = issues_map.get(choice, templates.fuzzy_search_feature())

    # Cria issue
    async with FakeGitHubAgent(owner, name, github_token) as agent:
        print(f"\n📝 Criando issue: {issue.title[:60]}...")
        print(f"🏷️  Labels: {', '.join(issue.labels)}")

        response = await agent.create_issue(issue)
        data = response.json()

        print(f"\n✅ Issue #{data['number']} criada com sucesso!")
        print(f"🔗 URL: {data['html_url']}")
        print(f"📦 Estado: {data['state']}")

        print("\n" + "=" * 80)
        print("⏳ AGUARDANDO WEBHOOK...")
        print("=" * 80)
        print("\n💡 O que acontece AGORA:")
        print("   1. GitHub envia webhook para cunning-dear-primate.ngrok-free.app")
        print("   2. Webhook Server recebe e processa")
        print("   3. TrelloIntegrationService cria card")
        print("   4. Card aparece no Trello com dados da issue")
        print("\n📋 Verifique:")
        print("   • Logs do servidor webhook (terminal onde está rodando)")
        print("   • Board do Trello (cards devem aparecer em instantes)")
        print(f"   • Issue no GitHub: {data['html_url']}")

        print("\n⏱️  Aguardando 5 segundos para o webhook ser processado...")
        await asyncio.sleep(5)

        print("\n" + "=" * 80)
        print("🎯 PRÓXIMOS PASSOS")
        print("=" * 80)
        print("\n1. Verifique os logs do servidor webhook")
        print("2. Abra o board do Trello e veja o card criado")
        print("3. Abra a issue no GitHub e veja os detalhes")
        print("\n🧹 LIMPEZA:")
        print("   • Issues têm label MOCK/TESTE para fácil identificação")
        print("   • Feche a issue manualmente quando terminar")
        print("   • Ou execute: python demo_github_to_trello.py --cleanup")

        print("\n" + "=" * 80)
        print("✨ DEMO CONCLUÍDA!")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
