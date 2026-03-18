# coding: utf-8
"""
DEMO: Teste de instalação de dependências para Memory RAG.

Este script valida que:
1. sqlite-vec está instalado e funciona
2. sentence-transformers está instalado e funciona
3. O modelo de embedding pode ser carregado

Executa uma demo minimal de geração de embedding.
"""

import sys
from pathlib import Path


def test_sqlite_vec():
    """Testa se sqlite-vec está instalado."""
    print("=" * 60)
    print("🧪 TESTE 1: sqlite-vec")
    print("=" * 60)

    try:
        import sqlite3
        import sqlite_vec  # type: ignore

        # Criar conexão de teste
        conn = sqlite3.connect(":memory:")

        # Carregar extensão sqlite-vec
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)

        print("✅ sqlite-vec instalado e carregado!")

        # Demo: Criar tabela vetorial simples
        conn.execute("""
            CREATE VIRTUAL TABLE vec_demo USING vec0(
                embedding_float(3)
            )
        """)

        # Inserir vetor de teste
        conn.execute(
            "INSERT INTO vec_demo(embedding_float) VALUES (?)",
            [[1.0, 2.0, 3.0]]
        )

        # Buscar vizinhos mais próximos
        result = conn.execute("""
            SELECT
                distance,
                embedding_float
            FROM vec_demo
            WHERE embedding_float MATCH ?
            ORDER BY distance
            LIMIT 5
        """, [[1.0, 2.0, 3.0]]).fetchall()

        print(f"✅ Busca vetorial funcionou! {len(result)} resultado(s)")

        conn.close()
        return True

    except ImportError as e:
        print(f"❌ ERRO: {e}")
        print("   Instale: pip install sqlite-vec")
        return False
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False


def test_sentence_transformers():
    """Testa se sentence-transformers está instalado."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 2: sentence-transformers")
    print("=" * 60)

    try:
        from sentence_transformers import SentenceTransformer

        print("📥 Carregando modelo paraphrase-multilingual-MiniLM-L12-v2...")
        print("   (pode demorar no primeiro uso - baixando modelo...)")

        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

        print("✅ Modelo carregado!")

        # Demo: Gerar embedding para frase de teste
        test_sentences = [
            "Sky é uma assistente IA muito especial",
            "A Sky gosta de aprender coisas novas",
            "Encoding de caracteres é importante",
        ]

        print("\n🔄 Gerando embeddings para demo:")
        embeddings = model.encode(test_sentences)

        for i, (sentence, emb) in enumerate(zip(test_sentences, embeddings), 1):
            print(f"   {i}. \"{sentence}\"")
            print(f"      → Dimensão: {emb.shape[0]}")
            print(f"      → Primeiros 3 valores: [{emb[0]:.4f}, {emb[1]:.4f}, {emb[2]:.4f}]")

        print(f"\n✅ Geração de embeddings funcionando!")
        print(f"   Dimensão do embedding: {embeddings[0].shape[0]}")

        return True

    except ImportError as e:
        print(f"❌ ERRO: {e}")
        print("   Instale: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False


def test_schema_creation():
    """Testa criação do schema do banco."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 3: Criação do Schema")
    print("=" * 60)

    try:
        from create_memory_schema import get_db_path, create_schema

        db_path = get_db_path()
        print(f"📍 Caminho do banco: {db_path}")

        create_schema(db_path)

        # Verificar que tabelas foram criadas
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        print(f"✅ Tabelas criadas: {', '.join(tables)}")

        # Verificar configurações das coleções
        cursor.execute("SELECT name, retention_days, purpose FROM collection_config")
        collections = cursor.fetchall()

        print("\n📦 Coleções configuradas:")
        for name, retention, purpose in collections:
            retention_str = f"{retention} dias" if retention else "permanente"
            print(f"   • {name}: {purpose} ({retention_str})")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 SKYBRIDGE MEMORY RAG - DEMO                  ║
║           Teste de Dependências e Setup                    ║
╚════════════════════════════════════════════════════════════╝
    """)

    results = {
        "sqlite-vec": test_sqlite_vec(),
        "sentence-transformers": test_sentence_transformers(),
        "schema": test_schema_creation(),
    }

    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"   {status}: {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n✨ Setup completo! O sistema está pronto para:")
        print("   • Criar VectorStore (tarefa 2.1)")
        print("   • Implementar EmbeddingClient (tarefa 3.1)")
        print("   • Desenvolver CognitiveLayer (tarefa 5.1)")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam. Verifique as dependências.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
