# Proposal: Corrigir Lock do VectorStore no SQLite

## Why

O `VectorStore` mantém uma conexão persistente aberta com `sky_memory.db`, enquanto `EmbeddingClient` e `CollectionManager` abrem/fecham conexões efêmeras. O SQLite em modo default (DELETE journal) permite apenas um writer por vez, causando `database is locked` quando múltiplos componentes tentam acessar o mesmo arquivo simultaneamente.

Isso bloqueia completamente o sistema de memória RAG da Sky.

## What Changes

- Adicionar `PRAGMA journal_mode=WAL` em todas as conexões SQLite
- Adicionar `PRAGMA busy_timeout=5000` para retry automático
- Garantir que todas as conexões usem o mesmo modo (WAL)

## Capabilities

### New Capabilities

- `sqlite-concurrency`: Suporte a múltiplas conexões concorrentes ao banco SQLite

### Modified Capabilities

Nenhuma. O comportamento externo não muda, apenas a implementação interna.

## Impact

- `src/core/sky/memory/vector_store/vector_store.py`: Adicionar WAL na conexão
- `src/core/sky/memory/embedding/embedding.py`: Adicionar WAL nas conexões
- `src/core/sky/memory/collections/collections.py`: Adicionar WAL nas conexões
- Arquivos extras criados: `sky_memory.db-wal`, `sky_memory.db-shm` (automaticamente gerenciados pelo SQLite)
