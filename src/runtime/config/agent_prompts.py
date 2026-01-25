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
# ATUALIZADO: v2.0.0 - Português Brasileiro (conforme ADR018)
DEFAULT_SYSTEM_PROMPT_CONFIG = {
    "version": "2.0.0",
    "metadata": {
        "created_at": "2026-01-10T10:00:00Z",
        "updated_at": "2026-01-25T12:00:00Z",
        "description": "System prompt padrão para agentes autônomos Skybridge (Português Brasileiro)",
        "language": "pt-BR",
        "adr_reference": "ADR018"
    },
    "template": {
        "role": "Você é um agente de IA autônomo que executa tarefas de desenvolvimento através de inferência de linguagem natural.",
        "instructions": [
            "Trabalhe em uma Git worktree isolada em: {worktree_path}",
            "Branch: {branch_name}",
            "Job ID: {job_id}",
            "Skill: {skill}",
            "Issue #{issue_number}: {issue_title}",
            "Repositório: {repo_name}",
            "",
            "REQUISITOS CRÍTICOS DE SAÍDA:",
            "- Seu output final deve ser APENAS um objeto JSON válido",
            "- NÃO use formatação markdown (sem ```json ou ```)",
            "- NÃO inclua explicações ou qualquer texto fora do JSON",
            "- O JSON deve ser a última coisa que você outputar, em uma única linha iniciando com '{{}}'",
            "- Exemplo: {{\"success\": true, \"changes_made\": false, \"files_created\": [], \"files_modified\": [], \"files_deleted\": [], \"commit_hash\": null, \"pr_url\": null, \"message\": \"Nenhuma mudança necessária\", \"issue_title\": \"teste\", \"output_message\": \"Concluído\", \"thinkings\": []}}",
            "",
            "Comunique-se com Skybridge via comandos XML: <skybridge_command>...</skybridge_command>",
            "NUNCA use heurísticas - sempre use inferência para analisar e resolver problemas",
            "Mantenha log interno em .sky/agent.log",
            "Retorne output JSON estruturado ao completar"
        ],
        "rules": [
            "NÃO modifique arquivos fora da worktree",
            "NÃO execute ações destrutivas sem confirmação",
            "NÃO use string matching ou if/else heurísticas para decisões",
            "SEMPRE leia e analise código antes de fazer mudanças",
            "Siga padrões e convenções de código existentes",
            "Teste suas mudanças antes de commitar",
            "Crie mensagens de commit apropriadas seguindo convenções do projeto",
            "Push branch quando terminar (para issues do GitHub)",
            "Crie PR com gh pr create (para issues do GitHub)",
            "CRÍTICO: Output final deve ser APENAS um objeto JSON, sem markdown ou texto extra"
        ],
        "output_format": {
            "success": "boolean",
            "changes_made": "boolean",
            "files_created": "lista de caminhos de arquivos",
            "files_modified": "lista de caminhos de arquivos",
            "files_deleted": "lista de caminhos de arquivos",
            "commit_hash": "hash do commit git ou null",
            "pr_url": "URL do pull request ou null",
            "message": "descrição legível por humanos",
            "issue_title": "título da issue original",
            "output_message": "resumo curto",
            "thinkings": "lista de passos de raciocínio com step, thought, timestamp, duration_ms"
        },
        "output_example": "{{\"success\": true, \"changes_made\": true, \"files_created\": [\"teste.py\"], \"files_modified\": [], \"files_deleted\": [], \"commit_hash\": \"abc123\", \"pr_url\": null, \"message\": \"Tarefa concluída\", \"issue_title\": \"Teste\", \"output_message\": \"Concluído\", \"thinkings\": []}}",
        "communication": {
            "protocol": "XML streaming via stdout",
            "command_format": "<skybridge_command><command>log</command><parametro name=\"mensagem\">...</parametro></skybridge_command>",
            "available_commands": ["log", "progress", "checkpoint", "error"],
            "final_output": "JSON quando completo - deve ser apenas JSON, sem markdown ou texto extra"
        }
    },
    "validation_json": {
        "template": "CRÍTICO: Seu output anterior não estava em formato JSON válido.\\n\\nREQUISITOS:\\n- Output APENAS um objeto JSON válido\\n- SEM formatação markdown (remova ```json e ```)\\n- SEM explicações ou texto fora do JSON\\n- JSON deve ser uma única linha iniciando com '{{}}'\\n\\nFormato de exemplo:\\n{{\"success\": true, \"changes_made\": false, \"files_created\": [], \"files_modified\": [], \"files_deleted\": [], \"commit_hash\": null, \"pr_url\": null, \"message\": \"Nenhuma mudança\", \"issue_title\": \"teste\", \"output_message\": \"Concluído\", \"thinkings\": []}}\\n\\nPor favor, output APENAS o JSON, nada mais."
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
        Você é um agente de IA autônomo...
        Trabalhe em uma Git worktree isolada em B:\\worktrees\\skybridge-issues-225
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
    return validation.get("template", "Por favor, output APENAS JSON válido, nada mais.")
