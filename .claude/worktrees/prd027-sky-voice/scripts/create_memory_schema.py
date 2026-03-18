# coding: utf-8
"""
Script de setup: Cria o schema do banco de memória da Sky.

Este script cria:
- Tabelas relacionais (metadata, cache)
- Tabelas virtuais vetoriais (sqlite-vec)
- Índices para performance
"""

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """Retorna o caminho do banco de dados."""
    data_dir = Path.home() / ".skybridge"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "sky_memory.db"


def create_schema(db_path: Path) -> None:
    """
    Cria o schema do banco de dados.

    Args:
        db_path: Caminho para o arquivo .db
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Criando schema em: {db_path}")

    # Tabela de metadados de memórias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            collection TEXT NOT NULL,
            source_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vector_rowid INTEGER
        )
    """)

    # Tabela de cache de embeddings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embeddings_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_hash TEXT UNIQUE NOT NULL,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de configurações das coleções
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collection_config (
            name TEXT PRIMARY KEY,
            retention_days INTEGER,
            purpose TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Inserir configurações das coleções
    collections = [
        ("identity", None, "Quem Sky é"),
        ("shared-moments", None, "Memórias afetivas compartilhadas"),
        ("teachings", None, "Ensinamentos do pai"),
        ("operational", 30, "Contexto recente (30 dias)"),
    ]

    cursor.executemany(
        "INSERT OR REPLACE INTO collection_config (name, retention_days, purpose) VALUES (?, ?, ?)",
        collections
    )

    conn.commit()
    conn.close()

    print("✓ Schema criado com sucesso!")


def main():
    """Função principal."""
    db_path = get_db_path()
    create_schema(db_path)
    print(f"\nBanco de dados criado em: {db_path}")
    print("\nPróximo passo: instalar dependências")
    print("  pip install sqlite-vec sentence-transformers")


if __name__ == "__main__":
    main()
