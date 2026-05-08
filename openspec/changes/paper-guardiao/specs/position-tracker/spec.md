## ADDED Requirements

### Requirement: Abrir posição
O PositionTracker SHALL registrar uma posição aberta para um ticker com preço de entrada.

#### Scenario: Abrir posição BTC
- **WHEN** chamar `tracker.open_position("BTC-USD", Decimal("50000"))`
- **THEN** a posição SHALL ser registrada com `ticker="BTC-USD"`, `preco_entrada=50000`, `status="aberta"`

#### Scenario: Tentar abrir posição duplicada
- **WHEN** já existe posição aberta para "BTC-USD" e chamar `open_position` novamente
- **THEN** SHALL ignorar (manter posição existente)

### Requirement: Fechar posição
O PositionTracker SHALL permitir fechar uma posição aberta, removendo-a do rastreamento.

#### Scenario: Fechar posição existente
- **WHEN** existe posição aberta para "BTC-USD" e chamar `close_position("BTC-USD")`
- **THEN** a posição SHALL ser removida

#### Scenario: Fechar posição inexistente
- **WHEN** não existe posição para "BTC-USD" e chamar `close_position("BTC-USD")`
- **THEN** SHALL ser no-op (sem erro)

### Requirement: Verificar Stop Loss
O PositionTracker SHALL gerar sinal de VENDA quando o preço atual cai abaixo do percentual de stop loss configurado.

#### Scenario: Stop Loss acionado (5%)
- **WHEN** posição aberta em `50000`, stop_loss_pct=`0.05`, e preço atual é `47000` (-6%)
- **THEN** SHALL retornar `SinalEstrategia` com `TipoSinal.VENDA` e razao contendo "Stop Loss"

#### Scenario: Stop Loss não acionado
- **WHEN** posição aberta em `50000`, stop_loss_pct=`0.05`, e preço atual é `48000` (-4%)
- **THEN** SHALL retornar `None`

#### Scenario: Stop Loss no limite exato
- **WHEN** posição aberta em `50000`, stop_loss_pct=`0.05`, e preço atual é `47500` (-5%)
- **THEN** SHALL retornar sinal de venda (limite é <=)

### Requirement: Verificar Take Profit
O PositionTracker SHALL gerar sinal de VENDA quando o preço atual sobe acima do percentual de take profit configurado.

#### Scenario: Take Profit acionado (10%)
- **WHEN** posição aberta em `50000`, take_profit_pct=`0.10`, e preço atual é `56000` (+12%)
- **THEN** SHALL retornar `SinalEstrategia` com `TipoSinal.VENDA` e razao contendo "Take Profit"

#### Scenario: Take Profit não acionado
- **WHEN** posição aberta em `50000`, take_profit_pct=`0.10`, e preço atual é `54000` (+8%)
- **THEN** SHALL retornar `None`

#### Scenario: Take Profit no limite exato
- **WHEN** posição aberta em `50000`, take_profit_pct=`0.10`, e preço atual é `55000` (+10%)
- **THEN** SHALL retornar sinal de venda (limite é >=)

### Requirement: Verificar sem posição aberta
O PositionTracker SHALL retornar `None` quando não há posição aberta para o ticker.

#### Scenario: Check sem posição
- **WHEN** não existe posição para "BTC-USD" e chamar `check_price("BTC-USD", Decimal("50000"))`
- **THEN** SHALL retornar `None`

### Requirement: Listar posições abertas
O PositionTracker SHALL permitir listar todas as posições atualmente abertas.

#### Scenario: Listar com posições
- **WHEN** existem posições abertas para "BTC-USD" e "ETH-USD"
- **THEN** `list_positions()` SHALL retornar lista com ambos tickers

#### Scenario: Listar sem posições
- **WHEN** não existem posições abertas
- **THEN** `list_positions()` SHALL retornar lista vazia

> "Stop loss é o paraquedas do trader" – made by Sky 🪂
