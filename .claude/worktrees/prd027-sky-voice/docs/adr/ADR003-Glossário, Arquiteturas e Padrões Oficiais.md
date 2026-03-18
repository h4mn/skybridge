---
status: aceito
data: 2025-12-23
---

# ADR003 — Glossário, Arquiteturas e Padrões Oficiais (Skybridge)

## Status
Aceito

## Contexto
Com a estrutura definida (ADR002) e a visão de produto estabelecida (Tooling Local → Plataforma de Agentes → Time/Self-host → Ecossistema de Plugins → SaaS Multi-tenant), precisamos fixar um vocabulário e um conjunto mínimo de arquiteturas/padrões para evitar deriva, reduzir boilerplate e manter decisões consistentes entre contexts, apps e plugins.

## Decisão
Adotar oficialmente:
1) **Arquitetura macro:** Monólito Modular (core) + Plugins opcionais (plugin-ready, market futuro).
2) **Modelagem:** DDD por Bounded Context (apenas onde há linguagem/regras: `fileops`, `tasks`).
3) **Fluxo de aplicação:** CQRS na superfície (API) para contornar limitações de rotas e manter contrato previsível.
4) **Persistência de histórico:** Event Sourcing **apenas** onde gerar valor (inicialmente `tasks`), com projeções.
5) **Estilo interno:** Clean/Hexagonal por módulo quando necessário (principalmente plugins e integrações).
6) **Configuração:** Configuração centralizada por perfil + arquivo por contexto, com precedence definido.
7) **Observabilidade e segurança:** Correlation ID, logs estruturados e políticas de segurança como padrão.

---

## Glossário Oficial (termos e uso)
- **Core**: o pacote principal (`src/skybridge`) que precisa existir para o produto funcionar. Ver seção [Terminologia](#terminologia) para distinção entre Core Package e Core Layer.
- **Context / Bounded Context (BC)**: fronteira de linguagem e regras de negócio (ex.: `fileops`, `tasks`).
- **Plugin**: extensão opcional (integração/pacote) que depende do **Kernel** (via ports aprovados) e pode ser instalada/removida. Nunca depende diretamente do domínio.
- **Shared**: mecanismos transversais sem regra de negócio (CQRS, auth, logging, types).
- **Support**: capacidades operacionais: versionamento → entrega (CI/CD, packaging, release notes).
- **Command**: intenção de mudar estado (side-effects).
- **Query**: leitura/consulta (sem side-effects).
- **Event**: fato ocorrido (imutável), produzido por comandos e consumido por projeções/handlers.
- **Projection**: visão materializada para leitura (derivada de eventos).
- **Adapter**: "borda" que conversa com o mundo (HTTP, CLI, Discord, FS, GitHub).
- **Contract**: especificação pública (OpenAPI/schemas) consumida por outros.

---

## Terminologia {#terminologia}

Esta seção esclarece distinções importantes entre conceitos arquiteturais e pacotes físicos.

### Core Package vs Core Layer

- **Core Package**: refere-se ao diretório `src/skybridge`, que contém o núcleo técnico da aplicação (engine, registry, adapters e integrações RPC).
- **Core Layer**: refere-se à camada de domínio definida na ADR002, responsável por regras de negócio puras e entidades independentes de infraestrutura.

> Esta distinção reduz ambiguidade entre conceito arquitetural e pacote físico sem invalidar ADR002 nem ADR003.

---

## Arquiteturas e Padrões Adotados

### A) Macro (sistema)
- **Monólito Modular** no core: contexts isolados, comunicação por eventos ou application services.
- **Plugins opcionais** para integrações e packs (catálogo/market no futuro).

### B) Domínio (DDD)
- DDD apenas onde há regras e invariantes:
  - `fileops`: políticas de acesso, allowlist, operações seguras, auditoria.
  - `tasks`: entidades (Task/Note/Group/List), promoções, histórico e estados.
- Proibido “DDD decorativo” em integrações simples.

### C) Aplicação (CQRS)
- Superfície externa baseada em **Commands/Queries**:
  - rotas de comando: `/cmd/<nome>`
  - rotas de query: `/qry/<nome>`
- Handlers vivem em `application/` do contexto correspondente.
- Contrato versionado em `openapi/`.

> **Nota:** ADR010 e ADR014 evoluíram o transporte para Sky-RPC com rotas `/ticket` e `/envelope`. O padrão CQRS (command/query) permanece na semântica, mas o envelope HTTP mudou.

### D) Event Sourcing (onde vale)
- Aplicar inicialmente em `tasks` para:
  - auditabilidade,
  - reconstrução de estado,
  - trilha de governança.
- `fileops` pode emitir eventos sem ser event-sourced (event-driven sem ES total).

### E) Clean/Hexagonal (uso seletivo)
- Preferencial em plugins e integrações:
  - `ports` (interfaces inbound/outbound) quando houver múltiplos adapters.
- Não obrigatório em todo lugar; usar quando reduzir acoplamento.

---

## Configuração Centralizada (profiles + context files)

### Fontes de configuração
- `config/base.*` (defaults globais versionados)
- `config/<profile>.*` (overrides por ambiente: dev/test/prod)
- `config/contexts/<context>.*` (config específica por BC: fileops/tasks/support)
- `.env` (apenas dev local; não versionado)
- **Env vars do sistema** (sempre vencem)

### Precedence (quem vence)
1) Env vars do sistema
2) `.env` (quando habilitado)
3) `config/<profile>`
4) `config/contexts/<context>`
5) `config/base`
6) defaults do código (último fallback)

### Perfis
- `dev`: logging verboso, defaults locais, permissões mais relaxadas
- `test`: paths temporários, stores isolados
- `prod`: segurança rígida, secrets apenas por env vars

---

## Observabilidade e Segurança (padrão mínimo)
- **Correlation ID** em comandos/queries/logs.
- Logs estruturados com nível por profile.
- Segurança por default:
  - allowlist de root no FileOps
  - secret scanning antes de versionar/entregar
  - audit log para ações sensíveis (write/delete/commit/publish)

---

## Regras de Dependência (Microkernel)

### Apps e Contexts
- `apps/*` são thin: chamam `application` e nunca `infrastructure` direto.
- `contexts/*` não importam outros contexts.
- `shared/*` não contém regra de negócio.

### Plugins e Microkernel
1. **Plugins dependem apenas do Kernel**, e **nunca diretamente do domínio**.
   - A comunicação com a Core Layer (domínio) deve ocorrer **exclusivamente através de ports aprovados**.
   - Exemplo válido: `plugin → kernel.port.fileops → domain.fileops.service`
   - Exemplo inválido: `plugin → domain.fileops.service`

2. **Kernel depende do Domínio (Core Layer)**, não o contrário.
   - O kernel orquestra, inicializa e publica interfaces (ports).

3. **Domínio (Core Layer)** permanece isolado.
   - Nenhum módulo fora do kernel pode importar diretamente código de domínio.

4. **Core não depende de plugins**.
   - Plugins são opcionais e removíveis; o core deve funcionar sem eles.

> Essa regra reforça o padrão Microkernel: o Kernel é o único ponto de acoplamento controlado entre extensões e o domínio.

---

## Consequências

### Positivas
- Vocabulário único reduz ambiguidade e retrabalho.
- Arquiteturas aplicadas onde trazem valor, evitando overengineering.
- Preparação real para plugins/market sem inflar o core.
- Configuração previsível para evolução (local → self-host → SaaS).

### Negativas / Trade-offs
- Exige disciplina (principalmente nas fronteiras de context e shared).
- CQRS aumenta quantidade de “handlers” (mitigar com templates e naming forte).
- ES pode parecer pesado se aplicado fora do lugar (por isso restrito a `tasks`).

---

## SPECs derivadas (quando necessário)
- SPEC000 — Envelope CQRS (payload, erros, correlation)
- SPEC001 — Config (formatos, merge, env naming)
- SPEC002 — Event Store (formato, projeções, snapshots)
- SPEC003 — Plugin Manifest + Permissões (futuro)

---
> "Termos fixos viram velocidade; termos soltos viram ruído." – made by Sky ✨
