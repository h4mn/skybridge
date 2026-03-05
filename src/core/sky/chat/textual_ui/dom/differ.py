# coding: utf-8
"""
Diff de estado - Comparação entre estados de widgets.

Algoritmo customizado para comparar dicts, listas, dataclasses e primitivos.
"""

from dataclasses import asdict, is_dataclass
from typing import Any


def diff_state(old: Any, new: Any, path: str = "") -> dict[str, dict[str, Any]]:
    """
    Compara dois valores e retorna as diferenças.

    Args:
        old: Valor antigo
        new: Valor novo
        path: Caminho atual (para recursão)

    Returns:
        Dict com diffs no formato {path: {"old": ..., "new": ...}}
    """
    # Casos especiais
    if old == new:
        return {}

    # Ambos são dicts
    if isinstance(old, dict) and isinstance(new, dict):
        return _diff_dicts(old, new, path)

    # Ambos são sequências (list/tuple)
    if isinstance(old, (list, tuple)) and isinstance(new, (list, tuple)):
        return _diff_sequences(old, new, path)

    # Dataclasses
    if is_dataclass(old) and is_dataclass(new):
        return _diff_dataclass(old, new, path)

    # Primitivos diferentes ou tipos incompatíveis
    return {path: {"old": old, "new": new}}


def _diff_dicts(
    old: dict, new: dict, path: str
) -> dict[str, dict[str, Any]]:
    """Diff entre dois dicts."""
    result = {}
    all_keys = set(old.keys()) | set(new.keys())

    for key in all_keys:
        key_path = f"{path}.{key}" if path else key
        old_val = old.get(key)
        new_val = new.get(key)

        # Key removida
        if key not in new:
            result[key_path] = {"old": old_val, "new": None}
        # Key adicionada
        elif key not in old:
            result[key_path] = {"old": None, "new": new_val}
        # Key em ambos - diff recursivo
        else:
            nested = diff_state(old_val, new_val, key_path)
            result.update(nested)

    return result


def _diff_sequences(
    old: list | tuple, new: list | tuple, path: str
) -> dict[str, dict[str, Any]]:
    """Diff entre duas sequências."""
    result = {}

    # Comparar até o menor tamanho
    min_len = min(len(old), len(new))
    for i in range(min_len):
        elem_path = f"{path}[{i}]"
        nested = diff_state(old[i], new[i], elem_path)
        result.update(nested)

    # Elements removidos (old mais longo)
    for i in range(min_len, len(old)):
        elem_path = f"{path}[{i}]"
        result[elem_path] = {"old": old[i], "new": None}

    # Elements adicionados (new mais longo)
    for i in range(min_len, len(new)):
        elem_path = f"{path}[{i}]"
        result[elem_path] = {"old": None, "new": new[i]}

    return result


def _diff_dataclass(old: Any, new: Any, path: str) -> dict[str, dict[str, Any]]:
    """Diff entre duas dataclasses."""
    old_dict = asdict(old)
    new_dict = asdict(new)
    return _diff_dicts(old_dict, new_dict, path)


def format_diff(diff: dict[str, dict[str, Any]]) -> str:
    """
    Formata diff para exibição com cores.

    Args:
        diff: Dict de diffs

    Returns:
        String formatada
    """
    if not diff:
        return "(sem mudanças)"

    lines = []
    for path, change in diff.items():
        old_val = change.get("old")
        new_val = change.get("new")

        if old_val is None:
            lines.append(f"[green]+ {path} = {new_val}[/]")
        elif new_val is None:
            lines.append(f"[red]- {path} = {old_val}[/]")
        else:
            lines.append(f"[yellow]~ {path}[/]")
            lines.append(f"    [red]  - {old_val}[/]")
            lines.append(f"    [green]  + {new_val}[/]")

    return "\n".join(lines)


__all__ = ["diff_state", "format_diff"]
