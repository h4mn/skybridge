# Issue #42: Implementação de Busca Fuzzy em Queries

## Resumo da Implementação

Implementamos funcionalidade de busca fuzzy usando o algoritmo `thefuzz` (alternativa moderna ao `fuzzywuzzy`) para permitir que usuários encontrem handlers de query mesmo com erros de digitação.

## Alterações Realizadas

### 1. Dependências
- **Arquivo**: `requirements.txt`
- **Adição**: `thefuzz>=0.3.0`
- **Motivo**: Biblioteca para cálculo de similaridade de strings (fuzzy matching)

### 2. Core - Query Registry
- **Arquivo**: `src/kernel/registry/query_registry.py`
- **Alterações**:
  - Import de `thefuzz.fuzz` e `thefuzz.process` (com fallback para substring se não disponível)
  - Novo método `fuzzy_search()` em `QueryRegistry`:
    - Suporta busca aproximada de nomes
    - Permite configurar `limit` (número máximo de resultados)
    - Permite configurar `min_score` (score mínimo 0-100)
    - Permite customizar `scorer` (função de similaridade)
    - Usa `fuzz.partial_ratio` por padrão (melhor para substrings)
    - Retorna lista de tuplas `(name, handler, score)` ordenada por score

### 3. Sky-RPC Registry
- **Arquivo**: `src/kernel/registry/skyrpc_registry.py`
- **Alterações**:
  - Novo método `fuzzy_search()` em `SkyRpcRegistry`:
    - Chama o método base do `QueryRegistry`
    - Enriquece resultados com metadados adicionais (kind, description, module, auth_required)
    - Retorna lista de dicionários com informações completas dos handlers

### 4. API Routes
- **Arquivo**: `src/runtime/delivery/routes.py`
- **Alterações**:
  - Novo endpoint `GET /search`:
    - Query param `q`: string de busca
    - Query param `limit`: número máximo de resultados (padrão: 5, max: 20)
    - Query param `min_score`: score mínimo (padrão: 60, range: 0-100)
    - Retorna JSON com `ok`, `query`, `total`, `results`
    - Referência à Issue #42 na documentação

### 5. CLI (Command Line Interface)
- **Arquivo**: `apps/cli/main.py`
- **Alterações**:
  - Novo comando `sb rpc search`:
    - Argumento posicional: `query` (string de busca)
    - Opção `--url, -u`: URL base da API
    - Opção `--limit, -l`: número máximo de resultados
    - Opção `--min-score, -s`: score mínimo
    - Opção `--output, -o`: formato de saída (table/json)
    - Exibe resultados em tabela colorida com score (verde >= 80, amarelo >= 60, vermelho < 60)
    - Mostra mensagem amigável quando nenhum resultado é encontrado

### 6. Testes Unitários
- **Arquivo**: `tests/kernel/registry/test_fuzzy_search.py`
- **Testes implementados**:
  1. `test_fuzzy_search_typo_correction`: Busca "fileop" encontra "fileops" ✓
  2. `test_fuzzy_search_webhook_typo`: Busca "webook" encontra "webhook" ✓
  3. `test_fuzzy_search_score_visibility`: Score de relevância visível ✓
  4. `test_fuzzy_search_returns_handler`: Retorna handler completo ✓
  5. `test_fuzzy_search_limit`: Respeita limite de resultados ✓
  6. `test_fuzzy_search_min_score_filter`: Filtra por score mínimo ✓
  7. `test_fuzzy_search_no_match`: Retorna vazio quando não há matches ✓
  8. `test_fuzzy_search_ordering`: Resultados ordenados por score decrescente ✓
  9. `test_fuzzy_search_case_insensitive`: Busca case-insensitive ✓
  10. `test_skyrpc_fuzzy_search_returns_enriched_metadata`: Metadados enriquecidos ✓
  11. `test_skyrpc_fuzzy_search_typo_correction`: SkyRpcRegistry typo correction ✓
  12. `test_skyrpc_fuzzy_search_score_visible`: Score visível em SkyRpcRegistry ✓

**Todos os testes passam (12/12)** ✓

## Critérios de Aceite

- [x] Busca "fileop" encontra "file_ops"
- [x] Busca "webook" encontra "webhook"
- [x] Score de relevância visível
- [x] Testes unitários

## Uso

### Via CLI
```bash
# Buscar handlers com erro de digitação
sb rpc search fileop
sb rpc search webook --limit 3
sb rpc search webhook --min-score 70

# Output em JSON
sb rpc search fileop --output json
```

### Via API
```bash
# Busca simples
curl "http://localhost:8888/search?q=fileop"

# Com parâmetros
curl "http://localhost:8888/search?q=webook&limit=3&min_score=70"
```

### Via Python
```python
from kernel.registry import get_query_registry, get_skyrpc_registry

# QueryRegistry básico
registry = get_query_registry()
results = registry.fuzzy_search("fileop", limit=5, min_score=60)
for name, handler, score in results:
    print(f"{name}: {score}")

# SkyRpcRegistry com metadados
skyrpc = get_skyrpc_registry()
results = skyrpc.fuzzy_search("webhook", limit=5)
for result in results:
    print(f"{result['method']}: {result['score']}")
```

## Detalhes Técnicos

### Algoritmo de Fuzzy Matching
- **Biblioteca**: `thefuzz` (fork mantido do `fuzzywuzzy`)
- **Scorer padrão**: `fuzz.partial_ratio`
  - Melhor para encontrar substrings em strings mais longas
  - Ex: "webook" vs "webhooks.receive" = 83 (vs 55 com `ratio`)
- **Score range**: 0-100 (onde 100 = match perfeito)

### Fallback
- Se `thefuzz` não estiver instalado, usa busca substring simples
- Garante funcionalidade básica mesmo sem a dependência opcional

### Performance
- Usa `process.extract()` do `thefuzz` para busca eficiente
- Limita resultados internamente para evitar processamento excessivo
- Ordenação por score decrescente é automática

## Benefícios

1. **UX Melhorada**: Usuários podem cometer erros de digitação e ainda encontrar handlers
2. **Descoberta**: Ajuda a encontrar handlers relacionados mesmo sem saber o nome exato
3. **Flexibilidade**: Permite configurar threshold de similaridade conforme necessidade
4. **Composição**: Score visível ajuda usuários a entenderem a qualidade do match

## Próximos Passos (Sugestões)

1. Adicionar fuzzy search em outras partes do sistema (ex: busca de arquivos, jobs)
2. Adicionar mais algoritmos de matching (ex: WRatio, token_sort_ratio)
3. Adicionar busca semântica com embeddings para matches contextuais
4. Adicionar sugestão automática "Did you mean?" quando busca exata falha

---

> "A simplicidade é o último grau de sofisticação" – made by Sky 🚀
