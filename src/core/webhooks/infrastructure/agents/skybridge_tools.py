# -*- coding: utf-8 -*-
"""
Skybridge Custom Tools - Tools decoradas com @tool para Claude Agent SDK.

PRD019: Custom tools substituem comandos XML (log, progress, checkpoint).

Estas tools são registradas via createSdkMcpServer() e ficam disponíveis
para o agente como mcp__skybridge__tool_name.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Import do SDK para custom tools (disponível quando claude-agent-sdk está instalado)
try:
    from claude_agent_sdk import createSdkMcpServer
    from mcp.server import Server as McpServer
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    createSdkMcpServer = None
    McpServer = None


def skybridge_log_tool(level: str, message: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Tool para enviar log estruturado para o Orchestrator.

    Substitui o comando XML <skybridge_log>.

    Args:
        level: Nível do log (info, warning, error)
        message: Mensagem do log
        metadata: Metadados adicionais (opcional)

    Returns:
        Dict com content para MCP response
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "metadata": metadata or {},
    }

    # Em produção, isso enviaria para o Orchestrator via event bus
    # Por ora, apenas imprime no stderr para ser capturado pelo SDK
    print(f"[SKYBRIDGE_LOG] {json.dumps(log_entry)}", file=sys.stderr)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Log [{level}]: {message}",
            }
        ]
    }


def skybridge_progress_tool(percent: int, message: str, status: str | None = None) -> dict[str, Any]:
    """
    Tool para reportar progresso da tarefa.

    Substitui o comando XML <skybridge_progress>.

    Args:
        percent: Percentual de progresso (0-100)
        message: Mensagem descritiva do progresso
        status: Status atual (running, completed, failed)

    Returns:
        Dict com content para MCP response
    """
    progress_entry = {
        "timestamp": datetime.now().isoformat(),
        "percent": max(0, min(100, percent)),
        "message": message,
        "status": status or "running",
    }

    print(f"[SKYBRIDGE_PROGRESS] {json.dumps(progress_entry)}", file=sys.stderr)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Progresso: {percent}% - {message}",
            }
        ]
    }


def skybridge_checkpoint_tool(label: str, description: str | None = None) -> dict[str, Any]:
    """
    Tool para criar checkpoint de estado.

    Substitui o comando XML <skybridge_checkpoint>.

    Args:
        label: Identificador do checkpoint
        description: Descrição do checkpoint (opcional)

    Returns:
        Dict com content para MCP response
    """
    checkpoint_entry = {
        "timestamp": datetime.now().isoformat(),
        "label": label,
        "description": description or f"Checkpoint: {label}",
    }

    print(f"[SKYBRIDGE_CHECKPOINT] {json.dumps(checkpoint_entry)}", file=sys.stderr)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Checkpoint criado: {label}",
            }
        ]
    }


def create_skybridge_mcp_server() -> McpServer | None:
    """
    Cria servidor MCP SDK com tools do Skybridge.

    O servidor expõe as tools:
    - mcp__skybridge__log: Envia log estruturado
    - mcp__skybridge__progress: Reporta progresso da tarefa
    - mcp__skybridge__checkpoint: Cria checkpoint de estado

    Returns:
        McpServer com as tools registradas ou None se SDK não disponível

    Example:
        >>> from core.webhooks.infrastructure.agents.skybridge_tools import create_skybridge_mcp_server
        >>> server = create_skybridge_mcp_server()
        >>> options = ClaudeAgentOptions(
        ...     mcp_servers={"skybridge": {"type": "sdk", "name": "skybridge", "instance": server}}
        ... )
    """
    if not SDK_AVAILABLE or createSdkMcpServer is None:
        # SDK não disponível - retorna None
        # O adapter funcionará sem custom tools
        return None

    # TODO: Implementar decorador @tool do SDK quando disponível
    # Por ora, retorna None - custom tools serão implementadas quando
    # a API do SDK Python estiver mais madura
    return None


# Funções helper para uso direto (sem MCP)
def send_log(level: str, message: str, metadata: dict[str, Any] | None = None) -> None:
    """
    Envia log estruturado (helper function).

    Args:
        level: Nível do log (info, warning, error)
        message: Mensagem do log
        metadata: Metadados adicionais
    """
    skybridge_log_tool(level, message, metadata)


def send_progress(percent: int, message: str, status: str | None = None) -> None:
    """
    Reporta progresso da tarefa (helper function).

    Args:
        percent: Percentual de progresso (0-100)
        message: Mensagem descritiva
        status: Status atual
    """
    skybridge_progress_tool(percent, message, status)


def create_checkpoint(label: str, description: str | None = None) -> None:
    """
    Cria checkpoint de estado (helper function).

    Args:
        label: Identificador do checkpoint
        description: Descrição do checkpoint
    """
    skybridge_checkpoint_tool(label, description)
