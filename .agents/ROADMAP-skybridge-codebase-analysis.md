# Skybridge: Análise do Codebase e Roadmap

## Estado Atual

O repositório `skybridge` evoluiu de **repositório de documentação** para **código funcional validado**. A arquitetura definida nos ADRs está implementada e testada.

**O que existe hoje:**
- ✅ Documentação completa (ADRs, PRDs, playbooks)
- ✅ Estrutura planejada criada (ADR002 executado)
- ✅ **Kernel implementado** (Result, Envelope, QueryRegistry)
- ✅ **Platform implementado** (Bootstrap, Config, Logger, Delivery)
- ✅ **FileOps Context implementado** (DDD completo com Ports/Adapters)
- ✅ **CQRS funcionando** (/health, /fileops/read)
- ✅ **Ngrok integration** com URL fixa
- ✅ **Segurança validada** (allowlist bloqueando path traversal)

**O que falta:**
- Tasks Context com Event Sourcing
- Commands (/cmd/*)
- CLI/REPL/Web UI
- Mais operações de FileOps (write, delete, list)
- Integrações como plugins

---

## Arquitetura Implementada (Validada)

```
src/skybridge/
├── kernel/          # ✅ Result, Envelope, QueryRegistry
├── core/
│   ├── contexts/
│   │   ├── fileops/ # ✅ Domain + Application + Ports + Adapters
│   │   └── tasks/   # ⏳ Próximo
│   └── shared/      # ✅ Health query
├── platform/        # ✅ Bootstrap, Config, Logger, Delivery
└── infra/           # ✅ FileSystemAdapter

apps/api/            # ✅ Thin adapter com FastAPI
plugins/             # ⏳ Estrutura pronta, sem plugins ainda
```

**Padrões validados na prática:**
- ✅ Monólito Modular com fronteiiras claras
- ✅ DDD por Bounded Context (FileOps)
- ✅ CQRS na superfície (/qry/* funcionando)
- ✅ Hexagonal Architecture (Ports/Adapters)
- ✅ Config centralizada com environment variables

---

## Experimentos Realizados

### PoC #1: Hello World Health Endpoint
**PRD002** — Validação inicial da arquitetura

| Resultado | Status |
|-----------|--------|
| Kernel base funcionando | ✅ |
| Platform bootstrap | ✅ |
| CQRS /qry/health | ✅ |
| Correlation ID middleware | ✅ |
| Ngrok integration | ✅ |

**Lições aprendidas:**
- Imports absolutos são mais fáceis de manter que relativos
- Envelope com método `.error()` conflita com atributo — renomeado para `.failure()`
- Logger estruturado facilita debugging

### PoC #2: FileOps Read Query
**PRD003** — DDD completo com allowlist de segurança

| Resultado | Status |
|-----------|--------|
| FileOps Domain (AllowedPath, FilePath, FileContent) | ✅ |
| FileSystemPort (interface) | ✅ |
| FileSystemAdapter (implementação) | ✅ |
| ReadFileQuery (application layer) | ✅ |
| Rota /qry/fileops/read | ✅ |
| Allowlist dev (codebase) | ✅ |
| Path traversal bloqueado | ✅ |
| Ngrok URL fixa | ✅ |

**Lições aprendidas:**
- DDD com Ports/Adapters funciona bem na prática
- Result type facilita error handling
- Validação de allowlist DEVE acontecer antes de acessar disco
- Config via environment variables é prático

### PoC #3: Ngrok URL Fixa
**PB002** — Domínio reservado para desenvolvimento consistente

| Resultado | Status |
|-----------|--------|
| Domínio reservado `cunning-dear-primate.ngrok-free.app` | ✅ |
| Config via .env funcionando | ✅ |
| URL persistente entre restarts | ✅ |

**Lições aprendidas:**
- Domínios gratuitos do Ngrok podem mudar
- pyngrok é mais fácil que CLI para integração programática
- Documentar experiência real é mais valioso que especulação

---

## Roadmap Atualizado

### Fase 1: Fundação ✅ **CONCLUÍDA**

| Item | Descrição | Status |
|------|-----------|--------|
| **1.1** | Criar estrutura de pastas do ADR002 | ✅ Concluído |
| **1.2** | Implementar Kernel base (contracts, envelope, registry) | ✅ Concluído |
| **1.3** | Config centralizada (base + profiles + context files) | ✅ Concluído |
| **1.4** | Platform bootstrap + DI + observabilidade (correlation ID) | ✅ Concluído |
| **1.5** | FileOps Context (DDD completo) | ✅ Concluído |
| **1.6** | Ngrok integration com URL fixa | ✅ Concluído |

### Fase 2: Domínios Core (Em Progresso)

| Item | Descrição | Prioridade | Status |
|------|-----------|------------|--------|
| **2.0** | **ADR + SPEC: Roteamento Dinâmico CQRS** | Alta | 🔄 Próximo |
| **2.1** | Tasks BC com Event Sourcing | Alta | ⏳ Pendente |
| **2.2** | Mais operações FileOps (write, delete, list) | Média | ⏳ Pendente |
| **2.3** | Commands (/cmd/*) além de Queries | Alta | ⏳ Pendente |
| **2.4** | Security layer expandida (secret scan) | Média | ⏳ Pendente |
| **2.5** | Event store + projections (JSON) | Média | ⏳ Pendente |

### Fase 3: Interfaces

| Item | Descrição | Prioridade | Status |
|------|-----------|------------|--------|
| **3.1** | API app (já funcionando, expandir) | Alta | ✅ Parcial |
| **3.2** | CLI/REPL com comandos CQRS | Média | ⏳ Pendente |
| **3.3** | OpenAPI spec versionado | Média | ⏳ Pendente |
| **3.4** | Health checks expandidos | Baixa | ⏳ Pendente |

### Fase 4: Integrações como Plugins

| Item | Descrição | Prioridade | Status |
|------|-----------|------------|--------|
| **4.1** | Plugin host + manifest definition | Média | ⏳ Pendente |
| **4.2** | Migrar integrações existentes → plugins | Baixa | ⏳ Pendente |

---

## Próximos Passos Imediatos

### 1. ADR + SPEC: Roteamento Dinâmico CQRS
**Objetivo:** Definir como rotas CQRS são registradas e descobertas dinamicamente.

**Problema atual:**
- Rotas são hardcoded em `routes.py`
- Registry precisa ser registrado manualmente no bootstrap
- Não há descoberta automática de handlers

**Solução proposta:**
- Decorador `@query` e `@command` para registrar handlers
- Auto-discovery de handlers nos contexts
- Roteamento dinâmico baseado em registry

### 2. SPECs Pendentes
- SPEC000 — Envelope CQRS (já usado em produção, falta formalizar)
- SPEC001 — Config (já usado, falta formalizar)
- SPEC002 — Event Store (para Tasks context)
- SPEC003 — Plugin Manifest + Permissões
- SPEC004 — Roteamento Dinâmico CQRS (novo)

### 3. Tasks Context
- Domain: Task, Note, Group, List
- Event Sourcing com JSON store
- Projeções para leitura
- Commands e Queries

---

## Domínios Implementados

### FileOps Context ✅

**Implementado:**
- Domain: AllowedPath, FilePath, FileContent
- Ports: FileSystemPort
- Application: ReadFileQuery
- Infra: FileSystemAdapter
- Delivery: `/qry/fileops/read`

**Segurança validada:**
- ✅ Allowlist bloqueia path traversal
- ✅ Modo dev: codebase inteiro acessível
- ✅ Modo production: apenas \workspace
- ✅ Erros retornam mensagens claras

**Próximos passos FileOps:**
- Write, Delete, Move, Copy operations
- List directory
- Secret scanning antes de versionar
- Audit log de operações

---

## Padrões Validados na Prática

### Padrões que FUNCIONAM:

1. **Imports absolutos** — `from skybridge.kernel import Result`
   - Mais fáceis de manter que relativos
   - IDEs conseguem resolver melhor

2. **Result type** — Para error handling sem exceptions
   - `Result<T, E>` com `.is_ok()`, `.unwrap()`, `.map()`
   - Encadeamento com `.and_then()`

3. **Envelope CQRS** — Resposta padronizada
   - correlation_id, timestamp, status, data, error
   - `Envelope.from_result(result)` converte Result para Envelope

4. **Query Registry** — Handlers registrados centralmente
   - `get_query_registry().register(name, handler, description)`
   - Discovery em runtime

5. **Config via .env** — Prático para desenvolvimento
   - `load_dotenv()` no entrypoint
   - `os.getenv()` com defaults

6. **Ports/Adapters** — Fronteira clara entre domínio e infra
   - Domain define interfaces (Ports)
   - Infra implementa (Adapters)
   - Application orquestra os dois

### Padrões a EVITAR:

1. **Imports relativos** — Causam erros de módulo não encontrado
2. **Mesmo nome para método e atributo** — `Envelope.error()` vs `error`
3. **Validação tardia** — Allowlist deve validar ANTES de acessar disco

---

## Especificações Técnicas (SPECs)

### SPEC000 — Envelope CQRS (Informal)
Já implementado, falta formalizar:
```python
@dataclass
class Envelope(Generic[T]):
    correlation_id: str
    timestamp: str
    status: str  # "success" | "error"
    data: T | None = None
    error: str | None = None
    metadata: dict | None = None
```

### SPEC001 — Config (Informal)
Já implementado:
- `load_dotenv()` no entrypoint
- Dataclasses frozen para configs
- Singleton pattern via `get_*config()`
- Precedence: env vars > .env > defaults

### SPEC004 — Roteamento Dinâmico (A definir)
**Próximo ADR + SPEC**

---

## Conclusão

A arquitetura definida nos ADRs **foi validada na prática**. Os padrões escolhidos funcionam bem:

- DDD com Ports/Adapters permite evolução controlada
- CQRS simplifica a surface da API
- Result type elimina complexidade de exceptions
- FileOps Context com allowlist prova que segurança é viável

**Próximo passo:** Formalizar roteamento dinâmico para escalar para mais contexts sem aumentar complexidade manual.

---

> "Teoria sem prática é vazia; prática sem teoria é cega. Nós temos ambas." – made by Sky ✨
