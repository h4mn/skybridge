#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar worktree de teste para desenvolver/testar agentes localmente.

DOC: PLAN.md Fase 5 - Script para Testes Locais

Uso:
    python scripts/create_test_agent.py --name hello-world --issue 999
    python scripts/create_test_agent.py --name bugfix --issue 123 --from-branch dev

Cria:
    - Worktree em B:/_repositorios/skybridge-auto/test/{name}/
    - Branch com prefixo sky-test/{name}-{timestamp}
    - Arquivo .sky/test-config.json com metadados

Convenções:
    - Prefixo sky-test/* para worktrees de desenvolvimento/teste
    - Útil para testar agentes localmente antes de integrar na branch auto
"""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


def create_test_worktree(
    name: str,
    issue_number: int,
    from_branch: str = "auto"
) -> tuple[str, str]:
    """
    Cria worktree de teste para desenvolvimento de agente.

    Args:
        name: Nome do teste (ex: hello-world, bugfix)
        issue_number: Número da issue associada (para metadados)
        from_branch: Branch base (default: auto)

    Returns:
        Tupla (worktree_path, branch_name) ou levanta RuntimeError

    Raises:
        RuntimeError: Se git worktree add falhar
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"sky-test/{name}-{timestamp}"
    worktree_path = f"B:/_repositorios/skybridge-auto/test/{name}"

    try:
        # Cria worktree
        result = subprocess.run(
            [
                "git", "worktree", "add",
                worktree_path,
                "-b", branch_name,
                from_branch
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        print(f"✓ Worktree criada: {worktree_path}")
        print(f"✓ Branch: {branch_name}")

        # Cria diretório .sky
        config_path = Path(worktree_path) / ".sky"
        config_path.mkdir(parents=True, exist_ok=True)

        # Cria config de teste
        test_config = {
            "test_name": name,
            "issue_number": issue_number,
            "branch": branch_name,
            "from_branch": from_branch,
            "created_at": datetime.now().isoformat(),
        }

        config_file = config_path / "test-config.json"
        config_file.write_text(json.dumps(test_config, indent=2), encoding="utf-8")

        print(f"✓ Config criado: {config_file}")
        print(f"\n  Para usar: cd {worktree_path}")

        return worktree_path, branch_name

    except subprocess.CalledProcessError as e:
        error_msg = f"Falha ao criar worktree: {e.stderr}\nReturn code: {e.returncode}"
        raise RuntimeError(error_msg) from e
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timeout ao criar worktree (>30s)") from None


def list_test_worktrees() -> list[str]:
    """
    Lista worktrees de teste existentes.

    Returns:
        Lista de caminhos de worktrees que começam com sky-test/
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        worktrees = []
        current_path = None
        current_branch = None

        for line in result.stdout.split("\n"):
            if line.startswith("worktree "):
                current_path = line[9:]
            elif line.startswith("branch "):
                current_branch = line[7:]
                if current_branch and current_branch.startswith("refs/heads/sky-test/"):
                    worktrees.append(current_path)

        return worktrees

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []


def remove_test_worktree(name: str) -> bool:
    """
    Remove worktree de teste pelo nome.

    Args:
        name: Nome do teste (ex: hello-world)

    Returns:
        True se removido com sucesso, False caso contrário
    """
    worktree_path = f"B:/_repositorios/skybridge-auto/test/{name}"

    try:
        # Remove worktree
        subprocess.run(
            ["git", "worktree", "remove", worktree_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        print(f"✓ Worktree removida: {worktree_path}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Falha ao remover worktree: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("✗ Timeout ao remover worktree")
        return False


def main():
    """Função principal para CLI."""
    parser = argparse.ArgumentParser(
        description="Criar worktree de teste para desenvolvimento de agente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Cria worktree de teste hello-world
  python scripts/create_test_agent.py --name hello-world --issue 999

  # Cria worktree a partir de dev em vez de auto
  python scripts/create_test_agent.py --name bugfix --issue 123 --from-branch dev

  # Lista worktrees de teste existentes
  python scripts/create_test_agent.py --list

  # Remove worktree de teste
  python scripts/create_test_agent.py --remove hello-world
        """
    )

    parser.add_argument("--name", help="Nome do teste (ex: hello-world)")
    parser.add_argument("--issue", type=int, help="Número da issue associada")
    parser.add_argument(
        "--from-branch",
        default="auto",
        help="Branch base (default: auto)"
    )
    parser.add_argument("--list", action="store_true", help="Listar worktrees de teste")
    parser.add_argument("--remove", help="Remover worktree de teste pelo nome")

    args = parser.parse_args()

    # Modo: listar worktrees
    if args.list:
        worktrees = list_test_worktrees()
        if worktrees:
            print("Worktrees de teste existentes:")
            for wt in worktrees:
                print(f"  - {wt}")
        else:
            print("Nenhuma worktree de teste encontrada.")
        return

    # Modo: remover worktree
    if args.remove:
        if remove_test_worktree(args.remove):
            print(f"Worktree '{args.remove}' removida com sucesso.")
        else:
            print(f"Falha ao remover worktree '{args.remove}'.")
            return 1
        return

    # Modo: criar worktree (requer --name e --issue)
    if not args.name or not args.issue:
        parser.error("--create requires --name and --issue")

    try:
        worktree_path, branch_name = create_test_worktree(
            args.name,
            args.issue,
            args.from_branch
        )
        print(f"\nPronto! Worktree criada em: {worktree_path}")
        print(f"Branch: {branch_name}")
        return 0

    except RuntimeError as e:
        print(f"\nErro: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
