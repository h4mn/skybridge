# coding: utf-8
"""
Script de Migração: JSON → RAG

Migra aprendizados do sky_memory.json para o banco RAG,
gerando embeddings para busca semântica.

Uso:
    python scripts/migrate_json_to_rag.py [--backup] [--dry-run]
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.sky.memory.cognitive_layer import CognitiveMemory
from src.core.sky.memory.collections import CollectionConfig


def get_backup_path(json_path: Path) -> Path:
    """Gera caminho para backup com timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return json_path.parent / f"{json_path.stem}_backup_{timestamp}{json_path.suffix}"


def backup_json(json_path: Path, backup_path: Path) -> None:
    """Cria backup do arquivo JSON."""
    if not json_path.exists():
        print(f"⚠️  Arquivo JSON não encontrado: {json_path}")
        return

    shutil.copy2(json_path, backup_path)
    print(f"✅ Backup criado: {backup_path}")


def infer_collection(content: str) -> str:
    """Infere a coleção apropriada baseado no conteúdo."""
    content_lower = content.lower()

    # Palavras-chave para cada coleção
    if any(kw in content_lower for kw in ["eu sou", "eu sou sky", "minha identidade", "sky é"]):
        return "identity"
    if any(kw in content_lower for kw in ["juntos", "compartilhamos", "momento", "vez que"]):
        return "shared-moments"
    if any(kw in content_lower for kw in ["papai ensinou", "ensinamento", "lição", "papai disse"]):
        return "teachings"
    if any(kw in content_lower for kw in ["deploy", "status", "agora", "hoje", "executando"]):
        return "operational"

    # Padrão: teachings (mais valioso)
    return "teachings"


def load_json_learnings(json_path: Path) -> list[dict]:
    """Carrega aprendizados do arquivo JSON."""
    if not json_path.exists():
        print(f"⚠️  Arquivo JSON não encontrado: {json_path}")
        return []

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Erro ao ler JSON: {e}")
        return []


def migrate_learnings(
    learnings: list[dict],
    cognitive_memory: CognitiveMemory,
    dry_run: bool = False,
) -> dict:
    """
    Migra aprendizados para o banco RAG.

    Returns:
        Dict com estatísticas da migração.
    """
    stats = {
        "total": len(learnings),
        "migrated": 0,
        "identity": 0,
        "shared-moments": 0,
        "teachings": 0,
        "operational": 0,
        "errors": 0,
    }

    print(f"\n📦 Migrando {stats['total']} aprendizados...")

    for i, learning in enumerate(learnings, 1):
        content = learning.get("content", "")
        timestamp = learning.get("timestamp", "")

        if not content:
            stats["errors"] += 1
            continue

        # Inferir coleção
        collection = infer_collection(content)

        if dry_run:
            print(f"   [DRY-RUN] {i}. [{collection}] \"{content[:50]}...\"")
            stats["migrated"] += 1
            stats[collection] += 1
            continue

        try:
            # Migrar para CognitiveMemory
            cognitive_memory.learn(
                content=content,
                collection=collection,
                metadata={"source_type": "migration", "original_timestamp": timestamp},
            )

            stats["migrated"] += 1
            stats[collection] += 1

            if i % 10 == 0 or i == len(learnings):
                print(f"   Progresso: {i}/{len(learnings)} ({100*i/len(learnings):.0f}%)")

        except Exception as e:
            print(f"   ⚠️  Erro ao migrar aprendizado {i}: {e}")
            stats["errors"] += 1

    return stats


def print_stats(stats: dict) -> None:
    """Imprime estatísticas da migração."""
    print("\n" + "=" * 50)
    print("📊 Estatísticas da Migração")
    print("=" * 50)

    print(f"\nTotal de aprendizados: {stats['total']}")
    print(f"Migrados com sucesso: {stats['migrated']}")
    print(f"Erros: {stats['errors']}")

    print("\nPor coleção:")
    for collection in ["identity", "shared-moments", "teachings", "operational"]:
        count = stats.get(collection, 0)
        print(f"   • {collection}: {count}")

    print("\n" + "=" * 50)


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Migra aprendizados do JSON para banco RAG"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Cria backup do JSON antes de migrar",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula migração sem fazer alterações",
    )
    parser.add_argument(
        "--json-path",
        type=str,
        default=None,
        help="Caminho para o arquivo JSON (padrão: ~/.skybridge/sky_memory.json)",
    )

    args = parser.parse_args()

    print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 MIGRAÇÃO JSON → RAG                            ║
║           Skybridge Memory Migration                        ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Determinar caminhos
    if args.json_path:
        json_path = Path(args.json_path)
    else:
        json_path = Path.home() / ".skybridge" / "sky_memory.json"

    print(f"📍 Arquivo JSON: {json_path}")

    # Backup se solicitado
    if args.backup and not args.dry_run:
        backup_path = get_backup_path(json_path)
        backup_json(json_path, backup_path)

    # Carregar aprendizados do JSON
    learnings = load_json_learnings(json_path)

    if not learnings:
        print("⚠️  Nenhum aprendizado encontrado para migrar.")
        return 0

    print(f"📦 {len(learnings)} aprendizados encontrados.")

    # Criar CognitiveMemory
    cognitive_memory = CognitiveMemory()

    # Migrar
    stats = migrate_learnings(learnings, cognitive_memory, dry_run=args.dry_run)

    # Imprimir estatísticas
    print_stats(stats)

    if args.dry_run:
        print("\n⚠️  MODO DRY-RUN: Nenhuma alteração foi feita.")
        print("   Execute novamente sem --dry-run para migrar.")
    else:
        print("\n✅ Migração concluída!")
        print(f"\nO arquivo JSON original foi preservado.")
        print("Para reverter, restaur o backup ou use o JSON antigo.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
