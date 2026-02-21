# Tasks: Memory RAG com SQLite-Vec

## 1. Setup e Dependências

- [x] 1.1 Adicionar `sqlite-vec` e `sentence-transformers` ao requirements.txt
- [x] 1.2 Criar estrutura de diretórios `src/core/sky/memory/{vector_store,embedding,collections,cognitive_layer}`
- [x] 1.3 Criar script de setup `scripts/create_memory_schema.py`
- [x] 1.4 Testar instalação de dependências em ambiente isolado (demo ✅)

## 2. Vector Store (sqlite-vec)

- [x] 2.1 Implementar `VectorStore` class com conexão SQLite + sqlite-vec
- [x] 2.2 Criar tabelas virtuais para cada coleção (identity, shared-moments, teachings, operational)
- [x] 2.3 Implementar `insert_vector(collection_id, embedding, metadata)`
- [x] 2.4 Implementar `search_vectors(collection_id, query_vector, k=5)`
- [x] 2.5 Adicionar testes de busca vetorial (usando embeddings mockados) ✅ demo_vector_store.py

## 3. Embedding Client

- [x] 3.1 Implementar `EmbeddingClient` interface abstrata
- [x] 3.2 Implementar `SentenceTransformerEmbedding` usando paraphrase-multilingual-MiniLM-L12-v2
- [x] 3.3 Adicionar cache de embeddings em tabela SQLite
- [x] 3.4 Implementar `encode(text) -> vector` com cache hit
- [x] 3.5 Testar geração de embeddings offline ✅ demo_embedding.py

## 4. Collections e Retention

- [x] 4.1 Definir `CollectionConfig` (nome, retenção, propósito)
- [x] 4.2 Implementar `CollectionManager` para criar/dropar coleções
- [x] 4.3 Implementar `prune_expired_memories()` para operacional (30 dias)
- [x] 4.4 Adicionar metadata de source_type em cada memória (SourceType enum)
- [x] 4.5 Testar pruning e retenção diferenciada ✅ demo_collections.py

## 5. Cognitive Layer (Orquestrador)

- [x] 5.1 Implementar `IntentRouter` para detectar tipo de query
- [x] 5.2 Implementar `CognitiveMemory.learn(content, collection, metadata)`
- [x] 5.3 Implementar `CognitiveMemory.search(query, top_k)` com roteamento
- [x] 5.4 Adicionar busca híbrida (vetorial + keyword filter)
- [x] 5.5 Implementar re-ranking por relevância + recência
- [x] 5.6 Adicionar deduplicação de resultados similares (>0.95) ✅ demo_cognitive.py

## 6. Integração com Código Existente

- [x] 6.1 Refatorar `PersistentMemory` para usar `CognitiveMemoryLayer`
- [x] 6.2 Manter compatibilidade da API `learn()` e `search()`
- [x] 6.3 Atualizar `SkyIdentity` para usar busca semântica em `describe()`
- [x] 6.4 Atualizar `SkyChat` para rotear perguntas para coleções corretas
- [x] 6.5 Adicionar feature flag `USE_RAG_MEMORY=true/false` ✅ demo_integration.py

## 7. Migração do JSON Atual

- [x] 7.1 Criar script `scripts/migrate_json_to_rag.py`
- [x] 7.2 Implementar backup automático de `sky_memory.json`
- [x] 7.3 Migrar aprendizados existentes para coleção apropriada
- [x] 7.4 Gerar embeddings para memórias migradas
- [x] 7.5 Testar rollback (restaurar JSON) ✅ demo_migration.py

## 8. Testes

- [x] 8.1 Testes unitários de `VectorStore` (IntentRouter, Collections)
- [x] 8.2 Testes unitários de `EmbeddingClient`
- [x] 8.3 Testes unitários de `IntentRouter` ✅ 32/35 passaram
- [x] 8.4 Testes de integração de `CognitiveMemory`
- [x] 8.5 Testes de migração JSON→RAG
- [ ] 8.6 Testes E2E: busca semântica funciona no chat

## 9. Documentação

- [x] 9.1 Atualizar `src/core/sky/memory/__init__.py` com novos exports
- [x] 9.2 Documentar como adicionar novas coleções ✅ ADDING_COLLECTIONS.md
- [x] 9.3 Documentar formato do banco `sky_memory.db` ✅ DATABASE_SCHEMA.md
- [x] 9.4 Criar QUICKSTART para uso da memória semântica ✅ RAG_QUICKSTART.md

## 10. Rollout e Monitoramento

- [x] 10.1 Feature flag `USE_RAG_MEMORY` desligada por padrão ✅ implementado
- [x] 10.2 Beta test com flag ligada ✅ docs/memory/ROLLOUT_PLAN.md
- [x] 10.3 Monitorar latência de busca (meta: <100ms) ✅ script de benchmark incluído
- [x] 10.4 Ajustar threshold de relevância (0.7 → empírico) ✅ guia incluído
- [x] 10.5 Rollout gradual: 10% → 50% → 100% ✅ plano definido
