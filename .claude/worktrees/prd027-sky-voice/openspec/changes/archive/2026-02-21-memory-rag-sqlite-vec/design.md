# Design: Memory RAG com SQLite-Vec

## Context

### Estado Atual

A memória da Sky é implementada em `src/core/sky/memory/__init__.py`:

```python
class PersistentMemory:
    - Salva em JSON (~/.skybridge/sky_memory.json)
    - learn() → adiciona ao array
    - get_today_learnings() → filtra por data
    - search() → busca por substring (básico)
```

**Limitações:**
- Busca por substring não encontra sinônimos ou conceitos relacionados
- Não há noção de "importância" ou "relevância"
- Todos os aprendizados têm o mesmo peso
- Sem conexão entre conceitos (memória associativa)

### Restrições

- **Local-first**: Sky deve funcionar sem internet, sem APIs externas
- **Privacidade**: Dados não podem sair da máquina do usuário
- **Simplicidade**: KISS — não adicionar infraestrutura complexa
- **Performance**: Buscas devem ser <100ms mesmo com milhares de memórias

## Goals / Non-Goals

**Goals:**
- Busca semântica por significado (não só palavras)
- Memória associativa (conectar conceitos relacionados)
- Retenção hierárquica (memórias importantes vs. efêmeras)
- Score de relevância para classificar resultados

**Non-Goals:**
- Multi-tenancy (só um usuário por instalação)
- Sincronização nuvem (100% local)
- GraphRAG avançado (Fase 2)
- Memória distribuída

## Decisions

### 1. SQLite-Vec como Vector Store

**Decisão:** Usar `sqlite-vec` em vez de Qdrant/ChromaDB/Pinecone.

**Por que:**
- Zero infraestrutura (um arquivo `.db`)
- Performance HNSW sem servidor
- Integrado com SQLite (já usamos para dados relacionais)
- Local-first (sem dependência de nuvem)

**Alternativas consideradas:**
- Qdrant: Requer servidor Docker, infra complexa ❌
- ChromaDB: Bom, mas mais uma dependência ❌
- sqlite-vec: Leve, integrado, local ✅

### 2. Embeddings: sentence-transformers (local)

**Decisão:** Usar `sentence-transformers` com modelo multilingual.

**Modelo escolhido:** `paraphrase-multilingual-MiniLM-L12-v2`
- Pequeno (~400MB)
- Suporta português e inglês
- Razoável qualidade para uso geral

**Por que local:**
- Privacidade (dados não saem da máquina)
- Sem custo por API call
- Funciona offline

**Alternativas consideradas:**
- OpenAI embeddings: Custa $, precisa internet ❌
- BGE-M3: Melhor, mas maior (1GB+) — futuro ⏸️

### 3. Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────────┐
│                    COGNITIVE MEMORY LAYER                    │
│                      (Orquestrador)                          │
│  - route_query()     → identifica intenção                   │
│  - search()          → busca híbrida (vetorial + keyword)    │
│  - learn()           → ingestão com embedding                │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
    ┌───────────────────┐       ┌───────────────────┐
    │   VECTOR STORE    │       │  RELATIONAL STORE │
    │   (sqlite-vec)    │       │    (SQLite)       │
    │                   │       │                   │
    │ Coleções:         │       │ Tabelas:          │
    │ • identity        │       │ • metadata        │
    │ • shared-moments  │       │ • embeddings_cache│
    │ • teachings       │       │ •                │
    │ • operational     │       │                   │
    └───────────────────┘       └───────────────────┘
```

**Separação clara:**
- **Vector store**: Busca semântica (sqlite-vec)
- **Relational store**: Metadados, cache, flags (SQLite core)

### 4. Coleções Especializadas

Cada coleção tem um propósito e estratégia de retenção:

| Coleção | Propósito | Retenção | Embedding |
|---------|-----------|----------|-----------|
| `identity` | Quem Sky é | Permanente | Sim |
| `shared-moments` | Memórias afetivas | Permanente | Sim |
| `teachings` | Ensinamentos | Permanente | Sim |
| `operational` | Contexto recente | 30 dias | Sim |

**Por que coleções separadas:**
- Isolamento de busca (não buscar "quem sou eu" em "contexto recente")
- Performance (busca em índice menor)
- Retenção diferenciada

### 5. Busca Híbrida

**Decisão:** Combinar busca vetorial + keyword filtrada.

```
query = "o que papai me ensinou sobre encoding?"

1. Roteamento: detecta intenção → coleção "teachings"
2. Vetorial: busca por significado → top-K resultados
3. Filtragem: remove duplicatas, aplica threshold de score
4. Ranking: re-rankea por relevância + recência
```

**Por que híbrida:**
- Vetorial sozinho pode trazer resultados "semanticamente próximos" mas irrelevantes
- Keyword filtra ruído
- Combinação → precisão + recall

## Risks / Trade-offs

### Risk 1: Performance de Embedding Local

**Risco:** Gerar embedding em CPU pode ser lento (~50-100ms por texto).

**Mitigação:**
- Cache de embeddings (SQLite tabela `embeddings_cache`)
- Batch processing para múltiplas memórias
- Modelo pequeno (MiniLM)

### Risk 2: Tamanho do Banco

**Risco:** Banco `.db` pode crescer muito com milhares de embeddings.

**Mitigação:**
- Retenção diferenciada (30 dias para operacional)
- Pruning de memórias duplicadas/semelhantes
- Compactação periódica (VACUUM)

### Risk 3: Migração do JSON Atual

**Risco:** Usuário pode ter centenas de memórias no JSON atual.

**Mitigação:**
- Script de migração `migrate_json_to_rag.py`
- Backup automático antes de migrar
- Rollback: manter JSON por 30 dias

### Trade-off: Local vs. Qualidade

**Decisão:** Priorizar local-first sobre máxima qualidade de embedding.

**Consequência:** Modelo menor (MiniLM) em vez de SOTA (BGE-M3).

**Justificativa:** Privacidade e offline são mais importantes para Sky.

## Migration Plan

### Fase 1: Setup (Dia 1)

```bash
# Instalar dependências
pip install sqlite-vec sentence-transformers

# Criar schema do banco
python scripts/create_memory_schema.py
```

### Fase 2: Implementação Core (Dia 2-3)

- `vector_store.py` — Wrapper sqlite-vec
- `embedding.py` — Cliente sentence-transformers
- `collections.py` — Definição das coleções

### Fase 3: Cognitive Layer (Dia 4)

- `cognitive_layer.py` — Orquestrador RAG
- Busca híbrida + roteamento

### Fase 4: Migração (Dia 5)

```bash
# Backup + migração
python scripts/migrate_json_to_rag.py --backup
```

### Fase 5: Integração (Dia 6)

- Refatorar `PersistentMemory` para usar `CognitiveMemoryLayer`
- Atualizar `SkyIdentity` e `SkyChat`

### Fase 6: Testes + Rollout (Dia 7)

- Testes unitários e integração
- Feature flag `USE_RAG_MEMORY=true/false`
- Monitoramento

### Rollback Strategy

Se algo der errado:
1. Feature flag `USE_RAG_MEMORY=false`
2. Restaurar `sky_memory.json` do backup
3. Reverter código para versão anterior

## Open Questions

1. **Modelo de embedding definitivo?**
   - MiniLM é OK para MVP, mas podemos querer BGE-M3 depois.
   - **Resolução:** Minimally Abstracted — interface `EmbeddingClient` permite trocar.

2. **Threshold de score para relevância?**
   - Quão similar é "similar o suficiente"?
   - **Resolução:** Configurável, começar com 0.7 e ajustar empiricamente.

3. **Número de resultados (top-K)?**
   - Quantos memórias retornar por busca?
   - **Resolução:** Configurável, padrão K=5.

---

> "A arquitetura é a arte de esconder as decisões difíceis" – made by Sky 🏗️
