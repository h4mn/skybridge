#!/usr/bin/env python3
"""Teste simples da Skypedia - importando direto."""

import sys
import sqlite3
import struct
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Importar sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("[ERROR] sentence-transformers não instalado")
    print("        Execute: pip install sentence-transformers")
    sys.exit(1)

# Importar sqlite-vec
try:
    import sqlite_vec
except ImportError:
    print("[ERROR] sqlite-vec não instalado")
    print("        Execute: pip install sqlite-vec")
    sys.exit(1)

# Caminho do banco
db_path = Path.home() / ".skybridge" / "sky_memory.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

EMBEDDING_DIM = 384

def serialize_vector(vector):
    """Serializa vetor para bytes."""
    return struct.pack(f"{len(vector)}f", *vector)

# Conteúdo do vídeo MOSS-TTS
VIDEO_CONTENT = """# Moss-TTS é uma alternativa GRÁTIS ao ElevenLabs?

O vídeo é um tutorial e revisão do modelo de Text-to-Speech (TTS) MOSS-TTS, disponível na plataforma Hugging Face. O apresentador explica o que é o MOSS-TTS, destacando sua natureza de código aberto e suas capacidades de geração de fala de alta fidelidade e expressividade.

MOSS-TTS é uma família de modelos de código aberto para geração de fala e som, projetado para alta fidelidade e alta expressividade. Ele pode cobrir diversos cenários, desde frases longas até diálogos complexos, e até mesmo imitar estilos de voz e efeitos sonoros.

A demonstração mostra o uso de duas interfaces online: a "MOSS-VoiceGenerator", para converter texto em fala com parâmetros ajustáveis, e a "MOSS-TTS", que permite a clonagem de voz a partir de um arquivo de áudio de referência.

Insights principais:
- Ferramentas de IA como MOSS-TTS estão se tornando acessíveis via interfaces web amigáveis
- Modelos open source oferecem qualidade profissional comparável a serviços pagos
- A clonagem de voz permite personalização avançada da saída
- O natureza open source permite contribuição da comunidade e adaptação para diversos usos
- A tecnologia de geração de voz evoluiu rapidamente, tornando-se viável para muitas aplicações
"""

def main():
    print("[INFO] Testando Skypedia...")
    print(f"[INFO] Banco de dados: {db_path}")

    # Conectar ao banco
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    # Carregar sqlite-vec
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)

    # Criar tabela virtual para skypedia se não existir
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_skypedia USING vec0(
            embedding FLOAT[384]
        )
    """)

    # Criar tabela de metadata se não existir
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            collection TEXT NOT NULL,
            source_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vector_rowid INTEGER
        )
    """)

    conn.commit()

    # Carregar modelo de embedding
    print("[INFO] Carregando modelo de embedding...")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print("[OK] Modelo carregado!")

    # Gerar embedding
    print("[INFO] Gerando embedding do conteúdo...")
    embedding = model.encode(VIDEO_CONTENT).tolist()
    print(f"[OK] Embedding gerado: {len(embedding)} dimensões")

    # Inserir na coleção skypedia
    print("[INFO] Inserindo na coleção skypedia...")
    serialized = serialize_vector(embedding)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vec_skypedia(embedding) VALUES (?)", [serialized])
    vector_rowid = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO memory_metadata (content, collection, source_type, vector_rowid)
        VALUES (?, ?, ?, ?)
        """,
        (VIDEO_CONTENT, "skypedia", "youtube", vector_rowid)
    )
    memory_id = cursor.lastrowid
    conn.commit()
    print(f"[OK] Memória inserida com ID: {memory_id}")

    # Buscar para testar
    print("\n[INFO] Testando busca...")
    query = "text to speech open source"
    query_embedding = model.encode(query).tolist()
    serialized_query = serialize_vector(query_embedding)

    cursor.execute(
        """
        SELECT
            v.rowid as vector_rowid,
            m.id,
            m.content,
            distance
        FROM vec_skypedia v
        LEFT JOIN memory_metadata m ON m.vector_rowid = v.rowid
        WHERE v.embedding MATCH ?
          AND k = ?
          AND m.collection = ?
        ORDER BY distance
        """,
        [serialized_query, 1, "skypedia"]
    )

    results = cursor.fetchall()
    if results:
        print(f"[OK] Encontrado {len(results)} resultado(s):")
        for vector_rowid, memory_id, content, distance in results:
            print(f"   Distance: {distance:.4f}")
            print(f"   Content: {content[:100]}...")
    else:
        print("[WARN] Nenhum resultado encontrado")

    # Estatísticas
    cursor.execute(
        "SELECT COUNT(*) FROM memory_metadata WHERE collection = ?",
        ("skypedia",)
    )
    count = cursor.fetchone()[0]
    print(f"\n[INFO] Estatísticas skypedia: {count} memórias")

    conn.close()

if __name__ == "__main__":
    main()
