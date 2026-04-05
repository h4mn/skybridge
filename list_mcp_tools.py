#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, 'src')
from src.core.discord.server import get_tool_definitions

tools = get_tool_definitions()
print(f'{len(tools)} ferramentas MCP Discord ativas:')
print()
for t in tools:
    print(f'  - mcp__discord__{t.name}')
