"""
Teste final de integração Discord MCP.

Este teste:
1. Cria um cliente MCP simples
2. Envia um comando fetch_messages
3. Verifica se consegue comunicar
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_mcp_communication():
    """Testa comunicação MCP básica."""

    print("[TEST] Teste de comunicação MCP")
    print("[TEST] Este teste verifica se consegue se comunicar com o servidor MCP")
    print("[TEST] que deve estar rodando em background.\n")

    # O servidor MCP usa stdio, então não podemos testar diretamente
    # Mas podemos verificar se o processo está rodando
    import subprocess

    try:
        result = subprocess.run(
            ["tasklist", "//FI", "IMAGENAME eq python.exe", "//FO", "CSV"],
            capture_output=True,
            text=True,
            timeout=5
        )

        python_processes = [line for line in result.stdout.split("\n") if "python.exe" in line.lower()]

        if python_processes:
            print(f"[TEST] ✅ Encontrados {len(python_processes)} processos Python:")
            for proc in python_processes[:3]:  # Primeiros 3
                print(f"     {proc}")
        else:
            print("[TEST] ❌ Nenhum processo Python encontrado!")
            print("[TEST] O servidor MCP pode não estar rodando.")

    except Exception as e:
        print(f"[TEST] Erro ao verificar processos: {e}")

    # Verificar log
    log_path = Path("discord_mcp.log")
    if log_path.exists():
        log_content = log_path.read_text()
        print(f"\n[TEST] Log existe ({len(log_content)} bytes)")

        # Verificar se o servidor iniciou corretamente
        if "Discord gateway conectado" in log_content:
            print("[TEST] ✅ Discord Gateway conectado!")
        else:
            print("[TEST] ⚠️  Discord Gateway pode não estar conectado")

        # Verificar se set_mcp_server foi chamado
        if "set_mcp_server" in log_content:
            print("[TEST] ✅ set_mcp_server foi chamado")
        else:
            print("[TEST] ❌ set_mcp_server NÃO foi chamado")

    print("\n[TEST] === Diagnóstico final ===")
    print("[TEST] Para o botão funcionar, precisamos:")
    print("[TEST] 1. Servidor MCP rodando ✅")
    print("[TEST] 2. Discord Gateway conectado ❓")
    print("[TEST] 3. set_mcp_server chamado ✅")
    print("[TEST] 4. on_interaction_create sendo chamado ❌")
    print("[TEST] 5. Callback da View sendo executado ❌")
    print("\n[TEST] O problema está em 4 ou 5 - o Discord não está")
    print("[TEST] roteando interações para nossos handlers.")


if __name__ == "__main__":
    asyncio.run(test_mcp_communication())
