# Comparativo de Bancos de Dados para Sistema de Trading

**Data:** 2026-05-09 | **Contexto:** SKY-39 + evolução multi-corretora + HFT futuro

## Cenário

Sistema de trading automatizado em Python evoluindo em 3 fases:

| Fase | Descrição | Escala |
|---|---|---|
| **Atual** | Paper trading, 1 corretora, 1min ticks | ~1K ticks/dia |
| **M2** | Multi-corretora (Binance, Coinbase, Yahoo), múltiplas estratégias simultâneas | ~50K ticks/dia |
| **Futuro** | HFT competitivo, sub-millisecond, múltiplos exchanges | ~1M+ ticks/dia |

---

## Performance

| Métrica | SQLite+WAL | DuckDB | PostgreSQL | TimescaleDB | ClickHouse | QuestDB |
|---|---|---|---|---|---|---|
| **Writes/sec (single)** | ~3,600 | ~100-500 | ~1,000-5,000 | **~111K** | ~50K+ | **~300K+** |
| **Writes/sec (batch)** | ~50K+ | ~15-20K | ~30K+ | **~1.4M** | ~200K+ | **~1M+** |
| **Analytics (OLAP)** | Lento | **10-100x vs SQLite** | Médio | **10-35x vs PG** | **Muito rápido** | Rápido |
| **Compression ratio** | N/A | N/A | N/A | **10-33x** | 10-30x | N/A |
| **File size (1M rows)** | ~60MB | **~35MB** | N/A (server) | ~35MB (compresso) | ~35MB | ~40MB |

### TimescaleDB — Destaques

- **Hypertables**: particionamento automático por tempo, chunk pruning elimina scans desnecessários
- **Continuous Aggregates**: OHLCV materializado e auto-refresh (5s, 1m, 15m, 1h, 1d) sem cron jobs
- **Compression**: 10-33x em dados de tick (Cloudflare: 1,616 GB → 49 GB em produção)
- **Retention Policy**: `add_retention_policy('ticks', INTERVAL '10 days')` — drop de chunks é instantâneo (metadata), sem VACUUM

### QuestDB — Destaque HFT

- Projetado para ingestão de time-series em alta frequência
- 4-22x mais rápido que TimescaleDB em ingestion pura (benchmarks QuestDB)
- Zero-friction SIMD-based analytics
- Mas: SQL limitado, sem JOINs completos, menos maduro

---

## Trading-Specific

| Critério | SQLite+WAL | DuckDB | PostgreSQL | TimescaleDB | ClickHouse | QuestDB |
|---|---|---|---|---|---|---|
| **Multi-corretora simultânea** | Single writer | Single writer | **Multi-writer** | **Multi-writer (MVCC)** | **Multi-writer** | Multi-writer |
| **ACID (nunca perde trade)** | **Completo** | Parcial | **Completo** | **Completo** | Com tuning | Limitado |
| **Window functions (MA, Sharpe)** | OK | **Excelente** | **Excelente** | **Excelente** | Suporta | Limitado |
| **ASOF JOIN (time-series)** | Não | **Nativo** | Não | **Nativo** | **Nativo** | **Nativo** |
| **OHLCV automático** | Manual | Nativo | Manual | **Continuous Aggregates** | Nativo | Nativo |
| **Retention automático** | Manual | N/A | Manual (VACUUM) | **Built-in** | TTL | Built-in |
| **Compression automática** | N/A | N/A | N/A | **Built-in (10-33x)** | Built-in | N/A |
| **Chunk sizing (ticks)** | N/A | N/A | N/A | **Auto (25M rows/chunk)** | Manual | Manual |

### Chunk Sizing — TimescaleDB

Fórmula: `chunk_interval = 25,000,000 / rows_per_second`

| Ingest Rate | Intervalo Ideal | Rows/Chunk |
|---|---|---|
| 100 rows/sec (atual) | ~3 dias | ~25M |
| 1,000 rows/sec | ~7 horas | ~25M |
| 10,000 rows/sec (M2) | ~40 minutos | ~25M |
| 60,000 rows/sec (HFT) | ~7 minutos | ~25M |

---

## Operacional

| Critério | SQLite+WAL | DuckDB | TimescaleDB | ClickHouse | QuestDB |
|---|---|---|---|---|---|
| **Tipo** | Embedded | Embedded | Servidor (extenso PG) | Servidor | Servidor |
| **Lib Python** | `sqlite3` (stdlib) | `duckdb` | `psycopg3`/`asyncpg` | `clickhouse-connect` | `questdb` |
| **Setup** | **Zero** | `pip install` | Docker/WSL2 | Docker | Docker |
| **Windows** | **Nativo** | **Nativo** | Docker+WSL2 | Docker | Docker |
| **Uso memória** | Baixo | Médio | 4-8GB (paper) | Alto | Médio |
| **Cloud path** | N/A | N/A | **Timescale Cloud ($36/mês)** | ClickHouse Cloud | QuestDB Cloud |
| **Multi-node** | N/A | N/A | **Sim (2x → 150K rows/sec)** | Sim | Limitado |

### TimescaleDB — Setup

```bash
# Docker (recomendado no Windows)
docker run -d --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=trading \
  timescale/timescaledb:latest-pg16

# Python
pip install "psycopg[binary]"
```

```python
# Criar hypertable para ticks
conn.execute("CREATE EXTENSION timescaledb")
conn.execute("""
    CREATE TABLE ticks (
        time    TIMESTAMPTZ NOT NULL,
        symbol  TEXT NOT NULL,
        price   DECIMAL,
        volume  DECIMAL,
        broker  TEXT
    )
""")
conn.execute("""
    SELECT create_hypertable('ticks', 'time',
        chunk_time_interval => INTERVAL '1 day')
""")

# Continuous Aggregate — OHLCV 1min automático
conn.execute("""
    CREATE MATERIALIZED VIEW ohlc_1min
    WITH (timescaledb.continuous) AS
    SELECT
        time_bucket('1 min', time) AS bucket,
        symbol, broker,
        FIRST(price, time) AS open,
        MAX(price) AS high,
        MIN(price) AS low,
        LAST(price, time) AS close,
        SUM(volume) AS volume
    FROM ticks
    GROUP BY bucket, symbol, broker
""")

# Auto-refresh + retention
conn.execute("""
    SELECT add_continuous_aggregate_policy('ohlc_1min',
        start_offset => INTERVAL '1 day',
        end_offset   => INTERVAL '1 min',
        schedule_interval => INTERVAL '1 min')
""")
conn.execute("""
    SELECT add_retention_policy('ticks', INTERVAL '10 days')
""")
conn.execute("""
    ALTER TABLE ticks SET (
        timescaledb.compress,
        timescaledb.compress_segmentby = 'symbol, broker'
    )
""")
```

---

## Descartados (para este cenário)

### TinyDB
- JSON em arquivo, sem índices, sem ACID, degrada acima de 10K registros

### Redis (para persistência)
- Persistência eventual = risco de perder trades
- Benchmark real: SQLite 3x mais rápido localmente (sem overhead de rede)
- Futuro: serve como **hot cache** no decision loop HFT, nunca como storage principal

### ClickHouse
- Imbatível em analytics de escala, mas setup complexo no Windows
- Overkill para sistema que ainda está em paper trading
- Reavaliar se volume passar de 10M+ ticks/dia

---

## Fit por Use Case (1-5)

| Use Case | SQLite+WAL | DuckDB | TimescaleDB | QuestDB |
|---|---|---|---|---|
| Tick storage tempo real | 4 | 2 | **5** | 5 |
| Trade history / journaling | **5** | 3 | **5** | 3 |
| Multi-corretora simultânea | 2 | 1 | **5** | 4 |
| Analytics (WR, PnL, Sharpe) | 2 | **5** | 4 | 3 |
| Backtesting storage | 2 | **5** | 4 | 3 |
| OHLCV automático | 1 | 3 | **5** | 4 |
| HFT-ready | 1 | 1 | 2 | **4** |
| Evolução para produção SaaS | 1 | 2 | **5** | 3 |
| **TOTAL** | **18** | **21** | **35** | **29** |

---

## HFT — Perspectiva Honesta

**Nenhum banco de dados geral é adequado para HFT verdadeiro (<100μs).**

Para trading de alta frequência competitivo, a arquitetura é:

```
Exchange WebSocket ──→ Order Book em memória (Rust/C)
                          │
                          ├─→ Decision Loop (<1ms, in-memory)
                          │
                          └─→ Async write → Banco de dados (persistence)
```

| Camada | Tecnologia | Latência |
|---|---|---|
| **Hot path** (decisão) | In-memory (dict/Rust/Redis) | <100μs |
| **Warm path** (persistência) | TimescaleDB / QuestDB | 1-50ms |
| **Cold path** (analytics) | DuckDB / ClickHouse | 100ms+ |
| **Archive** | Parquet / S3 | Batch |

O banco de dados **nunca** está no caminho crítico de decisão em HFT. Ele recebe dados async para persistência e analytics.

---

## Recomendação por Fase

### Fase Atual (Paper Trading, SKY-39)

**SQLite+WAL** — resolve hoje com zero dependências.

```
Estratégias → SQLite+WAL (trades, posições)
                  │
                  └─ sync → DuckDB (analytics local)
```

### Fase M2 (Multi-Corretora)

**TimescaleDB em Docker** — multi-writer nativo, OHLCV automático, compression.

```
Binance  ──┐
Coinbase ──┤→ [Write Queue per broker] → TimescaleDB (hypertables)
Yahoo    ──┘                                    │
                                    Continuous Aggregates (OHLCV automático)
                                    Compression (10-33x)
                                    Retention (10 dias raw, infinito agregado)
```

### Fase Futuro (HFT)

**TimescaleDB (persistência) + QuestDB/kdb+ (hot path)**

```
Exchange WS → Order Book (memória/Rust)
                  │
                  ├─→ Decision Loop (in-memory, <1ms)
                  │
                  └─→ Async → TimescaleDB (trades, analytics)
                              QuestDB (tick raw, HFT-grade ingestion)
```

---

## Decisão

| Critério | SQLite+WAL + DuckDB | TimescaleDB |
|---|---|---|
| **Resolve SKY-39 hoje** | **Sim** | Sim (overkill) |
| **Evolui para multi-corretora** | Limitado (single writer) | **Nativo** |
| **Evolui para HFT** | Não | **Persistência sim** |
| **Setup hoje** | **Zero** | Docker + WSL2 |
| **Manutenção** | **Mínima** | Baixa |
| **Custo futuro** | Grátis | **Grátis** (self-hosted) ou $36/mês (cloud) |

**Veredito:** Começar com SQLite+WAL + DuckDB (resolve SKY-39 sem atrito). Planejar migração para TimescaleDB ao entrar na fase multi-corretora (M2). O `PaperStatePort` hexagonal já abstrai a persistência — trocar o adapter é cirurgia local.

---

## Anexo: SQLite+WAL no Multi-Corretora — Bloqueantes e Workarounds

### O problema central: Single Writer

SQLite usa **file-level write lock** — só 1 processo/gravação por vez. Em WAL mode, leitores não bloqueiam escritor e vice-versa, mas **2 escritores ainda se bloqueiam**.

```
Binance  ──→ WRITE ──┐
                      ├─→ [ contention! ] ──→ trading.db
Coinbase ──→ WRITE ──┘
```

### Bloqueantes por Severidade

#### B1 (CONTORNOUVÉL) — Contenção de escrita

**O que acontece:** Múltiplas estratégias tentam gravar ao mesmo tempo. Uma espera a outra.

```python
# Estratégia A grava tick da Binance
conn.execute("INSERT INTO ticks VALUES (...)")  # 5ms

# Estratégia B tenta gravar tick da Coinbase 0.3ms depois
conn.execute("INSERT INTO ticks VALUES (...)")  # BUSY! Aguarda busy_timeout
```

**Com `busy_timeout=5000`**: a segunda espera até 5 segundos pela liberação do lock. Se não conseguir, lança `sqlite3.OperationalError: database is locked`.

**Workaround — Write Queue centralizada:**

```
Estratégia A ──┐
               ├─→ [asyncio.Queue] ──→ 1 Writer Thread ──→ trading.db
Estratégia B ──┘
```

```python
import sqlite3
import asyncio
from threading import Thread

class SQLiteWriter:
    def __init__(self, db_path: str):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    async def write(self, sql: str, params: tuple):
        future = asyncio.get_event_loop().create_future()
        self._queue.put_nowait((sql, params, future))
        return await future

    def _run(self):
        import queue
        while True:
            try:
                sql, params, future = self._queue.get(timeout=1)
                self._conn.execute(sql, params)
                self._conn.commit()
                # resolve future no event loop
            except Exception as e:
                # set exception no future
                pass
```

**Custo:** latência extra de ~1-5ms por write (queue overhead). Para paper trading 1min, imperceptível. Para HFT, inaceitável.

---

#### B2 (CONTORNOUVÉL) — Analytics cross-corretora

**O que acontece:** Queries analíticas cruzando dados de múltiplas corretoras (PnL consolidado, Sharpe global, correlação entre brokers).

```sql
-- PnL consolidado por broker
SELECT broker,
       COUNT(*) as trades,
       AVG(profit) as avg_pnl,
       -- Window functions em 100K+ rows...
       -- SQLite: 2-5 segundos
       -- DuckDB: 50-200ms
FROM trades
GROUP BY broker;
```

**Workaround — DuckDB lê SQLite diretamente:**

```python
import duckdb

analytics = duckdb.connect()
result = analytics.execute("""
    SELECT broker,
           COUNT(*) as trades,
           AVG(profit) as avg_pnl,
           SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as win_rate
    FROM sqlite_scan('trading.db', 'trades')
    GROUP BY broker
""").fetchall()
```

**Custo:** análise não é real-time (precisa ler o arquivo). Para dashboards e relatórios, serve. Para decisão em tempo real, não.

---

#### B3 (CONTORNOUVÉL) — Retenção de dados

**O que acontece:** Ticks de 3 brokers em 1min = ~4K rows/dia. Em 6 meses = ~720K rows. Em 1 ano = ~1.5M rows. SQLite começa a ficar lento em full table scans.

**Workaround — Particionamento por arquivo:**

```
trading/
├── trading.db          (ativo, últimos 30 dias)
├── archive/
│   ├── 2026-04.db      (abril)
│   ├── 2026-05.db      (maio)
│   └── ...
```

```python
def get_connection(broker: str, date: str = None) -> sqlite3.Connection:
    if date is None:
        return sqlite3.connect("trading/trading.db")
    month = date[:7]  # "2026-04"
    return sqlite3.connect(f"trading/archive/{month}.db")
```

**Custo:** queries cross-período precisam abrir múltiplos DBs e union. DuckDB facilita isso:

```python
duckdb.execute("""
    SELECT * FROM sqlite_scan('trading/trading.db', 'trades')
    UNION ALL
    SELECT * FROM sqlite_scan('trading/archive/2026-04.db', 'trades')
""")
```

---

#### B4 (BLOCKING se escalar) — Concorrência real multi-processo

**O que acontece:** Se estratégias rodarem em **processos separados** (containers, VPS diferentes, scaling horizontal):

```
VPS 1 (Binance)   ──→ trading.db   ← file lock! Não funciona via rede
VPS 2 (Coinbase)  ──→ trading.db   ← não consegue acessar
```

SQLite é **file-local**. Não funciona em NFS, não funciona via rede, não funciona multi-máquina.

**Workaround temporário:**

1. Todas as estratégias no **mesmo processo Python** (event loop + threads)
2. Ou: 1 arquivo `.db` por corretora + DuckDB para consolidation

```
trading/
├── binance.db
├── coinbase.db
├── yahoo.db
└── analytics.duckdb  (lê todos via sqlite_scan)
```

**Custo:** queries consolidadas precisam UNION manual. Perde visão transacional unificada.

**Quando vira bloqueante real:** no momento em que você precisar de 1 processo por corretora (escalabilidade horizontal) ou mover para VPS/cloud.

---

#### B5 (BLOCKING em HFT) — Latência de write

**O que acontece:** Em HFT, o decision loop precisa gravar cada tick. SQLite+WAL latência de write: **1-5ms**. Em HFT competitivo, isso é 10-50x mais lento que o aceitável.

**Sem workaround dentro do SQLite.** A única solução é in-memory para hot path + async write para DB.

---

### Resumo: até onde SQLite+WAL chega?

| Cenário | SQLite+WAL aguenta? | Como |
|---|---|---|
| 1 corretora, 1min, 1 processo | **Sim, fácil** | Direto |
| 3 corretoras, 1min, 1 processo | **Sim** | Write Queue + 1 DB |
| 3 corretoras, 1min, N threads | **Sim** | Write Queue centralizada |
| 3 corretoras, 1min, N processos | **Parcial** | 1 DB por corretora + DuckDB |
| 3 corretoras, 5sec ticks, 1 processo | **Sim** | Write Queue aguenta |
| 3 corretoras, 5sec ticks, N processos | **Parcial** | Mesmo workaround |
| 3 corretoras, sub-second | **Arriscado** | Contenção alta, queue fica cheia |
| 3 corretoras, HFT (<100ms) | **Não** | Precisa de servidor DB |
| Multi-VPS / cloud | **Não** | SQLite é file-local |

### Teto prático

**~50K ticks/dia (~35 ticks/min)** num único processo com write queue — cobre 3-5 corretoras em intervalos de 1min tranquilamente.

Acima disso, a fila de escrita começa a acumular e a latência de analytics cresce. O marco de migração é quando precisar de **processos separados** ou **latência sub-second**.

> "Conhecer os limites é tão importante quanto conhecer as capacidades" – made by Sky 🗄️

---

## Anexo B: Cálculo de Escala — Produção Estável

### Parâmetros da produção imaginada

| Dimensão | Quantidade | Intervalo | Horas/dia |
|---|---|---|---|
| **Futuros** | 5-10 | ~1-5 sec (market data) | ~18h (B3/BMF + CME overnight) |
| **Ações** | 10-50 | 5min+ | ~8h (pregão) |
| **Criptos** | 5-10 | 1min | 24h |
| **Corretoras** | 5-10 | — | — |
| **Estratégias/ativo** | 5+ | — | — |

### Carga de ticks por classe

| Classe | Assets | Ticks/dia (conservador) | Ticks/dia (pessimista) |
|---|---|---|---|
| **Futuros** (5sec) | 10 | 129,600 | 648,000 (1sec) |
| **Ações** (5min) | 50 | 4,800 | 24,000 (1min) |
| **Criptos** (1min) | 10 | 14,400 | 14,400 |
| **Total ticks/dia** | | **~150K** | **~686K** |

### Mas: estratégias não multiplicam ticks

Estratégias **leem** os mesmos ticks e **escrevem** sinais/trades. A carga de escrita é:

| Tipo de escrita | Volume/dia | Impacto |
|---|---|---|
| **Tick raw** (se armazenar) | 150K-686K | Dominante |
| **Sinais gerados** | 500-2,000 | Baixo (cruzamento ADX, etc.) |
| **Ordens executadas** | 100-500 | Muito baixo |
| **Atualizações de posição** | 100-500 | Muito baixo |

### A decisão arquitetural que muda tudo

#### Cenário A: Armazena TODOS os ticks raw

```
~150K-686K writes/dia
~3,600 writes/hora (conservador)
~60 writes/minuto contínuos
```

| DB | Aguenta? | Nota |
|---|---|---|
| **SQLite+WAL** | **Não no futuros** | 10 futuros a 1-5sec = contenção severa na write queue |
| **SQLite+WAL (sem futuros)** | **Sim** | Só ações+crypto = ~19K ticks/dia, tranquilo |
| **TimescaleDB** | **Sim, folgado** | 111K single inserts/sec, batch 1.4M/sec |
| **QuestDB** | **Sim, folgado** | Projetado para ingestion de ticks |

#### Cenário B: Armazena só OHLCV + trades (NÃO armazena tick raw)

```
~5K-30K OHLCV candles/dia + ~100-500 trades
~1-10 writes/minuto
```

| DB | Aguenta? | Nota |
|---|---|---|
| **SQLite+WAL** | **Sim, fácil** | 30K writes/dia é brincadeira para SQLite |
| **TimescaleDB** | **Overkill** | Desperdiça capability |
| **DuckDB** | **Sim** | Analytics sobre as candles consolidadas |

> Tick raw fica em memória (ring buffer) e é descartado após agregar OHLCV.
> Se precisar de replay, usa API da corretora ou arquivo Parquet por dia.

### Recomendação por cenário

#### Se armazena ticks raw → TimescaleDB é obrigatório a partir de futuros

```
Futuros (5-10) ──→ [ring buffer memória] ──→ async → TimescaleDB
Ações (10-50)  ──→ [ring buffer memória] ──→ async → TimescaleDB
Crypto (5-10)  ──→ [ring buffer memória] ──→ async → TimescaleDB
                                                      │
                                    Continuous Aggregates (OHLCV auto)
                                    Compression (10-33x)
                                    Retention (7 dias raw, infinito agregado)
```

Carga: ~150K-686K ticks/dia. TimescaleDB lida com isso em **<5% CPU**.

#### Se NÃO armazena ticks raw → SQLite+WAL aguenta a produção inteira

```
Futuros (5-10) ──→ [ring buffer] ──→ OHLCV 5sec/1min ──→ SQLite+WAL
Ações (10-50)  ──→ [ring buffer] ──→ OHLCV 5min     ──→ SQLite+WAL
Crypto (5-10)  ──→ [ring buffer] ──→ OHLCV 1min     ──→ SQLite+WAL
                                                         │
                                                   Trades, posições
                                                   Sinais, PnL
```

Carga: ~30K writes/dia. SQLite+WAL com write queue lida dormindo.

```python
# Ring buffer em memória — descarta ticks antigos
from collections import deque

class TickBuffer:
    def __init__(self, maxlen: int = 1000):
        self._ticks: deque = deque(maxlen=maxlen)

    def push(self, tick):
        self._ticks.append(tick)

    def aggregate_ohlcv(self, interval_sec: int) -> dict:
        # Agrega ticks em memória, retorna OHLCV candle
        ...
        return candle  # grava no SQLite
```

### Comparativo final para a sua produção

| Critério | SQLite+WAL (só OHLCV) | SQLite+WAL (com ticks) | TimescaleDB (com ticks) |
|---|---|---|---|
| **10 futuros (1-5sec)** | Agrega em OHLCV, grava candle | Contenção severa | **Folgado** |
| **50 ações (5min+)** | **Tranquilo** | **Tranquilo** | Folgado |
| **10 criptos (1min)** | **Tranquilo** | **Tranquilo** | Folgado |
| **5-10 corretoras** | 1 DB com coluna broker | Contention por broker | **Hypertable c/ segmentby** |
| **5 estratégias/ativo** | Estratégias leem memória | Estratégias leem DB | **Leem hypertable** |
| **Writes/dia** | ~30K | ~150K-686K | ~150K-686K |
| **Analytics (DuckDB)** | **Funciona** | Lento (muitas rows) | **Nativo** |
| **Setup** | **Zero** | Zero | Docker |
| **Armazenamento/mês** | ~50MB | ~500MB-2GB | ~50-200MB (compressed) |

### Veredito para a produção imaginada

**A resposta depende de 1 pergunta: você precisa replayar ticks raw?**

| Resposta | Recomendação | Razão |
|---|---|---|
| **Não** — só preciso de OHLCV + trades + analytics | **SQLite+WAL + DuckDB** | 30K writes/dia, zero infra, cobre tudo |
| **Sim** — preciso de cada tick para backtesting/calibração | **TimescaleDB** | 686K writes/dia com compression,Continuous Aggregates eliminam reconstrução |
| **Sim, e futuros em alta freq** — preciso de sub-second | **TimescaleDB + QuestDB** | QuestDB para tick ingestion, TimescaleDB para analytics/transacional |

> "A pergunta certa não é 'qual banco', é 'o que você guarda de cada tick'" – made by Sky 🗄️

---

## Anexo C: ML Evolutivo em Tempo Real — Por que Tick Raw é Obrigatório

### A pergunta

> Preciso de ticks raw em futuros se eu quiser rodar várias estratégias em janelas deslizantes de longos períodos contra a época atual para ML de criação e melhorias de estratégias em tempo real?

### Resposta: Sim. OHLCV mata o ML.

#### O que OHLCV perde

Dado um candle 1min de WIN (mini índice B3):

```
OHLCV: open=132500, high=132580, low=132450, close=132520, volume=1200
```

Você **não sabe**:

| Informação perdida | Por que importa para ML |
|---|---|
| **Sequência intra-candle** | Primeiro subiu depois caiu? Ou o contrário? Padrões completamente diferentes |
| **Velocidade do movimento** | Levou 50 segundos para subir 80pts ou 5 segundos? Momentum é feature ML crítica |
| **Volume por nível de preço** | Onde teve liquidez real vs thin? Support/resistance micro |
| **Bid-ask bounce** | Tick a tick revela pressão compradora/vendedora. OHLCV esconde |
| **Micro-gaps intra-candle** | Gaps de 2-5pts entre ticks consecutivos = slippage real em backtesting |
| **Spread dinâmico** | Spread varia dentro do candle. SL/TP real depende do spread no momento |
| **Rejeições de nível** | Quantas vezes o preço bateu no high antes de rejeitar? OHLCV diz "high" e pronto |

#### O que ML evolutivo precisa

```
                    Sliding Window (30 dias)
                    ┌──────────────────────────────┐
                    │ Tick raw (5sec) dos últimos 30d │
Mês 1 ────────┤    │ ~3.9M rows por futuro          │
Mês 2 ────────┤    │ Features por janela:            │
Mês 3 ────────┤    │ • ADX rolling (5s, 15s, 1m)   │
Hoje ──────────┘    │ • Volatilidade por tick         │
                    │ • Spread médio por horário      │
                    │ • Volume profile por nível      │
                    │ • Tick intensity (ticks/sec)    │
                    └──────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │ Modelo ML compara     │
                    │ época vs agora        │
                    │ → ajusta parâmetros   │
                    │ → cria nova estratégia│
                    └──────────────────────┘
```

**Sem tick raw**, o ML só pode:
- Treinar em padrões de candle (coarse, perde microestrutura)
- Calcular indicadores em resolution fixa (não pode mudar de 1min para 5sec dinamicamente)
- Simular slippage aproximado (sem saber o spread real no momento do sinal)

**Com tick raw**, o ML pode:
- Extrair features em **qualquer resolution** (5s, 15s, 1m, 5m) do mesmo dataset
- Simular backtesting **realista** com slippage e spread exatos
- Detectar **regime changes** (mercado mudou de comportamento) via microestrutura
- Treinar **por época** e comparar contra comportamento atual em tempo real

#### Exemplo concreto: Guardião Conservador evolutivo

```
Hoje: ADX(14), threshold=25, TP por faixa ADX

ML evolutivo pergunta:
  "O threshold 25 ainda é ótimo? E se for 22? E se ADX(10) performa melhor agora?"

Para responder precisa:
  1. Replayar 30 dias de ticks raw do WIN a 5sec
  2. Recalcular ADX com período 10, 12, 14, 16, 18
  3. Recalcular com thresholds 20, 22, 25, 28, 30
  4. Simular cada combinação com slippage REAL (tick a tick)
  5. Comparar contra o comportamento atual ( última semana )
  6. Gerar nova configuração otimizada

Resultado: ADX(12), threshold=22, TP dinâmico por volatilidade
→ tudo derivado de tick raw, impossível com OHLCV
```

---

### O impacto na escolha de banco

#### Com tick raw para ML → TimescaleDB é obrigatório desde o início

```
Futuros (5-10) ──→ ticks 5sec ──→ TimescaleDB (hypertable)
Ações (10-50)   ──→ ticks 5min  ──→ TimescaleDB (hypertable)
Crypto (5-10)   ──→ ticks 1min  ──→ TimescaleDB (hypertable)
                                       │
                         ┌──────────────┤
                         │              │
                    Continuous        Compression
                    Aggregates        10-33x
                    (OHLCV 5s,1m,5m)  (auto after 7d)
                         │              │
                         ▼              ▼
                    Estratégias      ML Training
                    leem OHLCV       leem ticks raw
                    (fast, pré-agg)  (sliding window)
```

#### Storage estimado com compression

| Período | Ticks raw | Sem compressão | Comprimido (10-33x) |
|---|---|---|---|
| 1 dia | ~150K-650K | ~100-400MB | ~10-40MB |
| 30 dias (ML window) | ~4.5-19.5M | ~3-12GB | **~150-800MB** |
| 90 dias | ~13.5-58.5M | ~9-36GB | **~450MB-2.4GB** |
| 1 ano | ~55-237M | ~36-150GB | **~1.8-10GB** |

TimescaleDB com compression + retention:
- Ticks raw: manter 90 dias comprimidos (~2GB), ML treina nisso
- OHLCV agregado: manter infinito (~500MB/ano)
- Archive Parquet: exportar ticks >90 dias para S3/local se quiser replay histórico

#### Por que não SQLite+WAL para isso

| Operação ML | SQLite+WAL | TimescaleDB |
|---|---|---|
| Ler 3.9M ticks (30 dias, 1 futuro) | **~15-30s** (full scan) | **~200-500ms** (chunk pruning + compression) |
| Extrair features em 5 resolutions | 5× slower | **Continuous Aggregates** já prontos |
| Retreinar 5 estratégias × 10 futuros | **~10-30 min** | **~1-3 min** |
| Sliding window de 30d deslizando 1d | Re-scan tudo | **Chunk incremental** |
| Escrita de 650K ticks/dia | Contention severa | **Batch COPY, zero contenção** |
| Multi-estratégia escrevendo junto | Write queue bottleneck | **MVCC, zero lock** |

---

### Arquitetura recomendada: ML Evolutivo

```
┌─────────────────────────────────────────────────────┐
│                    DECISION LOOP                      │
│                                                       │
│  Ticks ──→ Ring Buffer (memória) ──→ Estratégias     │
│              │                     │  │  │  │  │      │
│              │                     5+ estratégias     │
│              │                     avaliam em memória  │
│              │                                          │
└──────────────┼─────────────────────────────────────────┘
               │ async write
               ▼
┌─────────────────────────────────────────────────────┐
│                  TimescaleDB                          │
│                                                       │
│  hypertable: ticks_raw                               │
│    ├── compression after 7 days (10-33x)             │
│    ├── retention: 90 days                            │
│    └── segment by: symbol, broker                    │
│                                                       │
│  continuous aggregates:                              │
│    ├── ohlc_5sec  (auto-refresh a cada 10s)          │
│    ├── ohlc_1min  (auto-refresh a cada 1min)         │
│    ├── ohlc_5min  (auto-refresh a cada 5min)         │
│    └── ohlc_1h    (auto-refresh a cada 1h)           │
│                                                       │
│  regular tables:                                     │
│    ├── trades (ordens executadas)                    │
│    ├── positions (posições abertas/fechadas)         │
│    ├── strategy_params (configurações atuais)        │
│    └── ml_results (métricas de treino/validação)     │
│                                                       │
└─────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│              ML EVOLUTION ENGINE                      │
│                                                       │
│  1. Carrega janela de 30d ticks raw (comprimidos)    │
│  2. Extrai features em múltiplas resolutions         │
│  3. Compara época vs comportamento atual              │
│  4. Treina/ajusta modelo                             │
│  5. Gera novos parâmetros para estratégias            │
│  6. Valida contra última semana (walk-forward)       │
│  7. Se melhor → atualiza strategy_params             │
│  8. Se pior → mantém atual, tenta outra combinação   │
│                                                       │
│  Frequência: a cada 1h ou quando detectar regime change │
└─────────────────────────────────────────────────────┘
```

---

### Veredito atualizado

| Se o plano é... | Banco | Iniciar quando |
|---|---|---|
| Paper trading simples (hoje) | **SQLite+WAL** | Imediato (SKY-39) |
| Multi-corretora + OHLCV only | **SQLite+WAL + DuckDB** | M2 |
| ML evolutivo com tick raw | **TimescaleDB** | Antes do primeiro futuro |
| ML evolutivo + HFT competitivo | **TimescaleDB + QuestDB** | Quando escalar beyond single-machine |

**Se ML evolutivo é o destino, pular SQLite para ticks e começar TimescaleDB desde o primeiro futuro.** Mas para paper trading atual (SKY-39), SQLite resolve sem atrito — e o `PaperStatePort` hexagonal permite migrar trocando apenas o adapter.

> "O ML só evolve tão rápido quanto os dados permitem" – made by Sky 🧬
- [Cloudflare: How TimescaleDB Helped Us Scale Analytics](https://blog.cloudflare.com/timescaledb-art/)
- [Scaling Real-Time Tick-by-Tick Charting with TimescaleDB](https://medium.com/@ansujain/scaling-real-time-tick-by-tick-charting-with-timescaledb-7d29dd9034e6)
- [How TimescaleDB Chunks Actually Work](https://dev.to/philip_mcclarence_2ef9475/how-timescaledb-chunks-actually-work-and-why-size-matters-3hl5)
- [Continuously Aggregating Trade Data in TimescaleDB (Binance)](https://greyhoundanalytics.com/blog/continuously-aggregating-trade-data-in-timescaledb/)
- [TimescaleDB vs QuestDB — 2026 Benchmark](https://questdb.com/blog/timescaledb-vs-questdb-comparison)
- [TimescaleDB Compression: 150GB to 15GB](https://dev.to/polliog/timescaledb-compression-from-150gb-to-15gb-90-reduction-real-production-data-bnj)
- [SQLite in Production Benchmark — Shivek Khurana](https://shivekkhurana.com/blog/sqlite-in-production/)
- [DuckDB vs SQLite vs Pandas on 1M Rows — KDnuggets](https://www.kdnuggets.com/we-benchmarked-duckdb-sqlite-and-pandas-on-1m-rows-heres-what-happened)
- [Rearchitecting Redis to SQLite (3x faster) — Wafris](https://wafris.org/blog/rearchitecting-for-sqlite)
- [Selecting a Database for Algorithmic Trading — Medium](https://medium.com/prooftrading/selecting-a-database-for-an-algorithmic-trading-system-2d25f9648d02)
- [kdb+ vs TimescaleDB for Market Data](https://sanj.dev/post/kdb-vs-timescaledb-market-data-comparison)
