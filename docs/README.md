# Documentação Skybridge

## Definição

Skybridge é uma **ponte entre intenção humana e execução assistida por IA**.
Automatiza operações (arquivos, tarefas, publicação) com segurança, rastreabilidade
e múltiplas interfaces (API/CLI/REPL/UI). Evolui de ferramenta local → plataforma
pessoal → times → ecossistema → SaaS multi-tenant.

## Índice

### Core — Visão e Arquitetura

- [Visão do Produto](core/vision.md) — evolução embrionária → multi-tenant
- [Glossário Oficial](adr/ADR003-Glossário,%20Arquiteturas%20e%20Padrões%20Oficiais.md) — termos, arquiteturas e padrões

### ADRs — Architecture Decision Records

- [ADR000](adr/ADR000-Descoberta%20via%20Score%20de%20Snapshot.md) — Discovery via Snapshot + Score
- [ADR001](adr/ADR001-Feature-Map-Skybridge.md) — Feature Mapping
- [ADR002](adr/ADR002-Estrutura%20do%20Repositório%20Skybridge.md) — Estrutura do Repositório (Monólito Modular + DDD)
- [ADR003](adr/ADR003-Glossário,%20Arquiteturas%20e%20Padrões%20Oficiais.md) — Glossário, Arquiteturas e Padrões Oficiais
- [ADR004](adr/ADR004-adotar-json-rpc-contrato-canonico.md) — JSON-RPC (substituído pela ADR010)
- [ADR005](adr/ADR005-padronizar-naming-operações-auto-descoberta.md) — Naming de operações + discovery
- [ADR006](adr/ADR006-adotar-politica-id-correlation-idempotencia.md) — ID, correlation e idempotência
- [ADR007](adr/ADR007-adota-baseline-seguranca-llm.md) — Baseline de segurança para LLM
- [ADR008](adr/ADR008-adotar-https-transporte.md) — HTTPS como transporte
- [ADR009](adr/ADR009-cabecalho-utf8-em-python.md) — Cabeçalho UTF-8 em Python
- [ADR010](adr/ADR010-adotar-sky-rpc.md) — Sky-RPC: ticket + envelope
- [ADR011](adr/ADR011-snapshot-diff-estado-atual.md) — Snapshot/diff do estado atual
- [ADR012](adr/ADR012-estrategia-versionamento.md) — Estratégia de versionamento
- [ADR013](adr/ADR013-adotar-yamllint-openapi-validator.md) — Validação de YAML/OpenAPI
- [ADR014](adr/ADR014-evoluir-sky-rpc.md) — Evoluir Sky-RPC
- [ADR015](adr/ADR015-adotar-snapshot-como-serviço-plataforma.md) — Adotar Snapshot como serviço
- [ADR016](adr/ADR016-openapi-hibrido-estatico-dinamico.md) — OpenAPI Híbrido
- [ADR017](adr/ADR017-estrutura-workspace-dados-gerados.md) — Estrutura workspace dados gerados
- [ADR018](adr/ADR018-linguagem-portugues-brasil-codebase.md) — Português Brasileiro no código

### PRDs — Product Requirements

- [PRD000](prd/PRD000-Discovery%20Skybridge%20(Snapshot%20+%20Score).md) — Discovery Skybridge
- [PRD001](prd/PRD001-Feature-Map-Skybridge.md) — Feature Mapping e unificação
- [PRD002](prd/PRD002-PoC-Hello-World-Health-Endpoint.md) — PoC Health
- [PRD003](prd/PRD003-FileOps-Read-Query.md) — FileOps read
- [PRD004](prd/PRD004-PoC-JSON-RPC-ajustes.md) — PoC JSON-RPC (substituído)
- [PRD005](prd/PRD005-baseline-seguranca-llm.md) — Baseline de segurança LLM
- [PRD006](prd/PRD006-rotas-publicas-openrpc-privacy.md) — Rotas públicas (substituído)
- [PRD007](prd/PRD007-Sky-RPC-ticket-envelope.md) — Sky-RPC Ticket + Envelope
- [PRD008](prd/PRD008-Sky-RPC-v0.2-envelope-estruturado.md) — Sky-RPC v0.2 Envelope Estruturado
- [PRD009](prd/PRD009-Sky-RPC-v0.3-RPC-first-Semantico.md) — Sky-RPC v0.3 RPC-first Semântico
- [PRD010](prd/PRD010-OpenAPI-Hibrido.md) — OpenAPI Híbrido
- [PRD011](prd/PRD011-Snapshot-Service.md) — Snapshot Service
- [PRD012](prd/PRD012-Estrategia-Versionamento-Semver-CC.md) — Estratégia de Versionamento Semver CC
- [PRD013](prd/PRD013-webhook-autonomous-agents.md) — Webhook Autonomous Agents
- [PRD014](prd/PRD014-webui-dashboard.md) — WebUI Dashboard

### Specs — Contratos

- [SPEC001](spec/SPEC001-baseline-seguranca-llm.md) — Baseline de segurança LLM
- [SPEC002](spec/SPEC002-Sky-RPC-v0.1.md) — Sky-RPC v0.1
- [SPEC003](spec/SPEC003-Sky-RPC-v0.2.md) — Sky-RPC v0.2
- [SPEC004](spec/SPEC004-Sky-RPC-v0.3.md) — Sky-RPC v0.3
- [SPEC005](spec/SPEC005-documentacao-metadados.md) — Metadados de documentação
- [SPEC006](spec/SPEC006-Estrutura-de-Specs.md) — Estrutura de Specs
- [SPEC007](spec/SPEC007-Snapshot-Service.md) — Snapshot Service
- [SPEC008](spec/SPEC008-AI-Agent-Interface.md) — AI Agent Interface

### Playbooks — Guias Operacionais

- [PB000](playbook/PB000%20-%20Discovery%20da%20Skybridge%20via%20Snapshot%20+%20Scoring.md) — Discovery via Snapshot + Scoring
- [PB001](playbook/PB001-Feature-Mapping-Skybridge.md) — Feature Mapping
- [PB002](playbook/PB002-Ngrok-URL-Fixa.md) — Ngrok URL fixa
- [PB003](playbook/PB003-compatibilidade-breaking-changes.md) — Compatibilidade/breaking changes
- [PB004](playbook/PB004-validacao-postman-jsonrpc.md) — Validação manual (Postman)
- [PB005](playbook/PB005-api-keys-e-tokens-skybridge.md) — API keys e tokens
- [PB006](playbook/PB006-gpt-custom-auth.md) — GPT Custom Auth
- [PB007](playbook/PB007-ajuste-permissoes-skybridge.md) — Ajuste de permissões
- [PB008](playbook/PB008-envelope-estruturado-sky-rpc-v0.2.md) — Envelope estruturado Sky-RPC v0.2
- [PB009](playbook/PB009-Gestao-de-Taxa-de-Substituicao-de-ADRs.md) — Gestão de taxa de substituição de ADRs
- [PB010](playbook/PB010-redocly-cli-openapi.md) — Redocly CLI OpenAPI

### Tasks — Registro de Execução

- [TASK000](task/TASK000-2025-12-22-14-55.md) — Início do Discovery
- [TASK001](task/TASK001-2025-12-22-16-49.md) — Feature Mapping
- [TASK002](task/TASK002-2025-12-24-00-11.md) — Atualização de datas

### Reports — Descobertas e Análises

- [Inspiration Report](report/inspiration-report.md)
- [OpenAPI patternProperties Fix](report/openapi-patternproperties-fix.md) — Bug de 24h+ resolvido
- [Metadata Report](report/metadata-report.md)
- [API Automation Alternatives](report/api-automation-alternatives.md)
- [Bounded Context Analysis Agents](report/bounded-context-analysis-agents.md)
- [Claude Code CLI Infra](report/claude-code-cli-infra.md)
- [Knowledge Layer RAG Research](report/knowledge-layer-rag-research.md)
- [OpenAPI Modular Refs Research](report/openapi-modular-refs-research.md)
- [PR Automation Skill Study](report/pr-automation-skill-study.md)
- [Sky-RPC Evolution Analysis](report/sky-rpc-evolution-analysis.md)
- [SkyRPC Dependency Analysis](report/skyrpc-dependency-analysis.md)
- [SkyRPC Post Mortem Arquivamento](report/skyrpc-post-mortem-arquivamento.md)
- [SkyRPC vs JSONRPC Crossfire](report/skyrpc-vs-jsonrpc-crossfire.md)
- [Versionamento Profissional Padrões Estratégias](report/versionamento-profissional-padroes-estrategias.md)
- [Webhook Autonomous Agents Study](report/webhook-autonomous-agents-study.md)
- [Worktree Validation Example](report/worktree-validation-example.md)

---

## Validação de OpenAPI

**Ferramentas adotadas:** yamllint + openapi-spec-validator

```bash
# Validar YAML
yamllint openapi/v1/skybridge.yaml

# Validar OpenAPI
openapi-spec-validator openapi/v1/skybridge.yaml

# Rodar testes automatizados
python -m pytest tests/test_openapi_schema.py -v
```

Ver [ADR012](adr/ADR012-adotar-yamllint-openapi-validator.md) para detalhes.

## Contrato de API (Sky-RPC)

- Catálogo: `GET /openapi`
- Ticket: `GET /ticket?method=dominio.caso`
- Envelope: `POST /envelope` com parâmetros flat:
  - `detalhe` para argumento único
  - `detalhe_1`, `detalhe_2` para múltiplos argumentos
- Rotas públicas: `GET /privacy`

**Nota:** `method` é o nome da operação Sky-RPC (ex.: `fileops.read`), não o verbo HTTP.

## Baseline de Segurança (LLM)

- ADR: `docs/adr/ADR007-adota-baseline-seguranca-llm.md`
- SPEC: `docs/spec/SPEC001-baseline-seguranca-llm.md`
- PRD: `docs/prd/PRD005-baseline-seguranca-llm.md`

## Arquitetura Resumida

```
src/skybridge/
├── kernel/      # Microkernel (SDK estável)
├── core/        # DDD Bounded Contexts (fileops, tasks)
├── platform/    # Runtime (bootstrap, DI, observabilidade)
└── infra/       # Implementações concretas

apps/            # Thin adapters (api, cli, repl, web)
plugins/         # Extensões opcionais
```

---

> "Documentação é memória institucional." – made by Sky ✨
