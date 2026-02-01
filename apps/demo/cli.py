# -*- coding: utf-8 -*-
"""
Demo CLI — Interface de linha de comando para o Demo Engine.

Fachada para executar demonstrações do Skybridge via CLI.

Uso:
    python -m apps.demo.cli list
    python -m apps.demo.cli run trello-flow
    python -m apps.demo.cli info trello-flow
    python -m apps.demo.cli menu
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Adiciona src ao path - ANTES dos imports
_repo_root = Path(__file__).parent.parent.parent
_src_path = _repo_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from runtime.observability.logger import Colors, get_logger, print_separator


async def cmd_list(args: list[str]) -> int:
    """
    Lista todas as demos disponíveis.

    Uso:
        python -m apps.demo.cli list [--category <cat>] [--flow <flow>]
    """
    from runtime.demo.engine import get_demo_engine

    engine = get_demo_engine()

    # Parse args simples
    category = None
    flow_type = None

    i = 0
    while i < len(args):
        if args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == "--flow" and i + 1 < len(args):
            flow_type = args[i + 1]
            i += 2
        else:
            i += 1

    if flow_type:
        # Lista por fluxo
        demos = await engine.list_by_flow_type(flow_type)

        print()
        print_separator("=", 80)
        print(f"{Colors.CYAN}📋 Demos - Fluxo: {flow_type}{Colors.RESET}")
        print_separator("=", 80)

        if demos:
            for demo in demos:
                print(f"\n  {Colors.WHITE}{demo['id']}{Colors.RESET} - {demo['name']}")
                print(f"      {demo['description']}")
                print(f"      Categoria: {demo['category']}")
        else:
            print(f"\n{Colors.YELLOW}Nenhuma demo encontrada para este fluxo{Colors.RESET}")

    elif category:
        # Lista por categoria
        catalog = await engine.list_available()
        demos = catalog.get(category, [])

        print()
        print_separator("=", 80)
        print(f"{Colors.CYAN}📋 Demos - Categoria: {category.upper()}{Colors.RESET}")
        print_separator("=", 80)

        if demos:
            for demo in demos:
                print(f"\n  {Colors.WHITE}{demo['id']}{Colors.RESET} - {demo['name']}")
                print(f"      {demo['description']}")
                print(f"      Duração: ~{demo['estimated_duration']}s")
        else:
            print(f"\n{Colors.YELLOW}Nenhuma demo encontrada nesta categoria{Colors.RESET}")

    else:
        # Lista todas
        catalog = await engine.list_available()

        print()
        print_separator("=", 80)
        print(f"{Colors.CYAN}📋 TODAS AS DEMOS{Colors.RESET}")
        print_separator("=", 80)

        total = 0
        for cat, demos in catalog.items():
            if demos:
                print(f"\n{Colors.WHITE}{cat.upper()}{Colors.RESET}")
                for demo in demos:
                    total += 1
                    print(f"  {Colors.CYAN}{demo['id']}{Colors.RESET} - {demo['name']}")
                    tags_str = f" [{', '.join(demo['tags'])}]" if demo.get('tags') else ""
                    print(f"      {demo['description']}{tags_str}")

        print()
        print_separator("─", 80)
        print(f"{Colors.DIM}Total: {total} demos{Colors.RESET}")
        print_separator("─", 80)

    print()
    return 0


async def cmd_info(args: list[str]) -> int:
    """
    Mostra informações detalhadas de uma demo.

    Uso:
        python -m apps.demo.cli info <demo-id>
    """
    from runtime.demo.engine import get_demo_engine

    if not args:
        print(f"{Colors.ERROR}❌ Erro: especifique o ID da demo{Colors.RESET}")
        print(f"\nUso: python -m apps.demo.cli info <demo-id>")
        return 1

    demo_id = args[0]
    engine = get_demo_engine()
    info = await engine.get_demo_info(demo_id)

    if not info:
        print(f"{Colors.ERROR}❌ Demo não encontrada: {demo_id}{Colors.RESET}")
        return 1

    print()
    print_separator("=", 80)
    print(f"{Colors.CYAN}📋 {info['name']}{Colors.RESET}")
    print_separator("=", 80)

    print(f"\n{Colors.WHITE}ID:{Colors.RESET}         {info['id']}")
    print(f"{Colors.WHITE}Categoria:{Colors.RESET}   {info['category'].upper()}")
    print(f"{Colors.WHITE}Duração:{Colors.RESET}     ~{info['estimated_duration']}s")

    print(f"\n{Colors.WHITE}Descrição:{Colors.RESET}")
    print(f"  {info['description']}")

    if info.get('required_configs'):
        print(f"\n{Colors.WHITE}Configurações necessárias:{Colors.RESET}")
        for cfg in info['required_configs']:
            print(f"  • {cfg}")

    print(f"\n{Colors.WHITE}Fluxo:{Colors.RESET}")
    print(f"  {info['flow']}")

    print()
    return 0


async def cmd_run(args: list[str]) -> int:
    """
    Executa uma demo específica.

    Uso:
        python -m apps.demo.cli run <demo-id> [--param value]

    Exemplo:
        python -m apps.demo.cli run trello-flow
        python -m apps.demo.cli run github-real-flow --num-issues 3
    """
    from runtime.demo.engine import get_demo_engine

    if not args:
        print(f"{Colors.ERROR}❌ Erro: especifique o ID da demo{Colors.RESET}")
        print(f"\nUso: python -m apps.demo.cli run <demo-id> [--param value]")
        return 1

    demo_id = args[0]

    # Parse parâmetros simples (--key value)
    params = {}
    i = 1
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            key = args[i][2:].replace("-", "_")
            value = args[i + 1]
            # Tenta converter para int/float/bool
            if value.isdigit():
                value = int(value)
            elif value.replace(".", "").isdigit():
                value = float(value)
            elif value.lower() in ("true", "yes"):
                value = True
            elif value.lower() in ("false", "no"):
                value = False
            params[key] = value
            i += 2
        else:
            i += 1

    engine = get_demo_engine()
    result = await engine.run_demo(demo_id, params=params, verbose=True)

    # Resumo final
    print()
    print_separator("=", 80)
    if result["success"]:
        print(f"{Colors.INFO}✅ DEMO CONCLUÍDA{Colors.RESET}")
    else:
        print(f"{Colors.ERROR}❌ DEMO FALHOU{Colors.RESET}")
    print_separator("=", 80)

    print(f"\n🆔 Execução: {result['execution_id']}")
    print(f"⏱️  Duração: {result.get('execution_time_seconds', 0):.2f}s")

    if result.get('data'):
        print(f"\n📊 Dados retornados:")
        for key, value in result['data'].items():
            print(f"  • {key}: {value}")

    if result.get('log_file'):
        print(f"\n📄 Log completo: {result['log_file']}")

    print()

    return 0 if result["success"] else 1


async def cmd_menu(args: list[str]) -> int:
    """
    Exibe menu interativo de demos.

    Uso:
        python -m apps.demo.cli menu
    """
    from runtime.demo.engine import get_demo_engine

    engine = get_demo_engine()
    engine.print_menu()

    # Menu interativo simples
    from runtime.demo.registry import DemoRegistry

    print(f"{Colors.CYAN}Digite o ID da demo para executar (ou 'q' para sair):{Colors.RESET}")

    while True:
        choice = input(f"\n{Colors.WHITE}> {Colors.RESET}").strip()

        if choice.lower() in ('q', 'quit', 'exit', 'sair'):
            print(f"\n{Colors.DIM}Até logo! 👋{Colors.RESET}\n")
            break

        if not choice:
            continue

        demo_class = DemoRegistry.get(choice)
        if not demo_class:
            print(f"{Colors.ERROR}❌ Demo não encontrada: {choice}{Colors.RESET}")
            continue

        # Executa demo
        result = await engine.run_demo(choice, params={}, verbose=True)

        if result["success"]:
            print(f"\n{Colors.INFO}✅ {result['message']}{Colors.RESET}")
        else:
            print(f"\n{Colors.ERROR}❌ {result['message']}{Colors.RESET}")

        print(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
        input()

    return 0


async def cmd_stats(args: list[str]) -> int:
    """
    Mostra estatísticas das demos.

    Uso:
        python -m apps.demo.cli stats
    """
    from runtime.demo.engine import get_demo_engine

    engine = get_demo_engine()
    stats = engine.get_statistics()

    print()
    print_separator("=", 80)
    print(f"{Colors.CYAN}📊 ESTATÍSTICAS DAS DEMOS{Colors.RESET}")
    print_separator("=", 80)

    print(f"\n{Colors.WHITE}Total de demos:{Colors.RESET} {stats['total_demos']}")
    print(f"{Colors.WHITE}Duração média:{Colors.RESET} ~{stats['avg_duration']:.0f}s")
    print(f"{Colors.WHITE}Total de tags:{Colors.RESET} {stats['total_tags']}")

    print(f"\n{Colors.WHITE}Por categoria:{Colors.RESET}")
    for cat, count in stats['by_category'].items():
        if count > 0:
            print(f"  • {cat.upper()}: {count}")

    # Issue mapping
    from runtime.demo.registry import DemoRegistry

    issue_mapping = DemoRegistry.get_issue_mapping()
    if issue_mapping:
        print(f"\n{Colors.WHITE}Issues com demos:{Colors.RESET}")
        for issue, demo_ids in sorted(issue_mapping.items()):
            print(f"  • #{issue}: {', '.join(demo_ids)}")

    print()
    return 0


async def cmd_issues(args: list[str]) -> int:
    """
    Lista demos relacionadas a issues.

    Uso:
        python -m apps.demo.cli issues [--all]
        python -m apps.demo.cli issues <issue_number>
    """
    from runtime.demo.registry import DemoRegistry

    if "--all" in args:
        # Mostra todas as issues com demos
        issue_mapping = DemoRegistry.get_issue_mapping()

        print()
        print_separator("=", 80)
        print(f"{Colors.CYAN}📋 ISSUES COM DEMOS{Colors.RESET}")
        print_separator("=", 80)

        if issue_mapping:
            for issue, demo_ids in sorted(issue_mapping.items()):
                print(f"\n{Colors.WHITE}Issue #{issue}:{Colors.RESET}")
                for demo_id in demo_ids:
                    info = DemoRegistry.demo_info(demo_id)
                    if info:
                        print(f"  • {Colors.CYAN}{demo_id}{Colors.RESET} - {info['name']}")
        else:
            print(f"\n{Colors.YELLOW}Nenhuma issue com demos associadas{Colors.RESET}")

        print()
        return 0

    elif args and args[0].isdigit():
        # Mostra demos de uma issue específica
        issue_number = int(args[0])
        demos = DemoRegistry.list_by_issue(issue_number)

        print()
        print_separator("=", 80)
        print(f"{Colors.CYAN}📋 DEMOS PARA ISSUE #{issue_number}{Colors.RESET}")
        print_separator("=", 80)

        if demos:
            for demo_class in demos:
                print(f"\n{Colors.WHITE}{demo_class.demo_id}{Colors.RESET} - {demo_class.demo_name}")
                print(f"    {demo_class.description}")
        else:
            print(f"\n{Colors.YELLOW}Nenhuma demo encontrada para issue #{issue_number}{Colors.RESET}")

        print()
        return 0

    else:
        print(f"{Colors.ERROR}❌ Use --all ou especifique um número de issue{Colors.RESET}")
        return 1


async def cmd_diff(args: list[str]) -> int:
    """
    Compara snapshots de execuções de demos.

    Uso:
        python -m apps.demo.cli diff list <demo-id> [--exec <execution-id>]
        python -m apps.demo.cli diff show <diff-id>
        python -m apps.demo.cli diff compare <before-id> <after-id>

    Exemplos:
        python -m apps.demo.cli diff list trello-flow
        python -m apps.demo.cli diff list trello-flow --exec abc-123-def
        python -m apps.demo.cli diff show diff-abc123
        python -m apps.demo.cli diff compare snap-001 snap-002
    """
    import json
    from pathlib import Path

    if not args:
        print(f"{Colors.ERROR}❌ Erro: especifique uma sub-operação (list, show, compare){Colors.RESET}")
        print(f"\nUso: python -m apps.demo.cli diff <list|show|compare> [args]")
        return 1

    sub_command = args[0].lower()
    remaining_args = args[1:]

    # DOC: ADR024 - Usa workspace atual do contexto
    from runtime.config.config import get_workspace_logs_dir
    log_dir = get_workspace_logs_dir() / "demos"

    if sub_command == "list":
        # Lista snapshots de uma demo
        if not remaining_args:
            print(f"{Colors.ERROR}❌ Erro: especifique o ID da demo{Colors.RESET}")
            return 1

        demo_id = remaining_args[0]

        # Parse execution_id filter
        execution_id = None
        i = 1
        while i < len(remaining_args):
            if remaining_args[i] == "--exec" and i + 1 < len(remaining_args):
                execution_id = remaining_args[i + 1]
                i += 2
            else:
                i += 1

        print()
        print_separator("=", 80)
        print(f"{Colors.CYAN}📋 SNAPSHOTS - Demo: {demo_id}{Colors.RESET}")
        print_separator("=", 80)

        if execution_id:
            print(f"\n🆔 Execução: {execution_id}")

        # Busca arquivos de snapshot
        demo_dir = log_dir / demo_id
        if not demo_dir.exists():
            print(f"\n{Colors.YELLOW}Nenhuma execução encontrada para esta demo{Colors.RESET}")
            return 0

        snapshot_count = 0
        diff_count = 0

        for exec_dir in sorted(demo_dir.iterdir()):
            if not exec_dir.is_dir():
                continue

            # Filtra por execution_id se especificado
            if execution_id and exec_dir.name != execution_id:
                continue

            print(f"\n{Colors.WHITE}▸ {exec_dir.name}{Colors.RESET}")

            # Snapshots
            snap_dir = exec_dir / "snapshots"
            if snap_dir.exists():
                snapshots = list(snap_dir.glob("snapshot_*.json"))
                if snapshots:
                    print(f"  Snapshots:")
                    for snap_file in sorted(snapshots):
                        snapshot_count += 1
                        try:
                            with open(snap_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            subject = data.get("subject", "unknown")
                            target = data.get("target", "")[:30]
                            print(f"    • {Colors.CYAN}{snap_file.stem}{Colors.RESET} "
                                  f"[{subject}] {target}")
                        except Exception:
                            print(f"    • {snap_file.stem} {Colors.DIM}(erro ao ler){Colors.RESET}")

            # Diffs
            diff_dir = exec_dir / "diffs"
            if diff_dir.exists():
                diffs = list(diff_dir.glob("diff_*.json"))
                if diffs:
                    print(f"  Diffs:")
                    for diff_file in sorted(diffs):
                        diff_count += 1
                        try:
                            with open(diff_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            subject = data.get("subject", "unknown")
                            changes_count = len(data.get("changes", []))
                            print(f"    • {Colors.WARNING}{diff_file.stem}{Colors.RESET} "
                                  f"[{subject}] {changes_count} mudanças")
                        except Exception:
                            print(f"    • {diff_file.stem} {Colors.DIM}(erro ao ler){Colors.RESET}")

        print()
        print_separator("─", 80)
        print(f"{Colors.DIM}Snapshots encontrados: {snapshot_count} | Diffs encontrados: {diff_count}{Colors.RESET}")
        print_separator("─", 80)
        print()

        return 0

    elif sub_command == "show":
        # Mostra detalhes de um diff
        if not remaining_args:
            print(f"{Colors.ERROR}❌ Erro: especifique o ID do diff{Colors.RESET}")
            return 1

        diff_id = remaining_args[0]

        print()
        print_separator("=", 80)
        print(f"{Colors.CYAN}📋 DIFF: {diff_id}{Colors.RESET}")
        print_separator("=", 80)

        # Busca arquivo de diff
        diff_files = list(log_dir.rglob(f"{diff_id}.json"))

        if not diff_files:
            print(f"\n{Colors.YELLOW}Diff não encontrado{Colors.RESET}")
            return 0

        diff_file = diff_files[0]

        try:
            with open(diff_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"\n{Colors.WHITE}Arquivo:{Colors.RESET} {diff_file.relative_to(log_dir)}")
            print(f"{Colors.WHITE}Subject:{Colors.RESET} {data.get('subject', 'unknown')}")
            print(f"{Colors.WHITE}Before ID:{Colors.RESET} {data.get('before_snapshot_id', 'N/A')}")
            print(f"{Colors.WHITE}After ID:{Colors.RESET} {data.get('after_snapshot_id', 'N/A')}")
            print(f"{Colors.WHITE}Timestamp:{Colors.RESET} {data.get('timestamp', 'N/A')}")

            changes = data.get("changes", [])
            print(f"\n{Colors.WHITE}Mudanças ({len(changes)}):{Colors.RESET}")

            if not changes:
                print(f"  {Colors.DIM}Nenhuma mudança detectada{Colors.RESET}")
            else:
                for i, change in enumerate(changes, 1):
                    change_type = change.get("type", "UNKNOWN")
                    subject = change.get("subject", "unknown")
                    description = change.get("description", "")

                    # Cores por tipo de mudança
                    type_colors = {
                        "ADDED": Colors.GREEN,
                        "REMOVED": Colors.ERROR,
                        "MODIFIED": Colors.WARNING,
                        "MOVED": Colors.INFO,
                    }
                    color = type_colors.get(change_type, Colors.RESET)

                    print(f"\n  {i}. {color}[{change_type}]{Colors.RESET} {subject}")
                    if description:
                        print(f"     {description}")

                    # Detalhes adicionais
                    details = change.get("details", {})
                    if details:
                        for key, value in details.items():
                            print(f"     • {key}: {value}")

        except Exception as e:
            print(f"\n{Colors.ERROR}Erro ao ler diff: {e}{Colors.RESET}")
            return 1

        print()
        return 0

    elif sub_command == "compare":
        # Compara dois snapshots diretamente
        if len(remaining_args) < 2:
            print(f"{Colors.ERROR}❌ Erro: especifique before_id e after_id{Colors.RESET}")
            return 1

        before_id = remaining_args[0]
        after_id = remaining_args[1]

        print()
        print_separator("=", 80)
        print(f"{Colors.CYAN}📋 COMPARANDO SNAPSHOTS{Colors.RESET}")
        print_separator("=", 80)

        # Busca arquivos
        before_files = list(log_dir.rglob(f"{before_id}.json"))
        after_files = list(log_dir.rglob(f"{after_id}.json"))

        if not before_files:
            print(f"\n{Colors.ERROR}❌ Snapshot 'before' não encontrado: {before_id}{Colors.RESET}")
            return 1

        if not after_files:
            print(f"\n{Colors.ERROR}❌ Snapshot 'after' não encontrado: {after_id}{Colors.RESET}")
            return 1

        print(f"\n{Colors.WHITE}Before:{Colors.RESET} {before_files[0].relative_to(log_dir)}")
        print(f"{Colors.WHITE}After:{Colors.RESET} {after_files[0].relative_to(log_dir)}")

        # Lê snapshots
        try:
            with open(before_files[0], "r", encoding="utf-8") as f:
                before_data = json.load(f)
            with open(after_files[0], "r", encoding="utf-8") as f:
                after_data = json.load(f)

            print(f"\n{Colors.WHITE}Subject:{Colors.RESET} {before_data.get('subject', 'unknown')}")

            # Comparação simples baseada em subject
            if before_data.get("subject") == "trello":
                _compare_trello_snapshots(before_data, after_data)
            else:
                print(f"\n{Colors.DIM}Comparação genérica:{Colors.RESET}")
                print(f"  Before timestamp: {before_data.get('captured_at')}")
                print(f"  After timestamp: {after_data.get('captured_at')}")

        except Exception as e:
            print(f"\n{Colors.ERROR}Erro ao comparar: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
            return 1

        print()
        return 0

    else:
        print(f"{Colors.ERROR}❌ Sub-comando desconhecido: {sub_command}{Colors.RESET}")
        print(f"\nUse: list, show, ou compare")
        return 1


def _compare_trello_snapshots(before: dict, after: dict) -> None:
    """Compara dois snapshots do Trello e mostra diferenças."""
    from runtime.observability.snapshot.extractors.trello_extractor import TrelloExtractor

    # Cria snapshots fictícios para comparação
    from runtime.observability.snapshot.models import Snapshot

    before_snap = Snapshot(
        id=before.get("snapshot_id", "unknown"),
        subject="trello",
        target=before.get("target", ""),
        timestamp=before.get("captured_at", ""),
        data=before.get("data", {}),
    )

    after_snap = Snapshot(
        id=after.get("snapshot_id", "unknown"),
        subject="trello",
        target=after.get("target", ""),
        timestamp=after.get("captured_at", ""),
        data=after.get("data", {}),
    )

    # Usa extractor para comparar
    extractor = TrelloExtractor("", "")
    diff = extractor.compare(before_snap, after_snap)

    print(f"\n{Colors.WHITE}Cards:{Colors.RESET} {len(before.get('data', {}).get('cards', []))} → "
          f"{len(after.get('data', {}).get('cards', []))}")

    if diff.changes:
        print(f"\n{Colors.WHITE}Mudanças:{Colors.RESET}")
        for change in diff.changes:
            change_type = change.get("type", "UNKNOWN")
            subject = change.get("subject", "")
            desc = change.get("description", "")

            type_colors = {
                "ADDED": Colors.GREEN,
                "REMOVED": Colors.ERROR,
                "MODIFIED": Colors.WARNING,
                "MOVED": Colors.INFO,
            }
            color = type_colors.get(change_type, Colors.RESET)

            print(f"  {color}[{change_type}]{Colors.RESET} {desc or subject}")
    else:
        print(f"\n  {Colors.DIM}Nenhuma mudança detectada{Colors.RESET}")


async def main() -> int:
    """Função principal da CLI."""
    import os
    from dotenv import load_dotenv

    # Carrega .env
    load_dotenv()

    if len(sys.argv) < 2:
        _print_usage()
        return 1

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    commands = {
        "list": cmd_list,
        "ls": cmd_list,
        "info": cmd_info,
        "run": cmd_run,
        "menu": cmd_menu,
        "stats": cmd_stats,
        "issues": cmd_issues,
        "diff": cmd_diff,
    }

    if command not in commands:
        print(f"{Colors.ERROR}❌ Comando desconhecido: {command}{Colors.RESET}")
        _print_usage()
        return 1

    try:
        return await commands[command](args)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Interrupido pelo usuário{Colors.RESET}")
        return 130
    except Exception as e:
        print(f"\n{Colors.ERROR}❌ Erro: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return 1


def _print_usage() -> None:
    """Imprime usage da CLI."""
    print()
    print_separator("=", 80)
    print(f"{Colors.CYAN}🎯 SKYBRIDGE - DEMO CLI{Colors.RESET}")
    print_separator("=", 80)
    print()
    print(f"{Colors.WHITE}Uso:{Colors.RESET}")
    print(f"  python -m apps.demo.cli <command> [args]")
    print()
    print(f"{Colors.WHITE}Comandos:{Colors.RESET}")
    print(f"  {Colors.CYAN}list{Colors.RESET}        Lista todas as demos disponíveis")
    print(f"  {Colors.CYAN}info <id>{Colors.RESET}   Mostra informações detalhadas")
    print(f"  {Colors.CYAN}run <id>{Colors.RESET}    Executa uma demo específica")
    print(f"  {Colors.CYAN}menu{Colors.RESET}        Exibe menu interativo")
    print(f"  {Colors.CYAN}stats{Colors.RESET}       Mostra estatísticas")
    print(f"  {Colors.CYAN}issues{Colors.RESET}      Lista demos por issue")
    print(f"  {Colors.CYAN}diff{Colors.RESET}        Compara snapshots de execuções")
    print()
    print(f"{Colors.WHITE}Opções:{Colors.RESET}")
    print(f"  {Colors.CYAN}--category <cat>{Colors.RESET}   Filtra por categoria")
    print(f"  {Colors.CYAN}--flow <type>{Colors.RESET}      Filtra por tipo de fluxo")
    print()
    print(f"{Colors.WHITE}Exemplos:{Colors.RESET}")
    print(f"  python -m apps.demo.cli list")
    print(f"  python -m apps.demo.cli list --category trello")
    print(f"  python -m apps.demo.cli info trello-flow")
    print(f"  python -m apps.demo.cli run trello-flow")
    print(f"  python -m apps.demo.cli run github-flow --num-issues 3")
    print(f"  python -m apps.demo.cli issues --all")
    print(f"  python -m apps.demo.cli issues 38")
    print(f"  python -m apps.demo.cli diff list trello-flow")
    print(f"  python -m apps.demo.cli diff show diff-abc123")
    print(f"  python -m apps.demo.cli diff compare snap-001 snap-002")
    print()
    print_separator("=", 80)
    print()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
