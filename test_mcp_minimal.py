#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste mínimo do MCP server."""
import sys
import io
from pathlib import Path

# UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Teste 1: Import
try:
    from mcp.server.stdio import stdio_server
    from mcp import Server
    sys.stderr.write("PASS: Import MCP OK\n")
except Exception as e:
    sys.stderr.write(f"FALHA: Import MCP: {e}\n")
    sys.exit(1)

# Teste 2: Criar server
try:
    server = Server(name="test", version="0.1.0")
    sys.stderr.write("PASS: Criar server OK\n")
except Exception as e:
    sys.stderr.write(f"FALHA: Criar server: {e}\n")
    sys.exit(1)

# Teste 3: stdio_server context
try:
    import asyncio

    async def test():
        async with stdio_server() as (read_stream, write_stream):
            sys.stderr.write("PASS: stdio_server context OK\n")
            # NAO chama run() - so testa o context
            await asyncio.sleep(0.1)

    asyncio.run(test())
    sys.stderr.write("PASS: Tudo OK!\n")
except Exception as e:
    sys.stderr.write(f"FALHA: stdio_server: {e}\n")
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
