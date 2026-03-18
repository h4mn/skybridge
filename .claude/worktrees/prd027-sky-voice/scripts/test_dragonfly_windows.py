# -*- coding: utf-8 -*-
"""
Teste de Conexão Redis Python <-> DragonflyDB (Windows).

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
