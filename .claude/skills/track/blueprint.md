# /track - Blueprint Vivo

> Status: Otimização Performance ✅ (2026-04-04) | Criado: 2026-04-02

## Arquitetura Final

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           /track Skill (v2 - Optimistic)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Comando │───→│  Orqst  │←──→│ Toggl   │───→│ Rescue  │───→│ Verify  │  │
│  │ /track  │    │ Python  │OptM│ API     │    │ Time    │    │ Background│ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       │              │              │              │              │        │
│       v              v              v              v              v        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Menu    │    │ data/   │    │ Time    │    │ Prod    │    │ Rollback │  │
│  │ Options │    │ json    │    │ Entries │    │ Pulse   │    │ on Error │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│                                                                              │
│  Optimistic-Start: timer iniciado PRIMEIRO (perceived 25s)                   │
│  Verify-After: verificação em background (total 50s, mas usuário vê 25s)    │
│  CRUD Toggl: Create/Read/Update/Delete time_entries                         │
│  RescueTime: Read produtividade                                             │
│  Saídas: Cotas, Feedback Pomodoro, Alertas, Relatórios                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Fases de Evolução

### Fase 1 - MVP Core (Spike 2h)
- `/track` → menu de opções (fase/etapa/projeto)
- Cálculo de cotas: `tempo_horas × 0.625`
- Feedback simples no intervalo Pomodoro (10min)
- Estado salvo em `.claude/skills/track/data/state.json`
- **Sem alertas ainda**

### Fase 2 - Histórico e Estimativas (Depois da semana de prova)
- Busca histórico Toggl para sugerir estimativas
- Alerta: tarefa estagnada > 4h
- Alerta: estourou orçamento 120%
- Métrica: precisão de estimativa

### Fase 3 - Patterns e Contexto (Auto-evolução)
- Detecção automática de contexto (horário + PC + projeto)
- Alpha patterns (micro-hábitos lucrativos)
- Beta patterns (destruidores de valor)
- Alerta: muita distração > 2h
- Alerta: padrões negativos

## Otimização de Performance (2026-04-04)

### Problema
- Tempo resposta: 3-5 minutos
- Bottleneck: get_time_entries retornando 18 entries
- Raciocínio LLM intermediário

### Solução Cycle 1
- **Orquestrator Python** - Lógica de decisão externalizada
- **state.json local** - Cache evita MCP calls pesadas
- **Skill slim** - Só orquestra orquestrator + MCP

### Resultados Cycle 1
| Cenário | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Retoma pomodoro | 72-319s | **30s** | -96% |
| Nova track | 60-180s | **30s** | -83% |
| Status | 30-60s | **0.1s** | -99.7% |

**Status Cycle 1:** ✅ Target < 30s atingido em todos cenários

### Cycle 2 - Optimistic-Start (2026-04-04)

**Abordagem:** Perceived Performance via verify assíncrono

| Latência MCP | Verify-First | Optimistic | Melhoria Perceived |
|--------------|--------------|------------|-------------------|
| 100ms (mock) | 200.7ms | 100.35ms | **50%** |
| 25s (real) | 50s | 25s | **50%** |

**Implementação:**
- `orchestrator.py start --optimistic` → `action: "start_optimistic"`
- Timer iniciado PRIMEIRO (perceived: 25s)
- Verify em background (total: 50s)
- Rollback automático se verify falhar

**Status Cycle 2:** ✅ 50% melhoria perceived confirmada

## Tags (20) - Português

### Valor
- `alto-valor` - Impacto direto no negócio
- `medio-valor` - Manutenção, melhorias
- `baixo-valor` - Nice to have

### Tipo
- `feature` - Nova funcionalidade
- `bugfix` - Correção de bug
- `refactor` - Refatoração
- `docs` - Documentação
- `tests` - Testes
- `research` - Pesquisa/exploração

### Fase
- `especificacao` - Definindo o que fazer
- `implementacao` - Codificando
- `teste` - Validando
- `deploy` - Entregando

### Projeto
- `skybridge` - Projeto pessoal
- `hadsteca` - Trabalho (outros sistemas)

### Status
- `bloqueado` - Esperando algo/alguém
- `em-progresso` - Trabalhando ativamente
- `revisao` - Revisando/validando
- `concluido` - Pronto

## Contextos

| Contexto | Detecção |
|----------|----------|
| Trabalho | 08-19h + PC trabalho + projeto hadsteca/outros |
| Casa | Fora 08-19h + PC pessoal + projeto skybridge |

## Constantes

- **100 cotas/mês** = salário
- **0.625 cotas/hora** = custo do tempo
- **5 cotas/dia** (20 dias úteis)
- **Pomodoro**: 50min trabalho + 10min pausa (ajustado para trabalho com IA)

## Padrões de Trabalho com IA (2026-04-04)

### Mudança: 25+5 → 50+10

**Problema com 25min:**
- Muito pouco tempo para entrar em flow profundo
- Troca de contexto frequente quebra concentração
- "Aparece bastante problema e eu acabo não fazendo o que eu preciso"

**Por que 50+10 funciona melhor:**
- Tempo suficiente para 2-3 ciclos de trabalho profundo
- IA acelera execução, mas precisa de tempo de setup/contexto
- 10min de pausa permite digestão real + planejamento próximo ciclo

### Padrão "Human-AI Collaboration" vs "Solo Human"

| Aspecto | Solo Human (25+5) | Human + IA (50+10) |
|---------|-------------------|---------------------|
| Context setup | 5min (manual) | 2min (IA ajuda) |
| Deep work | 15min | 35min |
| Review/ajuste | 5min (próximo ciclo) | 10min (pausa + IA summary) |
| Total | 25min | 50min |

### Novo Fluxo Sugerido

```
┌─────────────────────────────────────────────────────────────┐
│  50min Trabalho + 10min Pausa (Human-AI Flow)             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Plan (2min) │───→│ Execute (35m)│───→│ Review (3m)│     │
│  │ + IA setup  │    │ + IA assist  │    │ + AI summary│     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                                       │            │
│         v                                       v            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Break (10m) │    │ Next cycle  │    │ Deliverable │     │
│  │ + digestão  │    │ + IA insights│    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Heurística Emergente

> **"Com IA no loop, menos ciclos mas mais profundos. Contexto é caro, então estica o ciclo. 50+10 > 25+5 para trabalho colaborativo human-AI."**

## Métricas Finais

1. **Precisão de Estimativa**
   - `(cotas_estimadas / cotas_reais) × 100`
   - Meta: > 80%

2. **Alpha Patterns**
   - Quais tags/comportamentos reduzem custo?
   - Ex: "testar antes = -30% tempo"

3. **Beta Patterns**
   - Quais tags/comportamentos aumentam custo?
   - Ex: "sem specs = +50% tempo"

## Estrutura de Dados

### state.json
```json
{
  "contexto": "casa",
  "tarefa_ativa": {
    "id": "toggl_entry_id",
    "projeto": "skybridge",
    "fase": "implementacao",
    "estimativa_cotas": 2.5,
    "inicio": "2026-04-02T10:00:00"
  },
  "cotas_hoje": 1.875,
  "ultimo_feedback": "2026-04-02T10:25:00"
}
```

### history.json
```json
{
  "tarefas": [
    {
      "id": "unique_id",
      "projeto": "skybridge",
      "fase": "implementacao",
      "estimativa_cotas": 2.5,
      "real_cotas": 3.125,
      "tags": ["feature", "alto-valor"],
      "concluido_em": "2026-04-02T12:00:00"
    }
  ]
}
```

## Decisões Tomadas

- ❌ **NÃO** integrar com `/tarefa do hadsteca`
- ✅ **Estado** em `.claude/skills/track/data/`
- ✅ **Toggl** CRUD completo (não só leitura)
- ✅ **Feedback** apenas em intervalos Pomodoro (10min)

## CRUD Toggl Completo

### Create (Criar)
- `/track nova` → Cria time_entry no Toggl automaticamente
- Com projeto, tags, descrição, estimativa

### Read (Ler)
- `/track status` → Busca time_entries ativos do Toggl
- `/track historico` → Lista entradas de hoje/semana

### Update (Atualizar)
- `/track continuar` → Atualiza descrição, tags, adiciona tempo
- `/track estimativa` → Ajusta estimativa de uma tarefa

### Delete (Deletar)
- `/track deletar` → Remove time_entry errada do Toggl
- Confirmação antes de deletar

### Benefício CRUD
Você **nunca** abre o Toggl manualmente. `/track` é sua única interface.

## Arquitetura de Notificações (EM ELABORAÇÃO)

### Problema
- App Toggl para/cria entries automaticamente (Pomodoro)
- Sky precisa saber quando mudar de tarefa
- Usuário esquecendo detalhes (sobrecarga cognitiva)

### Componentes Disponíveis

**1. Webhook Skybridge** ✅ (já existe)
- Usado para: Kanban Trello + GitHub
- Pode receber: Webhooks Toggl
- Endpoint: `https://seu-skybridge.com/webhooks/toggl`

**2. Claude Channels** ✅ (MCP instalado)
- Envia notificações SSE em tempo real
- Sky recebe推送 sem polling

### Fluxo Proposto (rascunho)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ App Toggl   │───→│ Webhook     │───→│ Sky         │
│ (Pomodoro)  │    │ Skybridge   │    │ (notificado)│
└─────────────┘    └─────────────┘    └─────────────┘
       │                                     │
       │  entry criada/parada                │
       v                                     v
┌─────────────┐                    ┌─────────────┐
│ Toggl API   │                    │ /track      │
│             │◄───────────────────│ (responde)  │
└─────────────┘     Claude         └─────────────┘
                    Channels
```

### Eventos Toggl para monitorar

- `timer.started` → Nova tarefa iniciada
- `timer.stopped` → Tarefa finalizada
- `entry.created` → Entry criada (Pomodoro auto)
- `entry.updated` → Entry modificada

### Decisões Pendentes

- [ ] Webhook Toggl está habilitado na conta?
- [ ] Claude Channels está configurado corretamente?
- [ ] Qual URL do webhook Skybridge?
- [ ] Como autenticar webhook do Toggl?
- [ ] Quer notificação para TODOS eventos ou só alguns?

### Próximos Passos Imediatos

1. **Hoje:** Documentar arquitetura existente
2. **Depois:** Sessão de trabalho - implementar webhook
3. **Teste:** App Toggl → Webhook → Sky → Claude Channels → Você

---

## Pontos de Decisão (descobrir na prática)

- ? Qual formato ideal de menu de opções?
- ? Quanto detalhe de feedback é útil vs. ruído?
- ? Precisa de comando `/track relatorio` ou automático?
- ? Como detectar início/fim de Pomodoro sem interromper?
- ⚠️ **NOVO:** Como webhook Toggl + Claude Channels funcionam junto?

## Próximos Passos

1. ✅ Blueprint criado
2. ✅ Spike Fase 1 (2h)
3. ✅ Otimização performance (2026-04-03): SKILL.md 1084→203 palavras, edge cases separados, project cache
4. ⏳ Semana de prova
5. ⏳ Decisão Fase 2 baseada em dados

## Estrutura de Arquivos (pós-otimização)

```
track/
  SKILL.md          # Runtime — decision table + maps + rules (30 linhas)
  edge-cases.md     # Referência — 10 edge cases com pseudocode
  blueprint.md      # Arquitetura + roadmap
  data/
    state.json      # Estado + cache (workspace_id, project_cache)
    history.json    # Histórico de tarefas
```

---

> "O mapa não é o território, mas ajuda a não se perder" – made by Sky [mapa]
