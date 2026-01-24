#!/usr/bin/env python3
"""
Script de teste de conexão com DragonflyDB.

Usage:
    python scripts/test_dragonfly.py
"""

import sys
try:
    import redis
except ImportError:
    print("❌ redis package não instalado")
    print("   Execute: pip install redis")
    sys.exit(1)


def test_connection():
    """Testa conexão com DragonflyDB."""
    try:
        # Conectar
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # Testar PING/PONG
        result = r.ping()
        if result:
            print("✅ Conexão com DragonflyDB estabelecida")
            print(f"   PING → PONG: {result}")

            # Testar SET/GET
            r.set('test_skybridge', 'fase2')
            value = r.get('test_skybridge')
            print(f"   SET/GET: test_skybridge = {value}")

            # Testar LPUSH/BRPOP (fila)
            r.lpush('skybridge:test_queue', 'job1')
            r.lpush('skybridge:test_queue', 'job2')
            queue_len = r.llen('skybridge:test_queue')
            print(f"   LPUSH/LLEN: test_queue = {queue_len} itens")

            # Limpar
            r.delete('test_skybridge')
            r.delete('skybridge:test_queue')

            # Info
            info = r.info()
            print(f"   Server: {info.get('server', {}).get('redis_version', 'unknown')}")

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
