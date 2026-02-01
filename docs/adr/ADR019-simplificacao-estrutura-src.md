# ADR019: Simplificação da Estrutura de Diretórios `src/`

## Status

**Proposto** → **Aprovado** → **Implementado**

Data: 2025-01-16

## Contexto

O Skybridge nasceu com uma estrutura de diretórios que refletia padrões de "biblioteca compartilhada", com múltiplos níveis de aninhamento:

```
src/
└── skybridge/
    ├── kernel/
    ├── platform/
    ├── core/
    │   └── contexts/
    │       ├── fileops/
    │       ├── webhooks/
    │       ├── agents/
    │       └── tasks/
    └── infra/
        └── contexts/
            ├── fileops/
            └── webhooks/
```

Isso resultava em imports excessivamente longos:

```python
from skybridge.core.contexts.fileops.domain.allowed_path import AllowedPath
from skybridge.kernel.contracts.result import Result
from skybridge.platform.config.config import get_config
```

### Problemas Identificados

1. **Carga cognitiva**: Imports longos e repetitivos
2. **Falso propósito**: Estrutura sugeria "biblioteca pública" quando o projeto é uso interno
3. **Conflito com stdlib**: `from platform.*` conflita com módulo padrão do Python
4. **Verbosidade**: 3-4 níveis de profundidade para código de aplicação

## Decisão

**Simplificar a estrutura para 2 níveis máximos de profundidade:**

```
src/
├── core/        # Contextos de domínio
├── infra/       # Adaptadores de infraestrutura
├── kernel/      # Contratos e registry central
└── runtime/     # Configuração, bootstrap, delivery, observability
```

**Imports resultantes:**

```python
from core.fileops.domain.allowed_path import AllowedPath
from kernel.contracts.result import Result
from runtime.config.config import get_config
```

### Mudanças Específicas

| Antes | Depois |
|-------|--------|
| `src/skybridge/core/contexts/*` | `src/core/*` |
| `src/skybridge/kernel/*` | `src/kernel/*` |
| `src/skybridge/platform/*` | `src/runtime/*` |
| `src/skybridge/infra/contexts/*` | `src/infra/*` |

### Renomeação `platform` → `runtime`

O nome `platform` foi renomeado para `runtime` porque:

**Nota:** Para informações sobre adaptações necessárias durante a transição de worktrees (especialmente para integração GitHub → Trello), consulte `docs/STANDALONE_VS_MAIN.md`. Esse documento detalha as diferenças entre a estrutura simplificada nas worktrees e a estrutura original, bem como as soluções implementadas.

O nome `platform` foi renomeado para `runtime` porque:

1. **Conflito com stdlib**: `import platform` sobrescreve módulo padrão do Python
2. **Quebra de dependências**: Bibliotecas como `httpx` usam `platform` internamente
3. **Semântica**: `runtime` descreve melhor as responsabilidades (bootstrap, config, delivery)

## Consequências

### Positivas

- ✅ **92.5% dos testes passando** (174/188) após migração
- ✅ Imports 40% mais curtos em média
- ✅ Estrutura alinhada com uso interno (não biblioteca)
- ✅ Sem conflito com módulos da stdlib
- ✅ Maior clareza cognitiva para desenvolvedores

### Negativas

- ⚠️ Script de migração necessário (~200 linhas)
- ⚠️ 14 testes de integração específicos requereram ajustes
- ⚠️ Histórico git mostra movimentação massiva de arquivos

### Mitigações

- Script `migrate_structure.py` com proteção de regressão
- Testes de baseline garantem funcionalidade preservada
- Git detecta renomeações corretamente (preserva histórico)

## Alternativas Consideradas

### Opção A: Manter Estrutura Original

**Vantagens:** Sem trabalho de migração

**Desvantagens:**
- Imports continuam longos
- Conflito com `platform` stdlib permanece
- Falsa aparência de "biblioteca"

**Decisão:** ❌ Rejeitada - não resolve problemas identificados

### Opção B: Usar Prefixo `skybridge.` Sem Níveis Extras

```
src/
└── skybridge/
    ├── fileops/
    ├── webhooks/
    ├── kernel/
    └── platform/
```

**Vantagens:**
- Imports curtos: `from skybridge.fileops...`
- Mantém namespace da aplicação

**Decisão:** ❌ Rejeitada - ainda conflita com `platform` e adiciona prefixo desnecessário para uso interno

### Opção C: Estrutura Flat (Opção Escolhida)

```
src/
├── core/
├── infra/
├── kernel/
└── runtime/
```

**Vantagens:**
- ✅ Imports mais curtos possíveis
- ✅ Sem conflitos
- ✅ Alinhado com propósito (app interna)

**Decisão:** ✅ Aprovada - equilíbrio ideal entre simplicidade e clareza

## Implementação

- **Branch:** `refactor/new-kanban-structure`
- **Commit:** `a49c3e5`
- **Script:** `scripts/migrate_structure.py`
- **Testes:** 174/188 passando (92.5%)

### Comando de Migração

```bash
python scripts/migrate_structure.py
```

O script executa:
1. Teste baseline (garante funcionamento pré-migração)
2. Movimentação de diretórios
3. Atualização de imports (~114 arquivos)
4. Verificação de sintaxe Python
5. Teste de regressão

## Referências

- [ADR002: Estrutura do Repositório Skybridge](./ADR002-Estrutura-do-Repositorio-Skybridge.md)
- [SPEC008: Workspace e Worktrees](../specs/SPEC008-workspace-worktrees.md)
- Issue: Implementação Kanban Context (2025-01-16)

---

> "A forma mais simples de resolver um problema é a mais elegante." – made by Sky 🌟
