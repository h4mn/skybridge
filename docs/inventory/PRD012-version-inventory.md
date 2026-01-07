# Inventário de Versões — Skybridge

**Data:** 2026-01-06
**Escopo:** Fase 1 do PRD012 — Descoberta e Inventário
**Status:** ✅ APROVADO — Implementação autorizada

---

## 1. Resumo Executivo

### ⚠️ Problemas Identificados

| Problema | Severidade | Impacto |
|----------|------------|---------|
| **Versões duplicadas em 3+ locais** | 🔴 Alta | Desalinhamento automático |
| **CLI vs Core divergentes** | 🟡 Média | CLI em 0.3.0, Core em 0.1.0 |
| **OpenAPI ahead do Core** | 🟢 Baixa | OpenAPI 0.2.2 vs Core 0.1.0 |
| **Kernel API sem versionamento próprio** | 🟡 Média | Misturado com Core |

---

## 2. Tabela de Inventário Completo

| Componente | Localização | Versão Atual | Formato | Observações |
|------------|-------------|--------------|---------|-------------|
| **App Skybridge** | `src/skybridge/__init__.py` | **0.1.0** | string | `__version__` |
| **Kernel API** | `src/skybridge/__init__.py` | **1.0.0** | string | `__kernel_api__` |
| **CLI App** | `apps/cli/__init__.py` | **0.3.0** | string | ⚠️ Divergente do Core |
| **setup.py** | `setup.py` | **0.3.0** | string | Pacote Python |
| **OpenAPI Contract** | `openapi/v1/skybridge.yaml` | **0.2.2** | string | ⚠️ Divergente do Core |
| **Platform Config** | `src/skybridge/platform/config/config.py` | **0.1.0** | string | Config padrão |

---

## 3. Discrepâncias Encontradas

### 3.1 Divergência Core vs CLI

```
Core (src/skybridge/__init__.py):   0.1.0
CLI (apps/cli/__init__.py):         0.3.0
```

**Análise:**
- CLI está 2 versões à frente do Core
- Provavelmente CLI foi versionado independentemente
- **Problema:** Usuários `pip install skybridge` recebem versão do setup.py (0.3.0), mas o código Core diz ser 0.1.0

### 3.2 OpenAPI Adiantado

```
Core (src/skybridge/__init__.py):   0.1.0
OpenAPI (openapi/v1/skybridge.yaml): 0.2.2
```

**Análise:**
- OpenAPI está sendo versionado mais frequentemente
- Documentação da API está ahead do código
- **Problema:** Consumidores da API veem versão 0.2.2, mas o Core diz 0.1.0

---

## 4. Análise por Componente

### 4.1 App Skybridge (Core)

**Arquivo:** `src/skybridge/__init__.py`

```python
__version__ = "0.1.0"
__kernel_api__ = "1.0.0"
```

**Status:** ✅ Definido como single source of truth pretendido
**Problema:** Outros componentes não leem daqui

---

### 4.2 Kernel API

**Arquivo:** `src/skybridge/__init__.py` (mesmo do Core)

```python
__kernel_api__ = "1.0.0"
```

**Status:** ⚠️ Misturado com Core
**Problema:** Deveria ter versionamento independente
**Recomendação:** Mover para `src/skybridge/kernel/__init__.py`

---

### 4.3 CLI App

**Arquivo:** `apps/cli/__init__.py`

```python
__version__ = "0.3.0"
```

**Status:** ⚠️ Divergente do Core
**Problema:** 2 versões à frente (0.3.0 vs 0.1.0)
**Recomendação:** Unificar com Core ou documentar porquê é diferente

---

### 4.4 OpenAPI Contract

**Arquivo:** `openapi/v1/skybridge.yaml`

```yaml
info:
  version: 0.2.2
```

**Status:** ⚠️ Divergente do Core
**Problema:** Não lê do `__version__`
**Recomendação:** Injetar versão via script/constraint

---

### 4.5 Platform Config

**Arquivo:** `src/skybridge/platform/config/config.py`

```python
version: str = "0.1.0"
```

**Status:** ⚠️ Hardcoded
**Problema:** Variável de fallback, mas não lê de lugar nenhum
**Observação:** Já tem `os.getenv("SKYBRIDGE_VERSION", "0.1.0")` — preparado para VERSION!

---

## 5. Arquivos SEM Versionamento (Identificados)

| Arquivo | Status | Recomendação |
|---------|--------|--------------|
| `pyproject.toml` | ❌ Não existe | Criar com versão do projeto |
| `src/skybridge/kernel/__init__.py` | ❌ Sem versão | Adicionar `__kernel_api__` próprio |
| `.env.example` | ❌ Não verificado | Adicionar `SKYBRIDGE_VERSION` |

---

## 6. Decisão: Versões Iniciais

**Decisão tomada (2026-01-06):** Rebaixar tudo para 0.1.0

```
SKYBRIDGE_VERSION=0.1.0
KERNEL_API_VERSION=0.1.0
OPENAPI_CONTRACT_VERSION=0.1.0
```

**Justificativa:**
- ✅ **Fresh start** — Antes não havia nada rastreando oficialmente
- ✅ **Sincronia total** — Todos os componentes começam alinhados
- ✅ **Sem confusão** — Evita discrepâncias entre versões anteriores não oficiais

**Mudanças necessárias:**
- Core: 0.1.0 → 0.1.0 (mantém)
- Kernel API: 1.0.0 → 0.1.0 (rebaixa)
- CLI: 0.3.0 → 0.1.0 (rebaixa)
- OpenAPI: 0.2.2 → 0.1.0 (rebaixa)
- Platform Config: 0.1.0 → 0.1.0 (mantém)

---

## 7. Arquivo VERSION Proposto

Baseado na ADR012, formato proposto:

```bash
# VERSION - Single Source of Truth
# Data de início: 2026-01-06
# Gerido automaticamente por workflows (PRD012)

SKYBRIDGE_VERSION=0.1.0
KERNEL_API_VERSION=0.1.0
OPENAPI_CONTRACT_VERSION=0.1.0
```

---

## 8. Próximos Passos (Fase 2: Implementação)

### ✅ APROVADO — Implementar Single Source of Truth

1. [ ] **Criar arquivo VERSION** na raiz
   ```
   SKYBRIDGE_VERSION=0.1.0
   KERNEL_API_VERSION=0.1.0
   OPENAPI_CONTRACT_VERSION=0.1.0
   ```

2. [ ] **Implementar script** `scripts/version.py` com `get_version(component)`

3. [ ] **Atualizar Core** (`src/skybridge/__init__.py`)
   - Ler `SKYBRIDGE_VERSION` do VERSION
   - Rebaixar `__kernel_api__` de 1.0.0 para 0.1.0

4. [ ] **Atualizar Kernel** (`src/skybridge/kernel/__init__.py`)
   - Adicionar `__kernel_api__` próprio
   - Ler `KERNEL_API_VERSION` do VERSION

5. [ ] **Atualizar CLI** (`apps/cli/__init__.py`)
   - Rebaixar de 0.3.0 para 0.1.0
   - Ler do VERSION ou do Core

6. [ ] **Atualizar OpenAPI** (`openapi/v1/skybridge.yaml`)
   - Rebaixar de 0.2.2 para 0.1.0
   - Injetar versão via script

7. [ ] **Atualizar setup.py**
   - Rebaixar de 0.3.0 para 0.1.0
   - Ler do VERSION

8. [ ] **Atualizar Platform Config**
   - Já preparado para ler `SKYBRIDGE_VERSION` env var

9. [ ] **Criar pyproject.toml** (se necessário)
   - Adicionar versão do projeto

---

## 9. Assinaturas

**Inventariado por:** Sky (Claude Code Agent)
**Data:** 2026-01-06
**Baseado em:** PRD012 - Estratégia de Versionamento (Semver + CC)

---

## A. Apêndice: Comandos Usados

```bash
# Busca de versões em Python
grep -r "__version__" --include="*.py"
grep -r "version.*=" --include="*.py"

# Busca de VERSION
find . -name "VERSION" -o -name "version"

# OpenAPI
find openapi -name "*.yaml" -o -name "*.yml"
```

---

> "Para versionar o futuro, primeiro precisamos entender o presente."
> — made by Sky 🔢✨
