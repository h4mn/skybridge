# PRD022 - Implementação do Claude Agent SDK

**Data:** 2026-01-24
**Status:** 🔄 Em Planejamento
**Versão:** 1.0
**ADR Relacionada:** ADR021 (aprovada)
**Branch:** `feat/claude-agent-sdk`
**Worktree:** `B:\_repositorios\skybridge-agent-sdk`
**Deadline:** 2026-01-31 (7 dias)

---

## 📊 Resumo Executivo

Este PRD detalha a implementação da **claude-agent-sdk** no Skybridge, conforme aprovado na **ADR021**. A PoC já foi validada em worktree dedicada (`B:\_repositorios\skybridge-poc-agent-sdk`), e esta implementação irá migrar a abordagem atual baseada em subprocess para a SDK oficial da Anthropic.

**Objetivo Principal:** Implementar `ClaudeSDKAdapter` com feature flag para migração gradual, garantindo 4-5x melhoria de latência e observabilidade nativa via hooks.

---

## 🎯 Objetivos

### 1.1 Objetivo Principal

Implementar a interface de agentes usando **claude-agent-sdk** como substituta da abordagem subprocess, com migração gradual via feature flag.

### 1.2 Objetivos Específicos

1. ✅ **ClaudeSDKAdapter** implementando interface `AgentFacade`
2. ✅ **Session continuity** nativa via SDK
3. ✅ **Custom tools** via `@tool` decorator (in-process)
4. ✅ **Hooks de observabilidade** (PreToolUse, PostToolUse)
5. ✅ **WebSocket `/ws/console`** para stream em tempo real
6. ✅ **Feature flag `USE_SDK_ADAPTER`** para rollout gradual
7. ✅ **Testes A/B** comparando SDK vs subprocess
8. ✅ **Métricas de performance** (4-5x melhoria esperada)

---

## 📋 Escopo

### Inclui

| Item | Descrição |
|------|-----------|
| **ClaudeSDKAdapter** | Nova implementação de AgentFacade usando SDK |
| **Feature flag** | `USE_SDK_ADAPTER=true/false` para migração gradual |
| **Custom tools** | Migração de XML commands para `@tool` decorator |
| **Hooks** | PreToolUseHook, PostToolUseHook para observabilidade |
| **WebSocket console** | Stream de output do agente em tempo real |
| **Testes A/B** | Comparação de funcionalidade e performance |
| **Documentação** | PRD + atualização de SPEC008 |

### Não Inclui

| Item | Razão |
|------|-------|
| **Multi-agent workflow** | Específico de SPEC009, será outra PRD |
| **Migração de system prompts** | Formato mantido, apenas integração |
| **Alterações no Snapshot Service** | Independente de interface de agente |

---

## 🔧 Arquitetura

### Componentes a Implementar

```
┌─────────────────────────────────────────────────────────────────┐
│                    ClaudeSDKAdapter (NOVO)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. get_sdk_options()    → Configuração da SDK                  │
│  2. spawn()              → Cria client SDK e executa            │
│  3. Custom Tools         → @tool decorator (in-process)         │
│  4. Observability Hooks  → PreToolUse, PostToolUse              │
│  5. Stream Console       → WebSocket broadcast                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Feature Flag: USE_SDK_ADAPTER                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  true  → ClaudeSDKAdapter (SDK oficial)                        │
│  false → ClaudeCodeAdapter (subprocess - fallback)             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📅 Cronograma (7 dias)

### Dia 1: Setup e Estrutura

**Tarefas:**
- [ ] Copiar PoC da worktree `skybridge-poc-agent-sdk`
- [ ] Adicionar `claude-agent-sdk` ao `requirements.txt`
- [ ] Instalar dependência: `pip install -e .[agents]`

### Dia 2-3: ClaudeSDKAdapter

**Tarefas:**
- [ ] Criar `src/core/webhooks/infrastructure/agents/claude_sdk_adapter.py`
- [ ] Implementar `ClaudeSDKAdapter` seguindo interface `AgentFacade`

### Dia 3 (continuação): Custom Tools + Hooks

**Tarefas:**
- [ ] Criar custom tools com `@tool` decorator
- [ ] Implementar PreToolUseHook e PostToolUseHook

### Dia 4-5: Feature Flag + Migração

**Tarefas:**
- [ ] Adicionar `USE_SDK_ADAPTER` ao `.env.example`
- [ ] Modificar `JobOrchestrator` para usar adapter baseado na flag

### Dia 6: Testes + Performance

**Tarefas:**
- [ ] Criar testes A/B comparando SDK vs subprocess
- [ ] Medir latência: esperado 4-5x melhoria

### Dia 7: Documentação + Merge

**Tarefas:**
- [ ] Atualizar ADR021 com status "implementada"
- [ ] Criar QUICKSTART
- [ ] Preparar merge para dev

---

## ✅ DoD (Definition of Done)

### Funcional

- [ ] `ClaudeSDKAdapter` implementa `AgentFacade`
- [ ] Feature flag `USE_SDK_ADAPTER` funciona
- [ ] SDK e subprocess produzem mesmos resultados

### Performance

- [ ] Latência 4-5x menor que subprocess
- [ ] Parse 100% confiável (sem regex)

### Qualidade

- [ ] Testes A/B passando
- [ ] Testes de session continuity passando

### Documentação

- [ ] ADR021 atualizada (status: implementada)
- [ ] PRD022 completa

---

## 📊 Métricas de Sucesso

| Métrica | Antes | Depois | Alvo |
|---------|-------|--------|------|
| **Latência média** | 200-500ms | 50-100ms | **4-5x** |
| **Parse reliability** | ~85% | 100% | **+15%** |
| **Custom tools latency** | ~50ms | <1ms | **98%** |

---

> "Performance não é otimização prematura, é infraestrutura para escalabilidade" – made by Sky 🚀
