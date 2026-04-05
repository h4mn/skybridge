#!/usr/bin/env python3
import sys
import os

# Forçar UTF-8
if sys.platform == "win32":
    import io
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Testa se o import do Agent SDK funciona
try:
    from claude_agent_sdk import query, ClaudeAgentOptions
    print("✅ Agent SDK import OK", file=sys.stderr)
except Exception as e:
    print(f"❌ Agent SDK import falhou: {e}", file=sys.stderr)

# Testa asyncio
try:
    import asyncio
    asyncio.run(lambda: None)
    print("✅ asyncio OK", file=sys.stderr)
except Exception as e:
    print(f"❌ asyncio falhou: {e}", file=sys.stderr)

# Lê stdin
try:
    data = sys.stdin.read()
    print(f"✅ stdin lido: {len(data)} chars", file=sys.stderr)
except Exception as e:
    print(f"❌ stdin falhou: {e}", file=sys.stderr)

print("TESTE COMPLETO")
