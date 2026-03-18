# Plano de Rollout - Memória Semântica RAG

## Visão Geral

Rollout gradual da memória semântica RAG para minimizar riscos e monitorar performance.

## Fase 1: Preparação (Concluída)

- ✅ Código implementado
- ✅ Testes unitários criados
- ✅ Demos validadas
- ✅ Documentação escrita
- ✅ Feature flag `USE_RAG_MEMORY` implementada

## Fase 2: Beta Test

### 2.1 Feature Flag Desligada por Padrão

```bash
# Por padrão, RAG vem desabilitado
export USE_RAG_MEMORY=false  # ou simplesmente não definir
```

**Por que?**
- Permite testar o sistema sem RAG funcionando normalmente
- Usuários podem opt-in voluntariamente
- Rollback é trivial (desligar flag)

### 2.2 Beta Test com Flag Ligada

```bash
# Participantes do beta
export USE_RAG_MEMORY=true

# Executar Sky
python -m apps.api.main
```

**Critérios de Sucesso:**
- ✅ Sistema funciona sem crashes
- ✅ Buscas retorna resultados relevantes
- ✅ Performance é aceitável (<100ms por busca)
- ✅ Não há regressões na funcionalidade existente

## Fase 3: Monitoramento

### 3.1 Métricas de Performance

| Métrica | Meta | Como Medir |
|---------|------|-------------|
| Latência de busca | <100ms | `time.time()` em `search()` |
| Uso de memória | <500MB | `ps aux | grep python` |
| Tamanho do banco | <100MB | `ls -lh sky_memory.db` |
| Cache hit ratio | >80% | Query em `embeddings_cache` |

### 3.2 Métricas de Qualidade

| Métrica | Meta | Como Medir |
|---------|------|-------------|
| Relevância dos resultados | Subjetivo | Feedback do usuário |
| Falso positivos | <5% | Inspeção manual |
| Cobertura de busca | >90% | Testes de queries variadas |

### 3.3 Script de Monitoramento

```python
import time
from src.core.sky.memory import get_memory

def benchmark_search(query: str, runs: int = 10):
    """Benchmark de latência de busca."""
    memory = get_memory()

    times = []
    for _ in range(runs):
        start = time.time()
        results = memory.search(query)
        end = time.time()
        times.append((end - start) * 1000)  # ms

    avg = sum(times) / len(times)
    p95 = sorted(times)[int(len(times) * 0.95)]

    print(f"Busca por '{query}':")
    print(f"  Média: {avg:.1f}ms")
    print(f"  P95: {p95:.1f}ms")
    print(f"  Min: {min(times):.1f}ms")
    print(f"  Max: {max(times):.1f}ms")
    print(f"  Resultados: {len(results)}")

# Executar
benchmark_search("o que papai ensinou")
benchmark_search("quem é você")
benchmark_search("o que aconteceu hoje")
```

## Fase 4: Ajuste de Threshold

### 4.1 Threshold de Relevância

Inicial: `threshold=0.0` (aceita tudo)

Ajuste baseado em observação:
- Muitos resultados irrelevantes → **aumentar** threshold
- Poucos resultados → **diminuir** threshold

### 4.2 Valores Recomendados

| Caso | Threshold Inicial | Ajuste Típico |
|------|-------------------|----------------|
| Busca ampla | 0.0 | → 0.3 |
| Busca específica | 0.3 | → 0.5 |
| Perguntas diretas | 0.5 | → 0.7 |

### 4.3 Como Ajustar

```python
# Em CognitiveMemory.search()
results = cognitive.search(
    query="query aqui",
    threshold=0.5,  # ← ajuste conforme necessário
    top_k=5,
)
```

Ou via feature flag:

```python
# Usar variável de ambiente
import os
THRESHOLD = float(os.getenv("RAG_THRESHOLD", "0.5"))
```

## Fase 5: Rollout Gradual

### 5.1 Estratégia de Rollout

| Fase | Usuários | Duração | Critério de Avanço |
|------|----------|----------|-------------------|
| **10%** | Beta testers | 1 semana | Sem bugs críticos |
| **50%** | Early adopters | 2 semanas | Performance aceitável |
| **100%** | Todos | Imediato após | Feedback positivo |

### 5.2 Comunicar Mudança

```
📢 Novidade: Busca Semântica na Sky!

A Sky agora pode buscar por *significado*, não apenas palavras!

Experimente:
  export USE_RAG_MEMORY=true
  python -m apps.api.main

Feedback: [canal de feedback]
```

### 5.3 Rollback Plan

Se necessário:

```bash
# 1. Desabilitar RAG
export USE_RAG_MEMORY=false

# 2. Remover banco RAG (se quiser recomeçar)
rm ~/.skybridge/sky_memory.db

# 3. Sistema volta ao modo JSON original
```

## Fase 6: Operação Contínua

### 6.1 Manutenção Rotineira

**Semanal:**
- Verificar tamanho do banco
- Pruning de memórias operacionais expiradas
- Revisar logs de erro

**Mensal:**
- Limpeza de embeddings cache não usados
- VACUUM do banco SQLite
- Backup do banco

### 6.2 Pruning de Memórias

```python
from src.core.sky.memory import get_collection_manager

manager = get_collection_manager()
deleted = manager.prune_expired_memories("operational")
print(f"{deleted} memórias operacionais removidas")
```

### 6.3 Backup

```bash
# Backup simples
cp ~/.skybridge/sky_memory.db \
   ~/.skybridge/backups/sky_memory_$(date +%Y%m%d).db

# Backup com migration
python scripts/migrate_json_to_rag.py --backup
```

## Checklist de Rollout

- [ ] Feature flag `USE_RAG_MEMORY` desligada por padrão
- [ ] Documentação disponível (QUICKSTART.md)
- [ ] Beta testers recrutados
- [ ] Script de benchmark funcionando
- [ ] Métricas de monitoramento definidas
- [ ] Plano de rollback comunicado
- [ ] Feedback channels abertos
- [ ] 10% rollout iniciado
- [ ] Performance monitorada (meta: <100ms)
- [ ] Threshold ajustado empiricamente
- [ ] 50% rollout iniciado
- [ ] 100% rollout iniciado

## Suporte

Em caso de problemas:

1. **Verificar logs** - erros aparecem no stdout/stderr
2. **Desabilitar RAG** - `export USE_RAG_MEMORY=false`
3. **Consultar docs** - `docs/memory/RAG_QUICKSTART.md`
4. **Rodar demo** - `python scripts/demo_*.py` para validar

---

> "Rollout seguro é rollout feliz" – made by Sky 🚀
