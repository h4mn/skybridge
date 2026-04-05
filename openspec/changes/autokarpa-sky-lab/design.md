# Design: Autokarpa Sky Lab

**Status:** Design dividido em sub-arquivos para evitar limite de tokens (11k → ~3k por arquivo).

## Índice

| Arquivo | Tokens | Conteúdo |
|---------|--------|----------|
| **[design-core.md](design-core.md)** | ~3k | Context, Goals, Decisões D1-D3, Arquitetura, Estrutura, Context Manager |
| **[design-testing.md](design-testing.md)** | ~2.5k | Decisão D4, D6, PBT/Hypothesis, Mutation (Windows-friendly), Debug |
| **[design-quality.md](design-quality.md)** | ~2k | Decisão D5, Complexity (radon), Refactoring Obrigatório |
| **[design-integration.md](design-integration.md)** | ~2.5k | Decisão D7, Snapshot+Diff, Git integration, Drift detection |

## Resumo das Decisões

| ID | Decisão | Arquivo |
|----|---------|---------|
| D1 | Arquitetura - Program (não Skill) | core |
| D2 | Ponto de Entrada - Nome da Change | core |
| D3 | Métrica de Code Health - Mutation Domina (50%) | core |
| D4 | Property-Based Testing - Hypothesis (1000 casos) | testing |
| D5 | Refactoring Obrigatório - Antes de PBT | quality |
| D6 | Debug Estruturado - Por Tipo de Mutant | testing |
| D7 | Results.tsv Expandido (20 colunas) + Registros Independentes | integration |

## Arquitetura Resumida

```
src/core/autokarpa/programs/skylab/
├── core/          # Sistema FIXO - coordena e valida
├── testing/       # Sistema FIXO - PBT, mutation, debug
├── quality/       # Sistema FIXO - complexity, refactor
├── target/        # Agente VARIÁVEL - código que evolui
└── results.tsv    # Experiment log (não versionado)
```

## Métrica de Code Health

```python
score = (mutation * 0.5) + (unit * 0.2) + (pbt * 0.15) + (complexity * 0.15)
```

**Por que mutation domina (50%):**
- Previne overfitting (agentes não podem "trapacear" com `return True`)
- Valida qualidade real (testes que não matam mutants são inúteis)

## Fluxo Principal

```
Spec → TDD → Código → REFACTOR → PBT → Mutation → Snapshot → Diff → Medição → Keep/Discard → Repita
```

## Modos de Execução

1. **Standalone (Padrão):** `run_skylab("change", iterations=100)`
2. **Com Ralph (Opcional):** Multi-sessão com persistência
3. **Com Autogrind (Opcional):** Wrapper redundante

## Riscos Mitigados

| Risco | Mitigação |
|-------|-----------|
| Context overflow | Context Manager com compactação |
| Mutation no Windows | Implementação em Python puro (sem mutmut) |
| Overfitting | Mutation score 50%, PBT 15% |
| Código espaguete | Refactoring OBRIGATÓRIO se complexidade > 10 |

> "Spec → Teste → Código → REFACTOR → PBT → Mutation → Snapshot → Diff → Medição → Repita" – Sky 🔬
