# Relatório: Investigação Trello vs Workflow Stages

**Data:** 2026-01-18
**Issue:** #39
**Status:** Análise Completa
**Autoria:** Sky 🦍✨

---

## 📊 Executive Summary

Este relatório investiga a estrutura do Trello Board vs os estágios de workflow publicados pelo sistema Skybridge. A análise revela **gaps significativos** entre o design conceitual e a implementação atual, criando oportunidades para melhorar a observabilidade e a experiência do usuário.

**Principais Descobertas:**
- ✅ Integração Trello funcional (criação de cards)
- ⚠️ Ausência de movimentação automática entre listas
- ⚠️ Workflow stages apenas via comentários (não reflete em status visual)
- ⚠️ Domain model define CardStatus mas não implementado no adapter

**Impacto:** Médio - Usuários têm visibilidade limitada do progresso visual no Trello

---

## 🎯 Objetivos da Investigação

1. **Mapear listas atuais do Trello Board**
2. **Identificar workflow stages publicados pelo sistema**
3. **Analisar gaps entre design vs implementação**
4. **Propor melhorias com priorização**

---

## 1. Listas Atuais do Trello Board

### 1.1 Configuração Esperada

**Variável de Ambiente:**
```bash
TRELLO_BOARD_ID=696aadc544fecc164175024c  # Exemplo da documentação
```

**Lista Padrão (Hardcoded):**
```python
# src/core/kanban/application/trello_integration_service.py:28
def __init__(self, trello_adapter: TrelloAdapter, default_list_name: str = "🎯 Foco Janeiro - Março"):
```

### 1.2 Listas Conhecidas

**Documentadas no ADR020:**
- "🎯 Foco Janeiro - Março" (lista padrão para criação de cards)

**Observação:**
- ⚠️ **Não há script automatizado para listar as listas do board**
- ⚠️ **Não há documentação das listas existentes no board atual**
- ⚠️ **Lista padrão é hardcoded e sazonal** ("Janeiro - Março")

### 1.3 Descoberta de Listas (Manual)

Para descobrir as listas do board, seria necessário:
```python
# Via API (não implementado no fluxo atual):
GET /1/boards/{board_id}/lists

# Ou via script disponível:
python src/core/kanban/testing/list_boards.py  # Lista boards, não listas
```

**Gap Identificado:**
- ❌ Falta script `list_lists.py` para descobrir listas do board
- ❌ Não há validação se a lista padrão existe no board
- ❌ Não há criação automática de listas se ausentes

---

## 2. Workflow Stages do Sistema

### 2.1 Estágios Publicados (via Comentários)

**Arquivo:** `src/core/webhooks/application/job_orchestrator.py`

**Método:** `_update_trello_progress(job, phase, status)`

**Fases Publicadas:**

| Fase | Phase | Status | Quando ocorre |
|------|-------|--------|---------------|
| 1 | "Início" | "Job iniciado" | Job dequeued |
| 2 | "Worktree" | "Criando ambiente isolado" | Antes de criar worktree |
| 3 | "Snapshot" | "Capturando estado inicial" | Antes do snapshot |
| 4 | "Agente" | "Executando IA" | Durante execução do Claude Code |
| 5 | "Concluído" | "Evento não requer ação" | Para eventos sem skill |
| 6 | "Falha" | "[erro]" | Quando qualquer passo falha |

**Formato do Comentário:**
```markdown
🔄 **Progresso do Agente**

**Fase:** {phase}
**Status:** {status}

---
*Atualização automática durante processamento da issue.*
```

### 2.2 Estados Finais

**Completo:**
```python
# _mark_trello_completed(job, summary, changes)
await trello_service.mark_card_complete(
    card_id=card_id,
    summary=summary,
    changes=changes,
)
```

**Formatação:**
```markdown
✅ **Implementação Concluída**

**Resumo:**
{summary}

**Mudanças:**
- {change_1}
- {change_2}

---
*Issue processada automaticamente pelo agente Skybridge.*
```

**Falha:**
```python
# _mark_trello_failed(job, error)
await adapter.add_card_comment(
    card_id=card_id,
    comment=f"""❌ **Job Falhou**

🕐 {timestamp}
**Erro:** {error}

---
O job encontrou um erro durante a execução. Verifique os logs para mais detalhes."""
)
```

### 2.3 Domain Model vs Implementação

**Domain Model (CardStatus):**
```python
# src/core/kanban/domain/card.py
class CardStatus(Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
```

**Port Contract:**
```python
# src/core/kanban/ports/kanban_port.py
async def update_card_status(
    card_id: str,
    status: CardStatus,
    correlation_id: Optional[str] = None,
) -> Result[Card, str]:
    """Atualiza o status de um card."""
```

**Implementação TrelloAdapter:**
```python
# src/infra/kanban/adapters/trello_adapter.py:222
async def update_card_status(
    self,
    card_id: str,
    status: CardStatus,
    correlation_id: Optional[str] = None,
) -> Result[Card, str]:
    """
    Atualiza o status de um card movendo-o entre listas.

    TODO: Implementar cache de listas para evitar múltiplas chamadas
    Por enquanto, apenas adiciona comentário com novo status
    """
    # ⚠️ NÃO MOVE O CARD - APENAS ADICIONA COMENTÁRIO
    comment = f"Status atualizado para: {status.value}"
    if correlation_id:
        comment += f"\n\nCorrelation ID: {correlation_id}"

    await self.add_card_comment(card_id, comment)

    # Buscar card atualizado
    return await self.get_card(card_id)
```

**Gap Crítico:**
- ❌ `update_card_status` **não move cards entre listas**
- ❌ Domain model define 7 statuses mas **nenhum é implementado visualmente**
- ❌ Comentário é adicionado mas **card permanece na lista inicial**

---

## 3. Gap Analysis

### 3.1 Lista no Trello vs Stages do Sistema

| Stage do Sistema | Ação no Trello | Status Visual | Gap |
|------------------|----------------|---------------|-----|
| "Início" | Comentário: "Job iniciado" | 🎯 Foco Janeiro - Março | ⚠️ Sem movimentação |
| "Worktree" | Comentário: "Criando ambiente isolado" | 🎯 Foco Janeiro - Março | ⚠️ Sem movimentação |
| "Snapshot" | Comentário: "Capturando estado inicial" | 🎯 Foco Janeiro - Março | ⚠️ Sem movimentação |
| "Agente" | Comentário: "Executando IA" | 🎯 Foco Janeiro - Março | ⚠️ Sem movimentação |
| Completo | Comentário: "✅ Implementação Concluída" | 🎯 Foco Janeiro - Março | ⚠️ **Deveria mover para "Done"** |
| Falha | Comentário: "❌ Job Falhou" | 🎯 Foco Janeiro - Março | ⚠️ **Deveria mover para "Blocked"** |

### 3.2 CardStatus Domain vs Trello Lists

**CardStatus Definido (não implementado):**
- ✅ BACKLOG → Lista "Backlog" (não existe?)
- ✅ TODO → Lista "To Do" ou "🎯 Foco Janeiro - Março"
- ✅ IN_PROGRESS → Lista "In Progress" (não existe?)
- ✅ REVIEW → Lista "Review" (não existe?)
- ✅ DONE → Lista "Done" (não existe?)
- ✅ BLOCKED → Lista "Blocked" (não existe?)
- ✅ CANCELLED → Lista "Cancelled" (não existe?)

**Realidade Atual:**
- ❌ Todos os cards ficam na lista "🎯 Foco Janeiro - Março"
- ❌ Status visual **nunca muda**, apenas comentários

### 3.3 Mapeamento Esperado (Design vs Realidade)

**Design Conceitual (ADR020):**
```
GitHub Issue → [🎯 Foco Janeiro - Março] (TODO)
            → [In Progress] (processando)
            → [Review] (validando)
            → [Done] (completo)
            → [Blocked] (falha)
```

**Implementação Atual:**
```
GitHub Issue → [🎯 Foco Janeiro - Março] ← FICA AQUI SEMPRE
            → Comentário: "Job iniciado"
            → Comentário: "Worktree criada"
            → Comentário: "Snapshot capturado"
            → Comentário: "Agente executando"
            → Comentário: "✅ Implementação Concluída"
```

---

## 4. Problemas Identificados

### 4.1 Problema #1: Ausência de Movimentação Visual (Alta Prioridade)

**Descrição:**
Cards nunca mudam de lista, permanecem em "🎯 Foco Janeiro - Março" do início ao fim.

**Impacto:**
- Usuário precisa **abrir o card** para saber o status
- **Impossível ver progresso** de múltiplos cards num glance
- **Kanban board perde sua função principal** (visualização do fluxo)

**Causa Raiz:**
```python
# trello_adapter.py:update_card_status()
# TODO comentado indica feature planejada mas não implementada
# Por enquanto, apenas adiciona comentário com novo status
```

### 4.2 Problema #2: Lista Padrão Sazonal (Média Prioridade)

**Descrição:**
`default_list_name = "🎯 Foco Janeiro - Março"` expira após 3 meses.

**Impacto:**
- Cards serão criados em lista obsoleta a partir de abril
- Requer alteração manual no código a cada trimestre

**Solução:**
- Configurar via environment variable
- Ou detectar lista automaticamente

### 4.3 Problema #3: Falta de Listas Padrão no Board (Média Prioridade)

**Descrição:**
Não há garantia que as listas mapeadas para `CardStatus` existem.

**Impacto:**
- `update_card_status` falharia se tentasse mover para lista inexistente
- Requer setup manual do board Trello

**Solução:**
- Script para criar listas automaticamente se não existirem
- Documentação de estrutura esperada do board

### 4.4 Problema #4: Sem Descoberta de Listas (Baixa Prioridade)

**Descrição:**
Não há forma fácil de descobrir quais listas existem no board.

**Impacto:**
- Dificulta debug e configuração
- Requer chamadas manuais à API

**Solução:**
- Script `list_lists.py` para debug
- Endpoint `/trello/lists` para consulta

---

## 5. Sugestões de Melhoria

### 5.1 Prioridade ALTA - Implementar Movimentação de Cards

**Objetivo:** Mover cards entre listas conforme progresso

**Implementação:**
```python
# trello_adapter.py:update_card_status()

# 1. Mapear CardStatus para nome de lista
STATUS_TO_LIST = {
    CardStatus.BACKLOG: "Backlog",
    CardStatus.TODO: "To Do",
    CardStatus.IN_PROGRESS: "In Progress",
    CardStatus.REVIEW: "Review",
    CardStatus.DONE: "Done",
    CardStatus.BLOCKED: "Blocked",
    CardStatus.CANCELLED: "Cancelled",
}

# 2. Buscar ID da lista de destino
list_name = STATUS_TO_LIST[status]
list_id_result = await self._get_list_id(list_name, board_id)

# 3. Mover card via API
await self._client.put(f"/cards/{card_id}", json={"idList": list_id})
```

**Changes Required:**
- [ ] Implementar cache de listas (evitar múltiplas chamadas)
- [ ] Mapear CardStatus → nome da lista
- [ ] PUT /1/cards/{id} com novo idList
- [ ] Tratar erro se lista não existir

**Benefícios:**
- ✅ Progresso visível no Kanban board
- ✅ Cards se movem automaticamente
- ✅ Usuário acompanha jobs sem abrir cards

**Estimativa:** 2-3 horas

---

### 5.2 Prioridade MÉDIA - Configurar Lista Padrão via ENV

**Objetivo:** Remover hardcoded "🎯 Foco Janeiro - Março"

**Implementação:**
```python
# .env
TRELLO_DEFAULT_LIST="To Do"
TRELLO_BOARD_ID=696aadc544fecc164175024c

# trello_integration_service.py
default_list_name = getenv("TRELLO_DEFAULT_LIST", "To Do")
```

**Changes Required:**
- [ ] Adicionar variável `TRELLO_DEFAULT_LIST`
- [ ] Atualizar `.env.example`
- [ ] Atualizar documentação

**Benefícios:**
- ✅ Não expira trimestralmente
- ✅ Flexível para diferentes boards
- ✅ Follow 12-factor app principles

**Estimativa:** 30 minutos

---

### 5.3 Prioridade MÉDIA - Script de Setup de Board

**Objetivo:** Criar listas automaticamente se não existirem

**Implementação:**
```python
# scripts/setup_trello_board.py

LISTAS_ESPERADAS = [
    "Backlog",
    "To Do",
    "In Progress",
    "Review",
    "Done",
    "Blocked",
    "Cancelled",
]

async def setup_board(board_id: str):
    """Cria listas que não existem no board."""
    existing = await list_lists(board_id)
    missing = [l for l in LISTAS_ESPERADAS if l not in existing]

    for lista in missing:
        await create_list(board_id, lista)
        print(f"✅ Lista criada: {lista}")
```

**Changes Required:**
- [ ] Criar script `scripts/setup_trello_board.py`
- [ ] Implementar `create_list()` no TrelloAdapter
- [ ] Adicionar instruções no README

**Benefícios:**
- ✅ Setup automatizado de boards novos
- ✅ Garante estrutura mínima
- ✅ Documentação executável

**Estimativa:** 1-2 horas

---

### 5.4 Prioridade BAIXA - Script de Descoberta (Debug)

**Objetivo:** Facilitar listagem de listas do board

**Implementação:**
```python
# scripts/list_trello_lists.py

async def main():
    adapter = TrelloAdapter(api_key, api_token, board_id)
    result = await adapter.list_lists()

    if result.is_ok:
        for lst in result.unwrap():
            print(f"📋 {lst['name']} (id: {lst['id']})")
```

**Changes Required:**
- [ ] Criar script `scripts/list_trello_lists.py`
- [ ] Implementar `list_lists()` no TrelloAdapter

**Benefícios:**
- ✅ Debug facilitado
- ✅ Descoberta de estrutura do board
- ✅ Documentação interativa

**Estimativa:** 30 minutos

---

### 5.5 Prioridade BAIXA - Mapear Job Stages para CardStatus

**Objetivo:** Usar CardStatus ao invés de comentários customizados

**Implementação:**
```python
# job_orchestrator.py

async def _update_trello_progress(job, phase, status):
    # ANTES: comentário customizado
    # await trello_service.update_card_progress(card_id, phase, status)

    # DEPOIS: mover entre listas
    card_status = PHASE_TO_STATUS[phase]  # TODO: mapear
    await trello_service.adapter.update_card_status(
        card_id=card_id,
        status=card_status,
        correlation_id=job.delivery_id,
    )
```

**Mapeamento Sugerido:**
| Phase | CardStatus |
|-------|------------|
| "Início" | TODO |
| "Worktree" | IN_PROGRESS |
| "Snapshot" | IN_PROGRESS |
| "Agente" | IN_PROGRESS |
| "Validação" | REVIEW |
| "Concluído" | DONE |
| "Falha" | BLOCKED |

**Benefícios:**
- ✅ Consistência com domain model
- ✅ Movimentação visual automática
- ✅ Comentários redundantes eliminados

**Estimativa:** 1 hora

---

## 6. Roadmap de Implementação

### Fase 1: Crítico (1 semana)
- [x] Investigação completada (este relatório)
- [ ] Implementar movimentação de cards (5.1)
- [ ] Configurar lista padrão via ENV (5.2)

### Fase 2: Importante (2 semanas)
- [ ] Script de setup de board (5.3)
- [ ] Mapear job stages para CardStatus (5.5)

### Fase 3: Opcional (1 semana)
- [ ] Script de descoberta (5.4)
- [ ] Endpoint `/trello/lists` para debug
- [ ] Dashboard CLI para visualizar board

---

## 7. Arquitetura Proposta

### 7.1 Fluxo Ideal (Após Implementação)

```
┌──────────────────────────────────────────────────────────────┐
│                     FLUXO COMPLETO                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. GitHub Issue aberta                                      │
│     → Webhook chega ao Skybridge                             │
│     → Card criado em "To Do" 📋                              │
│                                                              │
│  2. Job iniciado                                             │
│     → Card movido para "In Progress" ▶️                       │
│     → Comentário: "Job iniciado"                             │
│                                                              │
│  3. Worktree + Snapshot                                      │
│     → Card permanece em "In Progress" ▶️                     │
│     → Comentários: "Criando ambiente...", "Capturando..."    │
│                                                              │
│  4. Agente executando                                        │
│     → Card permanece em "In Progress" ▶️                     │
│     → Comentário: "Executando IA..."                         │
│                                                              │
│  5. Validação pós-agente                                     │
│     → Card movido para "Review" 👀                           │
│     → Comentário: "Validando mudanças..."                    │
│                                                              │
│  6a. Implementação aprovada                                  │
│     → Card movido para "Done" ✅                             │
│     → Comentário final: "✅ Implementação Concluída"         │
│                                                              │
│  6b. Implementação rejeitada                                 │
│     → Card movido para "Blocked" 🚫                          │
│     → Comentário: "❌ Validação falhou: [razão]"             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 7.2 Estrutura do Board Trello

**Colunas Esperadas (esquerda → direita):**
```
┌──────────┬──────────┬─────────────┬────────┬──────────┬───────────┐
│ Backlog  │ To Do    │ In Progress │ Review │ Done     │ Blocked   │
└──────────┴──────────┴─────────────┴────────┴──────────┴───────────┘
```

**Regra de Movimentação:**
- Cards **sempre** movem da esquerda para direita
- "Blocked" é exceção (pode vir de qualquer etapa)
- "Done" é estado final (arquivado após X dias)

---

## 8. Métricas de Sucesso

### 8.1 Antes da Implementação (Baseline)

**Observabilidade:**
- ❌ Progresso visível: 0% (precisa abrir card)
- ❌ Status visual: Apenas 1 lista ("🎯 Foco Janeiro - Março")
- ✅ Comentários de progresso: 100% (funcionando)

**Experiência do Usuário:**
- ❌ Time-to-understand: ~30 segundos por card
- ❌ Visão geral de jobs: Impossível sem abrir cards
- ✅ Rastreabilidade: Boa (comentários detalhados)

### 8.2 Após Implementação (Target)

**Observabilidade:**
- ✅ Progresso visível: 100% (posição no board)
- ✅ Status visual: 6 colunas (Backlog → Blocked)
- ✅ Comentários de progresso: 100% (mantido)

**Experiência do Usuário:**
- ✅ Time-to-understand: ~2 segundos (glance no board)
- ✅ Visão geral de jobs: Imediata (Kanban board funcional)
- ✅ Rastreabilidade: Excelente (posição + comentários)

### 8.3 KPIs Propostos

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Tempo para saber status de N cards | 30s × N | 2s | **15x mais rápido** |
| Cargas no Trello (visão geral) | 1 por card | 1 por board | **N cards → 1 carga** |
| Eficácia do Kanban board | 10% | 100% | **10x mais útil** |

---

## 9. Riscos e Mitigações

### 9.1 Risco: Listas Inexistentes no Board

**Probabilidade:** Alta
**Impacto:** Médio

**Mitigação:**
- Script `setup_trello_board.py` cria listas automaticamente
- Validação no startup do servidor
- Fallback: criar lista se não existir

### 9.2 Risco: Rate Limiting do Trello

**Probabilidade:** Baixa
**Impacto:** Médio

**Mitigação:**
- Cache de listas (já planejado no código)
- Batch updates se muitos cards
- Alerta se approaching limit

### 9.3 Risco: Cards Perdidos (Lista Deletada)

**Probabilidade:** Baixa
**Impacto:** Alto

**Mitigação:**
- Validação antes de mover (verificar se lista existe)
- Log de todas as movimentações
- Rollback manual se necessário

---

## 10. Conclusões

### 10.1 Resumo dos Gaps

| Gap | Severidade | Complexidade | Prioridade |
|-----|------------|--------------|------------|
| Sem movimentação visual | Alta | Média | **P0** |
| Lista padrão hardcoded | Média | Baixa | P1 |
| Falta de setup automatizado | Média | Média | P1 |
| Sem descoberta de listas | Baixa | Baixa | P2 |

### 10.2 Próximos Passos Imediatos

1. **Implementar movimentação de cards** (P0)
   - Estimativa: 2-3 horas
   - Impacto: Transforma o board em ferramenta útil

2. **Configurar lista padrão via ENV** (P1)
   - Estimativa: 30 minutos
   - Impacto: Remove obsolescência trimestral

3. **Script de setup de board** (P1)
   - Estimativa: 1-2 horas
   - Impacto: Facilita onboarding e novos ambientes

### 10.3 Recomendação Estratégica

**Adotar abordagem incremental:**
1. Implementar P0 (movimentação) primeiro
2. Testar com board manualmente configurado
3. Adicionar P1 (setup script) após validar P0
4. P2 (debug tools) pode ser opportunistic

**Justificativa:**
- P0 resolve o problema principal (falta de visualização)
- P1 facilita operação (não bloqueia P0)
- P2 é nice-to-have (pode ser adiado)

---

## 11. Referências

### 11.1 Arquivos do Código

- `src/core/kanban/application/trello_integration_service.py` - Service layer
- `src/infra/kanban/adapters/trello_adapter.py` - Adapter implementation
- `src/core/webhooks/application/job_orchestrator.py` - Job execution
- `src/core/kanban/domain/card.py` - Domain model (CardStatus)
- `src/core/kanban/ports/kanban_port.py` - Port contract

### 11.2 Documentação

- `docs/adr/ADR020-integracao-trello.md` - Arquitetura da integração
- `docs/FLUXO_GITHUB_TRELO_COMPONENTES.md` - Visão geral do fluxo
- `docs/STRATEGY_FLOW_STATUS_TAXONOMY.md` - Taxonomia de status

### 11.3 Scripts Úteis

- `src/core/kanban/testing/list_boards.py` - Lista boards disponíveis
- `scripts/test_kanban_trello.py` - Teste de integração

---

## Apêndice A: Exemplo de Uso (Após Implementação)

### A.1 Setup Inicial

```bash
# 1. Configurar variáveis de ambiente
cat >> .env <<EOF
TRELLO_API_KEY=sua_key
TRELLO_API_TOKEN=seu_token
TRELLO_BOARD_ID=seu_board_id
TRELLO_DEFAULT_LIST="To Do"
EOF

# 2. Setup do board (cria listas se não existirem)
python scripts/setup_trello_board.py

# 3. Verificar listas criadas
python scripts/list_trello_lists.py
```

### A.2 Durante Execução

```bash
# Job é criado no Trello
→ Card aparece em "To Do" 📋

# Job inicia processamento
→ Card move para "In Progress" ▶️
→ Comentário: "Job iniciado"

# Agente executando
→ Card permanece em "In Progress" ▶️
→ Comentários de progresso

# Job completado
→ Card move para "Done" ✅
→ Comentário final com resumo
```

### A.3 Monitoramento

```bash
# Visualizar board (glance)
→ Ver quais jobs em "In Progress"
→ Ver quais jobs em "Review"
→ Ver jobs falhados em "Blocked"

# Drill-down (abrir card específico)
→ Ler comentários detalhados
→ Ver correlation ID para consultar logs
→ Link para issue no GitHub
```

---

`★ Insight ─────────────────────────────────────`
**O Kanban board atual é como um relógio que mostra as horas apenas em texto:**
- Você sabe que são "14:30" (comentário)
- Mas não sabe se é dia ou noite (posição visual)

**Após implementar movimentação de cards:**
- O relógio terá ponteiros visíveis
- Um glance basta para saber onde tudo está
- A ferramenta cumpre sua promessa de **observabilidade visual**
`─────────────────────────────────────────────────`

> "O que não é visível, não é gerenciável" – made by Sky 🦍✨
