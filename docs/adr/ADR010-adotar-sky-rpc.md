---
status: abolida
data: 2025-12-26
abolida_por: ADR023
data_abolicao: 2026-01-31
motivo: Sky-RPC foi completamente removido em favor de REST puro com prefixo /api/*
---

# ADR-010 — Adoção do Sky-RPC ⚠️ **ABOLIDA**

> **⚠️ IMPORTANTE:** Esta ADR foi **ABOLIDA** (não apenas obsoleta) pela **[ADR023 — Padrão de Prefixos para Rotas API e Web](ADR023-padrao-prefixos-rotas-api-web.md)** em 2026-01-31.
>
> **Mudança:** Sky-RPC foi **completamente removido** do projeto.
>
> - ❌ `/ticket` — **ABOLIDA**
> - ❌ `/envelope` — **ABOLIDA**
> - ❌ Contrato Sky-RPC — **ABOLIDO**
>
> **Novo padrão:** REST puro com todas as rotas backend usando `/api/*`.
>
> Consulte ADR023 para o padrão atual de rotas.

---

## Contexto

Durante a integração entre GPT Custom Actions e o endpoint público, identificamos
uma limitação estrutural no wrapper local: o schema rígido rejeita campos fora do
modelo esperado. Isso inviabiliza o uso de `params` em JSON-RPC e quebra payloads
maiores (ex.: conteúdo de arquivo).

Além disso, manter JSON-RPC como contrato canônico gera fricção com ambientes
híbridos (LLM + API), onde a prioridade é confiabilidade do payload e validação
estrita do envelope.

---

### Diagrama de Causa (Ishikawa)

```
                            ┌───────────────────────────┐
                            │ Falha ao enviar `params`  │
                            └────────────┬──────────────┘
                                         │
 ┌───────────────────────┬────────────────┼────────────────────┬──────────────────────┐
 │ Ambiente Local        │ Binding Schema │ OpenRPC Mapping     │ API Remota           │
 ├───────────────────────┼────────────────┼────────────────────┼──────────────────────┤
 │ Schema rígido         │ additionalProperties:false    │ Campos não aninhados   │
 │ Validação antecipada  │ Falta de flatten reverso      │ Falta de suporte a meta│
 │ Anti-injection ativa  │ Erro antes do envio           │ Perda de semântica RPC │
 │ Erro no wrapper local │                               │ Rejeição de query      │
 └───────────────────────┴────────────────┴────────────────────┴──────────────────────┘
```

**Síntese:** a falha nasce no cliente, não no servidor. O binding local rejeita
`params` por schema fechado e validação precoce, impedindo a transmissão JSON-RPC válida.

---

## Decisão

**Esta ADR substitui a ADR004 (JSON-RPC como transporte canônico).** O contrato
canônico passa a ser o **Sky-RPC com ticket + envelope**, mantendo a chave
`method` como identificador de operação (influência do JSON-RPC), porém sem o
envelope JSON-RPC.

Rotas canônicas:

1) **GET /openapi** (catálogo de contrato)

2) **GET /ticket?method=dominio.caso**

O cliente solicita um ticket informando o método pretendido. O servidor responde
com um `ticket_id` temporário e metadados de validade.

Exemplo de request:

```
GET /ticket?method=fileops.read
```

Exemplo de resposta:

```json
{
  "ok": true,
  "ticket": {
    "id": "a3f9b1e2",
    "method": "fileops.read",
    "expires_in": 30,
    "accepts": "application/json"
  }
}
```

3) **POST /envelope** (payload real em detalhes flat)

O cliente envia detalhes flat referenciando o `ticket_id`. O servidor executa
o método registrado e retorna `result` ou `error`.

Exemplo de request:

```json
{
  "ticket_id": "a3f9b1e2",
  "detalhe": "README.md"
}
```

Exemplo de resposta:

```json
{
  "ok": true,
  "id": "a3f9b1e2",
  "result": {
    "path": "README.md",
    "content": "...",
    "size": 123
  }
}
```

Esse modelo preserva isolamento e validação (ticket), mas permite payloads
grandes e estruturados em detalhes flat (`detalhe`, `detalhe_1`, `detalhe_2`). A chave `method` continua sendo o identificador canônico de operação.

---

## Consequências

### Positivas

* Simplifica a comunicação entre serviços internos, removendo camadas de schema redundantes.
* Facilita discovery e documentação via `GET /openapi`.
* Cria base sólida para geração de SDKs automatizados.
* Reduz acoplamento com padrões externos (OpenAPI / JSON-RPC puros).

### Negativas / Riscos

* Requer novo parser nos gateways.
* Ferramentas externas não compreenderão o formato sem adaptação.
* Precisamos definir claramente as regras de compatibilidade (v1 do Sky-RPC).

---

## Próximos Passos

1. Verificar compatibilidade com decisões anteriores e aplicar patch se necessário.
2. Definir SPEC para a nova adoção.
3. Publicar `GET /openapi` como catálogo oficial.
4. Definir JSON Schema do Sky-RPC v0.1.
5. Documentar política de versionamento e compatibilidade.

---

> "Simplicidade é o poder de orquestrar complexidade sem ruído." – made by Sky ✨
