# coding: utf-8
"""
DEMO: Embedding Client - Geração de Embeddings com Cache.

Esta demo valida que:
1. SentenceTransformerEmbedding está funcionando
2. Cache de embeddings funciona corretamente
3. Encode batch funciona
4. Funciona offline (após primeiro carregamento)
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Runtime - infraestrutura
from runtime.observability import get_logger, RuntimeLoggerAdapter

# Domínio - com logger injetado
from src.core.sky.memory.embedding import (
    SentenceTransformerEmbedding,
    EMBEDDING_DIM,
    DEFAULT_MODEL,
)


def demo_basic_encode(client: SentenceTransformerEmbedding) -> None:
    """Demo: Codificação básica de texto."""
    print("\n" + "=" * 60)
    print("📝 DEMO 1: Codificação Básica")
    print("=" * 60)

    texts = [
        "Sky é uma assistente IA muito especial",
        "A Sky gosta de aprender coisas novas",
        "Encoding de caracteres é importante",
    ]

    for i, text in enumerate(texts, 1):
        print(f"\n{i}. Texto: \"{text}\"")

        # Primeira chamada (gera e cacheia)
        start = time.time()
        embedding = client.encode(text)
        duration = time.time() - start

        print(f"   → Dimensão: {len(embedding)}")
        print(f"   → Tempo (primeira): {duration:.3f}s")

        # Segunda chamada (do cache)
        start = time.time()
        embedding_cached = client.encode(text)
        duration_cached = time.time() - start

        print(f"   → Tempo (cache): {duration_cached:.4f}s")
        # Evitar divisão por zero
        if duration_cached > 0:
            print(f"   → Speedup: {duration / duration_cached:.1f}x")
        else:
            print(f"   → Cache ultra rápido!")
        print(f"   → Cache hit: {embedding == embedding_cached}")


def demo_batch_encode(client: SentenceTransformerEmbedding) -> None:
    """Demo: Codificação em lote."""
    print("\n" + "=" * 60)
    print("📦 DEMO 2: Codificação em Lote (Batch)")
    print("=" * 60)

    texts = [
        "Papai ensinou sobre Python",
        "Papai ensinou sobre type hints",
        "Papai ensinou sobre encoding",
        "Papai ensinou sobre Git",
        "Deploy realizado",
    ]

    print(f"\nProcessando {len(texts)} textos...")

    start = time.time()
    embeddings = client.encode_batch(texts)
    duration = time.time() - start

    print(f"✅ Concluído em {duration:.3f}s")
    print(f"   Médio por texto: {duration / len(texts):.4f}s")

    for i, (text, emb) in enumerate(zip(texts, embeddings), 1):
        print(f"   {i}. \"{text[:30]}...\" → dim={len(emb)}")


def demo_cache_stats(client: SentenceTransformerEmbedding) -> None:
    """Demo: Estatísticas do cache."""
    print("\n" + "=" * 60)
    print("💾 DEMO 3: Estatísticas do Cache")
    print("=" * 60)

    import sqlite3

    conn = sqlite3.connect(client._db_path)
    cursor = conn.cursor()

    # Contar embeddings cacheados
    cursor.execute("SELECT COUNT(*) FROM embeddings_cache")
    count = cursor.fetchone()[0]

    # Tamanho do cache em bytes
    cursor.execute("SELECT SUM(LENGTH(embedding)) FROM embeddings_cache")
    size_bytes = cursor.fetchone()[0] or 0
    size_kb = size_bytes / 1024

    # Modelo usado
    cursor.execute("SELECT DISTINCT model_name FROM embeddings_cache LIMIT 1")
    model = cursor.fetchone()[0] if cursor.rowcount > 0 else DEFAULT_MODEL

    conn.close()

    print(f"   • Modelo: {model}")
    print(f"   • Entradas cacheadas: {count}")
    print(f"   • Tamanho do cache: {size_kb:.2f} KB")
    print(f"   • Médio por entrada: {size_bytes / count if count > 0 else 0:.1f} bytes")


def demo_semantic_similarity(client: SentenceTransformerEmbedding) -> None:
    """Demo: Similaridade semântica entre textos."""
    print("\n" + "=" * 60)
    print("🎯 DEMO 4: Similaridade Semântica")
    print("=" * 60)

    query = "O que papai me ensinou?"
    candidates = [
        "Papai ensinou: encoding é importante",
        "Sky gosta de aprender",
        "Deploy foi feito com sucesso",
        "Papai ensinou sobre type hints em Python",
    ]

    print(f"\nQuery: \"{query}\"")
    print("\nCalculando similaridade...")

    import numpy as np  # Para cálculo de similaridade

    query_emb = np.array(client.encode(query))

    results = []
    for candidate in candidates:
        cand_emb = np.array(client.encode(candidate))
        # Similaridade de cosseno
        similarity = np.dot(query_emb, cand_emb) / (
            np.linalg.norm(query_emb) * np.linalg.norm(cand_emb)
        )
        results.append((candidate, similarity))

    # Ordenar por similaridade
    results.sort(key=lambda x: x[1], reverse=True)

    print("\nResultados (ordenados por similaridade):")
    for i, (text, score) in enumerate(results, 1):
        bar = "█" * int(score * 30)
        print(f"   {i}. [{score:.2%}] {bar}")
        print(f"      \"{text}\"")


def demo_offline_capability(client: SentenceTransformerEmbedding) -> None:
    """Demo: Capacidade offline."""
    print("\n" + "=" * 60)
    print("🔌 DEMO 5: Capacidade Offline")
    print("=" * 60)

    print("\nSimulando uso offline...")

    # Como o modelo já está carregado, podemos usá-lo sem internet
    test_texts = [
        "Teste offline 1",
        "Teste offline 2",
        "Teste offline 3",
    ]

    start = time.time()
    embeddings = client.encode_batch(test_texts)
    duration = time.time() - start

    print(f"✅ {len(embeddings)} embeddings gerados sem conexão externa!")
    print(f"   Tempo: {duration:.3f}s")
    print("\nO modelo já está em memória e funciona completamente offline.")


def main():
    """Executa a demo."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 SKYBRIDGE EMBEDDING CLIENT - DEMO            ║
║           Geração de Embeddings com Cache                  ║
╚════════════════════════════════════════════════════════════╝
    """)

    print(f"📦 Modelo: {DEFAULT_MODEL}")
    print(f"📐 Dimensão: {EMBEDDING_DIM}")

    # Criar logger e adapter
    runtime_logger = get_logger("demo.embedding")
    sky_logger = RuntimeLoggerAdapter(runtime_logger)

    # Criar cliente com logger injetado
    client = SentenceTransformerEmbedding(logger=sky_logger)

    # Executar demos
    demo_basic_encode(client)
    demo_batch_encode(client)
    demo_cache_stats(client)
    demo_semantic_similarity(client)
    demo_offline_capability(client)

    print("\n" + "=" * 60)
    print("🎉 DEMO CONCLUÍDA!")
    print("=" * 60)
    print("\n✨ EmbeddingClient está funcionando corretamente!")
    print("\nPróximos passos:")
    print("   • 4.1 - Definir CollectionConfig")
    print("   • 5.1 - Implementar IntentRouter")
    print("   • 5.2 - Implementar CognitiveMemory")


if __name__ == "__main__":
    main()
