# Tasks: Corrigir Lock do VectorStore no SQLite

## 1. VectorStore

- [x] 1.1 Adicionar `PRAGMA journal_mode=WAL` e `PRAGMA busy_timeout=5000` após abrir conexão em `_init_db()`

## 2. EmbeddingClient

- [x] 2.1 Adicionar `PRAGMA journal_mode=WAL` e `PRAGMA busy_timeout=5000` após abrir conexão em `_init_cache()`
- [x] 2.2 Adicionar `PRAGMA journal_mode=WAL` e `PRAGMA busy_timeout=5000` em `_get_from_cache()` após abrir conexão
- [x] 2.3 Adicionar `PRAGMA journal_mode=WAL` e `PRAGMA busy_timeout=5000` em `_save_to_cache()` após abrir conexão

## 3. CollectionManager

- [x] 3.1 Adicionar `PRAGMA journal_mode=WAL` e `PRAGMA busy_timeout=5000` em todos os métodos que abrem conexão

## 4. Verificação

- [x] 4.1 Testar operações concorrentes: VectorStore + EmbeddingClient simultaneamente
- [x] 4.2 Verificar que arquivos .db-wal e .db-shm são criados
- [x] 4.3 Testar cenário anterior que causava "database is locked"
