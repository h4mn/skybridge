# Spec: paper-facade-mcp

Tools e resources MCP para integração com LLMs.

## ADDED Requirements

### Requirement: Tool paper_criar_ordem
O sistema SHALL fornecer MCP tool para criar ordens de paper trading.

#### Scenario: Criar ordem via MCP
- **WHEN** a tool paper_criar_ordem é chamada com ticker, lado, quantidade
- **THEN** o sistema SHALL executar a ordem e retornar confirmação com ID

### Requirement: Tool paper_consultar_portfolio
O sistema SHALL fornecer MCP tool para consultar o portfolio.

#### Scenario: Consultar portfolio via MCP
- **WHEN** a tool paper_consultar_portfolio é chamada
- **THEN** o sistema SHALL retornar dados completos do portfolio

### Requirement: Tool paper_avaliar_risco
O sistema SHALL fornecer MCP tool para avaliar risco do portfolio.

#### Scenario: Avaliar risco via MCP
- **WHEN** a tool paper_avaliar_risco é chamada
- **THEN** o sistema SHALL retornar análise de risco do portfolio

### Requirement: Resource paper://portfolio
O sistema SHALL fornecer MCP resource para acesso ao portfolio.

#### Scenario: Acessar resource do portfolio
- **WHEN** o resource paper://portfolio é acessado
- **THEN** o sistema SHALL retornar representação do portfolio atual
