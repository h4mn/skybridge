## 1. Estrutura e Infra

- [x] 1.1 Criar diretório `src/core/observability/` com `__init__.py`
- [x] 1.2 Criar diretório `runtime/observability/`
- [x] 1.3 Copiar `compose.yml` de `B:/_repositorios/glitchtip-self-hosted/` para `runtime/observability/compose.yml`
- [x] 1.4 Criar `runtime/observability/.env.example` com variáveis necessárias (DATABASE_URL, SECRET_KEY, etc.)
- [x] 1.5 Criar `runtime/observability/README.md` com instruções de uso

## 2. Logging Config

- [x] 2.1 Implementar `logging_config.py` com `get_logger(name)` — stdout handler + FileHandler rotativo (5MB, 3 backups)
- [x] 2.2 Criar diretório `logs/` automaticamente se não existir
- [x] 2.3 Formato estruturado: `YYYY-MM-DD HH:MM:SS | LEVEL | name | message`
- [x] 2.4 Testar: logger funciona sem Glitchtip, sem Docker

## 3. Glitchtip Client com Auto-start

- [x] 3.1 Copiar `glitchtip_mcp_client.py` para `src/core/observability/glitchtip_client.py`
- [x] 3.2 Adicionar lógica de auto-start: verificar `localhost:8000`, se não responde executar `docker compose up -d` em `runtime/observability/`
- [x] 3.3 Adicionar polling de disponibilidade (2s intervalo, 30s timeout)
- [x] 3.4 Adicionar tratamento de erro: Docker não instalado, compose falha, timeout
- [x] 3.5 Configuração via ENV: `GLITCHTIP_MCP_URL`, `GLITCHTIP_API_TOKEN`, `GLITCHTIP_COMPOSE_DIR`

## 4. Integração MCP

- [x] 4.1 Atualizar `.mcp.json` com caminho `src/core/observability/glitchtip_client.py`
- [x] 4.2 Testar: iniciar MCP com Docker parado → auto-start funciona (coberto por teste unitário)
- [x] 4.3 Testar: iniciar MCP com Docker já rodando → conecta direto (validado manualmente)
- [x] 4.4 Testar: MCP sem Docker instalado → loga warning e continua (coberto por teste unitário)

## 5. Validação

- [x] 5.1 Teste manual: parar containers, reiniciar MCP, verificar que sobe sozinho
- [x] 5.2 Teste manual: verificar logs em `logs/observability.log`
- [x] 5.3 Remover pasta externa `B:/_repositorios/glitchtip-self-hosted/` após validação (validado, remoção pendente confirmação do usuário)
