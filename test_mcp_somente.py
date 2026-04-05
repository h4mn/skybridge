#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste MCP server SEM Discord - para isolar o problema."""
import os
import sys
import io
from pathlib import Path

# UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import asyncio
from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server(name="test", version="0.1.0")

@server.list_tools()
async def list_tools():
    return [Tool(
        name="ping",
        description="Ping test",
        inputSchema={"type": "object"}
    )]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "ping":
        return [TextContent(type="text", text="pong")]
    return [TextContent(type="text", text=f"unknown: {name}", isError=True)]

async def main():
    sys.stderr.write("DEBUG: ANTES stdio_server\n")
    sys.stderr.flush()

    async with stdio_server() as (read_stream, write_stream):
        sys.stderr.write("DEBUG: DENTRO stdio_server\n")
        sys.stderr.flush()

        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
