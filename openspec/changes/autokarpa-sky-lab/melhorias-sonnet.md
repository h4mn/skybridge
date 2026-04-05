# melhorias-sonnet.md
> Registro das correções aplicadas por Claude Sonnet 4.6 nos artefatos do `autokarpa-sky-lab`
> **Data:** Abril 2026 | **Sessão:** validação e correção do design + tasks

---

## Resumo

Seis problemas identificados e corrigidos nos arquivos `proposal.md`, `design.md` e `tasks.md`.
Nenhuma mudança de intenção — apenas correções de consistência, segurança e fidelidade ao padrão Karpathy.

---

## M1 — Renomear `target/train.py` → `target/solution.py`

**Severidade:** Crítico

**Problema:** O arquivo alvo do agente estava chamado `train.py`, nome herdado do autoresearch original onde o agente treina modelos de linguagem. No Skylab o agente implementa software — o nome `train.py` é semânticamente errado e vai confundir qualquer agente ou humano que ler o código.

**Arquivos alterados:** `proposal.md`, `design.md`, `tasks.md`

**Correção aplicada:**
- Todas as referências a `target/train.py` substituídas por `target/solution.py`
- Comentário explicativo adicionado na árvore de diretórios: "não train.py — o agente implementa software, não treina modelos"
- `calculate_complexity(file: str = "train.py")` corrigido para `"solution.py"`
- `git add train.py` corrigido para `git add solution.py`
- Task 1.4 adicionada: criar `target/solution.py` vazio explicitamente

---

## M2 — Remover passo de confirmação humana do loop

**Severidade:** Crítico

**Problema:** O fluxo de execução no `design.md` tinha um passo:

```
│  Sistema confirma: "Pode propor"       │
```

Isso é o anti-pattern **Excessive Deference** documentado no próprio `observations/` do projeto. Um agente que pause para pedir confirmação a cada iteração nunca vai rodar 100 experimentos enquanto você dorme — que é exatamente o ponto central do padrão Karpathy.

**Arquivo alterado:** `design.md`

**Correção aplicada:**
```
# ANTES
│  Sistema confirma: "Pode propor"
│  Agente modifica target/train.py

# DEPOIS
│  Agente modifica target/solution.py
│  SEM esperar confirmação — NEVER STOP
```

Nota adicionada na seção Separação Sistema/Agente: "O agente **nunca para para pedir confirmação** — o sistema decide keep/discard autonomamente."

---

## M3 — Branch naming: colchetes `[N]` → hífen `-N`

**Severidade:** Importante

**Problema:** O formato original `autoresearch/abr05[42]` usa colchetes, que são caracteres especiais no bash (glob expansion). Em vários contextos isso causa falhas silenciosas ou comportamento inesperado:

```bash
git checkout autoresearch/abr05[42]  # pode ser interpretado como glob
git branch -m autoresearch/abr05[0] autoresearch/abr05[42]  # idem
```

**Arquivos alterados:** `proposal.md`, `design.md`, `tasks.md`

**Correção aplicada:**
- Formato alterado de `autoresearch/abr05[42]` para `autoresearch/abr05-42`
- Comentário adicionado em todos os code blocks: "IMPORTANTE: colchetes [N] causam glob expansion no bash — usar hífen"
- `_generate_branch_tag()` corrigido nos exemplos de código
- Task 13.2 adicionada com aviso explícito sobre o problema

---

## M4 — Timing do `results.tsv` em relação ao `git reset`

**Severidade:** Importante

**Problema:** O design não especificava quando exatamente o `results.tsv` era gravado em relação ao `git reset`. Sem essa clareza, implementações podem gravar o TSV depois do reset, referenciando um commit que não existe mais no branch — ou pior, não gravar linhas `discard` corretamente.

**Arquivo alterado:** `design.md`, `tasks.md`

**Correção aplicada:**

Loop de avanço atualizado:
```python
# ANTES
5. Registra em results.tsv
6. Se melhorou → keep / Se piorou → git reset

# DEPOIS
5. Registra em results.tsv  # SEMPRE antes de decidir
   # O commit hash persiste mesmo após git reset
   # (pode ser recuperado com git show <hash>)
6. Se melhorou → keep / Se piorou → git reset
   # status = "discard" — linha já foi gravada com hash correto
```

Docstring de `record_experiment()` atualizada: "Chamado ANTES de git reset — hash referencia commit que existiu."

Task 13.4 adicionada: "Implementar timing correto do `results.tsv`: gravar ANTES do `git reset`."

---

## M5 — `MUTATION_BUDGET` e `MUTATION_TIMEOUT` como constantes fixas

**Severidade:** Importante

**Problema:** O risco R2 mencionava "limitar mutants a código crítico" mas não definia como. Sem um orçamento fixo, o tempo de mutation testing cresce linearmente com o tamanho do código — cada iteração fica mais lenta que a anterior, tornando os 100 experimentos progressivamente mais lentos. Isso viola o espírito do Karpathy, que usa `TIME_BUDGET = 300` exatamente para garantir comparabilidade e velocidade constante.

**Arquivos alterados:** `design.md`, `tasks.md`

**Correção aplicada:**

```python
# Adicionado em testing/mutation.py
MUTATION_BUDGET = 50   # máximo de mutants por run (amostragem aleatória se houver mais)
MUTATION_TIMEOUT = 60  # segundos máximos para o run inteiro de mutation
```

Seção R2 reescrita com explicação da analogia com `TIME_BUDGET`. Tasks 9.2 e 9.3 adicionadas para implementar o orçamento e a amostragem aleatória.

---

## M6 — Isolamento do target: agente não pode tocar no sistema

**Severidade:** Menor

**Problema:** O design não especificava explicitamente que o agente deve modificar APENAS `target/solution.py` e nunca os módulos do sistema (`core/`, `testing/`, `quality/`). Em sessões longas de 100+ iterações, um agente em drift pode tentar modificar o próprio sistema de avaliação para "melhorar" suas métricas.

**Arquivos alterados:** `design.md`, `tasks.md`

**Correção aplicada:**
- Seção R5 adicionada ao `design.md`: "Agente modifica arquivos do sistema em vez de apenas `target/solution.py`"
- Mitigação: `program.md` deve ser explícito sobre o isolamento; sistema valida que apenas `solution.py` foi alterado antes de aceitar o commit
- Task 15.8 adicionada: "Verificar isolamento: o agente deve ter modificado APENAS `target/solution.py`"

---

## Arquivos modificados

| Arquivo | Melhorias aplicadas |
|---|---|
| `proposal.md` | M1 (train→solution), M3 (branch naming) |
| `design.md` | M1, M2, M3, M4, M5, M6 (todas) |
| `tasks.md` | M1 (task 1.4), M3 (tasks 13.1-13.5), M4 (task 13.4), M5 (tasks 9.2-9.3), M6 (task 15.8) |

---

## O que não foi alterado

- Arquitetura geral Sistema/Agente — correta e bem pensada
- Métricas e pesos (mutation 50%, unit 20%, PBT 15%, complexity 15%)
- `ContextManager` com re-injeção, compactação e checkpoint
- Integração com OpenSpec como "prepare dinâmico"
- `DriftDetector` com stagnation, decline e repetition
- Fluxo TDD → Refactor → PBT → Mutation
- Integração Ralph Loop como opcional

---

> "A qualidade de um sistema autônomo é proporcional à qualidade das suas restrições." – Sky 🔬
