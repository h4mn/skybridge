# Design: Autokarpa Sky Lab

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

## Decisões

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

### D4: Property-Based Testing - Hypothesis

**Decisão:** Usar Hypothesis (Python) para PBT, gerando **1000 casos** por teste.

**Racional:**
- **Encontra edge cases não pensados**: Gera casos aleatórios automaticamente
- **Shrinking**: Reduz caso de falha ao mínimo reprodutível
- **Estado da arte**: Padrão em 2026 para Python
- **Substitui testes manuais**: Mais eficiente que escrever casos "na mão"

**Alternativas consideradas:**
- **Testes manuais**: Rejeitado - Não escala, propenso a erro humano
- **Fuzzing (libFuzzer)**: Rejeitado - Mais complexo, Hypothesis suficiente
- **Só unit tests**: Rejeitado - Não cobre edge cases adequadamente

### D5: Refactoring Obrigatório - Antes de PBT

**Decisão:** Refactoring é **OBRIGATÓRIO** após Green, antes de PBT/Mutation.

```
TDD → Código → REFACTOR → PBT → Mutation → Medição
```

**Racional:**
- **Martin Fowler (2023)**: "Negligenciar o terceiro passo é a forma mais comum de errar TDD"
- **Previne código espaguete**: Complexidade controlada antes de validar
- **Complexidade < 10**: Threshold aceitável (radon)

**Alternativas consideradas:**
- **Refactoring opcional**: Rejeitado - Código acumula debt
- **Refactoring após tudo**: Rejeitado - Muito tarde, código já complexo
- **Sem refactoring**: Rejeitado - Viola princípio TDD

### D6: Debug Estruturado - Por Tipo de Mutant

**Decisão:** Debugger classifica mutants por tipo (Boundary, Arithmetic, Comparison, etc.) e sugere teste específico.

**Racional:**
- **Raciocínio estruturado**: Cada tipo tem padrão de correção
- **Ação concreta**: Sugere teste pronto para copiar/colar
- **Previne erro humano**: Guia desenvolvedor na correção

**Alternativas consideradas:**
- **Lista crua de survivors**: Rejeitado - Não ajuda a corrigir
- **Sugestão genérica**: Rejeitado - Não é acionável
- **Sem debug**: Rejeitado - Usuário perdido com survivors

### D7: Results.tsv Expandido + Registros Independentes

**Decisão:** `results.tsv` tem 20 colunas organizadas em 6 grupos. Registros independentes (JSON/MD) guardam detalhes quando necessário.

**Racional:**
- **Redundância útil**: Componentes individuais permitem debugging rápido sem recalcular
- **Análise de padrões**: "Mutation sempre baixo", "Muitos arquivos criados = estagnação"
- **Drift auditável**: Guardar quando stagnation/decline ocorreu permite análise de saúde do loop
- **TSV não explode**: Detalhes pesados vão para arquivos separados (JSON/MD)

**Alternativas consideradas:**
- **Apenas code_health**: Rejeitado - Impossível saber onde está o problema
- **Apenas components sem drift**: Rejeitado - Perde visibilidade da saúde do loop
- **Tudo em JSON único**: Rejeitado - Difícil de fazer queries rápidas
- **Apenas registros independentes**: Rejeitado - Perde visão rápida do histórico

**Estrutura de 20 colunas:**

| Grupo | Colunas | Propósito |
|-------|---------|-----------|
| Score (1) | `code_health` | Decisão keep/discard |
| Components (4) | `mutation`, `unit`, `pbt`, `complexity` | Gargalos de qualidade |
| Drift (3) | `stagnation`, `decline`, `repetition` | Saúde do loop |
| Diff (7) | `added_files`, `modified_files`, ... | Mudanças estruturais |
| Metadata (3) | `commit`, `memory_gb`, `status` | Identificação |
| Descritores (2) | `description`, `diff_path` | Contexto |

**Registros independentes:**

| Registro | Quando | Formato | Conteúdo |
|----------|--------|---------|----------|
| `results/components/N.json` | Sempre | JSON | Detalhes granulares (mutants por tipo, survivors, etc.) |
| `results/drift/N.json` | Apenas se detectado | JSON | Janela, scores históricos, ação tomada |
| `results/review/N.md` | Sempre | Markdown | Diff estruturado navegável |

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
│   ├── __init__.py
│   ├── change_loader.py  # Load OpenSpec change artifacts
│   ├── spec_parser.py    # Parse specs → generate tests
│   ├── test_runner.py    # Run pytest, PBT, mutation
│   ├── metrics.py        # Calculate code health score
│   ├── evolution.py      # Main loop: coordena Agente
│   ├── state.py          # State management + results.tsv
│   └── context_manager.py # PROTEÇÃO: Gerencia janela de contexto
├── testing/              # SISTEMA (FIXO) - validação
│   ├── __init__.py
│   ├── pbt.py           # Hypothesis strategies
│   ├── mutation.py      # Mutmut wrapper
│   └── debug.py         # Survivor analysis
├── quality/              # SISTEMA (FIXO) - controle de qualidade
│   ├── __init__.py
│   ├── complexity.py    # Radon wrapper
│   └── refactor.py      # Auto-refactoring logic
├── target/               # AGENTE (VARIÁVEL) - código que evolui
│   ├── __init__.py      # Pacote Python
│   ├── solution.py      # Ponto de entrada/orquestração (OBRIGATÓRIO)
│   ├── domain.py        # Entidades, VOs, regras de domínio (SUGERIDO)
│   ├── application.py   # Casos de uso, handlers (SUGERIDO)
│   └── infra.py         # Implementações concretas (SUGERIDO)
├── results.tsv           # Experiment log (TSV, não versionado)
├── program.md            # Instruções para o Agente autônomo
└── pyproject.toml        # Dependencies
```

**Separação Sistema/Agente:**
- **Sistema (FIXO)**: `core/`, `testing/`, `quality/` - coordena loop, valida, calcula métricas
- **Agente (VARIÁVEL)**: modifica apenas `target/` - implementa código com estrutura DDD modular
- **Estrutura DDD**: SUGERIDA mas EVOLUTIVA - ajustes baseados em evidência são encorajados
- O agente **nunca para para pedir confirmação** — o sistema decide keep/discard autonomamente

### results.tsv (Padrão Karpathy)

```
# Header (criado automaticamente)
commit	code_health	mutation	unit	pbt	complexity	memory_gb	status	description

# Exemplo de dados
a1b2c3d	0.4500	0.6000	0.8000	0.7000	0.7500	2.1	keep	baseline - initial implementation
b2c3d4e	0.5200	0.7000	0.9000	0.7500	0.7000	2.3	keep	implement process() with validation
c3d4e5f	0.4800	0.6500	0.8000	0.7000	0.7500	2.2	discard	switch to recursive approach
d4e5f6g	0.6100	0.8000	0.9000	0.8000	0.7000	2.5	keep	add mutation testing integration
e5f6g7h	0.0000	0.0000	0.0000	0.0000	0.0000	0.0	crash	OOM - input too large
f6g7h8i	0.7800	0.8500	1.0000	0.9200	0.7500	2.8	keep	fix edge cases + PBT with Hypothesis
```

**9 Colunas (vs 4 no Autoresearch):**
1. `commit` - Git hash
2. `code_health` - Score principal (≈ val_bpb)
3. `mutation` - Mutation score
4. `unit` - Unit score
5. `pbt` - PBT score
6. `complexity` - Complexity score
7. `memory_gb` - Peak memory
8. `status` - keep/discard/crash
9. `description` - Descrição curta

**Observação:** `results.tsv` NÃO é versionado (adicionar ao `.gitignore`).

### Módulos de Proteção contra Drift

```python
# core/context_manager.py

class ContextManager:
    """
    Previne Context Overflow + Drift.

    Drift: LLM perde foco no prompt original quando contexto cresce.
    Overflow: Contexto excede janela e instruções "caem".
    """

    PROMPT_REINJECT_INTERVAL = 10   # A cada 10 iterações
    COMPACTION_THRESHOLD = 0.8      # 80% da janela
    CHECKPOINT_INTERVAL = 25        # A cada 25 iterações
    KEEP_LAST_ITERATIONS = 20       # Mantém últimas 20

    def __init__(self, original_prompt: str, max_tokens: int = 100_000):
        self.original_prompt = original_prompt
        self.max_tokens = max_tokens
        self.iterations = []

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
            self.iterations[-self.KEEP_LAST_ITERATIONS:],  # Recentes
        ]

    def reset_after_checkpoint(self):
        """Reseta contexto após checkpoint."""
        self.iterations = []
```

### Snapshot + Diff Estruturado

**Integração com Snapshot System:** Skylab usa o sistema de snapshot existente em `src/runtime/observability/snapshot/` para rastrear mudanças estruturais.

**Fluxo por iteração:**

```python
# Antes da iteração
snapshot_before = capture_snapshot(
    subject="skylab",
    target="target/",
    depth=10,
    metadata={"iteration": i}
)

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃  AGENTE implementa mudança em target/    ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

# Depois da iteração
snapshot_after = capture_snapshot(
    subject="skylab",
    target="target/",
    depth=10,
    metadata={"iteration": i, "agent_description": description}
)

# Diff estruturado
diff = compare_snapshots(snapshot_before, snapshot_after)

# Renderiza para review
diff_markdown = render_diff(diff, format="markdown")
diff_html = render_diff(diff, format="html")

# Salva como artefato de auditoria
save_diff(diff, format="markdown", report=diff_markdown)
```

**O que o diff mostra:**

```markdown
# diff_20260405_042

## Resumo
- Arquivos adicionados: 1
- Arquivos modificados: 2
- Arquivos removidos: 0
- Delta de tamanho: +1024 bytes

## Mudanças
- added: target/domain.py
- modified: target/solution.py
- modified: target/application.py
```

**Benefícios:**
- **Review navegável:** Diff em alto nível mostra "o que mudou de verdade"
- **Não depende de git diff verboso:** Estruturação automática
- **Artefato de auditoria:** Cada iteração tem seu diff salvo
- **Reset facilitado:** Snapshot anterior pode ser restaurado

**Integração com results.tsv:**

```tsv
commit	code_health	mutation	unit	pbt	complexity	memory_gb	status	description	diff_path
a1b2c3d	0.4500	0.60	0.80	0.70	0.75	2.1	keep	baseline	diffs/diff_20260405_001.md
b2c3d4e	0.5200	0.70	0.90	0.75	0.70	2.3	keep	add domain	diffs/diff_20260405_002.md
```

### Fluxo de Execução

```python
# Entrada
run_skylab("autokarpa-sky-lab")

# ━━━ SISTEMA (Framework Fixo) ━━━

# 1. LOAD CHANGE
change = load_change("autokarpa-sky-lab")
# → Lê proposal.md, specs/**/*.md, design.md, tasks.md

# 2. PARSE SPECS
tests = parse_specs(change.specs)
# → Gera test_functions a partir de requirements/scenarios

# 3. EVOLUTION LOOP (100 iterações)
for i in range(100):
    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃  SISTEMA coordena, AGENTE implementa    ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    # 3.0 SNAPSHOT - Sistema captura estado antes
    snapshot_before = capture_snapshot("skylab", target="target/", metadata={"iteration": i})

    # 3.1 TDD - Sistema gera testes (RED)
    print(f"❌ RED: {len(tests)} testes falhando")

    # 3.2 AGENTE - implementa código mínimo
    # ┌─────────────────────────────────────────┐
    # │  Agente lê testes, analisa, propõe mudança  │
    # │  "Vou implementar função X()"               │
    # │                                              │
    # │  Agente modifica target/solution.py          │
    # │  SEM esperar confirmação — NEVER STOP        │
    # └─────────────────────────────────────────┘
    git_commit()  # Commit da proposta do Agente

    # 3.3 Sistema roda testes (GREEN?)
    unit_results = run_pytest()
    if not unit_results["success"]:
        git_reset()  # Falhou, descarta
        continue

    # 3.3.1 SNAPSHOT - Sistema captura estado depois
    snapshot_after = capture_snapshot("skylab", target="target/", metadata={"iteration": i})

    # 3.3.2 DIFF - Sistema gera diff estruturado
    diff = compare_snapshots(snapshot_before, snapshot_after)
    diff_path = save_diff(diff, format="markdown")

    # 3.4 REFACTOR - Sistema exige se necessário
    complexity = calculate_complexity(code)
    if complexity > 10:
        print("⚠️ Complexidade > 10, refactoring OBRIGATÓRIO")
        # Agente deve refatorar antes de continuar

    # 3.5 PBT + Mutation - Sistema valida
    pbt_results = run_hypothesis()
    mutation_results = run_mutmut()

    # 3.6 MEDIÇÃO - Sistema calcula
    score = calculate_code_health(unit, pbt, mutation, complexity)

    # 3.7 DECISÃO - Sistema decide
    if score > best_score:
        print(f"✅ KEEP: {score:.4f} > {best_score:.4f}")
        # Mantém commit do Agente
    else:
        print(f"❌ DISCARD: {score:.4f} ≤ {best_score:.4f}")
        git_reset_hard()  # Descarta proposta do Agente

# 4. OUTPUT
return best_code, metrics
```

**Responsabilidades:**

| Ação | Responsável |
|------|-------------|
| Carregar change | Sistema |
| Gerar testes | Sistema |
| Capturar snapshot antes | Sistema |
| Propor mudança | Agente |
| Implementar código | Agente (`target/`) |
| Capturar snapshot depois | Sistema |
| Gerar diff estruturado | Sistema |
| Rodar testes | Sistema |
| Exigir refactoring | Sistema |
| Calcular code health | Sistema |
| Decisão keep/discard | Sistema |
| git commit/reset | Sistema |

## Integrações (Opcionais)

### Padrão Karpathy: results.tsv + Tags + Branches

Skylab segue o padrão estabelecido por Karpathy no Autoresearch:

**Branch Naming:**
```bash
# Formato: autoresearch/<data><mes>-<iteracao-vencedora>
# IMPORTANTE: colchetes [N] causam glob expansion no bash — usar hífen
git checkout -b autoresearch/abr05-0

# Quando encontrar melhor solução na iteração 42:
git branch -m autoresearch/abr05-0 autoresearch/abr05-42
```

**results.tsv (Tab-Separated Values):**
```tsv
commit	code_health	mutation	unit	pbt	complexity	memory_gb	status	description
a1b2c3d	0.4500	0.60	0.80	0.70	0.75	2.1	keep	baseline
b2c3d4e	0.5200	0.70	0.90	0.75	0.70	2.3	keep	implement process()
c3d4e5f	0.4800	0.65	0.80	0.70	0.75	2.2	discard	switch to recursion
d4e5f6g	0.6100	0.80	0.90	0.80	0.70	2.5	keep	add mutation testing
e5f6g7h	0.0000	0.00	0.00	0.00	0.00	0.0	crash	OOM on large input
f6g7h8i	0.7800	0.85	1.00	0.92	0.75	2.8	keep	fix edge cases + PBT
```

**Colunas (20 métricas organizadas em 6 grupos):**

| Grupo | Colunas | Propósito |
|-------|---------|-----------|
| **Score Principal** | `code_health` | Métrica agregada (0-1) - decisão keep/discard |
| **Componentes (4)** | `mutation`, `unit`, `pbt`, `complexity` | Análise de gargalos de qualidade |
| **Drift (3)** | `stagnation`, `decline`, `repetition` | Saúde do loop de evolução |
| **Diff (7)** | `added_files`, `modified_files`, `removed_files`, `moved_files`, `added_dirs`, `removed_dirs`, `size_delta` | Mudanças estruturais em `target/` |
| **Metadata (3)** | `commit`, `memory_gb`, `status` | Identificação e recursos |
| **Descritores (2)** | `description`, `diff_path` | Contexto humano e caminho para diff detalhado |

**Exemplo de linha:**
```tsv
a1b2c3d	0.5200	0.60	0.90	0.75	0.70	false	true	false	1	2	0	0	0	0	+1024	2.3	keep	baseline	diffs/diff_001.md
```

**Explicação dos campos de drift:**
- `stagnation`: `true` se variância < 0.01 nas últimas N iterações
- `decline`: `true` se segunda metade da janela 10% pior que a primeira
- `repetition`: `true` se similaridade > 0.9 nos últimos snippets

**Observação:** `results.tsv` NÃO é versionado (adicionar ao `.gitignore`).

### Registros Independentes (Detalhamento)

Quando o `results.tsv` não é suficiente para análise, Skylab gera registros independentes com detalhes adicionais.

```
results/
├── results.tsv          # Métricas principais (20 colunas)
├── components/          # Detalhes de Code Health
│   ├── iteration_001.json
│   ├── iteration_042.json
│   └── ...
├── drift/               # Detalhes de Detecção de Drift
│   ├── iteration_015.json  # stagnation detectado
│   ├── iteration_023.json  # decline detectado
│   └── ...
└── review/              # Detalhes de Snapshot/Diff
    ├── iteration_001.md
    ├── iteration_042.md
    └── ...
```

**Quando cada registro é gerado:**

| Registro | Quando gera | Conteúdo |
|----------|-------------|----------|
| `components/N.json` | Sempre | Detalhes granulares de cada componente (mutants por tipo, cobertura por arquivo, etc.) |
| `drift/N.json` | Apenas se drift detectado | Contexto completo: janela analisada, scores históricos, ação tomada |
| `review/N.md` | Sempre | Diff estruturado navegável (já existe em `diffs/`) |

**Exemplo: `results/components/iteration_042.json`**
```json
{
  "iteration": 42,
  "timestamp": "2026-04-05T10:30:00Z",
  "code_health": 0.6100,
  "components": {
    "mutation": {
      "score": 0.80,
      "killed": 16,
      "survived": 4,
      "total": 20,
      "by_type": {
        "Boundary": {"killed": 4, "survived": 1},
        "Arithmetic": {"killed": 3, "survived": 0},
        "Comparison": {"killed": 5, "survived": 2},
        "Logical": {"killed": 4, "survived": 1}
      },
      "survivors": [
        {"line": 23, "type": "Boundary", "suggestion": "add test for x=0"}
      ]
    },
    "unit": {
      "score": 0.90,
      "passed": 18,
      "failed": 2,
      "total": 20,
      "coverage": 0.85,
      "by_file": {
        "test_solution.py": {"passed": 15, "failed": 0},
        "test_domain.py": {"passed": 3, "failed": 2}
      }
    },
    "pbt": {
      "score": 0.75,
      "passed": 15,
      "failed": 5,
      "total": 20,
      "shrinks": 3,
      "max_examples": 1000
    },
    "complexity": {
      "score": 0.70,
      "avg": 6.0,
      "max": 12,
      "worst_function": "process_complex_data",
      "by_file": {
        "solution.py": {"avg": 5.0, "max": 8},
        "domain.py": {"avg": 7.0, "max": 12}
      }
    }
  }
}
```

**Exemplo: `results/drift/iteration_015.json`**
```json
{
  "iteration": 15,
  "timestamp": "2026-04-05T09:45:00Z",
  "drift_type": "stagnation",
  "detection": {
    "window_size": 10,
    "variance": 0.008,
    "threshold": 0.01,
    "scores": [0.61, 0.61, 0.60, 0.61, 0.60, 0.61, 0.60, 0.60, 0.61, 0.60]
  },
  "action_taken": "context_reset",
  "reason": "Variância abaixo do threshold indica agente repetindo soluções"
}
```

**Exemplo: `results/review/iteration_001.md`**
```markdown
# Diff: Iteration 1

**Timestamp:** 2026-04-05T08:00:00Z
**Commit:** a1b2c3d
**Status:** keep

## Resumo
- Arquivos adicionados: 1
- Arquivos modificados: 2
- Delta: +1024 bytes

## Mudanças
- `added`: target/domain.py (entidades)
- `modified`: target/solution.py (import domain)
- `modified`: target/application.py (handler)

## Análise
- **Mutation**: 0.60 - ⚠️ abaixo do esperado
- **Complexidade**: 5.0 média - ✅ aceitável

## Sobreviventes
1. `target/domain.py:23` - Boundary
   - Sugestão: teste para `x=0`
```

**Benefício:**
- `results.tsv` = visão rápida (20 colunas)
- Registros independentes = análise profunda quando necessário
- Não sobrecarrega o TSV com dados muito granulares

**Loop de Avanço (igual Autoresearch):**
```python
LOOP_FOREVER:
    1. Modifica solution.py
    2. git commit
    3. Roda experimento
    4. Extrai métricas
    5. Registra em results.tsv  # SEMPRE antes de decidir; hash persiste mesmo após git reset
    6. Se code_health melhorou:
       → Mantém commit (branch avança)
       → status = "keep"
       → Renomeia branch se necessário: -0 → -42
    7. Se code_health piorou:
       → git reset --hard HEAD~1 (volta ao início)
       → status = "discard"  # linha já gravada com hash correto
    8. Se crash:
       → git reset
       → status = "crash"
```

### Uso Direto (Padrão)

```python
# Uso mais simples: skylab standalone
from skylab import run_skylab

run_skylab("autokarpa-sky-lab", iterations=100)
# Skylab tem loop próprio, não precisa de nada externo
```

### Ralph Loop (Opcional - Multi-sessão)

```python
# Para experimentos longos com pausar/continuar
ralph.run(
    program="skylab",
    input_change="autokarpa-sky-lab",
    iterations=100,
    persist_state=True  # Salva estado a cada iteração
)

# Benefício: pode retomar se crashar
# Quando: experimentos muito longos (> 1 hora)
```

### Autogrind (Opcional - Conveniência)

```python
# Skylab já tem loop, mas Autogrind pode ser wrapper
autogrind.grind(
    program="skylab",
    change="autokarpa-sky-lab",
    repeats=100
)

# Nota: Autogrind é REDUNDANTE (skylab tem loop)
# Uso: apenas se quiser usar interface Autogrind
```

### Skill Wrapper (Opcional)

```python
# /evolve <change>
@skill
def evolve(change_name: str):
    return run_skylab(change_name)
```

---

## Métricas

### Visão Geral

Skylab usa múltiplas métricas para validar qualidade de código e prevenir overfitting.

```
                    CODE HEALTH SCORE
                           ↓
        ┌──────────────────┴──────────────────┐
        │                                     │
    Componentes                        Detecção de
    (50% + 20% + 15% + 15%)              Drift
        │                                     │
    Mutation  Unit   PBT   Complexity    Stagnation
    Score    Score  Score   Score        Patterns
```

### Métrica Principal: Code Health Score

```python
# core/metrics.py

def calculate_code_health(
    mutation_results: dict,
    unit_results: dict,
    pbt_results: dict,
    complexity_results: dict
) -> float:
    """
    Métrica composta que previne overfitting.

    Retorna: 0.0 a 1.0 (maior = melhor)
    """

    # 1. Mutation Score (50% - MAIS IMPORTANTE)
    mutation_score = mutation_results["killed"] / max(mutation_results["total"], 1)

    # 2. Unit Score (20%)
    unit_score = unit_results["passed"] / max(unit_results["total"], 1)

    # 3. PBT Score (15%)
    pbt_score = pbt_results["passed"] / max(pbt_results["total"], 1)

    # 4. Complexity Score (15%)
    complexity_score = max(0, 1 - (complexity_results["avg"] / 20))

    # COMBINAÇÃO PONDERADA
    code_health = (
        mutation_score * 0.50 +
        unit_score * 0.20 +
        pbt_score * 0.15 +
        complexity_score * 0.15
    )

    return round(code_health, 4)
```

### Métricas Componentes

#### M1: Mutation Score (50%)

```python
# testing/mutation.py

MUTATION_BUDGET = 50   # máximo de mutants por run (amostragem aleatória se houver mais)
MUTATION_TIMEOUT = 60  # segundos máximos — análogo ao TIME_BUDGET do Karpathy

def run_mutation_tests() -> dict:
    result = subprocess.run(
        ["mutmut", "run", "--nosetup"],
        timeout=MUTATION_TIMEOUT
    )
    return {"killed": ..., "survived": ..., "total": ..., "score": ...}
```

Thresholds: `> 0.80` ✅ | `0.60-0.80` ⚠️ | `< 0.60` ❌

#### M2: Unit Score (20%)

```python
# core/test_runner.py
def run_unit_tests() -> dict:
    result = subprocess.run(["pytest", "-v", "--tb=no"])
    return {"passed": ..., "failed": ..., "total": ..., "coverage": ...}
```

#### M3: PBT Score (15%)

```python
# testing/pbt.py
def run_pbt_tests() -> dict:
    result = subprocess.run(["pytest", "pessimist.py", "--hypothesis-seed=0"])
    # Hypothesis gera 1000 casos automaticamente
    return {"passed": ..., "failed": ..., "total": ..., "shrinks": ...}
```

#### M4: Complexity Score (15%)

```python
# quality/complexity.py
def calculate_complexity(file: str = "solution.py") -> dict:
    result = subprocess.run(["radon", "cc", file, "-a"])
    # Exemplo: "solution.py - A (3.5)"
    return {"avg": ..., "max": ..., "worst_function": ..., "acceptable": avg < 10}

# Score: complexity_score = max(0, 1 - (avg / 20))
# avg=5 → 0.75 | avg=10 → 0.50 | avg=20 → 0.00
```

### Métricas de Detecção de Drift

```python
# core/context_manager.py

class DriftDetector:
    def check_stagnation(self, current_score: float) -> bool:
        """Variância < 0.01 nas últimas N iterações → estagnado."""
        ...

    def check_decline(self) -> bool:
        """Segunda metade da janela 10% pior que a primeira → caindo."""
        ...

    def check_repetition(self, code_snippets: list) -> bool:
        """Similaridade média > 0.9 nos últimos snippets → repetindo."""
        ...
```

### Loop Principal com State Management

```python
# core/evolution.py

def run_skylab(change_name: str, iterations: int = 100):
    """Loop padrão Karpathy: results.tsv + branch advancement."""
    import subprocess

    state = SkylabState(change_name)
    branch_name = f"autoresearch/{state.branch_tag}"  # ex: autoresearch/abr05-0

    subprocess.run(["git", "checkout", "-b", branch_name])

    if not Path("results.tsv").exists():
        with open("results.tsv", "w") as f:
            f.write("commit\tcode_health\tmutation\tunit\tpbt\tcomplexity\tmemory_gb\tstatus\tdescription\n")

    detector = DriftDetector(window_size=10)

    for i in range(state.current_iteration, state.current_iteration + iterations):
        code = evolve_code(...)
        metrics = calculate_all_metrics(code)

        # Commit ANTES de decidir
        subprocess.run(["git", "add", "solution.py"])
        subprocess.run(["git", "commit", "-m", f"exp-{i}: {metrics.get('description', 'test')}"])

        # Registra em results.tsv SEMPRE (hash persiste mesmo após reset)
        state.record_metrics(metrics, code)

        current_score = metrics["code_health"]

        if current_score > state.best_score:
            log(f"✓ Kept: {current_score:.4f}")
            # branch avança, tag renomeada: abr05-0 → abr05-{i}
        else:
            log(f"✗ Discarded: {current_score:.4f}")
            subprocess.run(["git", "reset", "--hard", "HEAD~1"])

        # Drift detection + context management
        if detector.check_stagnation(current_score):
            context_manager.reset()
        elif detector.check_decline():
            state.save()
            context_manager.reset()

        if i % 10 == 0:
            context_manager.reinforce_prompt()
        if context_manager.should_compact():
            context_manager.compact()

    return state.get_best()
```

### State Management

```python
# core/state.py

class SkylabState:
    """
    Padrão Karpathy: results.tsv + branch por data + avanço com commits.

    - Gerencia branch naming (autoresearch/<data><mes>-<iter>)
    - Registra experiments em results.tsv (não versionado)
    - Persistência para Ralph Loop multi-sessão
    """

    def _generate_branch_tag(self) -> str:
        """
        Formato: autoresearch/<data><mes>-<iteracao-vencedora>
        Exemplo: autoresearch/abr05-0, autoresearch/abr05-42
        NOTA: colchetes evitados — são glob no bash
        """
        ...

    def update_branch_tag(self):
        """Ex: autoresearch/abr05-0 → autoresearch/abr05-42"""
        subprocess.run(["git", "branch", "-m",
            f"autoresearch/{old_tag}", f"autoresearch/{self.branch_tag}"])

    def record_experiment(self, metrics: dict, code: str, commit_hash: str):
        """
        Grava linha no results.tsv.
        Chamado ANTES de git reset — hash referencia commit que existiu.
        """
        tsv_line = "\t".join([commit_hash, f"{code_health:.4f}", ...]) + "\n"
        with open("results.tsv", "a") as f:
            f.write(tsv_line)
```

### Dashboard de Métricas

```
┌─────────────────────────────────────────────────────────────┐
│                    SKYLAB METRICS DASHBOARD                  │
├─────────────────────────────────────────────────────────────┤
│  Iteration: 47/100                                           │
│  CODE HEALTH: 0.7845 ████████████████████████░░░░            │
│  Components:                                                 │
│    Mutation: 0.85  ████████████████████████████ (17/20)     │
│    Unit:     1.00  █████████████████████████████ (100%)     │
│    PBT:      0.92  ████████████████████████████░ (23/25)    │
│    Complex:  0.75  ████████████████████████░░░░ (avg: 5.2)  │
│  Drift Detection:                                            │
│    Stagnation: ✅ None (variance: 0.15)                      │
│    Decline:    ✅ None (trend: +0.02)                        │
│  Context: 82,345 tokens (82% full)                          │
└─────────────────────────────────────────────────────────────┘
```

## Riscos / Trade-offs

### R1: Context Overflow + Drift

**Risco:** LLM perde foco no prompt original após muitas iterações.

**Mitigação — três camadas:**

```python
PROMPT_REINJECT_INTERVAL = 10  # Re-injeta instruções originais a cada 10 iter
COMPACTION_THRESHOLD = 0.8     # Compacta quando > 80% da janela
CHECKPOINT_INTERVAL = 25       # Reset de contexto a cada 25 iter
```

Compactação mantém: prompt original + melhor código + specs resumidas + últimas 20 iterações.

### R2: Performance de Mutation Testing

**Risco:** Mutation testing cresce linearmente com o tamanho do código.

**Mitigação — orçamento fixo (análogo ao `TIME_BUDGET` do Karpathy):**

```python
MUTATION_BUDGET = 50   # máximo de mutants por run (amostragem aleatória se houver mais)
MUTATION_TIMEOUT = 60  # segundos máximos para o run inteiro de mutation
```

Sem esses limites o loop fica progressivamente mais lento. Mutation incremental (apenas linhas modificadas) reduz ainda mais o custo.

### R3: Agentes Trapaceando Métrica

**Risco:** Agente pode "passar nos testes" sem implementar funcionalidade (`return True`).

**Mitigação:** Mutation testing com 50% de peso torna esta estratégia ineficaz — testes que não matam mutants não contam.

### R4: Complexidade de Implementação

**Risco:** Sistema é complexo (Hypothesis + mutmut + radon + pytest).

**Mitigação:** Demo com Todo List valida o fluxo completo antes de expandir.

### R5: Isolamento do Target

**Risco:** Agente modifica arquivos do sistema (`core/`, `testing/`, `quality/`) em vez de apenas `target/`.

**Mitigação (camadas):**

1. **Validação de escopo via git:**
   ```python
   # Sistema verifica antes de aceitar commit
   changed_files = git_diff_names()
   if any(not f.startswith("target/") for f in changed_files):
       reject("Escopo violado: apenas target/ pode ser modificado")
   ```

2. **Snapshot estruturado antes/depois:**
   - Sistema captura snapshot de `target/` antes da iteração
   - Depois da iteração, captura novo snapshot e gera diff
   - Diff estruturado mostra exatamente o que mudou

3. **Reset nuclear:**
   - Se iteração falhar: `rm -rf target/` + restore do snapshot anterior
   - Garante estado limpo para próxima iteração

### R6: Arquitetura DDD Modular

**Decisão:** `target/` usa estrutura DDD modular (SUGERIDA, EVOLUTIVA).

```
target/
├── __init__.py
├── solution.py      ← ORIGATÓRIO (ponto de entrada)
├── domain.py        ← SUGERIDO (domínio)
├── application.py   ← SUGERIDO (casos de uso)
└── infra.py         ← SUGERIDO (infraestrutura)
```

**Racional:**
- **Software realista:** Código real tende a ser multi-arquivo, não single-file
- **Escopo isolado:** Pasta `target/` é a unidade de mutação (análoga ao `train.py` do Karpathy)
- **DDD modular:** Separa responsabilidades de forma previsível
- **Aberto a evolução:** Ajustes na arquitetura são FATORES DE MEDIÇÃO para melhoria

**Validações possíveis:**
- `solution.py` DEVE existir (entry point obrigatório)
- `domain.py` não pode importar `application` ou `infra`
- Cyclical dependency check entre módulos

**Trade-offs:**
| Prós | Contras |
|------|---------|
| Software realista | `git diff target/` é verboso |
| Diff estruturado ajuda | Reset é nuclear (`rm -rf`) |
| Agente pode estruturar | Harder to spot "o que mudou" |

## Migration Plan

### Fase 1: Setup (1 dia)
- Criar estrutura `src/core/autokarpa/programs/skylab/`
- Configurar `pyproject.toml` com deps (hypothesis, mutmut, radon)
- Criar `target/` com estrutura DDD modular (solution.py + domain/application/infra.py)
- Adicionar `results.tsv` ao `.gitignore`
- Configurar integração com snapshot system existente

### Fase 2: Core (2 dias)
- Implementar `change_loader.py`, `spec_parser.py`, `test_runner.py`

### Fase 3: Testing + Snapshot (2 dias)
- Implementar `pbt.py`, `mutation.py` (com MUTATION_BUDGET/TIMEOUT), `debug.py`
- Implementar integração com snapshot system (`capture_snapshot`, `compare_snapshots`)
- Implementar geração de diff estruturado (markdown/html)

### Fase 4: Quality (1 dia)
- Implementar `complexity.py`, `refactor.py`

### Fase 5: Evolution + State + Drift (1 dia)
- Implementar `evolution.py`, `metrics.py`, `state.py`, `context_manager.py`

### Fase 6: Demo (1 dia)
- Demo Todo List — valida fluxo completo end-to-end com 100+ iterações

**Total: ~8 dias**

## Open Questions

1. **Q1**: Como lidar com failures de Hypothesis (shrinking complexo)?
   - **A**: Timeout + fallback para testes manuais

2. **Q2**: Mutants em código de teste (não apenas produção)?
   - **A**: Inicialmente apenas código produção

3. **Q3**: Como integrar com Ralph Loop?
   - **A**: Ralph é opcional. `run_skylab("change", iterations=100)` funciona standalone.

4. **Q4**: Validar specs antes de evoluir código?
   - **A**: Sim, fase de "dry run" para validar que specs são testáveis

5. **Q5**: Como detectar Drift?
   - **A**: `DriftDetector` monitora estagnação, declínio e repetição. Ação: reset de contexto + checkpoint.

6. **Q6**: Arquitetura DDD é obrigatória?
   - **A**: Não, é SUGERIDA e EVOLUTIVA. Ajustes baseados em evidência são encorajados e registrados em `meta-results.md`.

7. **Q7**: Como lidar com multi-arquivo em `target/`?
   - **A**: Snapshot + diff estruturado permitem review em alto nível. `git diff --name-only` valida escopo.

8. **Q8**: Quantas colunas no `results.tsv`?
   - **A**: 20 colunas em 6 grupos. Redundância útil para análise rápida e padrões.

9. **Q9**: Registros independentes valem a pena?
   - **A**: Sim. TSV para visão rápida, JSON/MD para detalhes quando necessário.

## Nota: Arquitetura Evolutiva

A estrutura DDD modular de `target/` é **SUGERIDA**, não obrigatória. Skylab deve registrar aprendizados em `meta-results.md` e ajustar a arquitetura baseado em evidência. A qualidade do código (mutation score) é a verdade final — a estrutura é meio, não fim.

**Princípio:** "A arquitetura que permite maior code health score é a correta."

> "Testes são a especificação que não mente" – made by Sky 🔬
