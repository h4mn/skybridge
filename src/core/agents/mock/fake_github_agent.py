# -*- coding: utf-8 -*-
"""
FakeGitHubAgent - Agente que cria issues REAIS no GitHub para testes.

Estratégia inteligente:
- Cria issues reais no GitHub (realed source)
- Usa httpx para API calls
- Baseado em casos de uso realistas do Skybridge
- Permite testar fluxo completo: GitHub → Webhook → Trello

Status Taxonomy:
- realed: Componente 100% real, dados reais
- mocked: Componente mockado, dados simulados
- paused: Componente real mas temporariamente desativado

Por que "Fake" e não "Mock"?
- "Mock" tradicionalmente retorna dados pré-programados (stubbing)
- Este agente cria dados REAIS no GitHub
- "Fake" é mais preciso: implementa a interface mas com comportamento simplificado
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
import httpx

if TYPE_CHECKING:
    from core.webhooks.ports.job_queue_port import JobQueuePort


class ComponentStatus(Enum):
    """Status dos componentes no fluxo."""
    REALED = "realed"   # 100% real, dados reais
    MOCKED = "mocked"   # Mockado, dados simulados
    PAUSED = "paused"   # Real mas desativado temporariamente


@dataclass
class RealisticIssue:
    """Issue realista baseada em casos do Skybridge."""
    title: str
    body: str
    labels: list[str]
    milestone: str | None = None

    def to_github_dict(self) -> dict:
        """Converte para formato da API do GitHub."""
        issue_data = {
            "title": self.title,
            "body": self.body,
            "labels": self.labels,
        }
        if self.milestone:
            issue_data["milestone"] = self.milestone
        return issue_data


class RealisticIssueTemplates:
    """Templates de issues realistas do Skybridge."""

    @staticmethod
    def fuzzy_search_feature() -> RealisticIssue:
        """Issue: Implementar busca fuzzy."""
        return RealisticIssue(
            title="[Feature] Implementar busca fuzzy em queries",
            body="""## Contexto
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
- [ ] Testes unitários

**TAG:** MOCK/TESTE - Gerado automaticamente para testes""",
            labels=["feature", "enhancement", "good-first-issue", "MOCK/TESTE", "auto-generated"],
        )

    @staticmethod
    def webhook_deduplication_bug() -> RealisticIssue:
        """Issue: Corrigir deduplicação de webhooks."""
        return RealisticIssue(
            title="[Bug] Webhooks being processed multiple times",
            body="""## Bug Description
Webhooks do GitHub estão sendo processados múltiplas vezes, causando jobs duplicados.

## Root Cause
O delivery ID não está sendo verificado antes de criar jobs.

## Reprodução
1. Enviar webhook `issues.opened`
2. Verificar que job é criado
3. Reenviar mesmo webhook
4. ❌ Job duplicado é criado

## Expected Behavior
Segundo webhook com mesmo delivery ID deve ser ignorado.

## Proposta de Fix
```python
# Em WebhookProcessor:
if await job_queue.exists_by_delivery(delivery_id):
    return Result.ok(None)  # Já processado
```

**TAG:** MOCK/TESTE - Gerado automaticamente para testes""",
            labels=["bug", "webhooks", "priority-high", "MOCK/TESTE", "auto-generated"],
        )

    @staticmethod
    def trello_integration_feature() -> RealisticIssue:
        """Issue: Integração com Trello."""
        return RealisticIssue(
            title="[Feature] Integrar com Trello para visibilidade de jobs",
            body="""## Contexto
Time precisa de visibilidade do progresso dos jobs em tempo real. Logs não são suficientes.

## Requisitos
- Criar card no Trello quando issue é aberta
- Atualizar card durante execução do job
- Marcar como DONE quando completado

## Implementação Proposta
1. `TrelloAdapter` - Comunicação com API do Trello
2. `TrelloIntegrationService` - Service layer com operações alto nível
3. Integrar com `WebhookProcessor` e `JobOrchestrator`

## Fluxo
```
GitHub Issue → WebhookProcessor → Trello Card criado
JobOrchestrator executa → Trello Card atualizado
Job completo → Trello Card marcado DONE
```

## Critérios de Aceite
- [ ] Card criado automaticamente
- [ ] Progresso visível em tempo real
- [ ] Erros não quebram o fluxo

**TAG:** MOCK/TESTE - Gerado automaticamente para testes""",
            labels=["feature", "integration", "trello", "MOCK/TESTE", "auto-generated"],
        )

    @staticmethod
    def agent_orchestrator_refactor() -> RealisticIssue:
        """Issue: Refatorar orquestrador de agentes."""
        return RealisticIssue(
            title="[Refactor] Simplificar JobOrchestrator com Domain Events",
            body="""## Contexto
JobOrchestrator está fazendo coisas demais: criar worktree, executar agente, validar, limpar, atualizar Trello...

## Problemas
- Baixa coesão (muitas responsabilidades)
- Difícil de testar
- Acoplado a muitos serviços

## Proposta
Usar Domain Events para desacoplar:
```python
# JobOrchestrator apenas orquestra:
job.events.append(WorktreeCreated(worktree_path))
job.events.append(AgentStarted(skill))
job.events.append(AgentCompleted(output))

# Outros services listen aos eventos:
TrelloService.on(AgentCompleted) → mark_card_complete
```

## Benefícios
- Maiar coesão
- Fácil testar
- Adicionar novos listeners sem mudar orquestrador

**TAG:** MOCK/TESTE - Gerado automaticamente para testes""",
            labels=["refactor", "architecture", "tech-debt", "MOCK/TESTE", "auto-generated"],
        )

    @staticmethod
    def rate_limiting_feature() -> RealisticIssue:
        """Issue: Implementar rate limiting."""
        return RealisticIssue(
            title="[Feature] Rate limiting para API do Claude",
            body="""## Contexto
Chamadas à API do Claude podem gerar custos excessivos se não limitadas.

## Requisitos
- Limitar chamadas por minuto/hora
- Queue de requests com prioridade
- Circuit breaker para falhas

## Implementação Proposta
```python
class RateLimiter:
    def __init__(self, max_requests: int, period: timedelta):
        self.max_requests = max_requests
        self.period = period
        self.requests = deque()

    async def acquire(self) -> bool:
        now = datetime.utcnow()
        # Remove requests antigos
        while self.requests and self.requests[0] < now - self.period:
            self.requests.popleft()
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

## Critérios de Aceite
- [ ] Máximo 10 requests/minuto
- [ ] Prioridade para jobs urgentes
- [ ] Circuit breaker após 5 falhas

**TAG:** MOCK/TESTE - Gerado automaticamente para testes""",
            labels=["feature", "performance", "rate-limiting", "MOCK/TESTE", "auto-generated"],
        )


class FakeGitHubAgent:
    """
    Agente Fake que cria issues REAIS no GitHub.

    Status: realed (cria issues de verdade no GitHub)
    Source: GitHub API (realed)

    Por que "Fake"?
    - Implementa a interface de um agente GitHub
    - Mas com comportamento simplificado
    - Cria dados REAIS (não stubbed)
    """

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        github_token: str,
        base_url: str = "https://api.github.com",
    ):
        """
        Inicializa FakeGitHubAgent.

        Args:
            repo_owner: Dono do repositório (ex: "skybridge")
            repo_name: Nome do repositório (ex: "skybridge")
            github_token: Personal Access Token do GitHub
            base_url: URL base da API (padrão: github.com)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=30.0,
        )

    @property
    def status(self) -> ComponentStatus:
        """Status deste componente."""
        return ComponentStatus.REALED

    @property
    def repo_full_name(self) -> str:
        """Nome completo do repositório."""
        return f"{self.repo_owner}/{self.repo_name}"

    async def create_issue(
        self,
        issue: RealisticIssue,
    ) -> httpx.Response:
        """
        Cria issue REAL no GitHub.

        Args:
            issue: Issue realista para criar

        Returns:
            Response da API do GitHub com a issue criada

        Raises:
            httpx.HTTPError: Se a requisição falhar
        """
        url = f"/repos/{self.repo_full_name}/issues"
        issue_data = issue.to_github_dict()

        response = await self.client.post(url, json=issue_data)
        response.raise_for_status()

        return response

    async def create_multiple_issues(
        self,
        issues: list[RealisticIssue],
        delay: float = 2.0,
    ) -> list[httpx.Response]:
        """
        Cria múltiplas issues com delay entre elas.

        Args:
            issues: Lista de issues para criar
            delay: Delay em segundos entre cada criação (padrão: 2s)

        Returns:
            Lista de responses da API
        """
        results = []
        for i, issue in enumerate(issues):
            print(f"📝 Criando issue {i+1}/{len(issues)}: {issue.title[:50]}...")

            try:
                response = await self.create_issue(issue)
                results.append(response)

                issue_data = response.json()
                issue_number = issue_data["number"]
                issue_url = issue_data["html_url"]

                print(f"  ✅ Issue #{issue_number} criada: {issue_url}")

                # Delay para não rate limit
                if i < len(issues) - 1:
                    await asyncio.sleep(delay)

            except httpx.HTTPError as e:
                print(f"  ❌ Erro ao criar issue: {e}")
                results.append(None)

        return results

    async def close_issue(self, issue_number: int) -> httpx.Response:
        """
        Fecha issue (útil para cleanup após testes).

        Args:
            issue_number: Número da issue

        Returns:
            Response da API do GitHub
        """
        url = f"/repos/{self.repo_full_name}/issues/{issue_number}"
        response = await self.client.patch(url, json={"state": "closed"})
        response.raise_for_status()
        return response

    async def close_all_test_issues(self) -> list[int]:
        """
        Fecha todas as issues com label MOCK/TESTE.

        Returns:
            Lista de números das issues fechadas
        """
        # Busca issues com label MOCK/TESTE
        url = f"/repos/{self.repo_full_name}/issues"
        params = {
            "labels": "MOCK/TESTE",
            "state": "open",
            "per_page": 100,
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        issues = response.json()

        closed = []
        for issue in issues:
            issue_number = issue["number"]
            await self.close_issue(issue_number)
            print(f"  ✅ Issue #{issue_number} fechada")
            closed.append(issue_number)

        return closed

    async def close(self):
        """Fecha o cliente HTTP."""
        await self.client.aclose()

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()


# Função de conveniência para demo
async def demo_create_test_issues(
    repo_owner: str,
    repo_name: str,
    github_token: str,
) -> None:
    """
    Demo: Cria issues de teste no GitHub.

    Args:
        repo_owner: Dono do repositório
        repo_name: Nome do repositório
        github_token: Token do GitHub

    Example:
        ```bash
        export GITHUB_TOKEN=ghp_xxx
        export GITHUB_REPO=skybridge/skybridge

        python -c "
        import asyncio
        from core.agents.mock.fake_github_agent import demo_create_test_issues
        asyncio.run(demo_create_test_issues('skybridge', 'skybridge', 'ghp_xxx'))
        "
        ```
    """
    templates = RealisticIssueTemplates()

    issues_to_create = [
        templates.fuzzy_search_feature(),
        templates.webhook_deduplication_bug(),
        templates.trello_integration_feature(),
        templates.agent_orchestrator_refactor(),
        templates.rate_limiting_feature(),
    ]

    async with FakeGitHubAgent(repo_owner, repo_name, github_token) as agent:
        print(f"\n🚀 Criando {len(issues_to_create)} issues de teste no GitHub")
        print(f"📦 Repositório: {agent.repo_full_name}")
        print(f"📊 Status: {agent.status.value}\n")

        results = await agent.create_multiple_issues(issues_to_create)

        print(f"\n✅ {sum(1 for r in results if r)}/{len(results)} issues criadas com sucesso!")
        print(f"💡 Estas issues vão disparar webhooks reais no GitHub!")
        print(f"💡 Configure o webhook server para receber: python github_webhook_server.py")
        print(f"💡 Use ngrok para expor localhost: http://localhost:8000\n")


if __name__ == "__main__":
    import os

    async def main():
        """Teste local do FakeGitHubAgent."""
        github_token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPO", "skybridge/skybridge")

        if not github_token:
            print("❌ GITHUB_TOKEN não configurado")
            print("💡 Crie um token em: https://github.com/settings/tokens")
            print("💡 Escopo necessário: repo (full repo access)")
            return

        owner, name = repo.split("/", 1)
        await demo_create_test_issues(owner, name, github_token)

    asyncio.run(main())
