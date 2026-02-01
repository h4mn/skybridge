# Sky-RPC Quickstart

## 3 Passos para Executar

| Passo | Endpoint | Descrição |
|-------|----------|-----------|
| 1 | `GET /discover` | Listar operações disponíveis |
| 2 | `GET /ticket?method=X` | Obter permissão para executar X |
| 3 | `POST /envelope` | Executar X com parâmetros |

---

## Exemplo Completo

```bash
# 1. Descobrir
curl https://cunning-dear-primate.ngrok-free.app/discover

# 2. Ticket
curl "https://cunning-dear-primate.ngrok-free.app/ticket?method=fileops.read" \
  -H "x-api-key: <key>"

# 3. Executar
curl https://cunning-dear-primate.ngrok-free.app/envelope \
  -H "x-api-key: <key>" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "<id>",
    "detail": {
      "context": "fileops",
      "action": "read",
      "subject": "README.md",
      "payload": {"encoding": "utf-8"}
    }
  }'
```

---

**Base URL:** `https://cunning-dear-primate.ngrok-free.app`
