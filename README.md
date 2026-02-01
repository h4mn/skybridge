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
