# PoC: DragonflyDB Windows Nativo (.exe) com Subprocess Log Streaming

**PRD Relacionado:** PRD018 Fase 2
**Data:** 2026-01-21
**Status:** 📋 Pendente

---

## 🎯 Objetivo

Testar a integração entre **cliente Redis Python** (`redis-py`) e **servidor DragonflyDB** executando nativamente no Windows via **`dragonfly.exe`** com streaming de logs em tempo real.

---

## 📋 Contexto

### Por que DragonflyDB nativo no Windows?

O DragonflyDB oferece binários nativos para Windows, permitindo:

- ✅ **Zero overhead** de virtualização (WSL/Docker)
- ✅ **Performance máxima** - execução direta no Windows
- ✅ **Setup simples** - baixar e executar o `.exe`
- ✅ **Logs em tempo real** via subprocess com streaming
- ✅ **Compatibilidade total** com `redis-py` (drop-in replacement)

### Limitações Conhecidas

- DragonflyDB para Windows está em beta
- Recursos como persistência em disco podem ter limitações
- Recomendado para desenvolvimento e testes iniciais

---

## 🔧 Pré-requisitos

### 1. Baixar DragonflyDB para Windows

Visite [DragonflyDB Releases](https://dragonflydb.io/releases) ou use o download direto:

```powershell
# Criar diretório para binários
mkdir -p bin

# Baixar dragonfly.exe (exemplo - verificar URL mais recente em dragonflydb.io)
# URL: https://dragonflydb.io/releases/latest
# Extrair para bin/dragonfly.exe
```

### 2. Python (Windows)

```bash
pip install redis>=5.0.0
```

### 3. Estrutura de Diretórios

```
skybridge/
├── bin/
│   └── dragonfly.exe      # Executável DragonflyDB
├── data/
│   └── dragonfly/         # Persistência (se suportado)
├── logs/
│   └── dragonfly.log      # Logs da instância
└── scripts/
    ├── dragonfly_windows.py
    └── test_dragonfly_windows.py
```

---

## 📝 Implementação da PoC

### 1. Script Python para iniciar DragonflyDB

**Arquivo:** `scripts/dragonfly_windows.py`

```python
# -*- coding: utf-8 -*-
"""
DragonflyDB Windows Launcher - Inicia dragonfly.exe nativo com log streaming.

Uso:
    python scripts/dragonfly_windows.py start
    python scripts/dragonfly_windows.py stop
    python scripts/dragonfly_windows.py logs
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# Configurações
DRAGONFLY_EXE = Path("./bin/dragonfly.exe")
DRAGONFLY_HOST = "localhost"
DRAGONFLY_PORT = 6379
DRAGONFLY_DIR = "./data/dragonfly"

PID_FILE = Path("./data/dragonfly.pid")
LOG_FILE = Path("./logs/dragonfly.log")


def start_dragonfly():
    """Inicia DragonflyDB nativo em background."""
    print(f"[INFO] Iniciando DragonflyDB nativo...")

    # Validar executável
    if not DRAGONFLY_EXE.exists():
        print(f"[ERROR] Executável não encontrado: {DRAGONFLY_EXE}")
        print("\nDicas:")
        print("  1. Baixe dragonfly.exe de https://dragonflydb.io/releases")
        print("  2. Coloque em ./bin/dragonfly.exe")
        return False

    # Criar diretórios
    Path(DRAGONFLY_DIR).mkdir(parents=True, exist_ok=True)
    Path("./logs").mkdir(parents=True, exist_ok=True)

    # Comando para iniciar DragonflyDB
    # --cli: Modo CLI com logs em stdout
    # --log-level debug: Logs detalhados
    cmd = [
        str(DRAGONFLY_EXE),
        "--cli",
        "--log-level", "debug",
        "--dir", DRAGONFLY_DIR,
        "--port", str(DRAGONFLY_PORT),
    ]

    # Iniciar processo em background
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,  # Line buffered
    )

    # Salvar PID
    PID_FILE.write_text(str(process.pid), encoding="utf-8")

    # Stream logs para arquivo e console
    with open(LOG_FILE, "w", encoding="utf-8") as log_f:
        print(f"[INFO] DragonflyDB iniciado (PID: {process.pid})")
        print(f"[INFO] Logs: {LOG_FILE}")
        print("[INFO] Aguardando startup...")

        # Aguardar confirmação de startup
        started = False
        for line in process.stdout:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] {line.rstrip()}"
            print(log_line)
            log_f.write(log_line + "\n")
            log_f.flush()

            if not started and ("ready" in line.lower() or "listening" in line.lower() or "started" in line.lower()):
                started = True
                print("[INFO] DragonflyDB pronto!")
                print(f"[INFO] Conexão: redis-cli -h {DRAGONFLY_HOST} -p {DRAGONFLY_PORT}")
                break

        # Continuar streaming em background (thread separada em produção)

    return True


def stop_dragonfly():
    """Para DragonflyDB."""
    if not PID_FILE.exists():
        print("[WARN] DragonflyDB não está rodando (sem PID file)")
        return False

    pid = int(PID_FILE.read_text(encoding="utf-8"))
    print(f"[INFO] Parando DragonflyDB (PID: {pid})...")

    try:
        # Windows usa TerminateProcess
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        PID_FILE.unlink(missing_ok=True)
        print("[INFO] DragonflyDB parado")
        return True
    except Exception as e:
        print(f"[ERROR] Falha ao parar: {e}")
        return False


def tail_logs():
    """Mostra logs em tempo real."""
    if not LOG_FILE.exists():
        print("[WARN] Arquivo de log não encontrado")
        return

    print(f"[INFO] Mostrando logs: {LOG_FILE}")
    print("[INFO] Ctrl+C para sair\n")

    # PowerShell Get-Content com -Wait para tail nativo
    cmd = ["powershell", "-Command", f"Get-Content {LOG_FILE} -Wait"]

    process = subprocess.Popen(
        cmd,
        universal_newlines=True,
    )

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n[INFO] Saindo...")
        process.terminate()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python dragonfly_windows.py [start|stop|logs]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        success = start_dragonfly()
        sys.exit(0 if success else 1)
    elif command == "stop":
        stop_dragonfly()
    elif command == "logs":
        tail_logs()
    else:
        print(f"Comando inválido: {command}")
        sys.exit(1)
```

---

### 2. Script de Teste de Conexão

**Arquivo:** `scripts/test_dragonfly_windows.py`

```python
# -*- coding: utf-8 -*-
"""
Teste de Conexão Redis Python <-> DragonflyDB (Windows Nativo).

Valida:
- Conexão via redis-py
- Operações básicas (PING, SET, GET)
- Operações de fila (LPUSH, BRPOP)
"""

import time
import sys


def test_connection():
    """Testa conexão com DragonflyDB."""
    try:
        import redis
    except ImportError:
        print("[ERROR] Package 'redis' não instalado")
        print("Execute: pip install redis>=5.0.0")
        return False

    print("[INFO] Conectando ao DragonflyDB...")
    client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
    )

    try:
        # Test 1: PING
        print("\n[Test 1] PING/PONG")
        result = client.ping()
        print(f"  Result: {result}")
        assert result is True

        # Test 2: SET/GET
        print("\n[Test 2] SET/GET")
        client.set("skybridge:test", "hello-world")
        value = client.get("skybridge:test")
        print(f"  Value: {value}")
        assert value == "hello-world"

        # Test 3: Queue Operations (LPUSH/LLEN)
        print("\n[Test 3] Queue Operations")
        client.delete("skybridge:jobs:queue")
        client.lpush("skybridge:jobs:queue", "job1", "job2", "job3")
        queue_len = client.llen("skybridge:jobs:queue")
        print(f"  Queue length: {queue_len}")
        assert queue_len == 3

        # Test 4: BRPOP (blocking dequeue)
        print("\n[Test 4] BRPOP (blocking dequeue)")
        print("  Aguardando item por 2 segundos...")
        start = time.time()
        result = client.brpop("skybridge:jobs:queue", timeout=2)
        elapsed = time.time() - start
        print(f"  Dequeued: {result}")
        print(f"  Latency: {elapsed:.3f}s")
        assert result is not None

        # Test 5: Remaining items
        print("\n[Test 5] Remaining items")
        remaining = client.lrange("skybridge:jobs:queue", 0, -1)
        print(f"  Remaining: {remaining}")
        assert len(remaining) == 2

        # Cleanup
        client.delete("skybridge:test", "skybridge:jobs:queue")

        print("\n[SUCCESS] Todos os testes passaram!")
        return True

    except redis.ConnectionError as e:
        print(f"[ERROR] Falha de conexão: {e}")
        print("\nDicas:")
        print("  1. Verifique se DragonflyDB está rodando: python scripts/dragonfly_windows.py logs")
        print("  2. Inicie DragonflyDB: python scripts/dragonfly_windows.py start")
        return False
    except AssertionError as e:
        print(f"[ERROR] Teste falhou: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Erro inesperado: {e}")
        return False
    finally:
        client.close()


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
```

---

## 🧪 Execução da PoC

### Passo 0: Download do Executável

```powershell
# Criar diretório bin
mkdir bin

# Baixar dragonfly.exe
# 1. Visite: https://dragonflydb.io/releases
# 2. Baixe a versão Windows (dragonfly-windows-amd64.exe ou similar)
# 3. Renomeie para dragonfly.exe e coloque em ./bin/dragonfly.exe
```

### Passo 1: Iniciar DragonflyDB

```bash
# Terminal 1 - Iniciar DragonflyDB
python scripts/dragonfly_windows.py start
```

**Saída esperada:**
```
[INFO] Iniciando DragonflyDB nativo...
[INFO] DragonflyDB iniciado (PID: 12345)
[INFO] Logs: ./logs/dragonfly.log
[INFO] Aguardando startup...
[2026-01-21 10:30:00] Dragonfly version x.y.z starting...
[2026-01-21 10:30:00] dfly 0.0.0.0:6379 flag: ...
[2026-01-21 10:30:01] Ready to accept connections
[INFO] DragonflyDB pronto!
[INFO] Conexão: redis-cli -h localhost -p 6379
```

### Passo 2: Testar Conexão

```bash
# Terminal 2 - Testar conexão
python scripts/test_dragonfly_windows.py
```

**Saída esperada:**
```
[INFO] Conectando ao DragonflyDB...

[Test 1] PING/PONG
  Result: True

[Test 2] SET/GET
  Value: hello-world

[Test 3] Queue Operations
  Queue length: 3

[Test 4] BRPOP (blocking dequeue)
  Aguardando item por 2 segundos...
  Dequeued: ('skybridge:jobs:queue', 'job3')
  Latency: 0.005s

[Test 5] Remaining items
  Remaining: ['job2', 'job1']

[SUCCESS] Todos os testes passaram!
```

### Passo 3: Monitorar Logs

```bash
# Terminal 3 - Logs em tempo real
python scripts/dragonfly_windows.py logs
```

### Passo 4: Parar DragonflyDB

```bash
python scripts/dragonfly_windows.py stop
```

---

## ✅ Critérios de Sucesso

A PoC será considerada **bem-sucedida** se:

1. ✅ `dragonfly.exe` inicia sem erros
2. ✅ Logs são streamados em tempo real para stdout e arquivo
3. ✅ Cliente `redis-py` conecta com sucesso
4. ✅ Operações básicas (PING, SET, GET) funcionam
5. ✅ Operações de fila (LPUSH, BRPOP) funcionam
6. ✅ Latência de conexão < 10ms (localhost nativo)
7. ✅ Processo pode ser parado com `stop`

---

## 🔍 Troubleshooting

### Erro: "Executável não encontrado"

**Causa:** `dragonfly.exe` não está em `./bin/`

**Solução:**
```powershell
# Criar diretório
mkdir bin

# Baixar do site oficial
# https://dragonflydb.io/releases
# Copiar para bin/dragonfly.exe
```

### Erro: "Connection refused"

**Causa:** DragonflyDB não está rodando.

**Solução:**
```bash
# Verificar logs
python scripts/dragonfly_windows.py logs

# Reiniciar
python scripts/dragonfly_windows.py stop
python scripts/dragonfly_windows.py start

# Verificar porta
netstat -ano | findstr :6379
```

### Porta 6379 já em uso

**Causa:** Outro processo está usando a porta 6379.

**Solução:**
```powershell
# Ver processo
netstat -ano | findstr :6379

# Matar processo
taskkill /PID <PID> /F

# Ou mudar porta no script
DRAGONFLY_PORT = 6380
```

### Erro: "O sistema não pode encontrar o arquivo especificado"

**Causa:** Caminho do executável incorreto ou problema de permissões.

**Solução:**
```powershell
# Usar caminho absoluto
DRAGONFLY_EXE = Path("B:/_repositorios/skybridge-refactor-events/bin/dragonfly.exe")

# Verificar permissões
# Clique direito em dragonfly.exe > Propriedades > Desbloquear
```

---

## 📊 Resultados Esperados

### Métricas de Performance (Windows Nativo)

| Operação | Latência Esperada | Observação |
|----------|-------------------|------------|
| PING | < 5ms | Nativo, sem overhead |
| SET/GET | < 10ms | Localhost |
| LPUSH | < 8ms | Write operation |
| BRPOP | < 15ms | Blocking read |

### Comparação de Alternativas Windows

| Solução | Latência PING | Vantagens | Desvantagens |
|---------|---------------|-----------|--------------|
| **dragonfly.exe nativo** | ~3-5ms | Performance máxima | Windows beta |
| WSL + DragonflyDB | ~8-12ms | Linux estável | Overhead WSL |
| Docker Desktop | ~20-30ms | Isolamento | Overhead VM |
| Redis Windows | ~10ms | Nativo | Descontinuado |

---

## 🚀 Próximos Passos

Após PoC bem-sucedida:

1. **Integrar ao Skybridge**
   - Configurar `.env`: `JOB_QUEUE_PROVIDER=dragonfly`
   - Usar `JobQueueFactory.create_from_env()`

2. **Automatizar Startup**
   - Script `start_dev.bat` para inicializar ambiente completo
   - Verificar se `dragonfly.exe` está rodando antes de iniciar API

3. **Produção**
   - Avaliar estabilidade do Windows build
   - Considerar migrar para Linux/Docker em produção

---

## 📚 Referências

- [Playbook PB018-Fase2](../playbook/PB018-Fase2-Redis-DragonflyDB.md)
- [Guia de Setup](../how-to/dragonfly-setup.md)
- [DragonflyDB Releases](https://dragonflydb.io/releases)
- [DragonflyDB Docs](https://dragonflydb.io/docs)
- [redis-py GitHub](https://github.com/redis/redis-py)

---

> "Nativo é rápido, simples é melhor" – made by Sky ⚡
