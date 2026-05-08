# Observabilidade — Glitchtip Local

Error tracking e performance monitoring via Glitchtip (compatível com Sentry SDK).

## Início rápido

O MCP client inicia o Docker automaticamente. Basta rodar o Claude Code com o MCP configurado.

## Setup manual (se necessário)

```bash
cd runtime/observability/
cp .env.example .env
# Edite o .env com suas configurações
docker compose up -d
```

Acesse `http://localhost:8000` para o dashboard.

## Auto-start

O `glitchtip_client.py` verifica se `localhost:8000` responde ao inicializar. Se não:
1. Executa `docker compose up -d` neste diretório
2. Aguarda o server ficar disponível (timeout 30s)
3. Conecta normalmente

Se Docker não estiver instalado, loga warning e continua sem Glitchtip.

## Variáveis

Ver `.env.example` para todas as variáveis disponíveis.

## Porta

Default: `8000`. Altere via `PORT` no `.env` e `GLITCHTIP_MCP_URL` no `.mcp.json`.
