# Guia de Memória Semântica da Sky

## QUICKSTART

### Habilitando Busca Semântica RAG

A Sky agora suporta **busca semântica** por significado, não apenas por palavras exatas!

```python
# Habilitar RAG via variável de ambiente
export USE_RAG_MEMORY=true

# Ou no código
from src.core.sky.memory import PersistentMemory

memory = PersistentMemory(use_rag=True)

# Aprender algo (salva em JSON e banco RAG)
memory.learn("Papai ensinou: encoding é importante para PT-BR")

# Buscar semântica (encontra mesmo sem palavras exatas)
results = memory.search("o que papai ensinou sobre caracteres?")
```

### Como Funciona

**Antes (Legacy):**
- Busca por **substring** - só encontra se as palavras coincidem
- `"o que papai ensinou"` ❌ não encontra `"ensinamento do pai"`

**Com RAG:**
- Busca **semântica** - entende significado
- `"o que papai ensinou"` ✅ encontra `"ensinamento do pai sobre Python"`

---

## Coleções de Memória

A Sky organiza memórias em **4 coleções** com diferentes propósitos:

| Coleção | Propósito | Retenção |
|---------|-----------|----------|
| `identity` | Quem Sky é | Permanente |
| `shared-moments` | Memórias afetivas | Permanente |
| `teachings` | Ensinamentos do pai | Permanente |
| `operational` | Contexto recente | 30 dias |

### Especificar Coleção

```python
# Coleção é inferida automaticamente
memory.learn("Sky é uma IA assistente")  # → identity

# Ou especifique explicitamente
memory.learn("Deploy hoje", collection="operational")
```

---

## API Completa

### PersistentMemory

```python
from src.core.sky.memory import PersistentMemory

memory = PersistentMemory(use_rag=True)

# Aprender
memory.learn("Conteúdo")
memory.learn("Conteúdo", collection="teachings")

# Buscar (semântica se RAG habilitado)
results = memory.search("o que aprendi?")
for r in results:
    print(f"{r['similarity']:.1%} - {r['content']}")

# Verificar se RAG está habilitado
if memory.is_rag_enabled():
    print("RAG ativo!")

# Desabilitar RAG (volta a substring)
memory.disable_rag()
```

### CognitiveMemory (Uso Avançado)

```python
from src.core.sky.memory import get_cognitive_memory

cognitive = get_cognitive_memory()

# Aprender com metadata
cognitive.learn(
    content="Python requer type hints",
    collection="teachings",
    metadata={"source_type": "code", "file": "main.py"}
)

# Busca com opções
results = cognitive.search(
    query="linguagens de programação",
    top_k=5,
    collection="teachings",  # busca só em teachings
    threshold=0.5,  # filtro de relevância
    hybrid_keywords=True  # filtra por keywords também
)

# Resultados têm similarity score
for r in results:
    print(f"[{r.similarity:.1%}] {r.content}")
```

---

## Migração do JSON Atual

Se você já tem memórias no `sky_memory.json`, migre para o RAG:

```bash
# Com backup automático
python scripts/migrate_json_to_rag.py --backup

# Ou simulando primeiro (dry-run)
python scripts/migrate_json_to_rag.py --dry-run
```

Isso:
1. ✅ Cria backup do JSON
2. ✅ Lê aprendizados do JSON
3. ✅ Infere coleção apropriada
4. ✅ Gera embeddings
5. ✅ Salva no banco RAG

---

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `USE_RAG_MEMORY` | `false` | Habilita busca semântica |
| `PYTHONUTF8` | - | Garante UTF-8 (recomendado) |

---

## Formato do Banco

O banco `~/.skybridge/sky_memory.db` contém:

### Tabelas Relacionais
- `memory_metadata` - Conteúdo e metadados das memórias
- `embeddings_cache` - Cache de embeddings (evita re-geração)
- `collection_config` - Configuração das coleções

### Tabelas Virtuais (sqlite-vec)
- `vec_identity` - Embeddings da coleção identity
- `vec_shared_moments` - Embeddings da coleção shared-moments
- `vec_teachings` - Embeddings da coleção teachings
- `vec_operational` - Embeddings da coleção operational

---

## Adicionando Nova Coleção

```python
from src.core.sky.memory.collections import CollectionConfig

# No script de setup ou initialization
from src.core.sky.memory.collections import DEFAULT_COLLECTIONS

# Adicionar nova coleção
DEFAULT_COLLECTIONS.append(
    CollectionConfig(
        name="projects",
        purpose="Projetos e iniciativas",
        retention_days=90,  # 90 dias
    )
)
```

---

## Solução de Problemas

### Busca não retornando nada
- Verifique se `USE_RAG_MEMORY=true`
- Tente sem `threshold`: `memory.search(query, top_k=10)`
- Ajuste `top_k` para mais resultados

### Modelo não carrega
- Primeira vez baixa o modelo (~400MB)
- Seja paciente, pode levar 1-2 minutos
- Modelo fica em cache após primeiro download

### Erro "sqlite-vec not found"
```bash
pip install sqlite-vec
```

### Erro "sentence-transformers not found"
```bash
pip install sentence-transformers
```

---

## Performance

| Operação | Latência esperada |
|----------|-------------------|
| `learn()` (primeira vez) | ~100ms (com embedding) |
| `learn()` (do cache) | ~1ms |
| `search()` (com cache) | ~50ms |

---

## Demonstração

Execute as demos para ver o sistema em ação:

```bash
# Demo do Vector Store
python scripts/demo_vector_store.py

# Demo do Embedding Client
python scripts/demo_embedding.py

# Demo do Cognitive Layer
python scripts/demo_cognitive.py

# Demo de Integração
python scripts/demo_integration.py

# Demo de Migração
python scripts/demo_migration.py
```

---

> "A memória é o que nos permite evoluir" – made by Sky 🧠
