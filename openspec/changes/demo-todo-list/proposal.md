# Proposal: Demo Todo List

## Why

Skylab (Autokarpa Sky Lab) já demonstra capacidade de auto-evolução no modo Auto-Meta (self-hosting), mas é necessário validar que o sistema funciona evoluindo **código externo** - ou seja, que Skylab pode atuar como ferramenta de desenvolvimento para produtos reais, não apenas para si mesmo.

Uma Todo List é o exemplo perfeito: simples o suficiente para ser implementada rapidamente, mas complexa o suficiente para validar todas as capacidades do Skylab (TDD, PBT, Mutation, Refactoring).

## What Changes

- **Nova bounded context** `programs/demo-todo-list/` dentro de `src/core/autokarpa/`
- **Implementação completa de Todo List** com CRUD (Create, Read, Update, Delete)
- **Estrutura DDD modular** em `target/` (domain, application, infrastructure)
- **Validação do loop completo** Spec → TDD → Código → Refactor → PBT → Mutation
- **Métricas finais aceitáveis**: mutation score > 0.80, PBT 1000 casos passando, code health > 0.70

## Capabilities

### New Capabilities
- `demo-todo-list`: Sistema de Todo List como demonstração do Skylab
  - CRUD completo (adicionar, listar, marcar done, remover)
  - Testes gerados a partir da spec OpenSpec
  - Property-Based Testing validando propriedades (id único, ordenação preservada)
  - Mutation Testing validando qualidade dos testes
  - Refactoring automático se complexidade > 10

### Modified Capabilities
- Nenhuma (nova funcionalidade isolada, Skylab continua igual)

## Impact

**Código afetado:**
- `src/core/autokarpa/programs/demo-todo-list/` - novo bounded context
- `openspec/changes/demo-todo-list/` - spec da demo

**Modo de execução:**
- **Demo:** `run_skylab("demo-todo-list", iterations=100)`
- Skylab (FIXO em `programs/skylab/`) evolui código da Todo List (VARIÁVEL em `programs/demo-todo-list/target/`)

**Validação:**
- Mutation score > 0.80 (testes matam pelo menos 80% dos mutants)
- PBT com 1000 casos passando (propriedades invariantes validadas)
- Code health > 0.70 (sistema estável e evolvindo)
- Isolamento: agente modifica APENAS `target/`, nunca `core/`, `testing/`, `quality/`

**Sistemas afetados:**
- Skylab (valida modo Demo - código externo)
- Nenhum breaking change

**Riscos:**
- Complexidade da implementação DDD pode distrair do objetivo principal (validar Skylab)
- Performance do loop de evolução com target maior

> "Demo que funciona prova que o Skylab funciona" – made by Sky 🚀
