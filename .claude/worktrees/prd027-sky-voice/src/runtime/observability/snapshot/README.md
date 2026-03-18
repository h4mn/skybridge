# Snapshot Service

Serviço de observabilidade estrutural para captura e comparação de estados.

## RPC

### snapshot.capture

Payload exemplo (Sky-RPC v0.2 estruturado):

```json
{
  "ticket_id": "<ticket>",
  "detail": {
    "context": "snapshot",
    "action": "capture",
    "subject": "fileops",
    "payload": {
      "target": ".",
      "depth": 5,
      "include_extensions": [".py", ".md"],
      "exclude_patterns": ["*/.git/*"]
    }
  }
}
```

### snapshot.compare

```json
{
  "ticket_id": "<ticket>",
  "detail": {
    "context": "snapshot",
    "action": "compare",
    "subject": "fileops",
    "payload": {
      "old_snapshot_id": "snap_...",
      "new_snapshot_id": "snap_...",
      "format": "markdown"
    }
  }
}
```
