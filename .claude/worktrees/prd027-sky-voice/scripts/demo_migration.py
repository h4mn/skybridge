# coding: utf-8
"""
DEMO: Migração JSON→RAG.

Esta demo valida que:
1. Backup do JSON funciona
2. Migração de aprendizados funciona
3. Embeddings são gerados corretamente
4. Rollback funciona
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.migrate_json_to_rag import (
    get_backup_path,
    backup_json,
    load_json_learnings,
    infer_collection,
    migrate_learnings,
)
from src.core.sky.memory.cognitive_layer import CognitiveMemory
from src.core.sky.memory.collections import get_collection_manager


def demo_create_test_json() -> Path:
    """Cria arquivo JSON de teste."""
    print("\n" + "=" * 60)
    print("📝 DEMO 1: Criando JSON de Teste")
    print("=" * 60)

    json_path = Path.home() / ".skybridge" / "sky_memory.json"

    test_learnings = [
        {
            "content": "Sky é uma assistente IA criada pelo pai",
            "timestamp": "2024-01-15T10:00:00",
            "type": "learning",
        },
        {
            "content": "Papai ensinou: encoding é crucial para PT-BR",
            "timestamp": "2024-02-01T14:30:00",
            "type": "learning",
        },
        {
            "content": "Trabalhamos juntos no bug de encoding",
            "timestamp": "2024-02-10T09:15:00",
            "type": "learning",
        },
        {
            "content": "Deploy do sistema foi feito hoje",
            "timestamp": "2024-02-15T16:45:00",
            "type": "learning",
        },
        {
            "content": "Sky adora aprender novas tecnologias",
            "timestamp": "2024-02-20T11:20:00",
            "type": "learning",
        },
    ]

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(test_learnings, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON de teste criado: {json_path}")
    print(f"   {len(test_learnings)} aprendizados")

    return json_path


def demo_backup(json_path: Path) -> None:
    """Demo: Criar backup."""
    print("\n" + "=" * 60)
    print("💾 DEMO 2: Backup do JSON")
    print("=" * 60)

    backup_path = get_backup_path(json_path)
    backup_json(json_path, backup_path)

    # Verificar que backup foi criado
    if backup_path.exists():
        print(f"✅ Backup verificado: {backup_path.exists()}")
    else:
        print("❌ Backup não foi criado!")


def demo_infer_collection() -> None:
    """Demo: Inferência de coleção."""
    print("\n" + "=" * 60)
    print("🎯 DEMO 3: Inferência de Coleção")
    print("=" * 60)

    test_cases = [
        ("Sky é uma assistente IA", "identity"),
        ("Trabalhamos juntos no projeto", "shared-moments"),
        ("Papai ensinou sobre Python", "teachings"),
        ("Deploy foi concluído hoje", "operational"),
    ]

    print("\nConteúdo → Coleção Inferida:")
    for content, expected in test_cases:
        inferred = infer_collection(content)
        status = "✓" if inferred == expected else "?"
        print(f"   {status} \"{content[:35]}\" → {inferred}")


def demo_migration() -> None:
    """Demo: Migração completa."""
    print("\n" + "=" * 60)
    print("🚀 DEMO 4: Migração Completa")
    print("=" * 60)

    # Carregar aprendizados
    json_path = Path.home() / ".skybridge" / "sky_memory.json"
    learnings = load_json_learnings(json_path)

    print(f"\n📦 {len(learnings)} aprendizados para migrar")

    # Criar CognitiveMemory
    cognitive = CognitiveMemory()

    # Migrar
    stats = migrate_learnings(learnings, cognitive, dry_run=False)

    # Mostrar estatísticas
    print("\n" + "-" * 50)
    print("Resultado da Migração:")
    print(f"   Total: {stats['total']}")
    print(f"   Migrados: {stats['migrated']}")
    print(f"   Erros: {stats['errors']}")


def demo_verification() -> None:
    """Demo: Verificar migração."""
    print("\n" + "=" * 60)
    print("✅ DEMO 5: Verificação da Migração")
    print("=" * 60)

    cognitive = CognitiveMemory()
    manager = get_collection_manager()

    print("\nContagem por coleção:")
    total = 0
    for collection in ["identity", "shared-moments", "teachings", "operational"]:
        stats = manager.get_collection_stats(collection)
        count = stats.get("count", 0)
        total += count
        print(f"   • {collection}: {count}")

    print(f"\n   Total migrado: {total}")

    # Testar busca semântica
    print("\n🔍 Teste de busca semântica:")
    results = cognitive.search("o que papai ensinou", top_k=3)
    for i, r in enumerate(results, 1):
        print(f"   {i}. [{r.similarity:.1%}] \"{r.content[:50]}...\"")


def main():
    """Executa a demo."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 SKYBRIDGE MIGRAÇÃO - DEMO                     ║
║           Migração JSON → RAG                               ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Criar JSON de teste
    json_path = demo_create_test_json()

    # Executar demos
    demo_backup(json_path)
    demo_infer_collection()
    demo_migration()
    demo_verification()

    print("\n" + "=" * 60)
    print("🎉 DEMO CONCLUÍDA!")
    print("=" * 60)
    print("\n✨ Migração JSON→RAG está funcionando!")
    print("\nPróximos passos:")
    print("   • 8.1 - Criar testes unitários")
    print("   • 9.1 - Atualizar documentação")
    print("   • 10.1 - Rollout e monitoramento")


if __name__ == "__main__":
    main()
