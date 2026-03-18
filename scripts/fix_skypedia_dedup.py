"""Script para adicionar deduplicação à Skypedia."""

import hashlib
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".skybridge" / "sky_memory.db"

def add_deduplication():
    """Adiciona coluna content_hash e índice único."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 1. Adicionar coluna content_hash se não existir
    try:
        cursor.execute("ALTER TABLE memory_metadata ADD COLUMN content_hash TEXT")
        print("[OK] Coluna content_hash adicionada")
    except sqlite3.OperationalError:
        print("[INFO] Coluna content_hash já existe")

    # 2. Gerar hashes para registros existentes
    print("[INFO] Gerando hashes para registros existentes...")
    cursor.execute("SELECT id, content FROM memory_metadata WHERE content_hash IS NULL")
    rows = cursor.fetchall()

    for row_id, content in rows:
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        cursor.execute(
            "UPDATE memory_metadata SET content_hash = ? WHERE id = ?",
            (content_hash, row_id)
        )
    print(f"[OK] {len(rows)} hashes gerados")

    # 3. Remover duplicatas ANTES de criar índice
    print("[INFO] Verificando duplicatas...")
    cursor.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT content_hash) FROM memory_metadata
    """)
    dup_count = cursor.fetchone()[0]

    if dup_count > 0:
        print(f"[WARN] Encontradas {dup_count} duplicatas! Removendo...")
        # Manter apenas o primeiro registro de cada hash
        cursor.execute("""
            DELETE FROM memory_metadata
            WHERE id NOT IN (
                SELECT MIN(id) FROM memory_metadata GROUP BY content_hash
            )
        """)
        deleted = cursor.rowcount
        print(f"[OK] {deleted} duplicatas removidas")
    else:
        print("[INFO] Nenhuma duplicata encontrada")

    # 4. Criar índice único
    try:
        cursor.execute("CREATE UNIQUE INDEX idx_content_hash ON memory_metadata(content_hash)")
        print("[OK] Índice único criado")
    except sqlite3.OperationalError as e:
        print(f"[WARN] Não foi possível criar índice: {e}")

    conn.commit()
    conn.close()

    # 4. Verificar resultado
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM memory_metadata WHERE collection='skypedia'")
    count = cursor.fetchone()[0]
    conn.close()

    print(f"\n[INFO] Total de memórias na skypedia: {count}")
    print("[OK] Deduplicação implementada!")

if __name__ == "__main__":
    add_deduplication()
