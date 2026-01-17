# -*- coding: utf-8 -*-
"""
Agent Prompts — System prompts como fonte da verdade em JSON.

Este módulo gerencia system prompts para agentes AI usando JSON como fonte
da verdade, conforme SPEC008 seção 7.

System prompts são ENTIDADES que evoluem com o projeto.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Caminho para o arquivo de configuração JSON (fonte da verdade)
_SYSTEM_PROMPT_JSON_PATH = Path(__file__).parent / "system_prompt.json"


# Configuração padrão de fábrica (fallback caso JSON não exista)
DEFAULT_SYSTEM_PROMPT_CONFIG = {
    "version": "1.0.0",
    "metadata": {
        "created_at": "2026-01-10T10:00:00Z",
        "updated_at": "2026-01-10T10:00:00Z",
        "description": "System prompt padrão para agentes autônomos"
    },
    "template": {
        "role": "You are an autonomous AI agent that executes development tasks through natural language inference.",
        "instructions": [
            "Work in an isolated Git worktree at {worktree_path}",
            "Communicate with Skybridge via XML commands: <skybridge_command>...</skybridge_command>",
            "NEVER use heuristics - always use inference to analyze and solve problems",
            "Maintain internal log at .sky/agent.log",
            "Return structured JSON output upon completion"
        ],
        "rules": [
            "DO NOT modify files outside the worktree",
            "DO NOT execute destructive actions without confirmation",
            "DO NOT use string matching or if/else heuristics for decisions",
            "ALWAYS read and analyze code before making changes"
        ],
        "output_format": {
            "success": "boolean",
            "files_created": "list of paths",
            "files_modified": "list of paths",
            "files_deleted": "list of paths",
            "thinkings": "list of reasoning steps"
        }
    }
}


def load_system_prompt_config() -> dict[str, Any]:
    """
    Carrega configuração de system prompt do JSON (fonte da verdade).

    Conforme SPEC008 seção 7, o JSON é a fonte da verdade para system prompts.

    Returns:
        Dicionário com a configuração do system prompt

    Raises:
        FileNotFoundError: Se o arquivo JSON não existir
        json.JSONDecodeError: Se o JSON for inválido
    """
    if not _SYSTEM_PROMPT_JSON_PATH.exists():
        # Cria arquivo padrão se não existir
        save_system_prompt_config(DEFAULT_SYSTEM_PROMPT_CONFIG)
        return DEFAULT_SYSTEM_PROMPT_CONFIG.copy()

    with open(_SYSTEM_PROMPT_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def render_system_prompt(config: dict[str, Any], context: dict[str, Any]) -> str:
    """
    Renderiza template de system prompt com variáveis injetadas.

    Args:
        config: Configuração carregada do JSON (fonte da verdade)
        context: Dicionário com valores para substituição (worktree_path, issue_number, etc)

    Returns:
        System prompt renderizado pronto para uso

    Example:
        >>> config = load_system_prompt_config()
        >>> context = {"worktree_path": "B:\\\\worktrees\\skybridge-issues-225", "issue_number": 225}
        >>> prompt = render_system_prompt(config, context)
        >>> print(prompt)
        You are an autonomous AI agent...
        Work in an isolated Git worktree at B:\\worktrees\\skybridge-issues-225
        ...
    """
    template = config.get("template", {})

    # Extrai componentes do template
    role = template.get("role", "")
    instructions = template.get("instructions", [])
    rules = template.get("rules", [])

    # Constrói o prompt
    parts = [role, ""]

    if instructions:
        parts.append("INSTRUCTIONS:")
        for instruction in instructions:
            # Substitui variáveis {var} pelo contexto
            formatted = _format_with_context(instruction, context)
            parts.append(f"- {formatted}")
        parts.append("")

    if rules:
        parts.append("RULES:")
        for rule in rules:
            # Substitui variáveis {var} pelo contexto
            formatted = _format_with_context(rule, context)
            parts.append(f"- {formatted}")
        parts.append("")

    parts.append("OUTPUT FORMAT:")
    output_format = template.get("output_format", {})
    for key, value in output_format.items():
        parts.append(f"- {key}: {value}")

    return "\n".join(parts)


def _format_with_context(text: str, context: dict[str, Any]) -> str:
    """
    Formata texto substituindo placeholders {var} pelo contexto.

    Args:
        text: Texto com placeholders {variavel}
        context: Dicionário com valores

    Returns:
        Texto formatado
    """
    try:
        return text.format(**context)
    except KeyError as e:
        # Placeholder não encontrado no contexto - retorna original
        return text


def save_system_prompt_config(config: dict[str, Any]) -> None:
    """
    Salva configuração de system prompt no JSON (fonte da verdade).

    Args:
        config: Nova configuração a ser salva

    Note:
        Sobrescreve system_prompt.json
    """
    with open(_SYSTEM_PROMPT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def reset_to_default_prompt() -> None:
    """
    Reseta configuração para o padrão de fábrica.

    Note:
        Restaura system_prompt.json para a configuração padrão
    """
    save_system_prompt_config(DEFAULT_SYSTEM_PROMPT_CONFIG.copy())


# Funções legadas para compatibilidade (obsoletas, usar load/save acima)
def get_system_prompt_template() -> str:
    """
    [OBSOLETO] Use load_system_prompt_config() e render_system_prompt().

    Mantido para compatibilidade com código existente.
    """
    config = load_system_prompt_config()
    # Retorna template como string para compatibilidade
    return json.dumps(config, indent=2)


def save_custom_prompt(template: str) -> None:
    """
    [OBSOLETO] Use save_system_prompt_config() com dict.

    Mantido para compatibilidade com código existente.
    """
    # Tenta fazer parse do template string para JSON
    try:
        config = json.loads(template)
        save_system_prompt_config(config)
    except json.JSONDecodeError:
        # Se não for JSON, cria config mínima
        config = DEFAULT_SYSTEM_PROMPT_CONFIG.copy()
        config["template"]["role"] = template
        save_system_prompt_config(config)


def get_json_validation_prompt() -> str:
    """
    Retorna o prompt de validação JSON.

    Usado quando o agente não retorna JSON válido, para solicitar correção.

    Returns:
        Prompt de validação JSON como string.
    """
    config = load_system_prompt_config()
    validation = config.get("validation_json", {})
    return validation.get("template", "Please output ONLY valid JSON, nothing else.")
