# Arquitetura do Módulo Paper Trading

Visão completa da arquitetura DDD + Hexagonal do `core/paper`, com diagramas Mermaid.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Camadas e Dependências](#2-camadas-e-dependências)
3. [Ports — Contratos de Infraestrutura](#3-ports--contratos-de-infraestrutura)
4. [Domain — Modelo de Domínio](#4-domain--modelo-de-domínio)
5. [Adapters — Implementações Concretas](#5-adapters--implementações-concretas)
6. [Application — CQRS](#6-application--cqrs)
7. [Facade — Delivery Layer](#7-facade--delivery-layer)
8. [Fluxo de Dados: Tick do Guardião](#8-fluxo-de-dados-tick-do-guardião)
9. [Persistência e Estado](#9-persistência-e-estado)
10. [Estratégia Guardião Conservador](#10-estratégia-guardião-conservador)
11. [Eventos de Domínio](#11-eventos-de-domínio)
12. [Diagrama de Classes Completo](#12-diagrama-de-classes-completo)

---

## 1. Visão Geral

O módulo `core/paper` implementa um **paper trading engine** com arquitetura **Hexagonal (Ports & Adapters)** sobre **DDD (Domain-Driven Design)** e **CQRS** na camada de aplicação.

### Diretórios

```
src/core/paper/
├── ports/              # Interfaces (contratos)
├── domain/             # Regras de negócio puras (zero I/O)
│   ├── entities/       # Entidades com identidade
│   ├── value_objects/  # Objetos imutáveis
│   ├── events/         # Eventos de domínio + EventBus
│   ├── services/       # Serviços de domínio
│   └── strategies/     # Estratégias de trading
├── adapters/           # Implementações das ports
│   ├── brokers/        # Execução simulada
│   ├── data_feeds/     # Yahoo Finance
│   ├── currency/       # Conversão de moedas
│   └── persistence/    # JSON file storage
├── services/           # Serviços de aplicação (quantity rules)
├── application/        # CQRS commands/queries/handlers
└── facade/             # Delivery layer
    ├── api/            # REST (FastAPI)
    ├── mcp/            # Model Context Protocol
    └── sandbox/        # Loop de execução contínua
        └── workers/    # Strategy + Position workers
```

---

## 2. Camadas e Dependências

Regra fundamental: **dependências apontam para dentro**. Domain nunca importa de adapters ou facade.

```mermaid
graph TD
    subgraph Facade
        API[API REST]
        MCP[MCP Tools]
        SBX[Sandbox Loop]
    end

    subgraph Application
        CMD[Commands]
        QRY[Queries]
        HDL[Handlers]
    end

    subgraph Ports
        BP[BrokerPort]
        DFP[DataFeedPort]
        PSP[PaperStatePort]
        RP[RepositoryPort]
        CCP[CurrencyConverterPort]
    end

    subgraph Domain
        ENT[Entities]
        VO[Value Objects]
        EVT[Events]
        SVC[Domain Services]
        STR[Strategies]
    end

    subgraph Adapters
        PB[PaperBroker]
        YF[YahooFinanceFeed]
        JFP[JsonFilePaperState]
        YCA[YahooCurrencyAdapter]
        IMR[InMemoryRepository]
    end

    SBX --> SVC
    SBX --> STR
    SBX --> BP
    SBX --> DFP
    API --> HDL
    MCP --> HDL
    HDL --> BP
    HDL --> DFP
    HDL --> PSP
    HDL --> CCP
    BP --> DFP
    PB -.-> BP
    YF -.-> DFP
    JFP -.-> PSP
    YCA -.-> CCP
    IMR -.-> RP
    SVC --> ENT
    SVC --> EVT
    STR --> VO

    style Domain fill:#e8f5e9,stroke:#4caf50
    style Ports fill:#e3f2fd,stroke:#2196f3
    style Adapters fill:#fff3e0,stroke:#ff9800
    style Application fill:#f3e5f5,stroke:#9c27b0
    style Facade fill:#fce4ec,stroke:#e91e63
```

---

## 3. Ports — Contratos de Infraestrutura

Interfaces abstratas que isolam o domínio de implementações concretas.

```mermaid
classDiagram
    class BrokerPort {
        <<abstract>>
        +conectar() async
        +desconectar() async
        +enviar_ordem(ticker, lado, qty, preco) str
        +cancelar_ordem(id) bool
        +consultar_ordem(id) dict
        +obter_saldo() Decimal
    }

    class DataFeedPort {
        <<abstract>>
        +conectar() async
        +desconectar() async
        +obter_cotacao(ticker) Cotacao
        +obter_historico(ticker, dias, intervalo) list
        +stream_cotacoes(tickers) AsyncIterator
        +validar_ticker(ticker) bool
    }

    class Cotacao {
        ticker: str
        preco: Decimal
        volume: int
        timestamp: str
    }

    class PaperStatePort {
        <<abstract>>
        +carregar() PaperStateData
        +salvar(estado) None
        +resetar(saldo_inicial) PaperStateData
    }

    class PaperStateData {
        version: int
        saldo_inicial: Decimal
        base_currency: str
        cashbook: Dict
        ordens: Dict
        posicoes: Dict
        +saldo: Decimal
        +to_dict() Dict
        +from_dict(data) PaperStateData
    }

    class CurrencyConverterPort {
        <<Protocol>>
        +get_rate(from, to) Decimal
        +convert(money, to) Money
    }

    class RepositoryPort {
        <<abstract>>
        +salvar_portfolio(portfolio) None
        +carregar_portfolio(id) Portfolio
        +salvar_ordem(ordem) None
        +listar_ordens(ticker) list
        +salvar_posicao(posicao) None
        +listar_posicoes() list
        +registrar_operacao(op) None
        +listar_historico() list
    }

    DataFeedPort --> Cotacao
    PaperStatePort --> PaperStateData
```

---

## 4. Domain — Modelo de Domínio

### 4.1 Value Objects

Objetos imutáveis que representam conceitos financeiros.

```mermaid
classDiagram
    class Currency {
        <<enum>>
        BRL USD EUR GBP BTC ETH
        +is_fiat: bool
        +is_crypto: bool
    }

    class Money {
        <<frozen>>
        amount: Decimal
        currency: Currency
        +__add__(other) Money
        +__sub__(other) Money
        +__mul__(factor) Money
        +convert_to(target, rate) Money
        +format() str
    }

    class Quantity {
        <<frozen>>
        value: Decimal
        precision: int
        min_tick: Decimal
        asset_type: AssetType
        +adjust_to_tick() Quantity
        +is_valid_for(ticker) bool
    }

    class AssetType {
        <<enum>>
        STOCK STOCK_FRACTION CRYPTO FOREX
    }

    class Ticker {
        <<frozen>>
        simbolo: str
    }

    class CashEntry {
        <<frozen>>
        currency: Currency
        amount: Decimal
        conversion_rate: Decimal
        +value_in_base_currency: Decimal
    }

    class CashBook {
        base_currency: Currency
        +total_in_base_currency: Decimal
        +get(currency) CashEntry
        +has_sufficient_funds(amount) bool
        +add(currency, amount) None
        +subtract(currency, amount) None
        +to_dict() Dict
        +from_single_currency(curr, amt) CashBook
    }

    Money --> Currency
    Quantity --> AssetType
    CashBook --> CashEntry
    CashEntry --> Currency
```

### 4.2 Entidades

```mermaid
classDiagram
    class Portfolio {
        id: str
        nome: str
        saldo_inicial: float
        saldo_atual: float
        criado_em: datetime
        +depositar(valor) None
        +retirar(valor) None
        +pnl() float
        +pnl_percentual() float
    }

    class PortfolioView {
        positions: list~PositionView~
        base_currency: Currency
        cash: Money
        +total_by_currency() Dict
        +total_converted(converter, target) Money
    }

    class PositionView {
        <<frozen>>
        ticker: str
        quantity: Quantity
        market_price: Money
        cost_basis: Money
        +market_value: Money
        +pnl: Money
    }

    PortfolioView --> PositionView
    PositionView --> Money
    PositionView --> Quantity
```

### 4.3 Worker (Domínio)

Modelo de domínio para lifecycle de workers — independente da execução física.

```mermaid
stateDiagram-v2
    [*] --> STOPPED
    STOPPED --> RUNNING: start
    RUNNING --> STOPPED: stop
    RUNNING --> ERROR: excecao
    ERROR --> STOPPED: reset

    note right of RUNNING
        tick gera WorkerTickComplete
    end note
```

```mermaid
classDiagram
    class WorkerId {
        <<frozen>>
        +value: str UUID
    }

    class WorkerName {
        <<frozen>>
        +value: str
    }

    class WorkerStatus {
        &lt;&lt;enum&gt;&gt;
        STOPPED RUNNING ERROR
        +can_transition_to(new) bool
    }

    class Worker {
        id: WorkerId
        name: WorkerName
        status: WorkerStatus
        +start() WorkerStarted
        +stop(reason) WorkerStopped
        +tick() WorkerTickComplete
    }

    class WorkerRegistry {
        -workers: Dict
        +register(worker) None
        +get(id) Worker
        +remove(id) None
        +list_all() list
        +list_by_status(status) list
    }

    Worker --> WorkerId
    Worker --> WorkerName
    Worker --> WorkerStatus
    WorkerRegistry --> Worker
```

---

## 5. Adapters — Implementações Concretas

```mermaid
classDiagram
    class PaperBroker {
        -_datafeed: DataFeedPort
        -_cashbook: CashBook
        -_posicoes: Dict
        -_ordens: Dict
        -_converter: CurrencyConverterPort
        +enviar_ordem(ticker, lado, qty, preco) str
        +obter_saldo() Decimal
        +listar_posicoes() list
        +listar_posicoes_marcadas() list
    }

    class JsonFilePaperBroker {
        -_state_port: PaperStatePort
        +enviar_ordem(...) str
        +reload() None
        -_load_from_state() None
        -_save_to_state() None
    }

    class YahooFinanceFeed {
        -_cache: TTLCache
        -_backoff: float
        +obter_cotacao(ticker) Cotacao
        +obter_historico(ticker, dias, intervalo) list
        +stream_cotacoes(tickers) AsyncIterator
    }

    class YahooCurrencyAdapter {
        -_cache: Dict
        -_cache_ttl: int
        +get_rate(from, to) Decimal
        +convert(money, to) Money
    }

    class JsonFilePaperState {
        -_path: Path
        +carregar() PaperStateData
        +salvar(estado) None
        +resetar(saldo_inicial) PaperStateData
        -_migrate_v1_to_v2(data) Dict
        -_migrate_v2_to_v3(data) Dict
    }

    class InMemoryPortfolioRepository {
        -_store: Dict
        +find_by_id(id) Portfolio
        +find_default() Portfolio
        +save(portfolio) None
    }

    PaperBroker <|-- JsonFilePaperBroker
    BrokerPort <|.. PaperBroker
    DataFeedPort <|.. YahooFinanceFeed
    CurrencyConverterPort <|.. YahooCurrencyAdapter
    PaperStatePort <|.. JsonFilePaperState
    PortfolioRepositoryPort <|.. InMemoryPortfolioRepository
```

---

## 6. Application — CQRS

Commands (escrita) e Queries (leitura) separados com handlers dedicados.

```mermaid
classDiagram
    direction LR

    class Commands {
        CriarOrdemCommand
        DepositarCommand
        ResetarCommand
        StartWorkerCommand
        StopWorkerCommand
    }

    class Queries {
        ConsultarCotacaoQuery
        ConsultarHistoricoQuery
        ConsultarOrdensQuery
        ConsultarPortfolioQuery
    }

    class Handlers {
        CriarOrdemHandler
        DepositarHandler
        ResetarHandler
        ConsultarCotacaoHandler
        ConsultarHistoricoHandler
        ConsultarOrdensHandler
        ConsultarPortfolioHandler
        StartWorkerHandler
        StopWorkerHandler
    }

    class OrchestrateWorkersUseCase {
        +execute() WorkerOrchestrationResult
    }

    Commands --> Handlers
    Queries --> Handlers
    Handlers --> OrchestrateWorkersUseCase
```

### Fluxo CQRS — Criar Ordem

```mermaid
sequenceDiagram
    participant CLI as API/MCP
    participant H as CriarOrdemHandler
    participant B as PaperBroker
    participant V as ValidadorDeOrdem
    participant E as EventBus

    CLI->>H: handle(CriarOrdemCommand)
    H->>V: validar_e_criar_ordem(ticker, lado, qty)
    V->>V: validar ticker, saldo, quantidade
    V->>E: publish(OrdemCriada)
    H->>B: enviar_ordem(ticker, lado, qty)
    B->>B: obter preço, executar
    B->>E: publish(OrdemExecutada)
    H-->>CLI: OrdemResult
```

---

## 7. Facade — Delivery Layer

### 7.1 API (FastAPI)

```mermaid
graph LR
    subgraph FastAPI
        R1["GET /mercado/cotacao/{ticker}"]
        R2["GET /mercado/historico/{ticker}"]
        R3["POST-GET /ordens/"]
        R4["GET-POST /portfolio/"]
        R5["GET-POST /risco/"]
    end

    subgraph Handlers
        CH[ConsultarCotacaoHandler]
        HH[ConsultarHistoricoHandler]
        OH[ConsultarOrdensHandler]
        PH[ConsultarPortfolioHandler]
        COH[CriarOrdemHandler]
        DH[DepositarHandler]
        RH[ResetarHandler]
    end

    R1 --> CH
    R2 --> HH
    R3 --> COH
    R3 --> OH
    R4 --> PH
    R4 --> DH
    R4 --> RH
    R5 -->|501 NI| x((stub))
```

### 7.2 MCP

```mermaid
graph LR
    subgraph MCP Tools
        T1[paper_criar_ordem]
        T2[paper_consultar_portfolio]
        T3[paper_cotacao_ticker]
        T4[paper_avaliar_risco]
    end

    T1 --> CriarOrdemHandler
    T2 --> ConsultarPortfolioHandler
    T3 --> ConsultarCotacaoHandler
    T4 -->|stub| x((NI))
```

### 7.3 Sandbox — Loop de Execução Contínua

```mermaid
graph TD
    RO[run_orchestrator.py] --> PO[PaperOrchestrator]
    PO -->|register| SW[StrategyWorker]
    PO -->|register| PW[PositionWorker]

    PO -->|tick loop| GL[asyncio.gather]
    GL --> SW
    GL --> PW

    subgraph StrategyWorker Internals
        SW --> DF[DataFeedPort]
        SW --> ST[Strategy.evaluate]
        SW --> PT[PositionTracker]
        SW --> EX[ExecutorDeOrdem]
        SW --> RC[ReversalCollector]
    end

    style RO fill:#ffeb3b,stroke:#f57f17
    style PO fill:#4caf50,stroke:#2e7d32,color:#fff
    style SW fill:#2196f3,stroke:#1565c0,color:#fff
    style PW fill:#90a4ae,stroke:#546e7f,color:#fff
```

---

## 8. Fluxo de Dados: Tick do Guardião

Este é o fluxo principal de execução do sistema em produção.

```mermaid
flowchart TD
    START([Tick]) --> QUOTE["1. Obter cotacao"]
    QUOTE --> TRAIL["2. Atualizar trailing stop"]
    TRAIL --> CHECK{"3. SL/TP<br/>acionado?"}

    CHECK -->|Sim| CLOSE_TP["Executar venda<br/>fechar posicao"]
    CLOSE_TP --> LOG_PNL["Log PnL + cor"]
    LOG_PNL --> REV_STOP{"ReversalCollector<br/>tracking?"}
    REV_STOP -->|Sim| REV_END[stop_tracking]
    REV_END --> NEXT_TICK
    REV_STOP -->|Nao| NEXT_TICK

    CHECK -->|Nao| REV_UPD{"4. ReversalCollector<br/>tracking?"}
    REV_UPD -->|Sim| REV_UPDATE["update preco"]
    REV_UPD -->|Nao| STALE
    REV_UPDATE --> STALE

    STALE{"5. Stale Guard<br/>preco mudou?"}
    STALE -->|"Nao >=2x"| NEXT_TICK(["Proximo ticker"])
    STALE -->|Sim| FETCH["6. Buscar historico"]

    FETCH --> BUILD[DadosMercado]
    BUILD --> EVAL["7. Strategy.evaluate"]
    EVAL --> TP_UPD["7b. Reavaliar TP dinamico<br/>via ADX atual"]
    TP_UPD --> SIGNAL{Sinal?}

    SIGNAL -->|Neutro| LOG_TICK["Log indicadores coloridos"]
    LOG_TICK --> NEXT_TICK

    SIGNAL -->|"Compra/Venda"| GUARD{"8. Position Guard"}
    GUARD -->|Duplicada| LOG_GUARD["GUARD: rejeitada"]
    LOG_GUARD --> NEXT_TICK
    GUARD -->|Valida| EXEC["9. Executar ordem"]

    EXEC --> |Compra| OPEN["Abrir posicao<br/>TP dinamico + Reversal start"]
    EXEC --> |Venda| CLOSE_SEL["Fechar posicao<br/>PnL + Reversal stop"]

    OPEN --> NEXT_TICK
    CLOSE_SEL --> NEXT_TICK

    NEXT_TICK --> HEARTBEAT{"60 ticks?"}
    HEARTBEAT -->|Sim| HB_LOG["Log heartbeat<br/>PnL + WR% + Posicoes"]
    HEARTBEAT -->|Nao| DONE(["Fim tick"])
    HB_LOG --> DONE

    style START fill:#4caf50,stroke:#2e7d32,color:#fff
    style DONE fill:#4caf50,stroke:#2e7d32,color:#fff
    style CLOSE_TP fill:#f44336,stroke:#c62828,color:#fff
    style OPEN fill:#ffeb3b,stroke:#f57f17
    style EXEC fill:#2196f3,stroke:#1565c0,color:#fff
    style EVAL fill:#9c27b0,stroke:#6a1b9a,color:#fff
    style GUARD fill:#ff9800,stroke:#e65100,color:#fff
```

---

## 9. Persistência e Estado

### Arquivo Único: `paper_state.json`

O `JsonFilePaperState` é o **single owner** do arquivo de estado, resolvendo conflitos de escrita entre broker e repository.

```mermaid
graph TD
    subgraph state["paper_state.json Schema V3"]
        META["version: 3"]
        CASH["cashbook: Dict"]
        ORD["ordens: Dict"]
        POS["posicoes: Dict"]
        PORT["portfolios: Dict"]
        CONF["config: saldo_inicial, base_currency"]
    end

    JFPS[JsonFilePaperState] -->|"carregar / salvar"| FILE["paper_state.json"]
    JFPB[JsonFilePaperBroker] -->|delegacao| JFPS
    JFPR[JsonFilePortfolioRepo] -->|delegacao| JFPS

    subgraph migration["Migracao Automatica"]
        V1["V1: legado"] -->|auto| V2["V2: unificado"]
        V2 -->|auto| V3[V3: multi-currency]
    end

    JFPS --> migration

    style FILE fill:#ffeb3b,stroke:#f57f17
    style JFPS fill:#4caf50,stroke:#2e7d32,color:#fff
```

### Estado do Guardião: `guardiao-state.json`

Arquivo separado gerenciado pelo `run_orchestrator.py` para persistir o estado da sessão:

```json
{
  "positions": [...],
  "closed_pnl": [12.50, -3.20, 8.75, ...]
}
```

---

## 10. Estratégia Guardião Conservador

### Pipeline de Decisão

```mermaid
flowchart TD
    PRECOS["Precos historicos"] --> ADX["Calculo ADX<br/>Wilders smoothing"]
    ADX --> PDI["+DI / -DI"]
    ADX --> ADX_VAL["ADX value"]

    PDI --> CROSS{Crossover?}
    CROSS -->|"+DI cruza acima"| COMPRA["Candidato COMPRA"]
    CROSS -->|"-DI cruza acima"| VENDA["Candidato VENDA"]
    CROSS -->|"Sem cruzamento"| NEUTRO[Neutro]

    COMPRA --> FILTRO_ADX{"ADX >= 25?"}
    VENDA --> FILTRO_ADX
    FILTRO_ADX -->|Sim| SINAL["Sinal + TP dinamico"]
    FILTRO_ADX -->|Nao| NEUTRO

    SINAL --> TP_MAP["TP por faixa ADX<br/>menor 20: 0.30%<br/>20-30: 0.40%<br/>30-40: 0.50%<br/>maior 40: 0.60%"]

    style ADX fill:#9c27b0,stroke:#6a1b9a,color:#fff
    style SINAL fill:#4caf50,stroke:#2e7d32,color:#fff
    style TP_MAP fill:#ffeb3b,stroke:#f57f17
```

### PositionTracker — SL/TP/Trailing

```mermaid
flowchart TD
    OPEN["Posicao Aberta<br/>entrada = E"] --> CHECK{"check_price"}

    CHECK -->|"variacao <= -SL"| SL["Stop Loss<br/>preco = E x 1-SL"]
    CHECK -->|"variacao >= TP"| TP["Take Profit<br/>preco = E x 1+TP"]
    CHECK -->|"preco <= trailing_stop"| TS[Trailing Stop]

    CHECK -->|Nenhum| TRAIL{"update_trailing"}

    TRAIL -->|"variacao menor 0.20%"| NO_TRAIL["Sem trailing"]
    TRAIL -->|"variacao maior 0.20%"| CALC_TRAIL["pico = max(atual, pico)<br/>stop = pico x 0.9985<br/>stop = max(stop, breakeven)"]

    subgraph params["Parametros do Guardiao"]
        SL_P["SL = -0.20%"]
        TP_P["TP = 0.30% - 0.60%<br/>dinamico por ADX"]
        TR_P["Trailing: ativa +0.20%<br/>distancia 0.15%<br/>breakeven floor"]
    end

    style SL fill:#f44336,stroke:#c62828,color:#fff
    style TP fill:#4caf50,stroke:#2e7d32,color:#fff
    style TS fill:#ff9800,stroke:#e65100,color:#fff
```

---

## 11. Eventos de Domínio

```mermaid
classDiagram
    class DomainEvent {
        <<frozen>>
        occurred_at: datetime
        event_type: str
        metadata: dict
        +to_dict() Dict
        +from_dict(data) DomainEvent
    }

    class OrdemCriada {
        ordem_id: str
        ticker: str
        lado: str
        quantidade: int
        preco_limit: Decimal
    }

    class OrdemExecutada {
        ordem_id: str
        ticker: str
        lado: str
        quantidade_executada: int
        preco_execucao: Decimal
    }

    class OrdemCancelada {
        ordem_id: str
        motivo: str
    }

    class StopLossAcionado {
        ticker: str
        preco_trigger: Decimal
        perda_percentual: Decimal
        quantidade: int
    }

    class PosicaoAtualizada {
        ticker: str
        quantidade_anterior: int
        quantidade_nova: int
        preco_medio_novo: Decimal
        preco_atual: Decimal
        pnl_nao_realizado: Decimal
    }

    DomainEvent <|-- OrdemCriada
    DomainEvent <|-- OrdemExecutada
    DomainEvent <|-- OrdemCancelada
    DomainEvent <|-- StopLossAcionado
    DomainEvent <|-- PosicaoAtualizada

    class EventBus {
        -_handlers: Dict
        +subscribe(event_class, handler)
        +unsubscribe(event_class, handler)
        +publish(event)
        +clear()
    }

    EventBus --> DomainEvent : publish
```

---

## 12. Diagrama de Classes Completo

Visão geral de todas as classes do módulo e seus relacionamentos.

```mermaid
graph TB
    subgraph "Domain Layer"
        direction TB
        CUR[Currency] --> MON[Money]
        AST[AssetType] --> QTY[Quantity]
        CUR --> CE[CashEntry]
        CUR --> CB[CashBook]
        CE --> CB

        PF[Portfolio] --> PV[PortfolioView]
        PV --> POSV[PositionView]
        MON --> POSV
        QTY --> POSV

        DE[DomainEvent] --> OC[OrdemCriada]
        DE --> OE[OrdemExecutada]
        DE --> OCa[OrdemCancelada]
        DE --> SLA[StopLossAcionado]
        DE --> PA[PosicaoAtualizada]

        EB[EventBus] --> DE

        VDO[ValidadorDeOrdem] --> EB
        EDO[ExecutorDeOrdem] --> EB
        CR[CalculadorDeRisco]
        GR[GeradorDeRelatorio]

        SP[StrategyProtocol] --> GC[GuardiaoConservador]
        SP --> DM[DadosMercado]
        GC --> SE[SinalEstrategia]
        PT[PositionTracker] --> SE
    end

    subgraph "Ports Layer"
        BP[BrokerPort]
        DFP[DataFeedPort] --> COT[Cotacao]
        PSP[PaperStatePort] --> PSD[PaperStateData]
        RP[RepositoryPort]
        CCP[CurrencyConverterPort]
    end

    subgraph "Adapters Layer"
        PB[PaperBroker] -.-> BP
        JFB[JsonFilePaperBroker] --> PB
        YF[YahooFinanceFeed] -.-> DFP
        YCA[YahooCurrencyAdapter] -.-> CCP
        JFPS[JsonFilePaperState] -.-> PSP
        IMR[InMemoryRepository] -.-> RP
        JFR[JsonFilePortfolioRepo] -.-> RP
    end

    subgraph "Application Layer"
        COC[CriarOrdemCommand] --> COH[CriarOrdemHandler]
        DEC[DepositarCommand] --> DEH[DepositarHandler]
        REC[ResetarCommand] --> REH[ResetarHandler]
        CCQ[ConsultarCotacaoQuery] --> CCH[ConsultarCotacaoHandler]
        CHQ[ConsultarHistoricoQuery] --> CHH[ConsultarHistoricoHandler]
        COQ[ConsultarOrdensQuery] --> COH2[ConsultarOrdensHandler]
        CPQ[ConsultarPortfolioQuery] --> CPH[ConsultarPortfolioHandler]
    end

    subgraph "Facade Layer"
        FAPI[FastAPI App] --> COH
        FMCP[MCP Facade] --> COH
        ORC[PaperOrchestrator] --> SW[StrategyWorker]
        ORC --> PW2[PositionWorker]
        SW --> GC
        SW --> PT
        SW --> EDO
        SW --> DFP
    end

    PB --> DFP
    PB --> CCP
    PB --> CB
    JFB --> PSP
    VDO --> DFP
    VDO --> CB
    EDO --> BP
    EDO --> DFP
    COH --> BP
    DEH --> PSP
    REH --> PSP
    CCH --> DFP
    CHH --> DFP
    COH2 --> BP
    COH2 --> PSP
    CPH --> BP
    CPH --> DFP
    CPH --> CCP
    GR --> CR
```

---

## KPIs do Guardião (Backtest 7d 1m BTC-USD)

| KPI | Valor | Descrição |
|---|---|---|
| PnL | +2.141% | Lucro/prejuízo total acumulado no período |
| Win Rate | 31.9% | Percentual de trades com PnL ≥ 0 |
| Sharpe Ratio | +0.090 | Retorno ajustado ao risco (risk-free = 0) |
| Max Drawdown | -1.600% | Maior queda desde o pico do patrimônio |
| Profit Factor | 1.23 | Soma ganhos / Soma perdas (> 1 é lucrativo) |
| Calmar Ratio | 1.34 | PnL anualizado / Max Drawdown anualizado |

---

> "Arquitetura é decisão que você toma uma vez e convive todos os dias." – made by Sky 🏛️
