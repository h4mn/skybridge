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

```bash
# Chat com respostas fixas (padrão)
sky

# Chat com Claude SDK (inferência de IA)
USE_CLAUDE_CHAT=true sky

# Ou use o atalho pré-configurado
sky_claude
```

**Comandos disponíveis:**
- `/new` — Iniciar nova sessão (limpa histórico)
- `/cancel` — Cancelar operação pendente
- `/sair`, `quit`, `exit` — Encerrar chat

**Variáveis de ambiente:**
- `USE_CLAUDE_CHAT` — Habilita chat com Claude SDK (`true`/`false`)
- `CLAUDE_MODEL` — Modelo Claude a usar (padrão: `glm-4.7`)
- `VERBOSE` — Exibe métricas detalhadas (`true`/`false`)

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
