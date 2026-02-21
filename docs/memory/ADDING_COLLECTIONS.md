# Adicionando Novas Coleções de Memória

## Visão Geral

O sistema de memória da Sky é organizado em **coleções especializadas**, cada uma com seu propósito e política de retenção.

## Coleções Padrão

| Nome | Propósito | Retenção |
|------|-----------|----------|
| `identity` | Quem Sky é | Permanente |
| `shared-moments` | Memórias afetivas | Permanente |
| `teachings` | Ensinamentos do pai | Permanente |
| `operational` | Contexto recente | 30 dias |

## Como Adicionar uma Nova Coleção

### 1. Definir a Coleção

Edite `src/core/sky/memory/collections/collections.py`:

```python
# Adicione à lista DEFAULT_COLLECTIONS
DEFAULT_COLLECTIONS = [
    # ... coleções existentes ...
    CollectionConfig(
        name="projects",           # Nome único
        purpose="Projetos e iniciativas em andamento",
        retention_days=90,         # 90 dias
        embedding_enabled=True,    # Gerar embeddings
    ),
]
```

### 2. Atualizar o VectorStore

Edite `src/core/sky/memory/vector_store/vector_store.py`:

```python
class VectorStore:
    # Coleções disponíveis
    COLLECTIONS = [
        "identity",
        "shared-moments",
        "teachings",
        "operational",
        "projects",  # ← Adicione aqui
    ]
```

### 3. (Opcional) Adicionar Padrões de Roteamento

Se quiser que o `IntentRouter` roteie queries para sua coleção, edite `src/core/sky/memory/cognitive_layer/cognitive_layer.py`:

```python
class IntentRouter:
    PATTERNS = {
        # ... padrões existentes ...
        "projects": [
            r"projeto .+ (andamento|atual|status)",
            r"qual (projeto|iniciativa)",
        ],
    }
```

### 4. (Opcional) Adicionar Inferência Automática

Para que `PersistentMemory._infer_collection()` reconheça sua coleção, edite `src/core/sky/memory/__init__.py`:

```python
def _infer_collection(self, content: str) -> str:
    content_lower = content.lower()

    # ... padrões existentes ...

    if any(kw in content_lower for kw in ["projeto", "iniciativa"]):
        return "projects"

    # ... restante do código ...
```

## Testando a Nova Coleção

```python
from src.core.sky.memory import get_cognitive_memory

cognitive = get_cognitive_memory()

# Aprender na nova coleção
cognitive.learn(
    content="Projeto X está em andamento",
    collection="projects"
)

# Buscar na coleção específica
results = cognitive.search(
    query="status do projeto",
    collection="projects",
    top_k=5
)
```

## Política de Retenção

### Retenção Temporária (dias)

```python
CollectionConfig(
    name="temporary",
    purpose="Dados temporários",
    retention_days=7,  # 7 dias
)
```

Memórias expiram após N dias e são removidas por `prune_expired_memories()`.

### Retenção Permanente

```python
CollectionConfig(
    name="permanent",
    purpose="Dados importantes",
    retention_days=None,  # None = permanente
)
```

Memórias nunca expiram automaticamente.

## Considerações

### Performance

- **Mais coleções** = Mais tabelas virtuais = Ligeiramente mais lento
- **Limite recomendado:** Máximo 10 coleções ativas

### Nomenclatura

- Use **kebab-case**: `user-preferences`, `work-logs`
- Use **nomes descritivos**: `shared-moments` (não `memories-2`)
- Evite nomes genéricos: `data`, `items`, `stuff`

### Embeddings

Coleções com `embedding_enabled=False` não geram embeddings, apenas armazenam texto:

```python
CollectionConfig(
    name="raw-logs",
    purpose="Logs brutos sem busca semântica",
    retention_days=7,
    embedding_enabled=False,  # ← Sem embeddings
)
```

Útil para dados que não precisam de busca semântica.

## Exemplo Completo

Adicionando coleção `goals` (metas/objetivos):

```python
# 1. DEFAULT_COLLECTIONS
CollectionConfig(
    name="goals",
    purpose="Metas e objetivos a alcançar",
    retention_days=365,  # 1 ano
)

# 2. VectorStore.COLLECTIONS
COLLECTIONS = [..., "goals"]

# 3. IntentRouter.PATTERNS
"goals": [
    r"(meta|objetivo) .+ (concluída|atingida)",
    r"progresso .+ meta",
]

# 4. _infer_collection()
if any(kw in content_lower for kw in ["meta", "objetivo", "goal"]):
    return "goals"
```

Uso:

```python
memory.learn("Meta: Aprender Rust", collection="goals")
results = memory.search("quais minhas metas?")
```
