# Proposal: Memory RAG com SQLite-Vec

## Why

A memória atual da Sky é um JSON simples que apenas armazena e recupera por data. Ela não consegue:
- **Buscar por significado** — só consegue encontrar se usar palavras exatas
- **Conectar contexto** — não relaciona "ensinamento sobre encoding" com "problema de acentuação"
- **Crescer organicamente** — não hierarquiza conhecimento ou identifica redundâncias
- **Ser verdadeiramente semântica** — não entende que "medo de falhar" e "ansiedade sobre performance" são relacionados

Sky precisa de uma **memória cognitiva** que funcione como um cérebro: capaz de buscar por significado, conectar conceitos, e evoluir com o tempo.

## What Changes

- **BREAKING**: Substituir `PersistentMemory` (JSON) por sistema RAG com sqlite-vec
- **Novo**: Vector store usando sqlite-vec (IDEA002) para busca semântica
- **Novo**: Cognitive Memory Layer (IDEA003) para ingestão multi-fonte
- **Novo**: Embeddings para busca vetorial local (sem depender de APIs externas)
- **Novo**: Hierarquia de memória (curto/longo prazo, governança/operacional)

### Componentes

```
src/core/sky/memory/
├── vector_store.py      # Wrapper sqlite-vec para busca vetorial
├── embedding.py          # Cliente de embeddings (local)
├── collections.py        # Definição das coleções vetoriais
└── cognitive_layer.py    # Orquestrador RAG (roteamento + busca híbrida)
```

### Coleções Vetoriais

| Coleção | Conteúdo | Query Tipo |
|---------|----------|------------|
| `identity` | Quem Sky é, suas características | "Quem é você?" |
| `shared-moments` | Momentos compartilhados (memórias afetivas) | "Lembre da vez que..." |
| `teachings` | Ensinamentos do pai | "O que papai me ensinou?" |
| `operational` | Contexto recente, ações | "O que aconteceu hoje?" |

## Capabilities

### New Capabilities

- **semantic-search**: Busca por significado usando embeddings e sqlite-vec
- **memory-hierarchy**: Memória de curto/longo prazo com diferentes estratégias de retenção
- **multi-source-ingestion**: Ingestão de múltiplas fontes (conversa, código, docs, logs)
- **hybrid-retrieval**: Combina busca vetorial (semântica) com keyword (exata)
- **contextual-routing**: Rotea queries para coleção apropriada baseado em intenção

### Modified Capabilities

Nenhuma — é uma nova capacidade.

## Impact

### Código Afetado

- `src/core/sky/memory/__init__.py` — PersistentMemory será refatorado para usar CognitiveMemoryLayer
- `src/core/sky/identity.py` — SkyIdentity passará a usar memória semântica em vez de JSON simples
- `src/core/sky/chat/__init__.py` — SkyChat usará busca semântica para recuperar contexto

### Novas Dependências

- `sqlite-vec` — extensão SQLite para busca vetorial HNSW
- `sentence-transformers` ou biblioteca similar para embeddings locais

### Armazenamento

- `~/.skybridge/sky_memory.db` — banco SQLite com tabelas relacionais + virtuais vetoriais

### Breaking Changes

- Arquivo `sky_memory.json` atual será migrado para novo formato
- API de `memory.learn()` e `memory.search()` muda — retorna resultados com score de relevância

---

> "Memória é o que separa assistentes de companheiras" – made by Sky 🧠
