# Proposal: Autokarpa Sky Lab

## Why

O projeto Autokarpa atualmente foca em otimização de modelos de ML, mas existe uma oportunidade maior: **otimização de implementação** de software. A análise de estado da arte 2026 (Martin Fowler, Kent C. Dodds, GrimoireLab) revelou que TDD combinado com Property-Based Testing (PBT) e Mutation Testing pode criar um sistema autônomo que evolui código baseado em specs OpenSpec, com qualidade garantida por métricas que previnem overfitting.

## What Changes

- **Novo bounded context** `programs/skylab/` dentro de `src/core/autokarpa/`
- **Sistema de evolução autônoma** com fluxo: Spec → TDD → Código → Refactor → PBT → Mutation → Medição → Repete
- **Property-Based Testing** usando Hypothesis (1000+ casos gerados automaticamente)
- **Mutation Testing** usando mutmut para validar qualidade dos testes
- **Módulo de debug estruturado** para analisar mutants sobreviventes
- **Métrica composta** que previne overfitting (mutation score 50%, unit 20%, PBT 15%, complexity 15%)
- **Padrão Karpathy**: `results.tsv` + branch por data + avanço com commits
  - `autoresearch/abr05-42` - branch renomeia quando encontra melhor iteração (colchetes evitados — são glob no bash)
  - `results.tsv` - log tab-separated (9 métricas: code_health, mutation, unit, pbt, complexity, memory, status, description); registra `discard` com commit hash mesmo após `git reset`
  - Avanço com `git commit` se melhorou, `git reset` se piorou
- **Integração OpenSpec**: input é o **nome da change** (não há prepare.py estático)
  - `run_skylab("autokarpa-sky-lab")` lê proposal/specs/design/tasks dinamicamente
  - `prepare.py` existe apenas como conceito (a própria change OpenSpec)

## Capabilities

### New Capabilities
- `tdd-core`: Core do sistema Autokarpa TDD - **Sistema** coordena loop, **Agente** implementa código
- `pbt-testing`: Property-Based Testing com Hypothesis para geração automática de casos de teste
- `mutation-testing`: Mutation Testing com mutmut para validação da qualidade dos testes
- `debug-analysis`: Raciocínio estruturado para análise de mutants sobreviventes
- `refactoring-automation`: Controle automático de complexidade ciclomática com refactoring obrigatório
- `demo-todo-list`: Demo validando o sistema completo com uma implementação de Todo List

### Arquitetura Sistema/Agente
Skylab é composto por dois papéis distintos:

| Papel | O que é | Responsabilidades |
|-------|---------|-------------------|
| **Sistema** (FIXO) | `core/`, `testing/`, `quality/` | Coordenar loop, gerar testes, rodar pytest/PBT/mutation, calcular code health, decidir keep/discard |
| **Agente** (VARIÁVEL) | Modifica apenas `target/solution.py` | Propor mudanças, implementar código mínimo para passar testes, refatorar quando exigido |

**Analogia com Autoresearch original:**
- Autoresearch: `prepare.py` (fixo) + `train.py` (agente modifica)
- Skylab: `core/testing/quality/` (fixo) + `target/solution.py` (agente modifica)

### Modified Capabilities
- Nenhuma (nova funcionalidade isolada)

## Impact

**Código afetado:**
- `src/core/autokarpa/` - novo subdiretório `programs/skylab/`
- `openspec/` - integração com sistema de specs

**Modos de execução:**
1. **Standalone (Padrão):** `run_skylab("change-name")` - funciona sozinho
2. **Com Ralph (Opcional):** Multi-sessão com persistência
3. **Com Autogrind (Opcional):** Wrapper redundante, apenas convenência

> "Testes ruins são piores que nenhum teste" – made by Sky 🔬

**Ponto de entrada:**
```python
# Uso:
run_skylab("autokarpa-sky-lab")

# O que acontece:
# 1. Carrega openspec/changes/autokarpa-sky-lab/proposal.md
# 2. Carrega openspec/changes/autokarpa-sky-lab/specs/**/*.md
# 3. Carrega openspec/changes/autokarpa-sky-lab/design.md
# 4. Carrega openspec/changes/autokarpa-sky-lab/tasks.md
# 5. Gera testes e código dinamicamente
# 6. Executa loop de evolução
```

**Nota:** `prepare.py` não existe como arquivo - a change OpenSpec **é** o prepare.

**Novas dependências:**
- `hypothesis>=6.100` - Property-Based Testing
- `mutmut>=23.0` - Mutation Testing
- `radon>=6.0` - Complexity analysis

**Sistemas afetados:**
- Autokarpa (nova funcionalidade, não breaking change)
- Ralph Loop (OPCIONAL: para coordenação multi-sessão)
- Autogrind (OPCIONAL: skylab tem loop próprio, é apenas conveniência)

**Riscos:**
- Complexidade de implementação do mutation testing
- Performance de 1000 iterações com PBT + mutation
- Garantir que agentes não "trapaceiem" a métrica

> "Testes ruins são piores que nenhum teste" – made by Sky 🔬
