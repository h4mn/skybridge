# -*- coding: utf-8 -*-
"""
Safe Git Tool - Custom tool para operações git seguras em worktrees de agentes.

DOC: PLAN.md Fase 2 - Criar Custom Tool safe_git

Regras:
- Apenas branches com prefixo sky/* ou sky-test/*
- Bloqueia checkout de branches existentes
- Bloqueia comandos destrutivos (reset --hard, clean, restore)
- Permite: commit, push, status, worktree add

Este módulo é uma custom tool decorada com @tool para uso com
claude-agent-sdk (ADR021).
"""
from __future__ import annotations

import re
import subprocess
from typing import Any

from kernel.contracts.result import Result


def safe_git(command: str, cwd: str) -> Result[str, str]:
    """
    Executa comandos git de forma segura para worktrees de agentes.

    Regras de segurança:
        1. Bloqueia git checkout de branches existentes
        2. Exige prefixo sky/* ou sky-test/* para criar branches
        3. Bloqueia comandos destrutivos (reset --hard, clean, restore)
        4. Permite operações seguras: commit, push, status, worktree add

    Args:
        command: Comando git completo (ex: "git status")
        cwd: Diretório de trabalho (worktree path)

    Returns:
        Result com stdout do comando ou erro

    Examples:
        >>> # Permitido: criar branch com prefixo sky/*
        >>> result = safe_git("git checkout -b sky/test-branch", "/path/to/worktree")
        >>> assert result.is_ok

        >>> # Bloqueado: criar branch sem prefixo
        >>> result = safe_git("git checkout -b feature-xyz", "/path/to/worktree")
        >>> assert result.is_err
        >>> assert "prefixo" in result.error.lower() or "sky/" in result.error.lower()

        >>> # Bloqueado: checkout de branch existente
        >>> result = safe_git("git checkout dev", "/path/to/worktree")
        >>> assert result.is_err
        >>> assert "checkout" in result.error.lower() or "existente" in result.error.lower()
    """
    # Validações de entrada
    if not command:
        return Result.err("Comando vazio não permitido")

    if not cwd:
        return Result.err("Diretório de trabalho (cwd) é obrigatório")

    # Normaliza o comando para análise
    command_normalized = command.strip()

    # Padrões de comandos bloqueados
    blocked_patterns = [
        # Comandos destrutivos
        (r"git\s+reset\s+--hard", "Comando destrutivo bloqueado: git reset --hard"),
        (r"git\s+clean\b", "Comando destrutivo bloqueado: git clean"),
        (r"git\s+restore\b", "Comando destrutivo bloqueado: git restore"),
    ]

    # Verifica comandos destrutivos
    for pattern, error_msg in blocked_patterns:
        if re.search(pattern, command_normalized, re.IGNORECASE):
            return Result.err(error_msg)

    # Padrões de checkout - bloqueia checkout de branches existentes
    # git checkout <branch_existente> é bloqueado
    # git checkout -b <nova_branch> só é permitido com prefixo sky/* ou sky-test/*
    checkout_match = re.search(
        r"git\s+checkout(?:\s+-(?:b|B|\-new-branch))?\s*(.+)?$",
        command_normalized,
        re.IGNORECASE
    )

    if checkout_match:
        # Extrai flags e branch
        has_dash_b = "-b" in command_normalized or "-B" in command_normalized or "--new-branch" in command_normalized
        branch_part = checkout_match.group(1) or ""

        # Limpa a branch de argumentos extras
        branch_name = branch_part.split()[0] if branch_part else ""

        # Se tem -b ou -B, é criação de nova branch
        if has_dash_b:
            # Exige prefixo sky/* ou sky-test/*
            if not (branch_name.startswith("sky/") or branch_name.startswith("sky-test/")):
                return Result.err(
                    f"Branch deve ter prefixo 'sky/*' ou 'sky-test/*': '{branch_name}'"
                )
        else:
            # Checkout sem -b: bloqueia se não for vazio (checkout de branch existente)
            if branch_name:
                return Result.err(
                    f"Checkout de branch existente bloqueado: '{branch_name}'. "
                    f"Use 'git checkout -b sky/{branch_name}' para criar nova branch."
                )

    # Executa o comando git (validações passaram)
    try:
        # Divide o comando em argumentos
        # Usa shlex para lidar com quotes e espaços corretamente
        import shlex
        args = shlex.split(command_normalized)

        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,  # Não levanta exceção, vamos verificar returncode
            timeout=30,
        )

        # Verifica se o comando falhou
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Erro desconhecido"
            return Result.err(f"Git falhou (exit code {result.returncode}): {error_msg}")

        # Sucesso
        return Result.ok(result.stdout or result.stderr or "Comando executado")

    except subprocess.TimeoutExpired:
        return Result.err("Timeout ao executar comando git (>30s)")
    except FileNotFoundError:
        return Result.err("Git não encontrado no sistema")
    except Exception as e:
        return Result.err(f"Erro ao executar comando git: {str(e)}")


# =============================================================================
# CUSTOM TOOL DECORADA COM @tool (claude-agent-sdk)
# =============================================================================

# Import do SDK para custom tools
SDK_AVAILABLE = False
tool = None
create_sdk_mcp_server = None

try:
    from claude_agent_sdk import tool, create_sdk_mcp_server
    SDK_AVAILABLE = True
except ImportError:
    pass


if SDK_AVAILABLE and tool is not None:

    @tool(
        "safe_git",
        "Executa comandos git de forma segura em worktrees de agentes",
        {"command": str, "cwd": str}
    )
    async def safe_git_tool(args: dict[str, Any]) -> dict[str, Any]:
        """
        Custom tool @tool para safe_git - compatível com claude-agent-sdk.

        Regras:
            1. Apenas branches com prefixo sky/* ou sky-test/*
            2. Bloqueia checkout de branches existentes
            3. Bloqueia comandos destrutivos (reset --hard, clean, restore)
            4. Permite: commit, push, status, worktree add

        Args:
            args: Dict com 'command' (comando git) e 'cwd' (diretório de trabalho)

        Returns:
            Dict com content para MCP response

        Example:
            >>> result = await safe_git_tool({
            ...     "command": "git checkout -b sky/test-branch",
            ...     "cwd": "/path/to/worktree"
            ... })
        """
        command = args.get("command", "")
        cwd = args.get("cwd", "")

        result = safe_git(command, cwd)

        if result.is_ok:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": result.value,
                    }
                ]
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Erro: {result.error}",
                    }
                ]
            }


def create_safe_git_mcp_server() -> Any:
    """
    Cria servidor MCP SDK com tool safe_git.

    Returns:
        McpSdkServerConfig com safe_git registrada ou None se SDK não disponível
    """
    if not SDK_AVAILABLE or create_sdk_mcp_server is None:
        return None

    return create_sdk_mcp_server(
        name="safe_git",
        version="1.0.0",
        tools=[safe_git_tool]
    )


__all__ = ["safe_git", "safe_git_tool", "create_safe_git_mcp_server"]
