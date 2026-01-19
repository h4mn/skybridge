# ADR020: Integração GitHub → Trello

**Status:** Aceito
**Data:** 2025-01-17
**Contexto:** Kanban Integration

---

## Contexto

O Skybridge já suporta webhooks do GitHub e execução de agentes para resolver issues automaticamente. No entanto, não há visibilidade do progresso dos jobs em tempo real - é necessário verificar logs ou consultar a API para saber o status.

**Problemas identificados:**
- Falta de visibilidade do progresso dos jobs
- Dificuldade de rastrear quais issues estão sendo processadas
- Sem interface visual para acompanhamento em tempo real
- Equipe precisa acessar logs/CLI para saber status

## Decisão

Integrar o **Trello** como interface visual de acompanhamento de jobs do Skybridge.

### Arquitetura

```
┌─────────────┐
│   GitHub    │ Issue aberta
└──────┬──────┘
       │ webhook
       ▼
┌─────────────────────────────┐
│   WebhookProcessor          │ 1. Cria card no Trello
│   + TrelloIntegrationService│
└──────┬──────────────────────┘
       │ job criado
       ▼
┌─────────────────────────────┐
│   JobOrchestrator           │ 2. Atualiza card com progresso
│   + TrelloIntegrationService│
└──────┬──────────────────────┘
       │ job completado
       ▼
┌─────────────────────────────┐
│   Trello Card               │ 3. Marcado como DONE
│   ✓ Comentários de progresso│
│   ✓ Histórico completo      │
└─────────────────────────────┘
```

### Componentes

#### 1. TrelloAdapter (Infra)

**Arquivo:** `src/infra/kanban/adapters/trello_adapter.py`

Implementa `KanbanPort` usando Trello REST API.

**Responsabilidades:**
- Comunicação com API do Trello
- Busca listas por nome
- Cria/ atualiza/ move cards
- Adiciona comentários

#### 2. TrelloIntegrationService (Application)

**Arquivo:** `src/core/kanban/application/trello_integration_service.py`

Service de aplicação com operações de alto nível.

**Responsabilidades:**
- Criar cards a partir de issues do GitHub
- Atualizar cards com progresso do agente
- Marcar cards como completados/ falhados
- Formatar descrições com metadados

**API principal:**
```python
class TrelloIntegrationService:
    async def create_card_from_github_issue(
        issue_number, issue_title, issue_body, ...
    ) -> Result[str, str]

    async def update_card_progress(
        card_id, phase, status
    ) -> Result[None, str]

    async def mark_card_complete(
        card_id, summary, changes
    ) -> Result[None, str]
```

#### 3. WebhookProcessor Integration

**Arquivo:** `src/core/webhooks/application/webhook_processor.py`

Modificado para aceitar `TrelloIntegrationService` opcional.

```python
class WebhookProcessor:
    def __init__(
        self,
        job_queue: JobQueuePort,
        trello_service: TrelloIntegrationService | None = None,
    ):
        ...
```

**Fluxo:**
1. Webhook chega do GitHub
2. Se `issues.opened` e `trello_service` configurado:
   - Cria card no Trello
   - Armazena `trello_card_id` nos metadados do job
3. Job enfileirado com metadados

#### 4. JobOrchestrator Integration

**Arquivo:** `src/core/webhooks/application/job_orchestrator.py`

Modificado para aceitar `TrelloIntegrationService` opcional.

```python
class JobOrchestrator:
    def __init__(
        self,
        job_queue: JobQueuePort,
        worktree_manager: WorktreeManager,
        agent_adapter: ClaudeCodeAdapter | None = None,
        trello_service: TrelloIntegrationService | None = None,
    ):
```

**Atualizações durante execução:**
- Início: "Job iniciado"
- Worktree: "Criando ambiente isolado"
- Snapshot: "Capturando estado inicial"
- Agente: "Executando IA"
- Validação: "Validando mudanças"
- Completo: "Issue resolvida com sucesso"
- Falha: "Job falhou: [erro]"

#### 5. WebhookJob Metadata

**Arquivo:** `src/core/webhooks/domain/webhook_event.py`

Adicionado campo `metadata` para armazenar `trello_card_id`:

```python
@dataclass
class WebhookJob:
    ...
    metadata: dict[str, Any] = field(default_factory=dict)
```

## Consequências

### Positivas

1. **Visibilidade em tempo real**
   - Equipe pode acompanhar progresso no Trello
   - Sem necessidade de acessar logs/CLI
   - Interface familiar e acessível

2. **Rastreabilidade**
   - Cada issue tem card correspondente
   - Histórico completo de progresso
   - Link bidirecional (GitHub ↔ Trello)

3. **Desacoplamento**
   - `TrelloIntegrationService` é opcional
   - Funciona sem Trello (feature toggle)
   - Fácil trocar por Jira/Asana

4. **Resiliência**
   - Falha no Trello NÃO quebra o fluxo
   - Apenas loga warnings
   - Job continua processando

### Negativas

1. **Dependência externa**
   - Requer API do Trello
   - Rate limits (100 requests/ 100ms para free tier)
   - Disponibilidade do serviço

2. **Complexidade adicional**
   - +3 arquivos novos
   - +2 parâmetros em construtores
   - Necessário configurar credenciais

3. **Sincronização**
   - Cards podem ficar desatualizados se Trello falhar
   - Necessário mecanismo de reconciliação (futuro)

## Alternativas Consideradas

### 1. Slack Notifications

**Vantagens:**
- Notificações em tempo real
- Familiar para time técnico

**Desvantagens:**
- Sem visibilidade de histórico (messages scroll)
- Sem organização por "cards"
- Dificulta acompanhar múltiplas issues

**Decisão:** Trello escolhido por ser mais visual e organizado.

### 2. Database Customizado

**Vantagens:**
- Controle total
- Sem dependências externas

**Desvantagens:**
- Requer implementar UI
- Mais desenvolvimento
- Menos familiar para time não-técnico

**Decisão:** Trello escolhido por ser pronto e familiar.

### 3. Domain Events

**Vantagens:**
- Maior desacoplamento
- Arquitetura mais limpa

**Disvantagens:**
- Complexidade prematura (YAGNI)
- Overhead para integração simples

**Decisão:** Implementar quando tiver 3+ integrações (ver ADR021).

## Configuração

### Variáveis de Ambiente

```bash
# .env
TRELLO_API_KEY=seu_api_key
TRELLO_API_TOKEN=seu_token
TRELLO_BOARD_ID=id_do_board
```

### Como Obter Credenciais

1. **API Key:** https://trello.com/app-key
2. **Token:** Link "Token" na mesma página
3. **Board ID:** Via API ou script `list_boards.py`

### Lista Padrão

Cards são criados na lista "🎯 Foco Janeiro - Março" por padrão.
Configurar via `TrelloIntegrationService(default_list_name=...)`.

## Uso

### Criar Card a Partir de Issue

```python
service = TrelloIntegrationService(trello_adapter)

result = await service.create_card_from_github_issue(
    issue_number=42,
    issue_title="[Feature] Dark mode",
    issue_body="## Contexto...",
    issue_url="https://github.com/skybridge/skybridge/issues/42",
    author="dev-ux",
    repo_name="skybridge/skybridge",
    labels=["feature", "ui"],
)
```

### Atualizar Progresso

```python
await service.update_card_progress(
    card_id="696b03cc8331874e6c09765f",
    phase="Agente",
    status="Executando implementação..."
)
```

### Marcar Completo

```python
await service.mark_card_complete(
    card_id="696b03cc8331874e6c09765f",
    summary="Dark mode implementado",
    changes=["Toggle component criado", "CSS variables configuradas"],
)
```

## Implementação

**Worktree:** `kanban/skybridge-trello-adapter`
**Branch:** `main` (após merge)

**Arquivos criados:**
- `src/infra/kanban/adapters/trello_adapter.py`
- `src/core/kanban/application/trello_integration_service.py`
- `src/core/webhooks/infrastructure/github_webhook_server.py`
- `src/core/kanban/testing/*.py` (demos)

**Arquivos modificados:**
- `src/core/webhooks/application/webhook_processor.py`
- `src/core/webhooks/domain/webhook_event.py`
- `src/core/webhooks/application/job_orchestrator.py`

## Próximos Passos

1. ✅ Integração básica funcional
2. ✅ Tratamento de erros
3. ✅ Documentação (ADR)
4. 🔄 Testes com webhooks reais do GitHub
5. ⏳ Melhorar error handling (retry logic)
6. ⏳ Adicionar métricas (cards criados, falhas, etc)
7. ⏳ Implementar reconciliação periódica

## Referências

- [Trello API Docs](https://developer.atlassian.com/cloud/trello/rest/)
- [Trello Rate Limits](https://developer.atlassian.com/cloud/trello/guides/rate-limits/)
- PB002: Ngrok URL Fixa
- PRD013: Webhook Worker

---

> "O que não é medido não é melhorado." – made by Sky 🦍✨
