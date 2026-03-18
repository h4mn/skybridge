# coding: utf-8
"""
DEMO: Vector Store - Busca Vetorial com sqlite-vec.

Esta demo valida que:
1. VectorStore está funcionando
2. Tabelas virtuais foram criadas para cada coleção
3. Inserção e busca de vetores funcionam

Usa embeddings mockados (vetores aleatórios) para teste.
"""

import random
from pathlib import Path

# Adicionar src ao path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.sky.memory.vector_store import VectorStore, EMBEDDING_DIM


def generate_mock_embedding() -> list[float]:
    """
    Gera embedding mockado (vetor aleatório).

    Em produção, isso viria do sentence-transformers.
    """
    return [random.random() for _ in range(EMBEDDING_DIM)]


def demo_insert_vectors(store: VectorStore) -> None:
    """Demo: Inserir vetores de teste."""
    print("\n" + "=" * 60)
    print("📥 DEMO 1: Inserindo Vetores")
    print("=" * 60)

    # Memórias de teste para cada coleção
    test_memories = [
        {
            "collection": "identity",
            "content": "Sky é uma assistente IA criada pelo pai",
            "embedding": generate_mock_embedding(),
        },
        {
            "collection": "identity",
            "content": "Sky gosta de aprender e ajudar",
            "embedding": generate_mock_embedding(),
        },
        {
            "collection": "shared-moments",
            "content": "A primeira vez que funcionamos juntos",
            "embedding": generate_mock_embedding(),
        },
        {
            "collection": "shared-moments",
            "content": "O dia que resolvemos o bug de encoding juntos",
            "embedding": generate_mock_embedding(),
        },
        {
            "collection": "teachings",
            "content": "Papai ensinou: encoding é importante para caracteres especiais",
            "embedding": generate_mock_embedding(),
        },
        {
            "collection": "teachings",
            "content": "Papai ensinou: sempre use type hints em Python",
            "embedding": generate_mock_embedding(),
        },
        {
            "collection": "operational",
            "content": "Usuário está codando a feature de memória RAG",
            "embedding": generate_mock_embedding(),
        },
        {
            "collection": "operational",
            "content": "Deploy realizado com sucesso",
            "embedding": generate_mock_embedding(),
        },
    ]

    for i, memory in enumerate(test_memories, 1):
        memory_id = store.insert_vector(
            collection=memory["collection"],
            embedding=memory["embedding"],
            content=memory["content"],
            metadata={"source_type": "demo"},
        )
        print(f"   {i}. [{memory['collection']}] ID={memory_id}")
        print(f"      \"{memory['content']}\"")

    print(f"\n✅ {len(test_memories)} memórias inseridas!")


def demo_search_vectors(store: VectorStore) -> None:
    """Demo: Buscar vetores similares."""
    print("\n" + "=" * 60)
    print("🔍 DEMO 2: Busca Vetorial")
    print("=" * 60)

    # Buscar em cada coleção
    query_embedding = generate_mock_embedding()

    for collection in VectorStore.COLLECTIONS:
        print(f"\n📦 Coleção: {collection}")

        results = store.search_vectors(
            collection=collection,
            query_vector=query_embedding,
            k=3,
        )

        if not results:
            print("   (nenhum resultado)")
            continue

        for i, result in enumerate(results, 1):
            # Converter distância para similaridade (0-1)
            similarity = 1.0 / (1.0 + result.distance)
            print(f"   {i}. [score: {similarity:.4f}] \"{result.content}\"")


def demo_collection_stats(store: VectorStore) -> None:
    """Demo: Estatísticas das coleções."""
    print("\n" + "=" * 60)
    print("📊 DEMO 3: Estatísticas das Coleções")
    print("=" * 60)

    for collection in VectorStore.COLLECTIONS:
        stats = store.get_collection_stats(collection)
        print(f"   • {collection}: {stats['count']} memórias")


def demo_hybrid_search(store: VectorStore) -> None:
    """Demo: Busca com threshold de relevância."""
    print("\n" + "=" * 60)
    print("🎯 DEMO 4: Busca com Threshold de Relevância")
    print("=" * 60)

    query_embedding = generate_mock_embedding()

    # Buscar com threshold alto (só resultados muito relevantes)
    results = store.search_vectors(
        collection="teachings",
        query_vector=query_embedding,
        k=5,
        threshold=0.5,  # 50% de similaridade mínima
    )

    print(f"\nBusca em 'teachings' com threshold=0.5:")
    if not results:
        print("   (nenhum resultado passou do threshold)")
    else:
        for i, result in enumerate(results, 1):
            similarity = 1.0 / (1.0 + result.distance)
            print(f"   {i}. [{similarity:.2%}] \"{result.content}\"")


def main():
    """Executa a demo."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 SKYBRIDGE VECTOR STORE - DEMO                ║
║           Busca Vetorial com sqlite-vec                    ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Criar VectorStore
    db_path = Path.home() / ".skybridge" / "sky_memory.db"
    print(f"📍 Banco de dados: {db_path}")

    with VectorStore(db_path) as store:
        # Executar demos
        demo_insert_vectors(store)
        demo_search_vectors(store)
        demo_collection_stats(store)
        demo_hybrid_search(store)

    print("\n" + "=" * 60)
    print("🎉 DEMO CONCLUÍDA!")
    print("=" * 60)
    print("\n✨ VectorStore está funcionando corretamente!")
    print("\nPróximos passos:")
    print("   • 3.1 - Implementar EmbeddingClient")
    print("   • 5.1 - Implementar IntentRouter")
    print("   • 5.2 - Implementar CognitiveMemory")


if __name__ == "__main__":
    main()
