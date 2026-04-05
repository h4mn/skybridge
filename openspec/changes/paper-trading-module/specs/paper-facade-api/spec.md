# Spec: paper-facade-api

API REST para paper trading via FastAPI.

## ADDED Requirements

### Requirement: Endpoint GET /cotacao/{ticker}
O sistema SHALL fornecer endpoint para obter cotação atual de um ativo.

#### Scenario: Cotação bem-sucedida
- **WHEN** GET /cotacao/PETR4.SA é chamado
- **THEN** o sistema SHALL retornar 200 com ticker, preco, volume, timestamp

#### Scenario: Ticker não encontrado
- **WHEN** GET /cotacao/INVALIDO é chamado
- **THEN** o sistema SHALL retornar 404 com mensagem de erro

### Requirement: Endpoint GET /historico/{ticker}
O sistema SHALL fornecer endpoint para obter histórico de cotações.

#### Scenario: Histórico padrão
- **WHEN** GET /historico/PETR4.SA é chamado
- **THEN** o sistema SHALL retornar 200 com lista de 30 candles diários

#### Scenario: Histórico customizado
- **WHEN** GET /historico/PETR4.SA?dias=7 é chamado
- **THEN** o sistema SHALL retornar 200 com lista de 7 candles diários

### Requirement: Endpoint POST /ordem
O sistema SHALL fornecer endpoint para executar ordens de compra/venda.

#### Scenario: Ordem de compra bem-sucedida
- **WHEN** POST /ordem é chamado com {ticker: "PETR4.SA", lado: "COMPRA", quantidade: 100}
- **THEN** o sistema SHALL retornar 200 com ordem_id, preco_execucao, valor_total, status

#### Scenario: Saldo insuficiente
- **WHEN** POST /ordem é chamado com valor maior que saldo
- **THEN** o sistema SHALL retornar 422 com detalhes do erro

### Requirement: Endpoint GET /posicoes
O sistema SHALL fornecer endpoint para listar posições marcadas a mercado.

#### Scenario: Listar posições
- **WHEN** GET /posicoes é chamado
- **THEN** o sistema SHALL retornar 200 com lista de posições com pnl calculado

### Requirement: Endpoint GET /portfolio
O sistema SHALL fornecer endpoint para resumo completo do portfolio.

#### Scenario: Resumo do portfolio
- **WHEN** GET /portfolio é chamado
- **THEN** o sistema SHALL retornar saldo_disponivel, valor_posicoes, patrimonio_total, pnl, posicoes

### Requirement: Endpoint GET /ordens
O sistema SHALL fornecer endpoint para listar histórico de ordens.

#### Scenario: Listar ordens
- **WHEN** GET /ordens é chamado
- **THEN** o sistema SHALL retornar 200 com lista de todas as ordens executadas
