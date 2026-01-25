# Guia de Setup: DragonflyDB para Skybridge

**PRD Relacionado:** PRD018 Fase 2
**Playbook:** PB018-Fase2-Redis-DragonflyDB.md
**Data:** 2026-01-21

---

## 📋 Visão Geral

Este guia documenta como configurar o **DragonflyDB** como substituto drop-in do Redis para o sistema de filas do Skybridge.

### Por que DragonflyDB?

- **Compatível com Redis:** Usa o cliente `redis-py` sem mudanças
- **Modo CLI:** `dragonfly --cli --log-level debug` para debug em tempo real
- **Multi-threaded:** 3x throughput comparado ao Redis tradicional
- **Processo único:** Sem servidor separado, simplifica deploy

---

## 1. Instalação

### Linux/Mac

```bash
curl -L https://dragonflydb.io/get.sh | sh
```

### Windows (WSL2)

```bash
# No WSL2
curl -L https://dragonflydb.io/get.sh | sh
```

### Docker (alternativa)

```bash
docker pull docker.dragonflydb.io/dragonflydb/dragonfly
```

---

## 2. Inicialização

### Modo Interativo (para testes)

```bash
# Criar diretório de dados
mkdir -p ./data/dragonfly

# Iniciar DragonflyDB
dragonfly --cli \
  --log-level debug \
  --dir ./data/dragonfly \
  --port 6379
```

### Modo Background (produção)

```bash
# Usar script fornecido
./scripts/start_dragonfly.sh

# Ver logs em tempo real
tail -f logs/dragonfly.log
```

---

## 3. Verificação

### Teste de Conexão

```bash
python scripts/test_dragonfly.py
```

### Comandos redis-cli

```bash
# Verificar se está rodando
redis-cli ping
# Saída: PONG

# Ver informações
redis-cli info

# Ver tamanho da fila
redis-cli LLEN skybridge:jobs:queue
```

---

## 4. Configuração Skybridge

### Variáveis de Ambiente

Adicionar ao `.env`:

```bash
# DragonflyDB
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379
DRAGONFLY_DIR=./data/dragonfly

# Provider
JOB_QUEUE_PROVIDER=dragonfly
```

### Uso no Código

```python
from infra.webhooks.adapters.job_queue_factory import create_job_queue

# Criar fila automaticamente baseado em JOB_QUEUE_PROVIDER
queue = create_job_queue()

# Ou especificar provider explicitamente
queue = create_job_queue(provider="dragonfly")
```

---

## 5. Estrutura de Dados

### Keyspaces

```
skybridge:jobs:queue          → Lista (LPUSH/BRPOP)
  - Fila principal de jobs

skybridge:jobs:{job_id}       → Hash (HGETALL/HSET)
  - Dados do job (status, payload, metadata)

skybridge:jobs:processing     → Set (SADD/SREM)
  - Jobs em processamento

skybridge:jobs:completed       → Set (SADD/SREM)
  - Jobs completados

skybridge:jobs:failed          → Set (SADD/SREM)
  - Jobs que falharam

skybridge:metrics:*            → String/Hash
  - Métricas (jobs_enqueued, etc.)
```

---

## 6. Troubleshooting

### Porta 6379 já em uso

```bash
# Ver processo
lsof -i :6379

# Matar processo
kill -9 <PID>
```

### Conexão recusada

```bash
# Verificar se DragonflyDB está rodando
ps aux | grep dragonfly

# Reiniciar
./scripts/stop_dragonfly.sh
./scripts/start_dragonfly.sh
```

### Limpar fila (cuidado!)

```bash
# Limpar apenas a fila
redis-cli DEL skybridge:jobs:queue

# Limpar tudo (PERIGO!)
redis-cli FLUSHDB
```

---

## 7. Monitoramento

### Ver métricas em tempo real

```bash
# Tamanho da fila
redis-cli LLEN skybridge:jobs:queue

# Jobs em processamento
redis-cli SCARD skybridge:jobs:processing

# Jobs completados/falhados
redis-cli SCARD skybridge:jobs:completed
redis-cli SCARD skybridge:jobs:failed

# Todas as keys do Skybridge
redis-cli KEYS skybridge:*
```

### Métricas via API

Endpoint `/metrics` retorna:

```json
{
  "queue_size": 0,
  "processing": 0,
  "completed": 42,
  "failed": 3,
  "total_enqueued": 45,
  "success_rate": 0.933
}
```

---

## 8. Persistência e Backup

### Snapshots

DragonflyDB persiste dados automaticamente no diretório configurado:

```bash
# Diretório de dados
./data/dragonfly/

# Backup (parar DragonflyDB primeiro)
./scripts/stop_dragonfly.sh
tar -czf dragonfly-backup-$(date +%Y%m%d).tar.gz ./data/dragonfly/

# Restore
tar -xzf dragonfly-backup-YYYYMMDD.tar.gz
./scripts/start_dragonfly.sh
```

---

## 9. Próximos Passos

Após configurar DragonflyDB:

1. ✅ **Instalar dependências:** `pip install redis`
2. ✅ **Configurar variáveis de ambiente**
3. ✅ **Iniciar DragonflyDB:** `./scripts/start_dragonfly.sh`
4. ✅ **Testar conexão:** `python scripts/test_dragonfly.py`
5. 🔄 **Usar no código:** `JOB_QUEUE_PROVIDER=dragonfly`

---

## 10. Referências

- [Playbook Completo](../playbook/PB018-Fase2-Redis-DragonflyDB.md)
- [DragonflyDB Docs](https://dragonflydb.io/docs)
- [PRD018](../prd/PRD018-roadmap-autonomia-incidente.md) (Fase 2)
- [redis-py Docs](https://redis-py.readthedocs.io/)

---

> "Persistência confiável é base para autonomia sustentável" – made by Sky 💾
