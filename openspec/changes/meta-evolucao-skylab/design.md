# Design: Meta-Evolução do Skylab

## Context

**Estado Atual:**
- Skylab evolui projetos (ex: demo-todo-list) modificando apenas `target/`
- `scope_validator` protege `core/`, `testing/`, `quality/` de qualquer modificação
- Tentativa de self-hosting (Iteração 3) foi bloqueada por scope violation
- Sem distinção entre "evolução autorizada" (meta) e "acidental" (bug)

**Constraints:**
- Sistema de evolução deve continuar funcionando após meta-evolução
- Rollback seguro se meta-evolução quebrar o sistema
- Testes devem validar tanto target quanto sistema após mudanças em `core/`
- Git já está disponível como mecanismo de versionamento

## Goals / Non-Goals

**Goals:**
- Permitir que Skylab evolua a si mesmo (meta-evolução) de forma controlada
- Manter proteção contra modificações acidentais de `core/` em modo normal
- Fornecer rollback atômico via git snapshots
- Isolar sessões de meta-evolução em branches separadas
- Validar meta-evolução com testes duplos (target + sistema)

**Non-Goals:**
- Meta-evolução sem supervisão (sempre requer intenção explícita)
- Modificação de `testing/` ou `quality/` (apenas `core/` e `target/`)
- Recursão infinita (limitada a N≤3)
- Snapshot engine customizado (usa git existente)

## Decisions

### 1. Git como Snapshot Engine

**Decisão:** Usar `git commit` e `git reset --hard` como mecanismo de snapshot.

**Racional:**
- Git já está disponível e é confiável
- Commits são atômicos e fornecem rollback garantido
- Branches naturais para isolamento de sessões
- Histórico completo para auditoria

**Alternativas Consideradas:**
- **Snapshot customizado em filesystem:** Mais complexo, não oferece histórico
- **Docker containers:** Overhead elevado, desnecessário para este caso

### 2. Meta-Gate como Camada Inviolável

**Decisão:** Criar `meta_gate.py` que NUNCA pode ser modificado (mesmo em meta-modo).

**Racional:**
- Portão fixo valida todas as entradas em meta-modo
- Critérios explícitos (intenção, baseline, Code Health) previnem abuso
- Ponto de auditoria único para meta-evoluções

**Alternativas Consideradas:**
- **Validação distribuída:** Mais difícil de manter consistente
- **Configuração externa:** Menos seguro, pode ser modificada acidentalmente

### 3. 3 Camadas com Responsabilidades Distintas

**Decisão:** Arquitetura em camadas com responsabilidades claras.

**Racional:**
- **Camada 0 (Inviolável):** Meta-gate + Snapshot + Rollback → nunca mudam
- **Camada 1 (Meta-Modificável):** Core com snapshot obrigatório → pode evoluir
- **Camada 2 (Livre):** Target → domínio da aplicação

**Alternativas Consideradas:**
- **2 camadas apenas:** Não distingue sistema fixo de evolutivo
- **Proteção por arquivo:** Mais granular, mais complexo de gerenciar

### 4. Recursão Controlada até N≤3

**Decisão:** Limitar recursão de meta-evolução a máximo 3 níveis.

**Racional:**
- **N=1 (Sandbox):** Skylab principal → Skylab sandbox (seguro)
- **N=2 (Meta-Mode):** Skylab → Skylab (main branch, controlado)
- **N≤3 (Meta-Gate):** Skylab → meta-gate → meta-gate melhorado (avançado)

**Alternativas Consideradas:**
- **Sem limite:** Risco de recursão infinita e instabilidade
- **N=1 apenas:** Muito limitante, não permite meta-gate evoluir

### 5. Teste Duplo Após Mudanças em Core

**Decisão:** Exigir testes de `target/` E do `sistema` após qualquer mudança em `core/`.

**Racional:**
- Meta-evolução pode quebrar o loop de evolução
- Testes de target sozinhos não detectam quebras no sistema
- Valida que "evolução continua evoluindo"

**Alternativas Consideradas:**
- **Teste apenas de target:** Não garante que sistema funciona
- **Teste apenas de sistema:** Não valida que domínio evoluiu corretamente

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| **Recursão infinita** | Limite N≤3 hardcoded, meta-gate nunca é modificado |
| **Corrupção de snapshot** | Git é testado e confiável; backup adicional antes de meta-modo |
| **Teste duplo falha** | Smoke tests rápidos + testes E2E completos |
| **Branch isolation falha** | `git checkout -b` cria branch isolado; merge manual requerido |
| **Code Health falso positivo** | PBT + Mutation Testing detectam qualidade real |
| **Meta-gate vira bottleneck** | Validação é rápida (< 1s); não está no loop crítico |
| **Complexidade adicional** | Camadas são simples; each has single responsibility |

## Migration Plan

**Fase 1: Meta-Gate + Snapshot (Camada 0)**
- Criar `meta_gate.py` com validações
- Criar `snapshot_engine.py` (git wrapper)
- Testes unitários de meta-gate

**Fase 2: Scope Validator + Integration**
- Modificar `scope_validator.py` para aceitar `meta_mode`
- Modificar `evolution.py` para integrar com meta-gate
- Testes de integração

**Fase 3: Self-Hosting Agent + Testes Duplos**
- Criar `self_hosting_agent.py`
- Criar `test_meta_mode.py` com testes duplos
- Executar self-hosting em sandbox

**Fase 4: Documentação**
- Criar `META-EVOLUÇÃO.md`
- Atualizar `PLAYBOOK.md` com meta-evolução

**Rollback Strategy:**
- `git reset --hard <baseline-commit>` restaura estado anterior
- Branch isolado permite descartar meta-evolução sem afetar main

## Open Questions

1. **Meta-gate evolui meta-gate?**
   - **Decisão:** Não. Meta-gate é Camada 0 (inviolável). Apenas Skylab (Camada 1) pode evoluir.

2. **Quem aprova merge de branch meta para main?**
   - **Decisão:** Humano. Branch meta fica isolado; merge requer revisão manual.

3. **Como detectar "stagnation" em meta-evolução?**
   - **Decisão:** Mesmo mecanismo de drift detection (stagnation/decline/repetition) já existente.

---

> "Arquitetura é a arte de esconder complexidades, não de eliminá-las" – made by Sky 🏗️
