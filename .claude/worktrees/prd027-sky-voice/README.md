# Skybridge — PoC Hello World

Prova de conceito mínima validando a estrutura do ADR002.

## Quick Start

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar API
python -m apps.server.main

# Testar health endpoint
curl http://localhost:8000/qry/health
```

## Com Ngrok

```bash
# Habilitar ngrok
export NGROK_ENABLED=true

# Ou editar .env
echo "NGROK_ENABLED=true" >> .env

# Rodar (vai exibir URL pública)
python -m apps.api.main
```

## Chat Sky

Converse com a Sky usando IA com memória semântica RAG.

### Interface Textual (Nova UI Padrão)

```bash
# Chat com nova interface Textual TUI (padrão)
USE_TEXTUAL_UI=true sky

# Ou use o atalho
sky_textual
```

**Recursos da UI Textual:**
- Tela de apresentação animada
- Header com título dinâmico e métricas em tempo real
- **Histórico de títulos** — Clique no título ou passe o mouse para ver o que a Sky fez durante a sessão
- Message bubbles estilizados (Sky e usuário)
- Indicador de "pensando" animado
- Suporte a Markdown com syntax highlighting
- Modais de confirmação para comandos destructivos
- Toast notifications para alertas
- Comandos `/help` e `/config` com screens dedicadas

**Comandos disponíveis na UI Textual:**
- `/new` — Iniciar nova sessão (com confirmação se 5+ mensagens)
- `/cancel` — Cancelar operação pendente
- `/config` — Abrir screen de configurações
- `/help` ou `?` — Abrir screen de ajuda
- `/sair`, `quit`, `exit` — Encerrar chat com resumo da sessão

**Variáveis de ambiente para UI Textual:**
- `USE_TEXTUAL_UI` — Habilita nova interface Textual (`true`/`false`, padrão: `false`)
- `USE_CLAUDE_CHAT` — Habilita chat com Claude SDK (`true`/`false`)
- `CLAUDE_MODEL` — Modelo Claude a usar (padrão: `glm-4.7`)
- `RAG_ENABLED` — Habilita busca RAG em memória (`true`/`false`, padrão: `true`)

### Interface Legado (Rich)

```bash
# Chat com interface legado (Rich console)
USE_TEXTUAL_UI=false sky

# Chat com Claude SDK (inferência de IA)
USE_CLAUDE_CHAT=true sky

# Ou use o atalho pré-configurado
sky_claude
```

**Comandos disponíveis (legado):**
- `/new` — Iniciar nova sessão (limpa histórico)
- `/cancel` — Cancelar operação pendente
- `/sair`, `quit`, `exit` — Encerrar chat

> 📖 Veja [docs/chat/CLAUDE_CHAT_QUICKSTART.md](docs/chat/CLAUDE_CHAT_QUICKSTART.md) para mais detalhes.

## Estrutura

```
src/skybridge/
├── kernel/          # Result, Envelope, Registry
├── core/shared/     # Health query
├── platform/        # Bootstrap, Config, Logger
└── apps/api/        # Thin adapter HTTP
```

## Endpoint

### GET /qry/health

```json
{
  "correlation_id": "uuid",
  "timestamp": "2025-12-24T...",
  "status": "success",
  "data": {
    "status": "healthy",
    "version": "0.1.0",
    "timestamp": "2025-12-24T...",
    "service": "Skybridge API"
  }
}
```

---

> "Simples hoje, completo amanhã." – made by Sky ✨
