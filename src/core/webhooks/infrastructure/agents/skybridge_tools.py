# -*- coding: utf-8 -*-
"""
Skybridge Custom Tools - Tools decoradas com @tool para Claude Agent SDK.

PRD019: Custom tools substituem comandos XML (log, progress, checkpoint).

Estas tools são registradas via create_sdk_mcp_server() e ficam disponíveis
para o agente como mcp__skybridge__tool_name.

Referência: https://platform.claude.com/docs/pt-BR/agent-sdk/python
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any

# Import do SDK para custom tools (disponível quando claude-agent-sdk está instalado)
try:
    from claude_agent_sdk import tool, create_sdk_mcp_server
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    tool = None
    create_sdk_mcp_server = None


# =============================================================================
# CUSTOM TOOLS DECORADAS COM @tool
# =============================================================================

if SDK_AVAILABLE and tool is not None:

    @tool(
        "skybridge_log",
        "Envia log estruturado para o Orchestrator Skybridge",
        {"level": str, "message": str, "metadata": dict}
    )
    async def skybridge_log(args: dict[str, Any]) -> dict[str, Any]:
        """
        Tool para enviar log estruturado para o Orchestrator.

        Substitui o comando XML <skybridge_log>.

        Args:
            args: Dict com level, message e metadata

        Returns:
            Dict com content para MCP response
        """
        level = args.get("level", "info")
        message = args.get("message", "")
        metadata = args.get("metadata")

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

    @tool(
        "skybridge_progress",
        "Reporta progresso da tarefa para o Orchestrator Skybridge",
        {"percent": int, "message": str, "status": str}
    )
    async def skybridge_progress(args: dict[str, Any]) -> dict[str, Any]:
        """
        Tool para reportar progresso da tarefa.

        Substitui o comando XML <skybridge_progress>.

        Args:
            args: Dict com percent, message e status

        Returns:
            Dict com content para MCP response
        """
        percent = args.get("percent", 0)
        message = args.get("message", "")
        status = args.get("status", "running")

        progress_entry = {
            "timestamp": datetime.now().isoformat(),
            "percent": max(0, min(100, percent)),
            "message": message,
            "status": status,
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

    @tool(
        "skybridge_checkpoint",
        "Cria checkpoint de estado no Orchestrator Skybridge",
        {"label": str, "description": str}
    )
    async def skybridge_checkpoint(args: dict[str, Any]) -> dict[str, Any]:
        """
        Tool para criar checkpoint de estado.

        Substitui o comando XML <skybridge_checkpoint>.

        Args:
            args: Dict com label e description

        Returns:
            Dict com content para MCP response
        """
        label = args.get("label", "")
        description = args.get("description")

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


def create_skybridge_mcp_server() -> Any:
    """
    Cria servidor MCP SDK com tools do Skybridge.

    O servidor expõe as tools:
    - mcp__skybridge__log: Envia log estruturado
    - mcp__skybridge__progress: Reporta progresso da tarefa
    - mcp__skybridge__checkpoint: Cria checkpoint de estado

    Returns:
        McpSdkServerConfig com as tools registradas ou None se SDK não disponível

    Example:
        >>> from core.webhooks.infrastructure.agents.skybridge_tools import create_skybridge_mcp_server
        >>> server = create_skybridge_mcp_server()
        >>> options = ClaudeAgentOptions(
        ...     mcp_servers={"skybridge": server},
        ...     allowed_tools=["mcp__skybridge__log", "mcp__skybridge__progress"]
        ... )
    """
    if not SDK_AVAILABLE or create_sdk_mcp_server is None:
        # SDK não disponível - retorna None
        # O adapter funcionará sem custom tools
        return None

    # Cria servidor MCP com as 3 custom tools do Skybridge
    return create_sdk_mcp_server(
        name="skybridge",
        version="1.0.0",
        tools=[skybridge_log, skybridge_progress, skybridge_checkpoint]
    )


# =============================================================================
# FUNÇÕES HELPER PARA USO DIRETO (SEM MCP)
# =============================================================================

def send_log(level: str, message: str, metadata: dict[str, Any] | None = None) -> None:
    """
    Envia log estruturado (helper function).

    Args:
        level: Nível do log (info, warning, error)
        message: Mensagem do log
        metadata: Metadados adicionais
    """
    # Usa a função helper diretamente sem decorador @tool
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "metadata": metadata or {},
    }
    print(f"[SKYBRIDGE_LOG] {json.dumps(log_entry)}", file=sys.stderr)


def send_progress(percent: int, message: str, status: str | None = None) -> None:
    """
    Reporta progresso da tarefa (helper function).

    Args:
        percent: Percentual de progresso (0-100)
        message: Mensagem descritiva
        status: Status atual
    """
    progress_entry = {
        "timestamp": datetime.now().isoformat(),
        "percent": max(0, min(100, percent)),
        "message": message,
        "status": status or "running",
    }
    print(f"[SKYBRIDGE_PROGRESS] {json.dumps(progress_entry)}", file=sys.stderr)


def create_checkpoint(label: str, description: str | None = None) -> None:
    """
    Cria checkpoint de estado (helper function).

    Args:
        label: Identificador do checkpoint
        description: Descrição do checkpoint
    """
    checkpoint_entry = {
        "timestamp": datetime.now().isoformat(),
        "label": label,
        "description": description or f"Checkpoint: {label}",
    }
    print(f"[SKYBRIDGE_CHECKPOINT] {json.dumps(checkpoint_entry)}", file=sys.stderr)
