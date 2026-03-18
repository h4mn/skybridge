# Formato do Banco de Dados - sky_memory.db

## Visão Geral

O banco `~/.skybridge/sky_memory.db` usa **SQLite** com a extensão **sqlite-vec** para busca vetorial.

## Estrutura

### Tabelas Relacionais

#### `memory_metadata`
Armazena conteúdo e metadados das memórias.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER | PK auto-increment |
| `content` | TEXT | Conteúdo da memória |
| `collection` | TEXT | Nome da coleção |
| `source_type` | TEXT | Tipo da fonte (chat, code, docs, logs, user, demo) |
| `created_at` | TIMESTAMP | Data de criação |
| `vector_rowid` | INTEGER | Referência para tabela vetorial |

#### `embeddings_cache`
Cache de embeddings para evitar re-geração.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER | PK auto-increment |
| `text_hash` | TEXT | Hash SHA256 do texto (UNIQUE) |
| `text` | TEXT | Texto original |
| `embedding` | BLOB | Embedding serializado (float array) |
| `model_name` | TEXT | Nome do modelo usado |
| `created_at` | TIMESTAMP | Data de criação |

#### `collection_config`
Configuração das coleções de memória.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `name` | TEXT | Nome da coleção (PK) |
| `purpose` | TEXT | Descrição do propósito |
| `retention_days` | INTEGER | Dias de retenção (NULL = permanente) |
| `embedding_enabled` | INTEGER | 1 se embeddings habilitado |
| `created_at` | TIMESTAMP | Data de criação |

### Tabelas Virtuais (sqlite-vec)

Cada coleção tem uma tabela virtual para busca vetorial:

#### `vec_identity`, `vec_shared_moments`, `vec_teachings`, `vec_operational`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `rowid` | INTEGER | PK (corresponde a vector_rowid em memory_metadata) |
| `embedding` | FLOAT[384] | Vetor de embedding (dimensão do modelo MiniLM) |

A busca é feita usando a sintaxe `MATCH` do sqlite-vec:

```sql
SELECT v.rowid, v.distance
FROM vec_teachings v
WHERE v.embedding MATCH ?
  AND k = 5
ORDER BY v.distance
```

## Dimensões do Embedding

- **Modelo:** `paraphrase-multilingual-MiniLM-L12-v2`
- **Dimensão:** 384 floats
- **Tamanho:** 384 × 4 bytes = ~1.5 KB por embedding
- **Serialização:** `struct.pack(f"{EMBEDDING_DIM}f", *vector)`

## Relacionamento

```
memory_metadata.vector_rowid → vec_*.*.rowid (1:1)
embeddings_cache.text_hash → índice único
collection_config.name → memory_metadata.collection (N:1)
```

## Manutenção

### Backup Simples
```bash
cp ~/.skybridge/sky_memory.db ~/.skybridge/sky_memory.db.backup
```

### Vacuum (Recompactar)
```bash
sqlite3 ~/.skybridge/sky_memory.db "VACUUM;"
```

### Verificar Tamanho
```bash
ls -lh ~/.skybridge/sky_memory.db
```

## Consultas Úteis

### Contar memórias por coleção
```sql
SELECT collection, COUNT(*) as count
FROM memory_metadata
GROUP BY collection;
```

### Memórias recentes (últimas 24h)
```sql
SELECT content, collection, created_at
FROM memory_metadata
WHERE datetime(created_at) > datetime('now', '-1 day')
ORDER BY created_at DESC;
```

### Cache hit ratio
```sql
SELECT
    COUNT(*) as total_memories,
    (SELECT COUNT(*) FROM embeddings_cache) as cached_embeddings,
    ROUND(100.0 * (SELECT COUNT(*) FROM embeddings_cache) / COUNT(*), 2) as cache_hit_pct
FROM memory_metadata;
```

## Schema Version

Versão atual: **1.0**

Mudanças de schema devem ser documentadas e migrations fornecidas.
