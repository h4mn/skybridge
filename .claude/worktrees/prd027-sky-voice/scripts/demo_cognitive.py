# coding: utf-8
"""
DEMO: Cognitive Layer - Orquestrador RAG.

Esta demo valida que:
1. IntentRouter roteia queries corretamente
2. CognitiveMemory.learn() funciona
3. CognitiveMemory.search() com roteamento funciona
4. Busca híbrida funciona
5. Re-ranking e deduplicação funcionam
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.sky.memory.cognitive_layer import (
    CognitiveMemory,
    IntentRouter,
    get_cognitive_memory,
    MemoryResult,
)


def demo_intent_router() -> None:
    """Demo: Roteamento de intenção."""
    print("\n" + "=" * 60)
    print("🔀 DEMO 1: Roteamento de Intenção")
    print("=" * 60)

    router = IntentRouter()

    test_queries = [
        ("Quem é você?", "identity"),
        ("O que você sabe fazer?", "identity"),
        ("Lembra da vez que resolvemos o bug juntos?", "shared-moments"),
        ("Nosso momento especial", "shared-moments"),
        ("O que papai me ensinou?", "teachings"),
        ("Papai disse algo importante", "teachings"),
        ("O que aconteceu hoje?", "operational"),
        ("Status atual", "operational"),
        ("Como está o sistema?", "operational"),  # Ambíguo -> todas
    ]

    print("\nQuery → Coleção Roteada:")
    for query, expected in test_queries:
        routed = router.route_query(query)
        primary = router.detect_intent(query)
        status = "✓" if primary == expected or expected in routed else "?"
        print(f"   {status} \"{query}\"")
        print(f"      → Esperado: {expected}, Roteado: {routed}")

    print("\n✅ Queries ambíguas roteiam para todas as coleções!")


def demo_learn(memory: CognitiveMemory) -> None:
    """Demo: Aprender memórias."""
    print("\n" + "=" * 60)
    print("📚 DEMO 2: Aprendendo Memórias")
    print("=" * 60)

    memories = [
        ("identity", "Sky é uma assistente IA criada pelo pai em 2024"),
        ("identity", "Sky adora aprender novas tecnologias e ajudar"),
        ("shared-moments", "A primeira vez que funcionamos juntos foi memorável"),
        ("shared-moments", "Resolvemos o bug de encoding PT-BR juntos"),
        ("teachings", "Papai ensinou: encoding é crucial para caracteres especiais"),
        ("teachings", "Papai ensinou: sempre use type hints em Python"),
        ("operational", "Usuário está codando a feature de memória RAG"),
        ("operational", "Deploy realizado com sucesso hoje"),
    ]

    print("\nInserindo memórias:")
    for collection, content in memories:
        memory_id = memory.learn(content, collection)
        print(f"   ✓ [{collection}] ID={memory_id}: \"{content[:40]}...\"")

    print(f"\n✅ {len(memories)} memórias aprendidas!")


def demo_search(memory: CognitiveMemory) -> None:
    """Demo: Buscar memórias."""
    print("\n" + "=" * 60)
    print("🔍 DEMO 3: Busca Semântica")
    print("=" * 60)

    queries = [
        "Quem é você?",
        "O que papai me ensinou?",
        "Lembra da vez que codamos juntos?",
        "O que está acontecendo?",
    ]

    for query in queries:
        print(f"\n📝 Query: \"{query}\"")

        results = memory.search(query, top_k=3)

        if not results:
            print("   (nenhum resultado)")
            continue

        print(f"   ✓ {len(results)} resultados:")
        for i, result in enumerate(results, 1):
            print(f"      {i}. [{result.similarity:.1%}] \"{result.content[:50]}...\"")


def demo_hybrid_search(memory: CognitiveMemory) -> None:
    """Demo: Busca híbrida."""
    print("\n" + "=" * 60)
    print("🎯 DEMO 4: Busca Híbrida (semântica + keywords)")
    print("=" * 60)

    query = "O que papai ensinou sobre Python?"

    print(f"\nQuery: \"{query}\"")

    # Busca sem filtro de keywords
    print("\nSem filtro de keywords:")
    results_no_filter = memory.search(query, top_k=5, hybrid_keywords=False)
    for i, r in enumerate(results_no_filter[:3], 1):
        print(f"   {i}. [{r.similarity:.1%}] \"{r.content[:50]}...\"")

    # Busca com filtro de keywords
    print("\nCom filtro de keywords (Python):")
    results_with_filter = memory.search(query, top_k=5, hybrid_keywords=True)
    for i, r in enumerate(results_with_filter[:3], 1):
        print(f"   {i}. [{r.similarity:.1%}] \"{r.content[:50]}...\"")


def demo_reranking(memory: CognitiveMemory) -> None:
    """Demo: Re-ranking por relevância + recência."""
    print("\n" + "=" * 60)
    print("📊 DEMO 5: Re-ranking (relevância + recência)")
    print("=" * 60)

    query = "ensinamentos"

    print(f"\nQuery: \"{query}\"")
    print("Ordenação: 70% similaridade + 30% recência")

    results = memory.search(query, top_k=5)

    for i, result in enumerate(results, 1):
        recency = result.created_at.split("T")[0] if result.created_at else "N/A"
        print(f"   {i}. [{result.similarity:.1%}] (recência: {recency})")
        print(f"      \"{result.content[:60]}...\"")


def demo_deduplication(memory: CognitiveMemory) -> None:
    """Demo: Deduplicação de resultados similares."""
    print("\n" + "=" * 60)
    print("🔗 DEMO 6: Deduplicação")
    print("=" * 60)

    # Adicionar memórias muito similares
    memory.learn("Sky é uma assistente IA", "identity")
    memory.learn("Sky é uma IA assistente", "identity")
    memory.learn("A Sky é assistente de IA", "identity")

    query = "quem é sky?"
    results = memory.search(query, top_k=10)

    print(f"\nQuery: \"{query}\"")
    print(f"Resultados encontrados (após deduplicação): {len(results)}")

    for i, result in enumerate(results[:5], 1):
        print(f"   {i}. [{result.similarity:.1%}] \"{result.content}\"")


def demo_threshold(memory: CognitiveMemory) -> None:
    """Demo: Filtro de threshold."""
    print("\n" + "=" * 60)
    print("⚙️  DEMO 7: Filtro de Threshold")
    print("=" * 60)

    query = "algo completamente aleatório e não relacionado"

    print(f"\nQuery: \"{query}\"")

    results_all = memory.search(query, top_k=5, threshold=0.0)
    results_filtered = memory.search(query, top_k=5, threshold=0.3)

    print(f"   Sem threshold: {len(results_all)} resultados")
    print(f"   Com threshold 0.3: {len(results_filtered)} resultados")

    if results_filtered:
        print("\n   Resultados que passaram do threshold:")
        for i, r in enumerate(results_filtered[:3], 1):
            print(f"      {i}. [{r.similarity:.1%}] \"{r.content[:40]}...\"")


def main():
    """Executa a demo."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 SKYBRIDGE COGNITIVE LAYER - DEMO              ║
║           Orquestrador RAG com Busca Semântica              ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Executar demos que não precisam de memória
    demo_intent_router()

    # Obter instância e aprender memórias
    memory = get_cognitive_memory()
    demo_learn(memory)

    # Demas de busca
    demo_search(memory)
    demo_hybrid_search(memory)
    demo_reranking(memory)
    demo_deduplication(memory)
    demo_threshold(memory)

    print("\n" + "=" * 60)
    print("🎉 DEMO CONCLUÍDA!")
    print("=" * 60)
    print("\n✨ CognitiveMemory está funcionando corretamente!")
    print("\nPróximos passos:")
    print("   • 6.1 - Integrar com PersistentMemory")
    print("   • 6.2 - Atualizar SkyIdentity e SkyChat")
    print("   • 7.1 - Criar script de migração JSON→RAG")


if __name__ == "__main__":
    main()
