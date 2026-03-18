# Relatório: Estrutura Trello vs Workflow Stages

**Data:** 2025-01-18
**Issue:** #39
**Status:** Investigação Completa

---

## 1. Listas Atuais do Trello Board

**Board ID:** Configurado via `TRELLO_BOARD_ID` (variável de ambiente)
**Localização:** `.env` ou configuração do runtime

### Lista Padrão

**🎯 Foco Janeiro - Março** (Hardcoded)
- **ID:** Configurado via API
- **Uso:** Lista padrão onde cards são criados pelo `TrelloIntegrationService`
- **Configuração:** Linha 28 de `trello_integration_service.py`

```python
def __init__(self, trello_adapter: TrelloAdapter, default_list_name: str = "🎯 Foco Janeiro - Março"):
```

**Observação:** O nome da lista está hardcoded no código como padrão, o que indica que:
- O board Trello atual tem esta lista específica
- Novas listas podem ser criadas manualmente no Trello
- O sistema não valida se a lista existe antes de criar cards

---

## 2. Workflow Stages do Sistema

### 2.1 Stages Publicados pelo JobOrchestrator

O `JobOrchestrator` (linha 109-197 de `job_orchestrator.py`) publica progresso em **7 fases distintas**:

#### Fase 1: Início
- **Status:** "Job iniciado"
- **Quando:** Job é retirado da fila e começa processamento
- **Método:** `_update_trello_progress(job, "Início", "Job iniciado")`

#### Fase 2: Worktree
- **Status:** "Criando ambiente isolado"
- **Quando:** Criando worktree para issue
- **Método:** `_update_trello_progress(job, "Worktree", "Criando ambiente isolado")`

#### Fase 3: Snapshot
- **Status:** "Capturando estado inicial"
- **Quando:** Extraindo snapshot inicial do repositório
- **Método:** `_update_trello_progress(job, "Snapshot", "Capturando estado inicial")`

#### Fase 4: Agente
- **Status:** "Executando IA"
- **Quando:** Spawna subagente Claude para resolver issue
- **Método:** `_update_trello_progress(job, "Agente", "Executando IA")`

#### Fase 5: Validação
- **Status:** "Validando mudanças"
- **Quando:** Validando worktree após execução do agente
- **Método:** `_update_trello_progress(job, "Validação", "Validando mudanças")`

#### Fase 6: Concluído (Sucesso)
- **Status:** "Issue resolvida com sucesso"
- **Resumo:** Contém mudanças realizadas
- **Método:** `_mark_trello_completed()` com:
  - Agente executado
  - Changes feitas
  - Validação OK

#### Fase 7: Erro (Falha)
- **Status:** "Job Falhou"
- **Quando:** Qualquer erro durante o processamento
- **Método:** `_mark_trello_failed()` com:
  - Timestamp do erro
  - Mensagem de erro detalhada

### 2.2 Operações do TrelloIntegrationService

O serviço oferece **3 métodos públicos** (linhas 39-238):

1. **`create_card_from_github_issue()`** (linha 39)
   - Cria card no Trello a partir de issue do GitHub
   - Adiciona metadados (issue URL, número, autor, repositório)
   - Retorna card_id para rastreamento

2. **`update_card_progress()`** (linha 163)
   - Atualiza card com comentário de progresso
   - Formato: `🔄 **Progresso do Agente**\n**Fase:** {phase}\n**Status:** {status}`

3. **`mark_card_complete()`** (linha 199)
   - Marca card como completo
   - Adiciona resumo e lista de mudanças
   - Formato: `✅ **Implementação Concluída**`

### 2.3 Operações do TrelloAdapter

O adapter implementa **KanbanPort** com os seguintes métodos (linhas 70-378):

1. **`create_card()`** (linha 164)
   - Cria card em lista específica
   - Suporta labels, due date, descrição

2. **`add_card_comment()`** (linha 251)
   - Adiciona comentário ao card
   - **USADO ATUALMENTE para todas as atualizações**

3. **`update_card_status()`** (linha 222) ⚠️ **NÃO IMPLEMENTADO**
   - Deveria mover cards entre listas
   - **TODO:** "Implementar cache de listas para evitar múltiplas chamadas"
   - **Atual:** Apenas adiciona comentário, não move card

4. **`get_card()`** (linha 142)
5. **`list_cards()`** (linha 307)
6. **`get_board()`** (linha 278)
7. **`list_boards()`** (linha 121)

---

## 3. Gap Analysis

### 3.1 Resumo Quantitativo

| Métrica | Valor | Observação |
|---------|-------|------------|
| **Total de Listas Trello** | 1+ (desconhecido, depende do board) | Apenas "🎯 Foco Janeiro - Março" é hardcoded |
| **Total de Fases do Sistema** | 7 fases + 1 erro | Início, Worktree, Snapshot, Agente, Validação, Concluído, Erro |
| **Listas com Mapeamento Explícito** | 1 | Apenas lista padrão hardcoded |
| **Movimentação Automática de Cards** | ❌ NÃO | Cards ficam na lista onde foram criados |

### 3.2 Gaps Identificados

#### Gap 1: Falta de Movimentação Automática ❌🔴

**Problema:**
- Cards são criados na lista "🎯 Foco Janeiro - Março"
- Cards **NÃO são movidos** conforme progresso das fases
- Progresso é visível apenas nos comentários
- Humanos precisam abrir cada card para ver o status

**Impacto:**
- Baixa observabilidade para humanos
- Dashboard do Trello não reflete estado real
- Impossível filtrar por "em andamento", "concluído", etc.

**Causa:**
- Método `update_card_status()` do `TrelloAdapter` está incompleto (linha 222-249)
- TODO no código indica que movimentação foi planejada mas não implementada
- Apenas adiciona comentário: `Status atualizado para: {status.value}`

**Código Atual:**
```python
async def update_card_status(
    self,
    card_id: str,
    status: CardStatus,
    correlation_id: Optional[str] = None,
) -> Result[Card, str]:
    """
    Atualiza o status de um card movendo-o entre listas.
    PUT /1/cards/{id}
    """
    try:
        # Mapear CardStatus para idList do Trello
        # TODO: Implementar cache de listas para evitar múltiplas chamadas
        # Por enquanto, apenas adiciona comentário com novo status

        comment = f"Status atualizado para: {status.value}"
        if correlation_id:
            comment += f"\n\nCorrelation ID: {correlation_id}"

        await self.add_card_comment(card_id, comment)

        # Buscar card atualizado
        return await self.get_card(card_id)
```

#### Gap 2: Mapeamento Implícito Hardcoded ⚠️🟡

**Problema:**
- Nome da lista hardcoded no código: `"🎯 Foco Janeiro - Março"`
- Nome muda conforme trimestre/ano → precisará de novo deploy
- Sem configuração externa ou ambiente

**Impacto:**
- Manutenção requer mudança de código
- Diferentes board/ambientes precisam de branches diferentes
- Não segue princípio de externalização de configuração

**Código:**
```python
# trello_integration_service.py, linha 28
def __init__(self, trello_adapter: TrelloAdapter, default_list_name: str = "🎯 Foco Janeiro - Março"):
```

#### Gap 3: Falta de Listas para Cada Fase ⚠️🟡

**Problema:**
- Sistema tem 7 fases distintas
- Trello tem 1 lista principal (desconhecido se há outras)
- Sem mapeamento fase → lista

**Impacto:**
- Impossível visualizar pipeline de trabalho no Trello
- Sem Kanban real (To Do → In Progress → Done)

#### Gap 4: Observabilidade Limitada ⚠️🟡

**Problema:**
- Progresso só aparece nos comentários
- Sem labels coloridas para status
- Sem badges visuais no card

**Impacto:**
- Humanos precisam abrir card para ver status
- Board não serve como dashboard rápido
- Dificulta gestão visual do trabalho

---

## 4. Sugestões de Melhoria

### 4.1 Implementar Movimentação Automática de Cards 🔴 **ALTA PRIORIDADE**

**Recomendação:**
Completar implementação do `update_card_status()` para mover cards entre listas.

**Arquivos a Modificar:**
1. `src/infra/kanban/adapters/trello_adapter.py`
2. `src/core/webhooks/application/job_orchestrator.py`

**Implementação:**

**Passo 1: Definir mapeamento de fases para listas**

```python
# config/trello_workflow_mapping.yaml (NOVO)
workflow_lists:
  backlog: "📥 Backlog"
  in_progress: "🔧 Em Desenvolvimento"
  agent: "🤖 Processando"
  validation: "👀 Em Revisão"
  done: "✅ Done"
  error: "❌ Erros"

# Ou como environment variables:
# TRELLO_LIST_BACKLOG="📥 Backlog"
# TRELLO_LIST_IN_PROGRESS="🔧 Em Desenvolvimento"
# TRELLO_LIST_AGENT="🤖 Processando"
# TRELLO_LIST_VALIDATION="👀 Em Revisão"
# TRELLO_LIST_DONE="✅ Done"
# TRELLO_LIST_ERROR="❌ Erros"
```

**Passo 2: Implementar `update_card_status()` no TrelloAdapter**

```python
# trello_adapter.py
async def update_card_status(
    self,
    card_id: str,
    status: CardStatus,
    correlation_id: Optional[str] = None,
) -> Result[Card, str]:
    """
    Move card para lista correspondente ao status.
    """
    try:
        # Buscar lista destino baseada no status
        target_list_name = self._map_status_to_list(status)
        list_id_result = await self._get_list_id(target_list_name)

        if list_id_result.is_err:
            return Result.err(f"Lista não encontrada: {target_list_name}")

        # Mover card via API do Trello
        response = await self._client.put(
            f"/cards/{card_id}",
            json={"idList": list_id_result.unwrap()}
        )
        response.raise_for_status()

        logger.info(f"Card {card_id} movido para {target_list_name}")
        return await self.get_card(card_id)

    except Exception as e:
        logger.error(f"Erro ao mover card {card_id}: {e}")
        return Result.err(f"Erro ao mover card: {str(e)}")

def _map_status_to_list(self, status: CardStatus) -> str:
    """Mapeia CardStatus para nome de lista."""
    mapping = {
        CardStatus.TODO: getenv("TRELLO_LIST_BACKLOG", "📥 Backlog"),
        CardStatus.IN_PROGRESS: getenv("TRELLO_LIST_IN_PROGRESS", "🔧 Em Desenvolvimento"),
        CardStatus.AGENT_RUNNING: getenv("TRELLO_LIST_AGENT", "🤖 Processando"),
        CardStatus.VALIDATING: getenv("TRELLO_LIST_VALIDATION", "👀 Em Revisão"),
        CardStatus.DONE: getenv("TRELLO_LIST_DONE", "✅ Done"),
        CardStatus.ERROR: getenv("TRELLO_LIST_ERROR", "❌ Erros"),
    }
    return mapping.get(status, "📥 Backlog")
```

**Passo 3: Atualizar JobOrchestrator para mover cards**

```python
# job_orchestrator.py

# Após criar worktree
await self._move_trello_card(job, CardStatus.IN_PROGRESS)

# Após executar agente
await self._move_trello_card(job, CardStatus.VALIDATING)

# Após validar
await self._move_trello_card(job, CardStatus.DONE)

# Em caso de erro
await self._move_trello_card(job, CardStatus.ERROR)

async def _move_trello_card(self, job: WebhookJob, status: CardStatus) -> None:
    """Move card no Trello para lista de status."""
    if not self.trello_service:
        return

    card_id = job.metadata.get("trello_card_id")
    if not card_id:
        return

    try:
        await self.trello_service.adapter.update_card_status(
            card_id=card_id,
            status=status
        )
    except Exception as e:
        logger.warning(f"Falha ao mover card no Trello: {e}")
```

**Estimativa:** 4-6 horas
**Benefícios:**
- ✅ Board Trello reflete estado real em tempo real
- ✅ Gestão visual do pipeline de trabalho
- ✅ Filtragem por status (drag & drop)
- ✅ Métricas visuais (WIP, throughput)

---

### 4.2 Adicionar Labels de Status nos Cards 🔴 **ALTA PRIORIDADE**

**Recomendação:**
Adicionar labels coloridas do Trello para identificar status visualmente.

**Implementação:**

```python
# trello_integration_service.py
async def update_card_progress(
    self,
    card_id: str,
    phase: str,
    status: str,
) -> Result[None, str]:
    """
    Atualiza card com comentário E label de status.
    """
    try:
        # Adiciona comentário (existente)
        comment = f"""🔄 **Progresso do Agente**

**Fase:** {phase}
**Status:** {status}

---
*Atualização automática durante processamento da issue.*"""

        result = await self.adapter.add_card_comment(card_id, comment)

        # NOVO: Adiciona label de status
        label_name = self._phase_to_label(phase)
        await self.adapter.add_card_label(card_id, label_name)

        return Result.ok(None)

    except Exception as e:
        logger.error(f"Erro ao atualizar card {card_id}: {e}")
        return Result.err(f"Erro ao atualizar card: {str(e)}")

def _phase_to_label(self, phase: str) -> str:
    """Mapeia fase para label colorida."""
    mapping = {
        "Início": "🚀 Iniciado",
        "Worktree": "🔧 Setup",
        "Snapshot": "📸 Snapshot",
        "Agente": "🤖 Processando",
        "Validação": "👀 Revisão",
        "Concluído": "✅ Sucesso",
        "Erro": "❌ Falha",
    }
    return mapping.get(phase, "🔄 Em Andamento")
```

**Labels Sugeridas no Trello:**
- 🚀 **Iniciado** (Azul)
- 🔧 **Setup** (Amarelo)
- 📸 **Snapshot** (Verde)
- 🤖 **Processando** (Laranja - pulsante!)
- 👀 **Revisão** (Roxo)
- ✅ **Sucesso** (Verde)
- ❌ **Falha** (Vermelho)

**Estimativa:** 2-3 horas
**Benefícios:**
- ✅ Identificação visual rápida
- ✅ Filtros por label no Trello
- ✅ Dashboard mais informativo

---

### 4.3 Externalizar Configuração de Listas 🟡 **MÉDIA PRIORIDADE**

**Recomendação:**
Mover nome da lista hardcoded para variável de ambiente ou arquivo de configuração.

**Implementação:**

```python
# trello_integration_service.py
def __init__(self, trello_adapter: TrelloAdapter, default_list_name: str | None = None):
    """
    Inicializa serviço de integração.

    Args:
        trello_adapter: Adapter para comunicação com Trello
        default_list_name: Nome da lista onde criar cards (usa env se não fornecido)
    """
    self.adapter = trello_adapter
    self.default_list_name = default_list_name or getenv(
        "TRELLO_DEFAULT_LIST",
        "🎯 Foco Janeiro - Março"
    )
```

```bash
# .env
TRELLO_DEFAULT_LIST="🎯 Foco Janeiro - Março"
# Ou mudar para:
TRELLO_DEFAULT_LIST="📥 Backlog"
```

**Estimativa:** 30 minutos
**Benefícios:**
- ✅ Configuração sem rebuild
- ✅ Ambientes diferentes (dev/prod)
- ✅ Melhor prática de 12-factor app

---

### 4.4 Criar Configuração de Mapeamento Workflow 🟡 **MÉDIA PRIORIDADE**

**Recomendação:**
Criar arquivo de configuração YAML para mapear fases → listas → labels.

**Implementação:**

```yaml
# config/trello_workflow.yaml
workflow:
  default_list: "📥 Backlog"

  lists:
    backlog: "📥 Backlog"
    in_progress: "🔧 Em Desenvolvimento"
    agent: "🤖 Processando"
    validation: "👀 Em Revisão"
    done: "✅ Done"
    error: "❌ Erros"

  labels:
    started: "🚀 Iniciado"
    setup: "🔧 Setup"
    snapshot: "📸 Snapshot"
    processing: "🤖 Processando"
    review: "👀 Revisão"
    success: "✅ Sucesso"
    failure: "❌ Falha"

  stages:
    - name: "Início"
      list: "in_progress"
      label: "started"
    - name: "Worktree"
      list: "in_progress"
      label: "setup"
    - name: "Snapshot"
      list: "in_progress"
      label: "snapshot"
    - name: "Agente"
      list: "agent"
      label: "processing"
    - name: "Validação"
      list: "validation"
      label: "review"
    - name: "Concluído"
      list: "done"
      label: "success"
    - name: "Erro"
      list: "error"
      label: "failure"
```

**Carregamento:**

```python
# config.py
from pathlib import Path
import yaml

def load_trello_workflow_config() -> dict:
    """Carrega configuração de workflow do Trello."""
    config_path = Path("config/trello_workflow.yaml")

    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    # Configuração padrão
    return {
        "default_list": "🎯 Foco Janeiro - Março",
        "lists": {},
        "labels": {},
        "stages": []
    }
```

**Estimativa:** 3-4 horas
**Benefícios:**
- ✅ Configuração centralizada
- ✅ Fácil mudança de workflow
- ✅ Documentação viva do fluxo

---

### 4.5 Adicionar Métricas de Tempo nas Fases 🟢 **BAIXA PRIORIDADE**

**Recomendação:**
Registrar timestamp de cada transição para calcular tempo por fase.

**Implementação:**

```python
# Complemento aos comentários de progresso
comment = f"""🔄 **Progresso do Agente**

**Fase:** {phase}
**Status:** {status}
**⏱️ Tempo decorrido:** {elapsed_time}s

---
*Atualização automática durante processamento da issue.*"""
```

**Estimativa:** 1-2 horas
**Benefícios:**
- ✅ Identificar bottlenecks
- ✅ Melhorar SLA
- ✅ Otimizar performance

---

### 4.6 Documentar Estrutura do Board Trello 🟢 **BAIXA PRIORIDADE**

**Recomendação:**
Criar documentação descrevendo estrutura ideal do board.

**Conteúdo:**
- Listas recomendadas
- Labels sugeridas
- Fluxo de trabalho visual
- Exemplos de uso

**Arquivo:** `docs/how-to/TRELLO_BOARD_STRUCTURE.md`

**Estimativa:** 2 horas
**Benefícios:**
- ✅ Onboarding mais rápido
- ✅ Consistência entre boards
- ✅ Referência para configuração

---

## 5. Roadmap de Implementação

### Fase 1: Automação de Movimentação 🔴 **1-2 semanas**

**Sprint 1:**
- [ ] Implementar `update_card_status()` no TrelloAdapter
- [ ] Criar mapeamento fase → lista (env vars)
- [ ] Atualizar JobOrchestrator para mover cards
- [ ] Testar com issues reais

**Sprint 2:**
- [ ] Adicionar labels de status
- [ ] Implementar remoção de labels ao mudar fase
- [ ] Testar filtros e visualizações
- [ ] Documentar configuração

**Entregáveis:**
- Cards movem automaticamente entre listas
- Labels coloridas indicam status
- Board reflete estado real do sistema

---

### Fase 2: Configuração Externalizada 🟡 **1 semana**

**Sprint 3:**
- [ ] Criar arquivo `trello_workflow.yaml`
- [ ] Implementar carregamento de config
- [ ] Mover hardcoded → configuração
- [ ] Adicionar validação de schema

**Entregáveis:**
- Configuração externa do workflow
- Sem hardcodes no código
- Fácil customização por ambiente

---

### Fase 3: Observabilidade Avançada 🟢 **1 semana**

**Sprint 4:**
- [ ] Adicionar timestamps em cada fase
- [ ] Calcular tempo por fase
- [ ] Adicionar métricas (WIP, cycle time)
- [ ] Dashboard de métricas

**Entregáveis:**
- Métricas de tempo por fase
- Identificação de bottlenecks
- Otimizações baseadas em dados

---

## 6. Comparativo: Antes vs Depois

### Antes (Estado Atual)

```
┌─────────────────────────────────────────────────────┐
│  TRELLO BOARD                                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🎯 Foco Janeiro - Março                            │
│  ├── Card #42 (todos os cards aqui)                │
│  ├── Card #99                                       │
│  └── Card #123                                      │
│      💬 Comentários:                                │
│      - "Job iniciado"                               │
│      - "Worktree: Criando ambiente..."              │
│      - "Agente: Executando IA..."                   │
│      - "Concluído"                                  │
│                                                     │
└─────────────────────────────────────────────────────┘

Problemas:
❌ Cards não movem → board não mostra pipeline
❌ Precisa abrir card para ver status
❌ Impossível filtrar por "em andamento"
❌ Sem gestão visual do trabalho
```

### Depois (Estado Proposto)

```
┌─────────────────────────────────────────────────────────────┐
│  TRELLO BOARD                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📥 Backlog                                                  │
│  └── Card #200 🚀 Iniciado                                  │
│                                                             │
│  🔧 Em Desenvolvimento                                      │
│  └── Card #198 🔧 Setup 📸 Snapshot                         │
│                                                             │
│  🤖 Processando                                             │
│  └── Card #199 🤖 Processando (pulsante!)                  │
│                                                             │
│  👀 Em Revisão                                              │
│  └── Card #197 👀 Revisão                                   │
│                                                             │
│  ✅ Done                                                     │
│  ├── Card #42 ✅ Sucesso                                    │
│  ├── Card #99 ✅ Sucesso                                    │
│  └── Card #123 ✅ Sucesso                                   │
│                                                             │
│  ❌ Erros                                                    │
│  └── Card #50 ❌ Falha                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Benefícios:
✅ Pipeline visual claro (Kanban real)
✅ Status visível sem abrir card
✅ Filtros por lista/label
✅ Gestão visual do trabalho
✅ Métricas visuais (WIP por lista)
```

---

## 7. Conclusões

### Descobertas Principais

1. **Movimentação de Cards NÃO Implementada**
   - Método existe mas está incompleto (TODO no código)
   - Cards ficam estáticos na lista inicial
   - Progresso apenas em comentários

2. **Integração Funcional, mas Limitada**
   - Cards são criados ✅
   - Comentários de progresso funcionam ✅
   - Marcação de conclusão funciona ✅
   - Mas sem movimentação automática ❌

3. **Configuração Hardcoded**
   - Nome da lista hardcoded no código
   - Sem flexibilidade para ambientes diferentes
   - Viola princípio de externalização de config

4. **Boa Fundação para Melhorias**
   - Arquitetura está bem desenhada (ports/adapters)
   - Serviço de integração bem separado
   - Fácil estender com movimentação

### Priorização de Melhorias

1. **🔴 ALTA: Movimentação automática** (4-6h)
   - Maior impacto na observabilidade
   - Transforma Trello em dashboard real

2. **🔴 ALTA: Labels de status** (2-3h)
   - Identificação visual rápida
   - Filtros e dashboards

3. **🟡 MÉDIA: Configuração externalizada** (3-4h)
   - Melhor prática
   - Flexibilidade de ambientes

4. **🟢 BAIXA: Métricas de tempo** (1-2h)
   - Otimização baseada em dados
   - Identificação de bottlenecks

### Próximos Passos Imediatos

1. **Implementar movimentação de cards**
   - Completar `update_card_status()`
   - Criar mapeamento fase → lista
   - Atualizar JobOrchestrator

2. **Testar com issues reais**
   - Criar issue de teste
   - Acompanhar movimento no Trello
   - Validar todas as fases

3. **Documentar configuração**
   - Criar `docs/how-to/TRELLO_BOARD_SETUP.md`
   - Instruções para criar listas no Trello
   - Exemplos de configuração

---

## 8. Referências

### Código Analisado

- `src/core/kanban/application/trello_integration_service.py`
- `src/infra/kanban/adapters/trello_adapter.py`
- `src/core/webhooks/application/job_orchestrator.py`

### Especificações Relacionadas

- **PRD013** — Webhook Autonomous Agents
- **SPEC008** — AI Agent Interface
- **SPEC009** — Orquestração de Workflow Multi-Agente
- **ADR020** — Integração Trello

### Documentação Útil

- `docs/FLUXO_GITHUB_TRELO_COMPONENTES.md` — Fluxo GitHub → Trello
- `docs/STRATEGY_FLOW_STATUS_TAXONOMY.md` — Taxonomia de Status
- `docs/how-to/TRELLO_API_SETUP.md` — Configuração API Trello

---

## 9. Anexos

### Anexo A: Exemplo de Comentário de Progresso (Atual)

```
🔄 **Progresso do Agente**

**Fase:** Agente
**Status:** Executando IA

---
*Atualização automática durante processamento da issue.*
```

### Anexo B: Exemplo de Comentário de Conclusão (Atual)

```
✅ **Implementação Concluída**

**Resumo:**
Issue resolvida com sucesso

**Mudanças:**
- Agente: resolve-issue
- Changes: True
- Validação: OK

---
*Issue processada automaticamente pelo agente Skybridge.*
```

### Anexo C: Exemplo de Comentário de Erro (Atual)

```
❌ **Job Falhou**

🕐 14:32:15
**Erro:** worktree creation failed: branch already exists

---
O job encontrou um erro durante a execução. Verifique os logs para mais detalhes.
```

---

> Este relatório foi gerado automaticamente como parte da issue #39
> Análise completa do código e arquitetura da integração Trello

---

> made by Sky 🦍✨
