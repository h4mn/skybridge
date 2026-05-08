# glitchtip-client Specification

## Purpose
TBD - created by archiving change internalizar-glitchtip. Update Purpose after archive.
## Requirements
### Requirement: MCP client com bridge stdio para HTTP/SSE
O sistema SHALL fornecer um client MCP que conecta ao Glitchtip via HTTP/SSE e expõe via stdio para integração com Claude Code.

#### Scenario: Conexão bem-sucedida ao server existente
- **WHEN** o client inicializa E o Glitchtip está rodando em `localhost:8000`
- **THEN** o client envia `initialize` via HTTP/SSE E recebe resposta com `serverInfo` E entra no loop stdio

#### Scenario: Server indisponível sem Docker
- **WHEN** o client inicializa E o Glitchtip NÃO está rodando E `docker` não está disponível no PATH
- **THEN** o client loga warning "Docker not available, Glitchtip auto-start skipped" E entra no loop stdio (conexão falhará se server nunca subir)

### Requirement: Auto-start Docker quando server indisponível
O sistema SHALL iniciar automaticamente o Docker Compose do Glitchtip quando o server não responde em `localhost:8000`.

#### Scenario: Auto-start com sucesso
- **WHEN** o client inicializa E `localhost:8000` não responde E `docker compose up -d` executa com sucesso em `runtime/observability/`
- **THEN** o client aguarda até o server responder (polling a cada 2s, timeout 30s) E conecta normalmente

#### Scenario: Timeout durante inicialização
- **WHEN** o client executa `docker compose up -d` E o server NÃO responde dentro de 30s
- **THEN** o client loga warning "Glitchtip startup timeout" E continua com conexão pendente

#### Scenario: Docker Compose falha
- **WHEN** `docker compose up -d` retorna código de saída não-zero (ex: porta em uso)
- **THEN** o client loga erro com stderr do comando E continua sem Glitchtip

### Requirement: Bridge stdio bidirecional
O sistema SHALL ler mensagens JSON do stdin, encaminhar ao Glitchtip via HTTP/SSE, e escrever respostas no stdout.

#### Scenario: Mensagem JSON válida
- **WHEN** o client recebe linha JSON válida no stdin
- **THEN** envia como POST para `/mcp` E escreve resposta JSON no stdout

#### Scenario: Resposta SSE
- **WHEN** o Glitchtip responde com `Content-Type: text/event-stream`
- **THEN** o client extrai JSON do campo `data:` da primeira linha SSE E retorna como JSON

#### Scenario: Erro no server
- **WHEN** o Glitchtip retorna erro HTTP (5xx)
- **THEN** o client retorna resposta de erro JSON-RPC com código `-32603` no stdout

### Requirement: Configuração via variáveis de ambiente
O sistema SHALL aceitar configuração via ENV: `GLITCHTIP_MCP_URL` (default `http://localhost:8000/mcp`), `GLITCHTIP_API_TOKEN`, `GLITCHTIP_COMPOSE_DIR` (default `runtime/observability/`).

#### Scenario: Defaults sem ENV
- **WHEN** nenhuma variável ENV é definida
- **THEN** o client usa `localhost:8000/mcp` como URL E não envia token E busca compose em `runtime/observability/`

#### Scenario: Token via argumento CLI
- **WHEN** `GLITCHTIP_API_TOKEN` não está definida E um argumento é passado via CLI
- **THEN** o client usa o argumento como token de autenticação

