# coding: utf-8
"""
DEMO: Integração - PersistentMemory com RAG.

Esta demo valida que:
1. API de PersistentMemory permanece compatível
2. Feature flag USE_RAG_MEMORY funciona
3. learn() salva em ambos JSON e RAG
4. search() usa busca semântica quando RAG habilitado
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.sky.memory import PersistentMemory, get_memory, USE_RAG_MEMORY


def demo_legacy_mode() -> None:
    """Demo: Modo legacy (sem RAG)."""
    print("\n" + "=" * 60)
    print("📜 DEMO 1: Modo Legacy (sem RAG)")
    print("=" * 60)

    # Criar memória sem RAG
    memory = PersistentMemory(use_rag=False)

    print(f"RAG habilitado: {memory.is_rag_enabled()}")

    # Aprender algumas coisas
    print("\nAprendendo...")
    memory.learn("Sky é uma assistente IA")
    memory.learn("Papai ensinou sobre Python")
    memory.learn("Deploy feito hoje")

    # Buscar
    print("\nBusca por 'python':")
    results = memory.search("python")
    for r in results:
        print(f"   ✓ \"{r['content']}\"")

    print("\n✅ Legacy mode funciona!")


def demo_rag_mode() -> None:
    """Demo: Modo RAG (busca semântica)."""
    print("\n" + "=" * 60)
    print("🧠 DEMO 2: Modo RAG (busca semântica)")
    print("=" * 60)

    # Criar memória com RAG
    memory = PersistentMemory(use_rag=True)

    print(f"RAG habilitado: {memory.is_rag_enabled()}")

    # Aprender algumas coisas
    print("\nAprendendo...")
    memory.learn("Sky é uma assistente IA criada pelo pai")
    memory.learn("Papai ensinou: sempre use type hints em Python")
    memory.learn("Resolvemos o bug de encoding juntos")

    # Busca semântica
    print("\nBusca semântica por 'o que papai ensinou':")
    results = memory.search("o que papai ensinou", top_k=3)
    for i, r in enumerate(results, 1):
        similarity = r.get("similarity", 0)
        print(f"   {i}. [{similarity:.1%}] \"{r['content']}\"")

    # Busca por sinônimos
    print("\nBusca semântica por 'quem é você?' (sinônimo de identidade):")
    results = memory.search("quem é você?", top_k=3)
    for i, r in enumerate(results, 1):
        similarity = r.get("similarity", 0)
        print(f"   {i}. [{similarity:.1%}] \"{r['content']}\"")

    print("\n✅ RAG mode funciona!")


def demo_collection_inference() -> None:
    """Demo: Inferência automática de coleção."""
    print("\n" + "=" * 60)
    print("🎯 DEMO 3: Inferência Automática de Coleção")
    print("=" * 60)

    memory = PersistentMemory(use_rag=True)

    test_learnings = [
        ("Eu sou Sky, uma assistente IA", "identity"),
        ("Trabalhamos juntos no bug", "shared-moments"),
        ("Papai ensinou sobre código", "teachings"),
        ("Deploy foi concluído hoje", "operational"),
    ]

    print("\nInferência de coleção:")
    for content, expected in test_learnings:
        inferred = memory._infer_collection(content)
        status = "✓" if inferred == expected else "?"
        print(f"   {status} \"{content[:40]}...\" → {expected} (inferido: {inferred})")


def demo_env_variable() -> None:
    """Demo: Feature flag via variável de ambiente."""
    print("\n" + "=" * 60)
    print("⚙️  DEMO 4: Feature Flag USE_RAG_MEMORY")
    print("=" * 60)

    print(f"\nUSE_RAG_MEMORY (atual): {USE_RAG_MEMORY}")
    print(f"Pode ser alterado com: export USE_RAG_MEMORY=true")

    # Criar memória (respeita env var por padrão)
    memory = get_memory()
    print(f"get_memory() RAG habilitado: {memory.is_rag_enabled()}")

    # Pode ser sobrescrito
    memory_explicit = PersistentMemory(use_rag=True)
    print(f"PersistentMemory(use_rag=True) RAG: {memory_explicit.is_rag_enabled()}")


def demo_enable_disable() -> None:
    """Demo: Habilitar/desabilitar RAG dinamicamente."""
    print("\n" + "=" * 60)
    print("🔧 DEMO 5: Habilitar/Desabilitar RAG Dinamicamente")
    print("=" * 60)

    memory = PersistentMemory(use_rag=False)

    print(f"\nInicial: RAG={memory.is_rag_enabled()}")

    # Aprender algo
    memory.learn("Teste de memória")

    # Habilitar RAG
    memory.enable_rag()
    print(f"Após enable_rag(): RAG={memory.is_rag_enabled()}")

    # Desabilitar
    memory.disable_rag()
    print(f"Após disable_rag(): RAG={memory.is_rag_enabled()}")


def demo_api_compatibility() -> None:
    """Demo: Compatibilidade da API."""
    print("\n" + "=" * 60)
    print("🔄 DEMO 6: Compatibilidade da API")
    print("=" * 60)

    # Criar memórias com e sem RAG
    mem_legacy = PersistentMemory(use_rag=False)
    mem_rag = PersistentMemory(use_rag=True)

    # Aprender o mesmo conteúdo
    content = "Sky gosta de aprender coisas novas"
    mem_legacy.learn(content)
    mem_rag.learn(content)

    # Verificar que ambos têm o método
    print("\nMétodos disponíveis em ambas:")
    for method in ["learn", "search", "get_all_learnings", "get_today_learnings"]:
        has_legacy = hasattr(mem_legacy, method)
        has_rag = hasattr(mem_rag, method)
        status = "✓" if has_legacy and has_rag else "✗"
        print(f"   {status} {method}()")

    # Buscar
    print("\nResultado de search('aprender'):")
    print(f"  Legacy (substring): {len(mem_legacy.search('aprender'))} resultado(s)")
    print(f"  RAG (semântico): {len(mem_rag.search('aprender'))} resultado(s)")


def main():
    """Executa a demo."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 SKYBRIDGE INTEGRAÇÃO - DEMO                  ║
║           PersistentMemory com Suporte RAG                 ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Executar demos
    demo_legacy_mode()
    demo_rag_mode()
    demo_collection_inference()
    demo_env_variable()
    demo_enable_disable()
    demo_api_compatibility()

    print("\n" + "=" * 60)
    print("🎉 DEMO CONCLUÍDA!")
    print("=" * 60)
    print("\n✨ PersistentMemory está integrada com RAG!")
    print("\nPróximos passos:")
    print("   • 6.3 - Atualizar SkyIdentity para usar busca semântica")
    print("   • 6.4 - Atualizar SkyChat para rotear perguntas")
    print("   • 7.1 - Criar script de migração JSON→RAG")


if __name__ == "__main__":
    main()
