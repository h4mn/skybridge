src/core/paper/
│
├── README.md
│
├── doc/                         # Documentação
│
├── domain/                      # Entidades e regras
│   ├── entities/
│   ├── value_objects/
│   ├── events/
│   └── services/
│
├── application/                 # Casos de uso
│   ├── commands/
│   ├── queries/
│   └── handlers/
│
├── ports/                       # Interfaces
│   ├── broker_port.py
│   ├── data_feed_port.py
│   └── repository_port.py
│
├── adapters/                    # Implementações
│   ├── brokers/
│   ├── data_feeds/
│   └── persistence/
│
└── facade/                      # 🆕 Facades agrupadas
    ├── __init__.py
    ├── api/                     # Facade API (REST)
    │   ├── __init__.py
    │   ├── facade.py
    │   ├── routes/
    │   │   ├── ordens.py        # POST /ordens, GET /ordens/{id}
    │   │   ├── portfolio.py     # GET /portfolio
    │   │   └── risco.py         # GET /risco/status
    │   ├── schemas/
    │   │   ├── ordem_schema.py  # Pydantic models
    │   │   └── portfolio_schema.py
    │   └── dependencies.py      # Injeção de dependências
    └── mcp/                     # Facade MCP (LLM Tools)
        ├── __init__.py
        ├── facade.py            # Registro de tools
        ├── tools/
        │   ├── criar_ordem.py      # Tool: paper_criar_ordem
        │   ├── consultar_portfolio.py
        │   └── avaliar_risco.py
        └── resources/
            └── portfolio_resource.py  # Resource: paper://portfolio
```
