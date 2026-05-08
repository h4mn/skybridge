## Context

O Glitchtip é um error tracker open-source (compatível com Sentry SDK) rodando localmente via Docker. Atualmente está em `B:/_repositorios/glitchtip-self-hosted/` — pasta sem git, sem versionamento. O MCP client (`glitchtip_mcp_client.py`) faz bridge stdio↔HTTP/SSE para o server rodando em `localhost:8000`.

O pipeline de transcrição YouTube (change `1-youtube-pipeline`) precisa do Glitchtip para monitoramento de exceções. Sem ele integrado ao projeto, cada máquina que for rodar precisa configurar manualmente.

### Estado atual
- MCP client: arquivo solto, sem auto-start Docker
- Docker: compose.yml com `glitchtip/glitchtip:6` + `postgres:18`
- `.mcp.json`: aponta para caminho absoluto externo

## Goals / Non-Goals

**Goals:**
- Versionar infra + código de observabilidade dentro da skybridge
- Auto-start Docker quando MCP client inicializa e server não está disponível
- Logging centralizado com FileHandler rotativo para uso independente do Glitchtip
- Separação clara: código Python em `src/core/`, infra Docker em `runtime/`

**Non-Goals:**
- Não criar SDK próprio para Glitchtip — usar o MCP client existente como bridge
- Não modificar o container Glitchtip — usar imagem oficial sem customização
- Não implementar health checks além da verificação de conectividade na inicialização
- Não gerenciar múltiplos ambientes Glitchtip (dev/staging/prod) — apenas local

## Decisions

### 1. Estrutura de diretórios: `src/core/` vs `runtime/`

```
src/core/observability/              ← código Python
├── __init__.py
├── glitchtip_client.py              ← MCP client com auto-start
├── logging_config.py                ← config de logging centralizado
└── docs/

runtime/observability/               ← infra Docker
├── compose.yml
├── .env.example
└── README.md
```

**Racional:** Seguir padrão hexagonal — código (bounded context) separado de infra (deploy). O `runtime/` já é usado para outros serviços Docker na skybridge.

**Alternativa considerada:** Tudo em `src/core/observability/` com subpasta `docker/`. Rejeitada porque mistura responsabilidades.

### 2. Auto-start: subprocess vs docker SDK

Usar `subprocess.run(["docker", "compose", "up", "-d"])` no diretório `runtime/observability/`.

**Racional:** Simples, sem dependência adicional (`docker` Python package). O Docker CLI já precisa estar instalado para usar o Glitchtip de qualquer forma.

**Alternativa considerada:** `docker` Python SDK. Rejeitada por adicionar dependência pesada para funcionalidade simples (1 comando).

### 3. Verificação de disponibilidade: HTTP GET poll

Após `docker compose up -d`, fazer polling em `localhost:8000` com `httpx.get(timeout=2)` a cada 2s, máximo 30s.

**Racional:** O Glitchtip demora ~10-15s para inicializar. Polling HTTP é mais confiável que verificar estado do container.

### 4. Logging: módulo independente

`logging_config.py` fornece `get_logger(name)` que retorna logger com FileHandler rotativo (`logs/observability.log`, 5MB, 3 backups). Disponível mesmo sem Glitchtip.

**Racional:** O plano YouTube exige logging em arquivo independente do Glitchtip. O Glitchtip é camada adicional, não dependência.

## Risks / Trade-offs

- **[Docker não instalado]** → Auto-start falha silenciosamente, client loga warning e continua sem Glitchtip. Logging em arquivo continua funcionando.
- **[Timeout de inicialização]** → Se Glitchtip demorar >30s (máquina lenta), client continua sem conexão. Próxima execução do MCP tenta novamente.
- **[Porta 8000 em uso]** → Docker compose falha. Client loga erro claro com instrução de resolver conflito.
- **[Dados do PostgreSQL]** → Volume Docker `pg-data` persiste entre reinicializações. Se usuário limpar volumes, perde histórico. Documentar no README.

## Migration Plan

1. Copiar `glitchtip_mcp_client.py` → `src/core/observability/glitchtip_client.py`
2. Copiar `compose.yml` → `runtime/observability/compose.yml`
3. Adicionar auto-start ao client
4. Criar `logging_config.py`
5. Atualizar `.mcp.json` com novo caminho
6. Commit na skybridge
7. Pasta externa `glitchtip-self-hosted/` pode ser removida após validação

**Rollback:** Reverter `.mcp.json` para caminho antigo. Pasta externa mantida até validação completa.

## Open Questions

- Deixar porta e URL configuráveis via `.env` ou hardcode `localhost:8000`?
  → **Decisão:** via ENV com default `localhost:8000` (já é o padrão do client atual)

> "Infra que versiona junto com o código." – made by Sky 🏗️
