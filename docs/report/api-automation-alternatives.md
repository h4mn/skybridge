# API Automation Alternatives — Beyond GPT Custom

**Contexto:** Skybridge API (FastAPI) atualmente utiliza GPT Custom como principal forma de automação. Este relatório explora alternativas automatizadas para interação com APIs, comparando casos de uso e anti-padrones.

---

## 1. MCP (Model Context Protocol)

### O que é
Protocolo padronizado para expor tools/resources a LLMs via stdio, SSE ou HTTP.

### ✅ Onde aplicar

| Cenário | Justificativa |
|---------|---------------|
| **Claude Desktop integrado** | Integração nativa como tool, sem camadas extras |
| **Multi-modelo** | Claude, ChatGPT e outros usam mesmo protocolo |
| **Descoberta dinâmica** | Endpoints mudam frequentemente? Auto-descoberta via tools/resources |

### ❌ Onde NÃO aplicar

| Cenário | Motivo |
|---------|--------|
| Scripts simples (bash/curl) | MCP é overkill |
| CI/CD headless | Ambientes sem suporte MCP |
| Performance crítica | Overhead de stdio/json pode ser demais |

### Implementação sugerida para Skybridge
```python
# plugins/skybridge-mcp/src/server.py
from mcp.server import Server
from skybridge.core.shared.queries.health import HealthQuery

app = Server("skybridge-mcp")

@app.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="health://status",
            name="Health Status",
            description="Current health status of Skybridge"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "health://status":
        result = HealthQuery.execute()
        return json.dumps(result.value)
```

---

## 2. CLI (Typer/Click)

### O que é
Interface de linha de comando com autocompletção e documentação embutida.

### ✅ Onde aplicar

| Cenário | Justificativa |
|---------|---------------|
| **Developer workflows** | `sb ticket create`, `sb envelope send` |
| **Scripting integrado** | Pipes, loops bash, automações shell |
| **Users técnicos** | Times de dev, SREs, Ops |

### ❌ Onde NÃO aplicar

| Cenário | Motivo |
|---------|--------|
| Users não-técnicos (PMs, designers) | Não usam terminal |
| Interfaces complexas com state pesado | UI web é melhor |
| Batch massivo | Python direto é mais eficiente |

### Implementação sugerida para Skybridge
```python
# apps/cli/main.py (extensão)
import typer

app = typer.Typer()

@app.command()
def ticket(operation: str, payload: str = None):
    """Operations on tickets (create/read/list)"""
    # Mapeia para Sky-RPC /ticket/*

@app.command()
def envelope(action: str, target: str):
    """Envelope operations (send/verify/status)"""
    # Mapeia para Sky-RPC /envelope/*
```

---

## 3. OpenAPI Client Generation

### O que é
Gerar clientes type-safe a partir do spec OpenAPI/Sky-RPC.

### ✅ Onde aplicar

| Cenário | Justificativa |
|---------|---------------|
| **Frontend TypeScript** | React/Vue/Svelte com client type-safe |
| **SDKs públicos** | Expor API para devs externos |
| **Multi-languages** | Gerar clients em TS, Python, Go, etc. |

### ❌ Onde NÃO aplicar

| Cenário | Motivo |
|---------|--------|
| Uso interno único | curl/requests suficiente |
| API muto rápida | Clients gerados ficam obsoletos |
| 2-3 endpoints simples | Cliente gerado é código demais |

### Implementação sugerida para Skybridge
```bash
# Gerar cliente TypeScript
openapi-generator-cli generate \
  -i openapi/v1/skybridge.yaml \
  -g typescript-axios \
  -o ./clients/ts

# Gerar cliente Python
openapi-generator-cli generate \
  -i openapi/v1/skybridge.yaml \
  -g python \
  -o ./clients/py
```

---

## 4. Postman/Newman Collections

### O que é
Collections JSON para testes, documentação e automação de API.

### ✅ Onde aplicar

| Cenário | Justificativa |
|---------|---------------|
| **Testes automatizados** | CI/CD pipelines para validar endpoints |
| **Documentação viva** | Equipe visualiza requests |
| **Onboarding** | Novos devs entendem API via UI |

### ❌ Onde NÃO aplicar

| Cenário | Motivo |
|---------|--------|
| Produção runtime | Postman é dev/test, não produção |
| Workflows condicionais complexos | Código real é melhor |
| Headless environments | Servidores sem GUI |

### Implementação sugerida para Skybridge
```json
{
  "info": { "name": "Skybridge Collection" },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/qry/health"
      }
    },
    {
      "name": "Create Ticket",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/ticket",
        "body": {
          "mode": "raw",
          "raw": "{\"operation\": \"file.read\", \"payload\": {...}}"
        }
      }
    }
  ]
}
```

---

## 5. Webhooks + Event Driven

### O que é
Disparar eventos HTTP para endpoints externos quando ações ocorrem.

### ✅ Onde aplicar

| Cenário | Justificativa |
|---------|---------------|
| **Integrações externas** | Discord, Slack, Trello notificados |
| **Async workflows** | Snapshot pronto → próxima etapa |
| **Multi-sistema** | Skybridge dispara, outros ouvem |

### ❌ Onde NÃO aplicar

| Cenário | Motivo |
|---------|--------|
| Request/response síncrono | Cliente precisa resposta imediata |
| Redes fechadas (firewall) | Webhooks bloqueados |
| Simple operations | Criar webhook pra GET /health é overkill |

### Implementação sugerida para Skybridge
```python
# src/skybridge/core/shared/webhooks.py
from httpx import AsyncClient

async def trigger_webhook(event: str, payload: dict):
    """Trigger configured webhook for event"""
    webhooks = load_webhooks_for_event(event)

    async with AsyncClient() as client:
        for webhook in webhooks:
            await client.post(
                webhook.url,
                json={
                    "event": event,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": payload
                },
                headers={"Authorization": f"Bearer {webhook.token}"}
            )
```

---

## Tabela Comparativa

| Alternativa | Melhor para | Evitar se | Esforço inicial | Manutenção |
|-------------|-------------|-----------|-----------------|------------|
| **MCP** | Claude Desktop + multi-modelo | Scripts simples, CI puro | Médio | Baixa |
| **CLI** | Dev workflows, scripting | Users não-técnicos | Baixo (já existe base) | Média |
| **OpenAPI Gen** | Frontend type-safe, SDKs | API interno só seu | Baixo (já tem spec) | Baixa |
| **Postman** | Testes, docs, onboarding | Produção runtime | Baixo | Média |
| **Webhooks** | Integrações externas, async | Síncrono simples | Médio | Média |

---

## Recomendação Prioritária para Skybridge

### Fase 1 (Imediato)
- **Expansão CLI**: Já existe `apps/cli/main.py` — adicionar comandos Sky-RPC
- **OpenAPI Hybrid**: Já tem spec — gerar cliente TS para frontend futuro

### Fase 2 (Curto prazo)
- **MCP Server**: Integração Claude Desktop → tools nativas
- **Postman Collections**: Testes automatizados + onboarding

### Fase 3 (Médio prazo)
- **Webhooks**: Quando integrações externas (Discord/Trello) forem prioritárias

---

## Notas de Arquitetura

### Princípio: Core Pequeno, Canais Plugáveis
```
┌─────────────────────────────────────────────────┐
│            Canais de Acesso                     │
│  ┌─────┐ ┌─────┐ ┌────────┐ ┌──────┐ ┌─────┐  │
│  │ CLI │ │ MCP │ │ OpenAPI │ │Postman│ │Webhook│ │
│  └──┬──┘ └──┬──┘ └───┬────┘ └──┬───┘ └──┬──┘  │
├─────┼──────┼────────┼─────────┼────────┼──────┤
│     │      │        │         │        │      │
│     └──────┴────────┴─────────┴────────┴──────┤
│            Sky-RPC (Contrato Canônico)          │
│  ┌────────┐ ┌─────────┐ ┌──────────────────┐  │
│  │/ticket │ │/envelope│ │/qry/* (queries) │  │
│  └────────┘ └─────────┘ └──────────────────┘  │
├─────────────────────────────────────────────────┤
│            Core (FileOps, Tasks)                │
└─────────────────────────────────────────────────┘
```

### Padrão: RPC-first, Auto-descoberta
- Sky-RPC define contrato canônico
- Cada canal expõe RPC de forma nativa
- OpenAPI/Spec gera clientes automaticamente

---

## Referências

- MCP Specification: https://modelcontextprotocol.io/
- OpenAPI Generator: https://openapi-generator.tech/
- Newman (Postman CLI): https://learning.postman.com/docs/running-collections/using-newman-cli/command-line-integration-with-newman/

---

> "Ferramenta certa, trabalho leve. Automação liberta mente criativa." – made by Sky 🛠️
