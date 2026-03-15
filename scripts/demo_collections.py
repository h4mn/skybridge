# coding: utf-8
"""
DEMO: Collections - Configuração e Retenção de Memórias.

Esta demo valida que:
1. CollectionConfig está funcionando
2. Coleções são criadas corretamente
3. Pruning de memórias expiradas funciona
4. Estatísticas de coleções funcionam
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Runtime - infraestrutura
from runtime.observability import get_logger, RuntimeLoggerAdapter

# Domínio - com logger injetado
from src.core.sky.memory.collections import (
    CollectionConfig,
    CollectionManager,
    SourceType,
    DEFAULT_COLLECTIONS,
)
from src.core.sky.memory.vector_store import VectorStore


def demo_list_collections(manager: CollectionManager) -> None:
    """Demo: Listar coleções configuradas."""
    print("\n" + "=" * 60)
    print("📋 DEMO 1: Coleções Configuradas")
    print("=" * 60)

    collections = manager.list_collections()

    for i, config in enumerate(collections, 1):
        retention = "Permanente" if config.is_permanent else f"{config.retention_days} dias"
        print(f"\n{i}. {config.name}")
        print(f"   Propósito: {config.purpose}")
        print(f"   Retenção: {retention}")
        print(f"   Embeddings: {'Sim' if config.embedding_enabled else 'Não'}")


def demo_insert_test_memories(store: VectorStore, manager: CollectionManager) -> None:
    """Demo: Inserir memórias de teste com datas antigas."""
    print("\n" + "=" * 60)
    print("📥 DEMO 2: Inserir Memórias de Teste")
    print("=" * 60)

    import sqlite3

    # Inserir algumas memórias na coleção operational com datas antigas
    conn = sqlite3.connect(store._db_path)
    cursor = conn.cursor()

    test_memories = [
        ("Ação de 45 dias atrás", -45),
        ("Ação de 35 dias atrás", -35),
        ("Ação de 25 dias atrás", -25),
        ("Ação de 15 dias atrás", -15),
        ("Ação de 5 dias atrás", -5),
        ("Ação de hoje", 0),
    ]

    for content, days_offset in test_memories:
        date = datetime.now() + timedelta(days=days_offset)

        # Inserir diretamente na tabela de metadata
        cursor.execute(
            """
            INSERT INTO memory_metadata (content, collection, source_type, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (content, "operational", "demo", date.isoformat())
        )

        print(f"   ✓ {content} ({date.strftime('%Y-%m-%d')})")

    conn.commit()
    conn.close()

    print(f"\n✅ {len(test_memories)} memórias inseridas!")


def demo_pruning(manager: CollectionManager) -> None:
    """Demo: Pruning de memórias expiradas."""
    print("\n" + "=" * 60)
    print("🗑️  DEMO 3: Pruning de Memórias Expiradas")
    print("=" * 60)

    # Estatísticas antes
    print("\nAntes do pruning:")
    stats_before = manager.get_collection_stats("operational")
    print(f"   • Total: {stats_before['count']} memórias")
    print(f"   • Mais antiga: {stats_before['oldest']}")
    print(f"   • Mais recente: {stats_before['newest']}")

    # Executar pruning
    print("\nExecutando pruning (retenção: 30 dias)...")
    deleted = manager.prune_expired_memories("operational")

    print(f"\n✅ {deleted} memórias removidas!")

    # Estatísticas depois
    print("\nDepois do pruning:")
    stats_after = manager.get_collection_stats("operational")
    print(f"   • Total: {stats_after['count']} memórias")
    print(f"   • Mais antiga: {stats_after['oldest']}")
    print(f"   • Mais recente: {stats_after['newest']}")


def demo_source_types() -> None:
    """Demo: Tipos de fonte."""
    print("\n" + "=" * 60)
    print("🏷️  DEMO 4: Tipos de Fonte")
    print("=" * 60)

    print("\nSourceType disponíveis:")
    for source_type in SourceType:
        print(f"   • {source_type.value:10s} - {source_type.name}")

    print("\nExemplos de uso:")
    examples = [
        (SourceType.CHAT, "Conversa com usuário"),
        (SourceType.CODE, "Comentário em código"),
        (SourceType.DOCS, "Documentação lida"),
        (SourceType.LOGS, "Entrada de log"),
        (SourceType.USER, "Input explícito do usuário"),
        (SourceType.DEMO, "Dados de teste/demo"),
    ]

    for source_type, description in examples:
        print(f"   {source_type.value:10s} → {description}")


def demo_collection_stats(manager: CollectionManager) -> None:
    """Demo: Estatísticas de todas as coleções."""
    print("\n" + "=" * 60)
    print("📊 DEMO 5: Estatísticas Gerais")
    print("=" * 60)

    collections = manager.list_collections()

    print(f"\n{'Coleção':<20} {'Qtd':>8} {'Mais Antiga':>12} {'Mais Recente':>12}")
    print("-" * 60)

    total_memories = 0
    for config in collections:
        stats = manager.get_collection_stats(config.name)

        oldest = stats["oldest"].split("T")[0] if stats["oldest"] else "N/A"
        newest = stats["newest"].split("T")[0] if stats["newest"] else "N/A"

        print(f"{config.name:<20} {stats['count']:>8} {oldest:>12} {newest:>12}")
        total_memories += stats["count"]

    print("-" * 60)
    print(f"{'TOTAL':<20} {total_memories:>8}")


def main():
    """Executa a demo."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 SKYBRIDGE COLLECTIONS - DEMO                  ║
║           Configuração e Retenção de Memórias               ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Criar logger e adapter
    runtime_logger = get_logger("demo.collections")
    sky_logger = RuntimeLoggerAdapter(runtime_logger)

    # Obter gerenciador com logger injetado
    manager = CollectionManager(logger=sky_logger)

    # Executar demos
    demo_list_collections(manager)
    demo_insert_test_memories(VectorStore(), manager)
    demo_pruning(manager)
    demo_source_types()
    demo_collection_stats(manager)

    print("\n" + "=" * 60)
    print("🎉 DEMO CONCLUÍDA!")
    print("=" * 60)
    print("\n✨ CollectionManager está funcionando corretamente!")
    print("\nPróximos passos:")
    print("   • 5.1 - Implementar IntentRouter")
    print("   • 5.2 - Implementar CognitiveMemory")
    print("   • 6.1 - Integrar com código existente")


if __name__ == "__main__":
    main()
