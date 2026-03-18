# Playbook Fase 2: Redis com DragonflyDB

**PRD Relacionado:** PRD018 - Roadmap para Autonomia Completa
**Fase:** Fase 2 - Redis com DragonflyDB
**Data:** 2026-01-21
**Status:** 📋 Guia de Implementação
**Autor:** Sky

---

## 📋 Resumo

Este playbook documenta as etapas **manuais** necessárias para configurar o DragonflyDB como substituto do Redis para o sistema de filas do Skybridge.

### Por que DragonflyDB?

- **Compatível com Redis:** Usa o cliente `redis-py` sem mudanças
- **Modo CLI:** `dragonfly --cli --log-level debug` para debug em tempo real
- **Multi-threaded:** 3x throughput comparado ao Redis tradicional
- **Sem servidor separado:** Processo CLI simplificado

---

## 🎯 Objetivos da Fase 2

1. Instalar DragonflyDB
2. Configurar modo CLI com log streaming
3. Criar script de startup
4. Instalar cliente redis Python
5. Testar conexão
6. Implementar RedisJobQueue adapter
7. Criar Factory pattern para migração

---

## 1. Instalação do DragonflyDB

### Opção A: Linux/Mac (curl)

```bash
# Download binário mais recente
curl -L https://dragonflydb.io/get.sh | sh

# Verificar instalação
dragonfly --version
# Saída esperada: Dragonfly version 1.x.x
```

### Opção B: Docker

```bash
# Pull da imagem oficial
docker pull docker.dragonflydb.io/dragonflydb/dragonfly

# Verificar
docker run --rm docker.dragonflydb.io/dragonflydb/dragonfly --version
```

### Opção C: Windows (WSL2)

```bash
# No WSL2, usar Opção A
curl -L https://dragonflydb.io/get.sh | sh

# Ou via Docker Desktop
docker pull docker.dragonflydb.io/dragonflydb/dragonfly
```

---

## 2. Configurar Modo CLI

### Criação de Diretório de Dados

```bash
# Criar diretório para persistência
mkdir -p ./data/dragonfly

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path .\data\dragonfly
```

### Startup em Modo CLI

```bash
# Iniciar DragonflyDB em modo CLI
dragonfly --cli \
  --log-level debug \
  --dir ./data/dragonfly \
  --port 6379

# Saída esperada:
# DragonflyDB version 1.x.x starting...
# [DEBUG] Listening on 127.0.0.1:6379
# [INFO] Ready to accept connections
```

**Flags Importantes:**

| Flag | Descrição |
|------|-----------|
| `--cli` | Modo CLI (streaming de logs para stdout) |
| `--log-level` | Nível de log: debug, info, warn, error |
| `--dir` | Diretório de persistência |
| `--port` | Porta (padrão: 6379) |

---

## 3. Script de Startup

### Criar `scripts/start_dragonfly.sh`

```bash
#!/bin/bash
# scripts/start_dragonfly.sh

set -e

# Configurações
DRAGONFLY_DIR="./data/dragonfly"
DRAGONFLY_PORT=6379
LOG_FILE="./logs/dragonfly.log"
PID_FILE="./data/dragonfly/dragonfly.pid"

# Criar diretórios
mkdir -p "$DRAGONFLY_DIR"
mkdir -p "./logs"

# Verificar se já está rodando
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "DragonflyDB já está rodando (PID: $PID)"
        exit 0
    fi
fi

# Iniciar DragonflyDB em background
echo "Iniciando DragonflyDB..."
nohup dragonfly --cli \
  --log-level debug \
  --dir "$DRAGONFLY_DIR" \
  --port "$DRAGONFLY_PORT" \
  >> "$LOG_FILE" 2>&1 &

# Salvar PID
echo $! > "$PID_FILE"

# Aguardar inicialização
sleep 2

# Verificar se iniciou
if ps -p $(cat "$PID_FILE") > /dev/null; then
    echo "✅ DragonflyDB iniciado com sucesso"
    echo "   Logs: $LOG_FILE"
    echo "   PID: $(cat $PID_FILE)"
else
    echo "❌ Falha ao iniciar DragonflyDB"
    exit 1
fi
```

### Tornar executável

```bash
chmod +x scripts/start_dragonfly.sh
```

### Script de Parada (`scripts/stop_dragonfly.sh`)

```bash
#!/bin/bash
# scripts/stop_dragonfly.sh

PID_FILE="./data/dragonfly/dragonfly.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Parando DragonflyDB (PID: $PID)..."
    kill $PID
    rm "$PID_FILE"
    echo "✅ DragonflyDB parado"
else
    echo "DragonflyDB não está rodando"
fi
```

---

## 4. Cliente Redis Python

### Instalação via pip

```bash
# Adicionar ao pyproject.toml
pip install redis

# Ou com requirements.txt
echo "redis>=5.0.0" >> requirements.txt
pip install -r requirements.txt
```

### Verificação

```python
import redis
print(redis.__version__)  # Saída: 5.x.x ou superior
```

---

## 5. Teste de Conexão

### Script: `scripts/test_dragonfly.py`

```python
#!/usr/bin/env python3
"""Script de teste de conexão com DragonflyDB."""

import redis
import sys

def test_connection():
    """Testa conexão com DragonflyDB."""
    try:
        # Conectar
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # Testar PING/PONG
        result = r.ping()
        if result:
            print("✅ Conexão com DragonflyDB estabelecida")
            print(f"   PING → PONG")

            # Testar SET/GET
            r.set('test_skybridge', 'fase2')
            value = r.get('test_skybridge')
            print(f"   SET/GET: test_skybridge = {value}")

            # Limpar
            r.delete('test_skybridge')

            print("✅ Todos os testes passaram")
            return 0
        else:
            print("❌ PING falhou")
            return 1

    except redis.ConnectionError as e:
        print(f"❌ Erro de conexão: {e}")
        print("   Verifique se DragonflyDB está rodando:")
        print("   ./scripts/start_dragonfly.sh")
        return 1
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_connection())
```

### Executar Teste

```bash
# Iniciar DragonflyDB
./scripts/start_dragonfly.sh

# Testar conexão
python scripts/test_dragonfly.py

# Ver logs em tempo real
tail -f logs/dragonfly.log
```

---

## 6. Variáveis de Ambiente

### Atualizar `.env.example`

```bash
# DragonflyDB Configuration
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379
DRAGONFLY_DIR=./data/dragonfly
DRAGONFLY_LOG_LEVEL=debug

# Job Queue Provider
JOB_QUEUE_PROVIDER=dragonfly

# Redis (fallback)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## 7. Estrutura no DragonflyDB

### Keyspaces Utilizadas

```
skybridge:jobs:queue → List (LPUSH/BRPOP)
  - Fila principal de jobs

skybridge:jobs:{job_id} → Hash (HGETALL/HSET)
  - Dados do job específico

skybridge:jobs:processing → Set (SADD/SREM)
  - Jobs em processamento

skybridge:jobs:completed → Set (SADD/SREM)
  - Jobs completados

skybridge:jobs:failed → Set (SADD/SREM)
  - Jobs que falharam

skybridge:metrics:* → String/Hash
  - Métricas persistidas
```

---

## 8. Comandos Úteis

### Verificar Fila

```bash
# Conectar via redis-cli
redis-cli -h localhost -p 6379

# Ver tamanho da fila
LRANGE skybridge:jobs:queue 0 -1

# Ver todos os jobs
KEYS skybridge:jobs:*

# Ver job específico
HGETALL skybridge:jobs:job-123
```

### Limpar Fila (CUIDADO)

```bash
# Limpar apenas a fila (não os jobs)
DEL skybridge:jobs:queue

# Limpar tudo (PERIGO)
FLUSHDB
```

---

## 9. Troubleshooting

### Problema: DragonflyDB não inicia

**Sintoma:** `command not found: dragonfly`

**Solução:**
```bash
# Verificar instalação
which dragonfly

# Adicionar ao PATH
export PATH="$PATH:/usr/local/bin"

# Reinstalar se necessário
curl -L https://dragonflydb.io/get.sh | sh
```

### Problema: Porta 6379 já em uso

**Sintoma:** `Address already in use`

**Solução:**
```bash
# Ver processo usando porta
lsof -i :6379

# Matar processo (se for seguro)
kill -9 <PID>

# Ou usar porta diferente
dragonfly --cli --port 6380
```

### Problema: Conexão recusada

**Sintoma:** `Connection refused`

**Solução:**
```bash
# Verificar se DragonflyDB está rodando
ps aux | grep dragonfly

# Ver logs
tail -f logs/dragonfly.log

# Reiniciar se necessário
./scripts/stop_dragonfly.sh
./scripts/start_dragonfly.sh
```

---

## 10. Checklist de Implementação

- [ ] **Pré-requisitos**
  - [ ] Python 3.10+
  - [ ] pip instalado
  - [ ] Git configurado

- [ ] **DragonflyDB**
  - [ ] Binário instalado
  - [ ] `scripts/start_dragonfly.sh` criado
  - [ ] `scripts/stop_dragonfly.sh` criado
  - [ ] DragonflyDB iniciado e testado

- [ ] **Cliente Python**
  - [ ] `pip install redis` executado
  - [ ] `scripts/test_dragonfly.py` criado
  - [ ] Teste de conexão passou

- [ ] **Configuração**
  - [ ] `.env.example` atualizado
  - [ ] `.env` configurado
  - [ ] Documentação criada

---

## 11. Próximos Passos

Após completar este playbook:

1. **INFRA-06 a INFRA-08:** Implementar `RedisJobQueue`
   - Arquivo: `src/infra/webhooks/adapters/redis_job_queue.py`
   - Implementar `enqueue()`, `dequeue()`, `get_job()`, `update_status()`
   - Adicionar métricas embutidas

2. **INFRA-09:** Migration e Factory
   - Feature flag: `JOB_QUEUE_PROVIDER=redis|dragonfly|file`
   - Factory pattern em `src/infra/webhooks/adapters/job_queue_factory.py`

3. **Testes de Integração**
   - Testar enqueue/dequeue
   - Verificar persistência após restart
   - Validar métricas

---

## 12. Referências

- **DragonflyDB Docs:** https://dragonflydb.io/docs
- **Redis-py:** https://redis-py.readthedocs.io/
- **PRD018:** `docs/prd/PRD018-roadmap-autonomia-incidente.md` (Seção 5)

---

> "Infraestrutura sólida é a base para autonomia sustentável" – made by Sky 🏗️
> "Playbooks transformam incerteza em processo repetível" – made by Sky 📋
