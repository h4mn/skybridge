#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Limpeza - PRD021: Refatoração de Prompts e Skills

Remove arquivos antigos após migração bem-sucedida para não deixar bagunça.

⚠️  AVISO: Execute APENAS após validar que a migração foi bem-sucedida!
"""

from pathlib import Path
import sys

def cleanup_old_files(dry_run=True):
    """
    Remove arquivos antigos da estrutura de prompts/skills.

    Args:
        dry_run: Se True, apenas mostra o que seria removido (não remove nada)
    """
    project_root = Path(__file__).parent.parent

    # Arquivos e diretórios a remover
    items_to_remove = [
        # Plugin antigo (toda a estrutura)
        "plugins/skybridge-workflows/",

        # Arquivos de backup temporários
        "src/runtime/config/system_prompt.json.bak",
        "src/runtime/config/system_prompt.json.bak2",
        "src/runtime/config/agent_prompts.py.bak",

        # Arquivo .bak criado anteriormente
        "src/runtime/config/system_prompt.json.bak",
    ]

    print("=" * 60)
    print("🧹 LIMPEZA DE ARQUIVOS ANTIGOS - PRD020")
    print("=" * 60)
    print()

    if dry_run:
        print("⚠️  MODO DRY RUN (nada será removido)")
        print("   Execute com --force para realmente remover")
        print()

    removed_count = 0
    kept_count = 0

    for item in items_to_remove:
        item_path = project_root / item

        if not item_path.exists():
            print(f"⏭️  IGNORADO (não existe): {item}")
            kept_count += 1
            continue

        # Verifica se é diretório ou arquivo
        is_dir = item_path.is_dir()
        item_type = "diretório" if is_dir else "arquivo"
        item_emoji = "📁" if is_dir else "📄"

        # Pergunta em modo interativo (se não for dry_run)
        if not dry_run:
            response = input(f"Remover {item_type} {item_path}? [y/N]: ")
            if response.lower() != 'y':
                print(f"⏭️  MANTIDO: {item}")
                kept_count += 1
                continue

        # Remove
        if is_dir:
            import shutil
            try:
                shutil.rmtree(item_path)
                print(f"✅ REMOVIDO {item_emoji}: {item}")
                removed_count += 1
            except Exception as e:
                print(f"❌ ERRO ao remover {item}: {e}")
        else:
            try:
                item_path.unlink()
                print(f"✅ REMOVIDO {item_emoji}: {item}")
                removed_count += 1
            except Exception as e:
                print(f"❌ ERRO ao remover {item}: {e}")

    print()
    print("=" * 60)
    print(f"📊 RESUMO:")
    print(f"   Removidos: {removed_count}")
    print(f"   Mantidos:  {kept_count}")
    print("=" * 60)

    return removed_count, kept_count


def validate_before_cleanup():
    """
    Valida que a migração foi bem-sucedida antes de permitir limpeza.

    Returns:
        True se migração está OK, False caso contrário
    """
    print("🔍 VALIDANDO MIGRAÇÃO...")

    errors = []

    # Verifica nova estrutura existe
    checks = [
        ("src/runtime/prompts/", "Diretório prompts/"),
        ("src/runtime/prompts/system/", "Diretório system/"),
        ("src/runtime/prompts/skills/", "Diretório skills/"),
        ("src/runtime/prompts/system/system_prompt.json", "System prompt"),
        ("src/runtime/prompts/agent_prompts.py", "Agent prompts"),
    ]

    for path_str, description in checks:
        path = Path(path_str)
        if not path.exists():
            errors.append(f"❌ {description} não encontrado em {path_str}")
        else:
            print(f"✅ {description} encontrado")

    # Verifica imports funcionam
    try:
        sys.path.insert(0, "src")
        from runtime.prompts import load_system_prompt_config
        config = load_system_prompt_config()
        print(f"✅ Import funcionando (versão: {config.get('version', 'UNKNOWN')})")
    except ImportError as e:
        errors.append(f"❌ Import falhando: {e}")
    except Exception as e:
        errors.append(f"❌ Erro no import: {e}")

    # Verifica skills existem
    expected_skills = ["create-issue", "resolve-issue", "test-issue", "challenge-quality"]
    for skill in expected_skills:
        skill_path = Path(f"src/runtime/prompts/skills/{skill}/SKILL.md")
        if not skill_path.exists():
            errors.append(f"❌ Skill {skill} não encontrada")
        else:
            print(f"✅ Skill {skill} encontrada")

    print()

    if errors:
        print("⚠️  VALIDAÇÃO FALHOU:")
        for error in errors:
            print(f"   {error}")
        print()
        return False

    print("✅ VALIDAÇÃO OK - Migração bem-sucedida!")
    print()
    return True


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Limpeza de arquivos antigos após PRD020"
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/prd020_cleanup.py --dry-run     # Apenas mostra o que será removido
  python scripts/prd020_cleanup.py --force       # Realmente remove
  python scripts/prd020_cleanup.py --force --skip-validation  # Remove sem validar
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Modo dry-run (padrão): apenas mostra o que seria removido"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Realmente remove os arquivos (desliga dry-run)"
    )

    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Pula validação antes da limpeza (perigoso!)"
    )

    args = parser.parse_args()

    # Valida antes de permitir limpeza real
    if args.force and not args.skip_validation:
        if not validate_before_cleanup():
            print()
            print("❌ Migração não validada - abortando limpeza")
            print("   Use --skip-validation para forçar (não recomendado)")
            sys.exit(1)

    # Executa limpeza
    dry_run = args.dry_run
    removed, kept = cleanup_old_files(dry_run=dry_run)

    # Exit code
    if removed > 0 and not dry_run:
        print(f"\n✅ {removed} itens removidos com sucesso!")
        sys.exit(0)
    elif dry_run:
        print(f"\n📋 Modo dry-run: {removed} itens seriam removidos")
        print("   Execute com --force para realmente remover")
        sys.exit(0)
    else:
        print(f"\n⚠️  Nenhum item removido")
        sys.exit(1)


if __name__ == "__main__":
    main()
