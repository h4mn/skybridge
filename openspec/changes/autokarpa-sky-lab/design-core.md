# Design: Autokarpa Sky Lab - Core

## Context

**Estado atual:** Autokarpa foca em otimização de modelos de ML usando `programs/skyllm/` com arquivo `program.md` como prompt estático.

**Oportunidade:** Extensão do conceito para otimização de **implementação de software**, não apenas modelos. Análise de estado da arte 2026 revelou que TDD + PBT + Mutation Testing pode criar um sistema de evolução autônoma de código.

**Restrições:**
- Deve integrar-se com OpenSpec (ler changes dinamicamente)
- Pode ser coordenável por Ralph Loop (**OPCIONAL** - multi-sessão)
- Tem loop próprio (Autogrind é **OPCIONAL** - apenas conveniência)
- Não deve criar `prepare.py` estático (a change é o prepare)

**Stakeholders:**
- Usuário final (invoca skylab diretamente ou via Ralph/skill)
- Ralph Loop (**OPCIONAL** - coordena multi-sessão)
- Autogrind (**OPCIONAL** - skylab tem loop próprio)

## Goals / Non-Goals

**Goals:**
- Sistema autônomo que evolui código baseado em specs OpenSpec
- Métrica composta que previne overfitting (mutation testing é chave)
- Property-Based Testing para geração automática de casos (1000+)
- Debug estruturado para análise de mutants sobreviventes
- Refactoring obrigatório controlado por complexidade ciclomática

**Non-Goals:**
- Não é um skill interativo (é um program autônomo)
- Não substitui Autokarpa ML (coexiste como `programs/skylab/`)
- Não implementa funcionalidade específica (é framework genérico)
- Não usa `prepare.py` estático (lê change OpenSpec dinamicamente)

## Decisões Core

### D1: Arquitetura - Program (não Skill)

**Decisão:** Skylab é um **program** (`src/core/autokarpa/programs/skylab/`), não uma skill.

**Racional:**
- Código que **evolui autonomamente**, não interativo
- Tem **loop próprio** (não precisa Autogrind, mas pode usar)
- **Estado persistente opcional** via Ralph Loop (multi-sessão)
- Usa `program.md` como instruções para agente
- Skill `/evolve` seria wrapper opcional

**Alternativas consideradas:**
- **Skill interativa**: Rejeitada - Skylab não é interativo, é autônomo
- **MCP Plugin**: Rejeitada - Não expõe API externa
- **Biblioteca**: Rejeitada - Tem lógica própria de execução, não apenas funções

### D2: Ponto de Entrada - Nome da Change

**Decisão:** Input é **nome da change OpenSpec**, não parâmetros.

```python
run_skylab("autokarpa-sky-lab")
```

**Racional:**
- Change contém proposal/specs/design/tasks - tudo necessário
- Não precisa de `prepare.py` estático
- Permite reutilizar estrutura OpenSpec existente
- Change é "self-contained" com todos os artefatos

**Alternativas consideradas:**
- **Parâmetros explícitos**: Rejeitado - Duplica informação já na change
- **prepare.py estático**: Rejeitado - Perde flexibilidade dinâmica
- **Arquivo de config separado**: Rejeitado - Change já é o config

### D3: Métrica de Code Health - Mutation Domina

**Decisão:** Mutation testing tem peso **50%**, seguido por unit (20%), PBT (15%), complexity (15%).

```python
score = (mutation * 0.5) + (unit * 0.2) + (pbt * 0.15) + (complexity * 0.15)
```

**Racional:**
- **Previne overfitting**: Agentes não podem "trapacear" com `return True`
- **Valida qualidade real**: Testes que não matam mutants são inúteis
- **Estado da arte 2026**: Martin Fowler, Kent C. Dodds corroboram

**Alternativas consideradas:**
- **Pesos iguais**: Rejeitado - Mutation é muito mais importante
- **Coverage-based**: Rejeitado - Coverage não mede qualidade
- **Unit-dominated**: Rejeitado - Vulnerável a overfitting

## Arquitetura

### Modos de Execução

Skylab suporta 3 modos de execução:

1. **Standalone (Padrão):** `run_skylab("change", iterations=100)` - Loop próprio
2. **Com Ralph (Opcional):** Multi-sessão com persistência - Para experimentos longos
3. **Com Autogrind (Opcional):** Wrapper redundante - Apenas conveniência de interface

**Recomendação:** Começar com standalone. Adicionar Ralph/Autogrind se necessário.

### Estrutura de Diretórios

```
src/core/autokarpa/programs/skylab/
├── __init__.py           # EntryPoint: run_skylab(change_name)
├── core/                 # SISTEMA (FIXO) - coordena e valida
│   ├── change_loader.py  # Load OpenSpec change artifacts
│   ├── spec_parser.py    # Parse specs → generate tests
│   ├── test_runner.py    # Run pytest, PBT, mutation
│   ├── metrics.py        # Calculate code health score
│   ├── evolution.py      # Main loop: coordena Agente
│   ├── state.py          # State management + results.tsv
│   └── context_manager.py # PROTEÇÃO: Gerencia janela de contexto
├── testing/              # SISTEMA (FIXO) - validação
│   ├── pbt.py           # Hypothesis strategies
│   ├── mutation.py      # Mutation testing
│   └── debug.py         # Survivor analysis
├── quality/              # SISTEMA (FIXO) - controle de qualidade
│   ├── complexity.py    # Radon wrapper
│   └── refactor.py      # Auto-refactoring logic
├── target/               # AGENTE (VARIÁVEL) - código que evolui
│   ├── solution.py      # Ponto de entrada (OBRIGATÓRIO)
│   ├── domain.py        # Entidades, VOs (SUGERIDO)
│   ├── application.py   # Casos de uso (SUGERIDO)
│   └── infra.py         # Implementações (SUGERIDO)
├── results.tsv           # Experiment log (TSV, não versionado)
└── program.md            # Instruções para o Agente
```

**Separação Sistema/Agente:**
- **Sistema (FIXO)**: `core/`, `testing/`, `quality/` - coordena loop, valida, calcula métricas
- **Agente (VARIÁVEL)**: modifica apenas `target/` - implementa código com estrutura DDD modular
- **Estrutura DDD**: SUGERIDA mas EVOLUTIVA - ajustes baseados em evidência são encorajados

### results.tsv (Padrão Karpathy)

```
commit	code_health	mutation	unit	pbt	complexity	memory_gb	status	description
a1b2c3d	0.45	0.60	0.80	0.70	0.75	2.1	keep	baseline implementation
b2c3d4e	0.52	0.70	0.90	0.75	0.70	2.3	keep	implement process()
c3d4e5f	0.48	0.65	0.80	0.70	0.75	2.2	discard	switch to recursive
```

**Observação:** `results.tsv` NÃO é versionado (adicionar ao `.gitignore`).

### Context Manager - Proteção contra Drift

```python
class ContextManager:
    """Previne Context Overflow + Drift."""

    PROMPT_REINJECT_INTERVAL = 10   # A cada 10 iterações
    COMPACTION_THRESHOLD = 0.8      # 80% da janela
    CHECKPOINT_INTERVAL = 25        # A cada 25 iterações
    KEEP_LAST_ITERATIONS = 20       # Mantém últimas 20

    def should_reinject_prompt(self, iteration: int) -> bool:
        """Re-injeta prompt original periodicamente."""
        return iteration % self.PROMPT_REINJECT_INTERVAL == 0

    def should_compact(self, current_tokens: int) -> bool:
        """Verifica se contexto precisa de compactação."""
        return current_tokens > (self.max_tokens * self.COMPACTION_THRESHOLD)

    def compact(self) -> list:
        """Remove iterações antigas, mantém essencial."""
        return [
            self.original_prompt,          # Sempre no topo
            self.best_code,                # Melhor solução
            self.specs_summary,            # Specs resumidas
            self.iterations[-20:],         # Recentes
        ]
```

> "Mutation testing domina porque previne overfitting" – Sky 🔬
