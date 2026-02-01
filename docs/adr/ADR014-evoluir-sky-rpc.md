---

status: aceito
data: 2025-12-27
supersedes: ADR010-adotar-sky-rpc
---------------------------------

# ADR014 — Evoluir Sky-RPC para arquitetura RPC-first semântica

## Contexto

A ADR010 introduziu o modelo `ticket + envelope`, rompendo com o JSON-RPC puro.
A SPEC002 consolidou a primeira evolução do Sky-RPC com o **envelope estruturado**,
incluindo `context`, `subject`, `action` e `payload`, mantendo compatibilidade via `oneOf`.

Com a adoção do SPEC002, a plataforma passou a ter um formato mais estável e validável,
porém ainda sem introspecção e reload dinâmico. O próximo passo natural é evoluir
para um modelo **RPC-first semântico**, com documentação e auto-descoberta.

---

## Decisão

**O Sky-RPC torna-se o contrato canônico da plataforma**, agora com:

1. **Contrato estático (`/openapi`)** — Define schemas, métodos e exemplos estáveis por domínio.
2. **Contrato dinâmico (`/discover`)** — Reflete os handlers realmente carregados no runtime, com metadados (`context`, `action`, `kind`, `module`, `input_schema`, `output_schema`).

O envelope definido em v0.2 é mantido, e o formato `detail` estruturado passa a ser
base de todo o fluxo RPC.

---

## Estrutura do Envelope (v0.3.0)

```json
{
  "ticket_id": "uuid",
  "detail": {
    "context": "fileops",
    "action": "read",
    "subject": "docs/adr/ADR005.md",
    "scope": "tenant:sky",
    "options": { "limit": 100 },
    "payload": { "encoding": "utf-8" }
  }
}
```

Campos adicionais como `scope` e `options` são introduzidos para reforçar semântica
entre domínios e reduzir sobrecarga do `payload`. O `payload` agora é **opcional**,
permitindo operações simples sem parâmetros adicionais.

---

## Rotas canônicas

| Método                              | Caminho                                           | Descrição |
| ----------------------------------- | ------------------------------------------------- | --------- |
| `GET /openapi`                      | Retorna contrato estático e schemas versionados   |           |
| `GET /ticket?method=context.action` | Cria ticket temporário para execução              |           |
| `POST /envelope`                    | Executa a operação com envelope semântico         |           |
| `GET /discover`                     | Retorna catálogo dinâmico de handlers ativos      |           |
| `POST /discover/reload`             | Força reload do registry a partir do código atual |           |

---

## Consequências

### Positivas

* Mantém compatibilidade com SPEC002.
* Introduz introspecção e reload dinâmico de handlers.
* Garante sincronização entre código, documentação e runtime.
* Facilita geração de SDKs e tooling (`skyctl rpc list`, `skyctl rpc call`).
* Reforça semântica do envelope sem quebrar clientes v0.2.

### Negativas

* Maior complexidade no core de introspecção.
* Requer atualização de clients para suportar campos opcionais adicionais.
* Necessidade de controle de acesso em `/discover`.

---

## Próximos Passos

1. Implementar `/discover` com schema `SkyRpcDiscovery`.
2. Criar mecanismo de reload dinâmico do registry.
3. Formalizar estrutura `specs/` (ver [SPEC006](../spec/SPEC006-Estrutura-de-Specs.md)).
4. Atualizar CLI `sb rpc` para suportar introspecção.
5. Documentar compatibilidade v0.2 → v0.3.

---

## Emendments (Emendas)

### Emendment 1 (2025-12-28): OpenAPI Híbrido (ADR016)

**Contexto:** A seção "Contrato estático (`/openapi`)" criou ambiguidade sobre o que seria "estático":
- Interpretado inicialmente como **100% estático** (operações + schemas)
- Isso criou gap entre documento YAML e registry runtime

**Decisão:** Conforme **[ADR016](./ADR016-openapi-hibrido-estatico-dinamico.md)**:
- **`/openapi` torna-se HÍBRIDO:**
  - **Operações HTTP:** Estáticas (definidas em YAML)
  - **Schemas:** Dinâmicos (injetados do registry em runtime)
- **`/discover`** continua sendo 100% dinâmico

**Impacto:**
- Schemas sempre sincronizados com o código
- Zero esforço manual para manter documentação atualizada
- Contrato HTTP permanece estável para clientes

**Ver também:**
- [ADR016 — OpenAPI Híbrido](./ADR016-openapi-hibrido-estatico-dinamico.md)
- [PRD010 — OpenAPI Híbrido](../prd/PRD010-OpenAPI-Hibrido.md)
- [PB010 — Redocly CLI para OpenAPI](../playbook/PB010-redocly-cli-openapi.md)

---

> “RPC não é só chamada remota — é linguagem compartilhada.”
> – made by Sky ✨

---
