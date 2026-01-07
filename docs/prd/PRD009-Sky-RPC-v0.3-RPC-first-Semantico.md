---
status: proposta
data: 2025-12-28
relacionado:
  - PRD008-Sky-RPC-v0.2-envelope-estruturado.md
  - SPEC004-Sky-RPC-v0.3.md
  - ADR014-evoluir-sky-rpc.md
---

# PRD009 — Sky-RPC v0.3 (RPC-first Semântico)

## 1) Problema

A v0.2 do Sky-RPC introduziu o envelope estruturado, mas:
- Não possui introspecção de runtime (descoberta dinâmica de handlers)
- Não há mecanismo de reload dinâmico do registry
- Documentação estática (`/openapi`) pode ficar desalinhada do código
- Clients precisam conhecer métodos antecipadamente (hardcoded)
- Não há distinção clara entre contrato estático (design-time) e dinâmico (runtime)

## 2) Objetivo

Evoluir Sky-RPC para v0.3 com arquitetura **RPC-first semântica**:
- **Contrato dinâmico:** `GET /discover` expõe handlers realmente carregados no runtime
- **Reload dinâmico:** `POST /discover/reload` permite recarregar registry sem restart
- **Sincronização:** Garante alinhamento entre código, documentação e runtime
- **Envelope v0.3:** Novos campos opcionais `scope` e `options` para reduzir sobrecarga de `payload`
- **Payload opcional:** Operações simples podem não requerer payload adicional

## 3) Escopo

### Inclui

- Novo endpoint `GET /discover` com schema `SkyRpcDiscovery`
- Novo endpoint `POST /discover/reload` para reload do registry
- Campo opcional `scope` no envelope (ex: `tenant:sky`)
- Campo opcional `options` no envelope (objeto de opções específicas)
- Campo `payload` torna-se **opcional** (era obrigatório em v0.2)
- Metadados de handler: `method`, `kind`, `module`, `input_schema`, `output_schema`, `description`
- Controle de acesso em `/discover` (não público)
- Atualização de CLI `sb` para suportar introspecção
- Documentação de compatibilidade v0.2 → v0.3

### Não inclui

- Mudança na lógica de tickets (mantido de v0.2)
- Alteração de autenticação/autorização existente
- Mudança no formato de resposta (`EnvelopeResponse`)
- Substituição do `/openapi` estático (complementar)

## 4) Requisitos Funcionais

### Introspecção

| ID | Descrição |
|----|-----------|
| **RF1** | `GET /discover` retorna catálogo de handlers ativos no runtime |
| **RF2** | Resposta inclui: `method`, `kind`, `module`, `input_schema`, `output_schema`, `description` |
| **RF3** | `kind` indica tipo de operação: `query` ou `command` |
| **RF4** | `module` indica caminho do código que implementa o handler |
| **RF5** | `input_schema` e `output_schema` são JSON Schemas válidos |
| **RF6** | `/discover` requer autenticação (não é público) |
| **RF7** | `GET /openapi` continua disponível (contrato estático) |

### Reload Dinâmico

| ID | Descrição |
|----|-----------|
| **RF8** | `POST /discover/reload` força recarga do registry a partir do código atual |
| **RF9** | Reload é idempotente (múltiplas chamadas não causam duplicação) |
| **RF10** | Reload retorna lista de handlers adicionados/removidos |
| **RF11** | Reload requer autenticação e privilégios elevados |
| **RF12** | Em caso de erro no reload, registry anterior é preservado (rollback) |

### Envelope v0.3

| ID | Descrição |
|----|-----------|
| **RF13** | Campo `scope` é opcional no envelope (ex: `tenant:sky`) |
| **RF14** | Campo `options` é opcional no envelope (objeto de opções) |
| **RF15** | Campo `payload` é **opcional** (era obrigatório em v0.2) |
| **RF16** | Campos obrigatórios permanecem: `ticket_id`, `detail.context`, `detail.action` |
| **RF17** | Clients v0.2 continuam funcionando (backward compatibility) |

## 5) Requisitos Não-Funcionais

### Performance

| ID | Descrição |
|----|-----------|
| **RNF1** | `GET /discover` deve responder em < 100ms |
| **RNF2** | `POST /discover/reload` deve completar em < 2s |
| **RNF3** | Introspecção não deve impactar performance de handlers em execução |

### Segurança

| ID | Descrição |
|----|-----------|
| **RNF4** | `/discover` e `/discover/reload` requerem autenticação |
| **RNF5** | `/discover/reload` requer privilégios de administrador |
| **RNF6** | Metadados de handlers não devem expor informações sensíveis |

### Compatibilidade

| ID | Descrição |
|----|-----------|
| **RNF7** | Clients v0.2 devem funcionar sem modificação |
| **RNF8** | Envelope v0.2 é subset válido de v0.3 |
| **RNF9** | Breaking changes devem ser documentados em CHANGELOG |

## 6) Estrutura de Arquivos

> **Estrutura completa de `docs/spec/` definida em [SPEC006](../spec/SPEC006-Estrutura-de-Specs.md)**

### Novos arquivos

```
specs/
├─ discover/
│  └─ discover-spec.yaml        # Schema de SkyRpcDiscovery
└─ contexts/
   ├─ fileops.yaml              # Schemas específicos de fileops
   ├─ tasks.yaml                # Schemas específicos de tasks
   └─ common.yaml               # Schemas compartilhados (atualizado)
```

### Arquivos modificados

```
specs/openapi/openapi.yaml       # Adicionar rotas /discover e /discover/reload
src/skybridge/kernel/registry/  # Lógica de introspecção e reload
src/skybridge/core/platform/    # Expor endpoints novos
cli/sb/                          # CLI principal com subcomandos
```

## 7) Exemplos de Uso

### Descoberta de handlers

```bash
# Listar todos os handlers ativos
curl -H "Authorization: Bearer $TOKEN" \
  https://api.skybridge.dev/discover

# Resposta
{
  "version": "0.3.0",
  "discovery": {
    "health": {
      "method": "health",
      "kind": "query",
      "module": "skybridge.core.handlers.health",
      "input_schema": { "type": "object" },
      "output_schema": { "$ref": "#/schemas/HealthResponse" },
      "description": "Health check do sistema"
    },
    "fileops.read": {
      "method": "fileops.read",
      "kind": "query",
      "module": "skybridge.core.contexts.fileops.handlers",
      "input_schema": {
        "type": "object",
        "properties": {
          "context": { "type": "string" },
          "action": { "type": "string" },
          "subject": { "type": "string" }
        },
        "required": ["context", "action", "subject"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "content": { "type": "string" },
          "size": { "type": "integer" }
        }
      },
      "description": "Lê conteúdo de um arquivo"
    }
  }
}
```

### Reload dinâmico

```bash
# Via HTTP
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.skybridge.dev/discover/reload

# Via CLI
sb rpc reload

# Resposta (mesmo para ambos)
{
  "ok": true,
  "added": ["fileops.write", "tasks.create"],
  "removed": ["legacy.method"],
  "total": 15
}
```

### Envelope v0.3 (com novos campos)

```json
{
  "ticket_id": "a3f9b1e2",
  "detail": {
    "context": "fileops",
    "action": "read",
    "subject": "docs/adr/ADR005.md",
    "scope": "tenant:sky",
    "options": { "limit": 100 }
  }
}
```

### Envelope v0.3 (payload opcional)

```json
{
  "ticket_id": "b4f2c1e3",
  "detail": {
    "context": "health",
    "action": "check"
  }
}
```

### Exemplos da CLI `sb`

```bash
# Listar todos os handlers ativos
sb rpc list

# Detalhes de um handler específico
sb rpc discover fileops.read

# Chamar uma operação RPC
sb rpc call fileops.read --subject README.md

# Recarregar registry (requer admin)
sb rpc reload --token $ADMIN_TOKEN
```

## 8) Critérios de Aceite

### Core

- [ ] `GET /discover` retorna catálogo de handlers ativos
- [ ] Catálogo inclui todos os metadados especificados
- [ ] `POST /discover/reload` recarrega registry sem restart
- [ ] Reload é idempotente e preserva registry em caso de erro
- [ ] Envelope v0.3 aceita `scope`, `options` e `payload` opcional
- [ ] Clients v0.2 continuam funcionando

### Segurança

- [ ] `/discover` requer autenticação
- [ ] `/discover/reload` requer privilégios de administrador
- [ ] Metadados não expõem informações sensíveis

### CLI

- [ ] `sb rpc list` lista handlers ativos
- [ ] `sb rpc call <method>` invoca operação via RPC
- [ ] `sb rpc discover [method]` mostra metadados de handler específico
- [ ] `sb rpc reload` força recarga do registry (requer credencial admin)

### Documentação

- [ ] SPEC004 atualizada com v0.3
- [ ] OpenAPI inclui rotas `/discover` e `/discover/reload`
- [ ] Guia de migração v0.2 → v0.3 documentado
- [ ] CHANGELOG registra breaking changes (se houver)

## 9) Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Reload causar downtime em produção | Baixa | Alto | Implementar rollback automático; testar exaustivamente em staging |
| `/discover` expor informações sensíveis | Média | Médio | Controle de acesso rigoroso; sanitizar metadados |
| Clients v0.2 quebrarem | Baixa | Alto | Testes de compatibilidade; período de transição |
| Performance degrade com introspecção | Baixa | Médio | Cache de descoberta; lazy loading |

## 10) Cronograma

| Fase | Atividades | Dependências |
|-------|------------|---------------|
| **Fase 1** | Implementar `/discover` | SPEC004 estável |
| **Fase 2** | Implementar `/discover/reload` | Fase 1 completa |
| **Fase 3** | Atualizar envelope v0.3 | Fase 2 completa |
| **Fase 4** | Atualizar CLI `sb` | Fase 3 completa |
| **Fase 5** | Testes e documentação | Fase 4 completa |

## 11) Próximos Passos

1. Criar `specs/discover/discover-spec.yaml`
2. Implementar core de introspecção no registry
3. Adicionar endpoints `/discover` e `/discover/reload`
4. Atualizar schema de envelope para v0.3
5. Implementar reload dinâmico com rollback
6. Atualizar CLI `sb` com subcomandos RPC
7. Escrever testes de compatibilidade v0.2 → v0.3
8. Documentar guia de migração

---

## Referências

- [ADR014 — Evoluir Sky-RPC para arquitetura RPC-first semântica](../adr/ADR014-evoluir-sky-rpc.md)
- [SPEC004 — Sky-RPC v0.3](../spec/SPEC004-Sky-RPC-v0.3.md)
- [SPEC006 — Estrutura de Specs](../spec/SPEC006-Estrutura-de-Specs.md)
- [PRD008 — Sky-RPC v0.2 (Envelope Estruturado)](./PRD008-Sky-RPC-v0.2-envelope-estruturado.md)

---

> "Introspecção é a diferença entre RPC e chute no escuro." – made by Sky 🔍
