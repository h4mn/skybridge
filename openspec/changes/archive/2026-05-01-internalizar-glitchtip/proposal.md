## Why

O Glitchtip (error tracking + performance monitoring) está em `B:/_repositorios/glitchtip-self-hosted/` como pasta solta sem versionamento. O MCP client que conecta ao Glitchtip via HTTP/SSE é necessário para o pipeline de transcrição YouTube (item 1.2 do plano), mas não está integrado ao projeto. Além disso, o MCP não inicia o Docker automaticamente, exigindo intervenção manual. Migrar para dentro da skybridge com separação código/infra resolve versionamento, facilita deploy e habilita auto-start.

## What Changes

- **Mover MCP client** de pasta externa para `src/core/observability/glitchtip_client.py`
- **Mover compose.yml** para `runtime/observability/compose.yml`
- **Adicionar auto-start Docker** no client: verifica `localhost:8000`, se não responde executa `docker compose up -d`, aguarda disponibilidade (timeout 30s)
- **Adicionar logging_config.py** com configuração centralizada de logging (rotação, formato estruturado)
- **Atualizar `.mcp.json`** com novo caminho do client
- **Criar `.env.example`** em `runtime/observability/` com variáveis necessárias

## Capabilities

### New Capabilities
- `glitchtip-client`: Cliente MCP para Glitchtip com auto-start Docker e bridge stdio↔HTTP/SSE
- `logging-config`: Configuração centralizada de logging com FileHandler rotativo e formato estruturado

### Modified Capabilities
<!-- Nenhuma spec existente é modificada -->

## Impact

- **Código novo**: `src/core/observability/` (bounded context)
- **Infra Docker**: `runtime/observability/` (compose.yml + .env)
- **Configuração**: `.mcp.json` atualizado com novo path do client
- **Dependências**: `httpx` já está nos requirements; `docker compose` precisa estar disponível no PATH
- **Dependentes**: Pipeline YouTube (change `1-youtube-pipeline`) depende desta change para monitoramento de exceções

> "Observabilidade que nasce com o projeto, não depois." – made by Sky 🔭
