# Guia de Decisão: Quando Migrar de Standalone para Redis

**Data:** 2026-01-17
**Autor:** Sky
**Baseado em:** PRD017 (Mensageria Standalone)

---

## 📊 Matriz de Decisão por Números

### Pergunta Chave
**"Quando o custo de operar standalone supera o custo de Redis?"**

---

## 🎯 Break-Even Analysis

### Custo Standalone (Operacional)

| Item | Custo | Observação |
|------|------|------------|
| Desenvolvimento inicial | $0 | Já foi feito |
| Manutenção | ~2h/mês | Monitoramento de disco |
| Debug de problemas | ~1h/mês | Logs em arquivo |
| Risco de perda de dados | BAIXO | Arquivo local |
| **Custo Total Mensal** | **~$0** | Apenas tempo |

### Custo Redis (Infraestrutura)

| Item | Custo (Self-Hosted) | Custo (Managed) |
|------|---------------------|-----------------|
| Servidor (DigitalOcean) | $5-12/mês | - |
| Redis Cloud (Free tier) | $0 | 30MB RAM |
| Redis Cloud (Paid) | - | $7/mês (256MB) |
| Memória ElasticCache | - | $15-30/mês |
| Setup inicial | 2-4h | 1h |
| Manutenção | 0h/mês | 0h/mês |
| **Custo Total Mensal** | **$5-12/mês** | **$7-30/mês** |

---

## 📈 Análise por Throughput

### Capacidade Standalone (Baseada em Testes)

```
Operações de I/O em arquivo:
- enqueue(): ~50ms (write + sync)
- dequeue(): ~50ms (read + move)
- complete(): ~30ms (move)

Tempo total por job: ~130ms

Throughput teórico máximo:
- 1 job / 0.13s = ~7.7 jobs/segundo = ~460 jobs/hora

CAPADO com segurança (50% margem):
- ~230 jobs/hora

CAPADO com lock contention (múltiplos workers):
- ~20-30 jobs/hora (realístico)
```

### Capacidade Redis (Baseado em Documentação)

```
Operações de Redis:
- enqueue(): ~5ms (LPUSH)
- dequeue(): ~5ms (RPOP)
- complete(): ~2ms (SET)

Tempo total por job: ~12ms

Throughput teórico máximo:
- 1 job / 0.012s = ~83 jobs/segundo = ~5,000 jobs/hora

CAPADO com segurança (50% margem):
- ~2,500 jobs/hora

CAPADO com network overhead:
- ~500-1,000 jobs/hora (realístico)
```

### Break-Even Point

```
Standalone vs Redis:

┌─────────────────────────────────────────────────────────────┐
│  Standalone = Econômico se throughput < 20 jobs/hora        │
├─────────────────────────────────────────────────────────────┤
│  Redis = Econômico se throughput > 20 jobs/hora            │
│  PORQUE: Custo de operação (tempo) > Custo Redis ($7)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧮 Calculadora de Decisão

### Fórmula

```
SCORE = (jobs_per_hora / 20) * 3 +
        (latency_p95_ms / 100) * 2 +
        (backlog_age_min / 5) * 2 +
        (disk_usage_mb / 500) * 1

SE SCORE >= 5:
    → MIGRAR PARA REDIS

SENÃO:
    → CONTINUAR STANDALONE
```

### Exemplos Práticos

#### Cenário 1: Projeto Pequeno

```
Métricas:
- jobs_per_hora: 5
- latency_p95_ms: 40ms
- backlog_age_min: 1min
- disk_usage_mb: 50MB

SCORE = (5 / 20) * 3 + (40 / 100) * 2 + (1 / 5) * 2 + (50 / 500) * 1
      = 0.75 + 0.8 + 0.4 + 0.1
      = 2.05

DECISÃO: ✅ CONTINUAR STANDALONE (2.05 < 5)
Custo Mensal: $0
```

#### Cenário 2: Projeto Médio

```
Métricas:
- jobs_per_hora: 15
- latency_p95_ms: 80ms
- backlog_age_min: 3min
- disk_usage_mb: 200MB

SCORE = (15 / 20) * 3 + (80 / 100) * 2 + (3 / 5) * 2 + (200 / 500) * 1
      = 2.25 + 1.6 + 1.2 + 0.4
      = 5.45

DECISÃO: ⚠️ AVALIAR MIGRAÇÃO (5.45 >= 5)
Recomendação: Planejar migração nos próximos 30 dias
Custo Mensal Standalone: $0 + ~2h tempo de debug
Custo Mensal Redis: $7
```

#### Cenário 3: Projeto Alto Volume

```
Métricas:
- jobs_per_hora: 25
- latency_p95_ms: 150ms
- backlog_age_min: 8min
- disk_usage_mb: 600MB

SCORE = (25 / 20) * 3 + (150 / 100) * 2 + (8 / 5) * 2 + (600 / 500) * 1
      = 3.75 + 3.0 + 3.2 + 1.2
      = 11.15

DECISÃO: 🚀 MIGRAR PARA REDIS AGORA (11.15 >> 5)
Justificativa: Perda de produtividade > Custo Redis
Custo Mensal Standalone: $0 + ~10h tempo de debug
Custo Mensal Redis: $7
ECONOMIA: ~10h tempo - $7 = LUCRO
```

---

## 📊 Projeções de Crescimento

### Curva de Custo

```
Custo Acumulado (6 meses):

Standalone:
  Mês 1: $0
  Mês 2: $0
  Mês 3: $0  → throughput cresce
  Mês 4: 4h debug = $100 (tempo)
  Mês 5: 6h debug = $150 (tempo)
  Mês 6: 8h debug = $200 (tempo)
  ────────────────────────
  Total 6 meses: $450

Redis:
  Setup: 2h = $50 (tempo)
  Mês 1: $7
  Mês 2: $7
  Mês 3: $7
  Mês 4: $7
  Mês 5: $7
  Mês 6: $7
  ────────────────────────
  Total 6 meses: $50 + $42 = $92

BREAK-EVEN: Mês 4 (quando debug time > $50)
```

### Regra de Ouro

```
┌─────────────────────────────────────────────────────────────┐
│  MIGRAR SE:                                                  │
│  ✓ Você vai gastar > 4h/mês debugando standalone           │
│  OU throughput > 20 jobs/hora consistentemente              │
│  OU precisa de múltiplos workers                            │
├─────────────────────────────────────────────────────────────┤
│  FICAR STANDALONE SE:                                        │
│  ✓ throughput < 15 jobs/hora                                │
│  ✓ Single server suficiente                                │
│  ✓ Custo é prioridade absoluta                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔢 Thresholds Concretos

| Métrica | Standalone OK | Avaliar Migrar | Migrar Agora |
|---------|---------------|----------------|--------------|
| **jobs/hora** | < 10 | 10-20 | > 20 |
| **latência p95** | < 50ms | 50-100ms | > 100ms |
| **backlog age** | < 2min | 2-5min | > 5min |
| **backlog size** | < 20 | 20-50 | > 50 |
| **disk usage** | < 200MB | 200-500MB | > 500MB |
| **workers** | 1 | 1-2 | > 2 |

---

## 💰 Análise de ROI

### Cenário: 10 jobs/hora → 50 jobs/hora (crescimento 5x)

#### Opção A: Continuar Standalone

```
Mês 1 (10 jobs/h): $0
Mês 2 (20 jobs/h): 2h debug = $50
Mês 3 (30 jobs/h): 4h debug = $100
Mês 4 (40 jobs/h): 6h debug = $150
Mês 5 (50 jobs/h): 8h debug + restarts = $250
Mês 6 (50 jobs/h): 10h debug + latência = $300
─────────────────────────────────────────
Total: $850 + perda de agilidade
```

#### Opção B: Migrar no Mês 3

```
Mês 1 (10 jobs/h): $0 (standalone)
Mês 2 (20 jobs/h): $0 (standalone)
Mês 3 (30 jobs/h): MIGRAÇÃO = 4h setup + $7 Redis = $100
Mês 4 (40 jobs/h): $7
Mês 5 (50 jobs/h): $7
Mês 6 (50 jobs/h): $7
─────────────────────────────────────────
Total: $121 + agilidade mantida

ECONOMIA: $850 - $121 = $729 (86% de economia)
```

---

## 🎯 Playbook de Decisão

### Checklist de Migração

```
[ ] Passou 1 mês em produção com standalone?
[ ] Métricas coletadas são confiáveis?
[ ] Score da calculadora >= 5?
[ ] Orçamento aprovado para $7-30/mês?
[ ] Tempo disponível para migração (2-4h)?
[ ] Testes em staging passaram?

Se 3+ respostas SIM:
    → MIGRAR PARA REDIS
Senão:
    → CONTINUAR STANDALONE e reavaliar em 30 dias
```

### Timeline de Migração

```
Dia 1-2: Setup Redis local
Dia 3:   Implementar RedisJobQueue
Dia 4:   Testes A/B (standalone vs redis)
Dia 5:   Deploy em staging
Dia 6:   Monitoramento
Dia 7:   Deploy em produção (se estável)
```

---

## 📊 Decision Tree

```
                    INÍCIO
                       │
          throughput < 10/hora?
                       │
           ┌───────────┴───────────┐
          SIM                    NÃO
           │                      │
           │          latency_p95 > 100ms?
           │                      │
           │           ┌──────────┴──────────┐
           │          SIM                   NÃO
           │           │                      │
      STANDALONE    MIGRAR?          backlog > 50?
           │           │                      │
           │      ┌────┴────┐             ┌────┴────┐
           │      SIM       NÃO          SIM       NÃO
           │       │          │             │          │
      STANDALONE  REDIS    AVALIAR    AVALIAR    STANDALONE
                        em 30d     em 30d
```

---

## 🧪 Simulador de Decisão

```python
# tools/calculate_migration_score.py

def calculate_migration_score(metrics: dict) -> dict:
    """Calcula score e recomendação."""

    score = 0
    factors = []

    # Fator 1: Throughput (peso: 3)
    throughput = metrics["jobs_per_hour"]
    throughput_score = min(throughput / 20, 3)
    score += throughput_score
    factors.append({
        "name": "Throughput",
        "value": f"{throughput:.1f} jobs/h",
        "score": throughput_score,
        "weight": 3
    })

    # Fator 2: Latência (peso: 2)
    latency = metrics["enqueue_latency_p95_ms"]
    latency_score = min(latency / 100, 2)
    score += latency_score
    factors.append({
        "name": "Latência P95",
        "value": f"{latency:.1f}ms",
        "score": latency_score,
        "weight": 2
    })

    # Fator 3: Backlog Age (peso: 2)
    backlog_age = metrics["backlog_age_seconds"] / 60
    backlog_score = min(backlog_age / 5, 2)
    score += backlog_score
    factors.append({
        "name": "Backlog Age",
        "value": f"{backlog_age:.1f}min",
        "score": backlog_score,
        "weight": 2
    })

    # Fator 4: Disk Usage (peso: 1)
    disk = metrics["disk_usage_mb"]
    disk_score = min(disk / 500, 1)
    score += disk_score
    factors.append({
        "name": "Disk Usage",
        "value": f"{disk:.0f}MB",
        "score": disk_score,
        "weight": 1
    })

    # Decisão
    if score >= 5:
        recommendation = "MIGRAR PARA REDIS"
        color = "red"
        urgency = "IMEDIATA" if score >= 8 else "PLANEJADA"
    elif score >= 3:
        recommendation = "AVALIAR MIGRAÇÃO"
        color = "yellow"
        urgency = "EM 30 DIAS"
    else:
        recommendation = "CONTINUAR STANDALONE"
        color = "green"
        urgency = "REAVALIAR EM 90 DIAS"

    return {
        "score": round(score, 2),
        "recommendation": recommendation,
        "color": color,
        "urgency": urgency,
        "factors": factors
    }

# Exemplo de uso:
metrics = {
    "jobs_per_hour": 18.5,
    "enqueue_latency_p95_ms": 85,
    "backlog_age_seconds": 240,
    "disk_usage_mb": 350
}

result = calculate_migration_score(metrics)
print(f"Score: {result['score']}/7")
print(f"Recomendação: {result['recommendation']}")
print(f"Urgência: {result['urgency']}")
```

---

## 📊 Conclusão

### Regras Simples

1. **Startups/Projetos Pequenos**: Comece com Standalone
   - Zero custos
   - Funciona até 20 jobs/hora
   - Migre quando crescer

2. **Projetos Médios**: Avalie aos 3 meses
   - Se growing fast → Migrar
   - Se stable → Standalone é suficiente

3. **Projetos Grandes**: Redis desde o início
   - Throughput > 20 jobs/hora previsto
   - Múltiplos workers necessários
   - Orçamento disponível

---

`★ Insight ─────────────────────────────────────`
A decisão não é técnica, é **econômica**: "O custo de operar standalone (tempo de debug) supera o custo de Redis ($7/mês)?" Use a calculadora para responder objetivamente.
`─────────────────────────────────────────────────`

> "Números não mentem, mas interpretações sim" – made by Sky 🧮
