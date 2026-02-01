---
status: aceito
data: 2025-12-23
---

# ADR002 — Estrutura do Repositório Skybridge (Monólito Modular + Microkernel + DDD)

## Status

Aceito

## Contexto

Após o discovery (ADR000) e o mapeamento de capacidades, ficou claro que a Skybridge deve evoluir como um **monólito modular**, com **Bounded Contexts bem definidos** e governança explícita, mas com **um microkernel real** para sustentar extensibilidade (plugins) sem acoplamento estrutural.

O objetivo é maximizar clareza, reduzir entropia e permitir evolução futura (plugins/market) **sem antecipar complexidade** nem “vazar” regras do domínio para interfaces, infra ou plugins.

A Skybridge terá:

* poucos domínios centrais (FileOps e Tasks),
* múltiplas interfaces (API/CLI/REPL/Web),
* documentação governada,
* e extensões opcionais desacopladas com contrato estável (Kernel).

## Decisão

Adotar uma arquitetura **Monólito Modular orientada a DDD** com separação explícita de camadas internas:

* **Kernel**: microkernel/SDK estável (contratos, envelope, registry, compatibilidade de plugins).
* **Core**: domínio e casos de uso (DDD por Bounded Context).
* **Platform**: host/runtime (bootstrap, DI, observabilidade, plugin host, policies).
* **Infra**: implementações concretas (IO, integrações, persistência).

Regras centrais:

* `src/skybridge/` representa o **core executável do produto** (kernel + core + platform + infra).
* Apps são **thin adapters** e não carregam regra de negócio.
* Plugins dependem **somente** de contratos do Kernel (e, quando permitido, de ports do Core), nunca de detalhes internos de contexts.
* Documentação e governança vivem exclusivamente em `docs/`.

### Estrutura canônica do repositório

```text
skybridge/
├─ apps/                               # Interfaces (thin)
│  ├─ api/
│  ├─ cli/
│  ├─ repl/
│  └─ web/
│
├─ src/skybridge/                      # Pacote principal (core executável)
│  ├─ kernel/                          # Microkernel (SDK estável p/ apps+plugins)
│  │  ├─ contracts/                    # Result, Errors, IDs, envelopes base
│  │  ├─ envelope/                     # validação/serialização
│  │  ├─ registry/                     # registry + discovery de handlers
│  │  ├─ plugin_api/                   # protocolo de plugin + capabilities
│  │  └─ versioning/                   # compat policy (kernel_api v1/v2…)
│  │
│  ├─ core/                            # DDD (domínio + casos de uso)
│  │  ├─ contexts/                     # Bounded Contexts
│  │  │  ├─ fileops/
│  │  │  │  ├─ domain/
│  │  │  │  ├─ application/
│  │  │  │  ├─ ports/                  # interfaces (repos, gateways, clocks…)
│  │  │  │  ├─ adapters/               # anti-corruption/mapeadores (thin)
│  │  │  │  └─ README.md
│  │  │  └─ tasks/
│  │  │     ├─ domain/
│  │  │     ├─ application/
│  │  │     ├─ ports/
│  │  │     ├─ adapters/
│  │  │     └─ README.md
│  │  └─ shared/                       # mínimo (sem “dono”), se necessário
│  │     └─ README.md
│  │
│  ├─ platform/                        # Host/runtime do produto
│  │  ├─ bootstrap/                    # composição do app (wire-up)
│  │  ├─ config/
│  │  ├─ di/
│  │  ├─ observability/
│  │  ├─ plugin_host/                  # loader + lifecycle + policies
│  │  ├─ security/                     # policies runtime (allow/deny, rate-limit)
│  │  └─ delivery/                     # empacotamento/release/runtime concerns
│  │
│  └─ infra/                           # Implementações concretas (IO)
│     ├─ contexts/                     # implementações dos ports por BC
│     │  ├─ fileops/
│     │  └─ tasks/
│     ├─ persistence/                  # db/eventstore/filesystem
│     └─ integrations/                 # discord/gmail/github/ngrok/etc
│
├─ plugins/                            # Extensões opcionais (market-ready)
│  ├─ README.md
│  └─ <plugin_name>/
│     ├─ manifest.(json|toml|yaml)
│     └─ src/<plugin_name>/
│        ├─ domain/
│        ├─ application/
│        ├─ adapters/
│        └─ infra/
│
├─ openapi/                            # Contratos externos versionados
│  └─ v1/
│     └─ skybridge.yaml
│
├─ docs/                               # Governança e conhecimento
│  ├─ core/
│  ├─ adr/
│  ├─ prd/
│  ├─ spec/
│  ├─ playbook/
│  ├─ tasks/
│  └─ README.md
│
└─ .agents/                            # Workspace livre do agente (scratchpad)
```

### READMEs obrigatórios (contrato de clareza)

`src/skybridge/kernel/README.md`

* O que é o Kernel (contrato estável)
* Envelope/handlers/capabilities
* Política de compatibilidade e versionamento do kernel_api

`src/skybridge/core/contexts/<bc>/README.md`

* Linguagem e limites do contexto (o que é / o que não é)
* Entidades e invariantes
* Eventos emitidos/consumidos
* Dependências permitidas (ports/adapters)

`src/skybridge/platform/README.md`

* Responsável pelo runtime (bootstrap, DI, observabilidade, plugin host)
* Proibido conter regras de negócio de BC

`src/skybridge/infra/README.md`

* Implementações concretas dos ports
* Contratos que implementa e como testar (contract tests)

`plugins/README.md`

* Plugins são opcionais
* Nunca dependem de outros plugins
* Dependem do Kernel (e, quando aplicável, ports do Core)
* Proibido importar `core/contexts/*/domain` diretamente

`docs/README.md`

* Índice canônico
* “Skybridge em 10 linhas”
* Links para ADRs, PRDs, SPECs e Playbooks

### Opções consideradas

1. Estrutura flat por tipo (rápida, gera entropia)
2. Multi-repo (mais limpo, maior custo de coordenação)
3. Monólito modular com DDD, sem microkernel explícito (plugins acoplam no core)
4. Monólito modular com DDD + Kernel/Platform explícitos (**escolhida**)

### Consequências

#### Positivas

* Fronteiras mais claras (Kernel/Platform/Core/Infra)
* Plugins com contrato estável e compatibilidade versionável
* Apps múltiplos sem duplicar runtime/observabilidade/DI
* DDD aplicado onde faz sentido (FileOps, Tasks) com ports explícitos

#### Negativas / Trade-offs

* Mais estrutura inicial (pastas/READMEs)
* Exige disciplina de imports (governança/linters)
* Infra “pesada” precisa ser conscientemente empurrada para `infra/` (não para dentro do domínio)

### Regras complementares

* Apps são thin e **não** implementam regras de negócio
* `core/domain` **não** importa `platform` nem `infra`
* Contexts não se importam entre si (comunicação via eventos ou application services/ports)
* Plugins não importam `core/contexts/*/domain` (somente Kernel + ports permitidos)
* `.agents/` é scratchpad; “código-produto” deve migrar para o lugar correto via governança (ADR/PRD/SPEC)

### Próximos passos

* Criar a árvore acima no repositório
* Criar os READMEs mínimos por pasta
* Definir política de compatibilidade do `kernel_api` (v1)
* Adicionar guardrails (lint/checks de import) para manter fronteiras

---

> "Fronteira explícita hoje é liberdade de refatorar amanhã." – made by Sky ✨
