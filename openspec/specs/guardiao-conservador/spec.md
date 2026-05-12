## ADDED Requirements

### Requirement: Cálculo de ADX via Wilder's smoothing
O Guardião Conservador SHALL calcular +DI, -DI e ADX via Wilder's smoothing a partir de uma lista de preços.

#### Scenario: ADX com dados suficientes
- **WHEN** calcular ADX(14) com >= 29 preços (period*2+1)
- **THEN** SHALL retornar séries de +DI, -DI e ADX com valores válidos

#### Scenario: ADX com dados insuficientes
- **WHEN** calcular ADX(14) com < 15 preços
- **THEN** SHALL retornar séries de zeros

### Requirement: Detecção de crossover +DI/-DI
O Guardião Conservador SHALL detectar quando +DI cruza -DI para cima (compra) ou para baixo (venda).

#### Scenario: Crossover de compra
- **WHEN** +DI anterior <= -DI anterior E +DI atual > -DI atual
- **THEN** SHALL gerar sinal com `TipoSinal.COMPRA` e razao contendo "+DI=" e "-DI="

#### Scenario: Crossover de venda
- **WHEN** +DI anterior >= -DI anterior E +DI atual < -DI atual
- **THEN** SHALL gerar sinal com `TipoSinal.VENDA`

#### Scenario: Sem crossover
- **WHEN** não há cruzamento entre +DI e -DI
- **THEN** SHALL retornar `None`

### Requirement: Filtro ADX >= 25
O Guardião Conservador SHALL bloquear sinais quando ADX < threshold (default 25).

#### Scenario: Sinal bloqueado por ADX baixo
- **WHEN** crossover detectado E ADX < 25
- **THEN** SHALL retornar `None`

#### Scenario: Sinal permitido por ADX alto
- **WHEN** crossover detectado E ADX >= 25
- **THEN** SHALL gerar sinal com TP dinâmico

### Requirement: Filtro de volume (deprecated)
O `_calc_volume_ratio()` SHALL retornar `Decimal("1.0")` sempre (filtro desativado).

> **Nota**: Volume yfinance crypto não é confiável. ADX>=25 já filtra whipsaws. Reativar com exchange API direta.

### Requirement: TP dinâmico por faixa de ADX
O Guardião Conservador SHALL mapear ADX para TP dinâmico: <20→0.30%, 20-30→0.40%, 30-40→0.50%, >=40→0.60%.

#### Scenario: TP conservador por faixa de ADX
- **WHEN** sinal de COMPRA gerado com ADX=28
- **THEN** `take_profit_pct` SHALL ser `Decimal("0.0040")`

#### Scenario: TP para ADX alto
- **WHEN** sinal gerado com ADX=45
- **THEN** `take_profit_pct` SHALL ser `Decimal("0.0060")`

### Requirement: SL fixo 0.50% (removido SL dinâmico)
O Guardião Conservador SHALL usar SL fixo de 0.50% via PositionTracker, removendo `_sl_for_adx()`.

> **Nota**: SL dinâmico por ADX foi removido em favor de SL fixo 0.50% validado pelo ML como ponto doce.

### Requirement: Swing low lookback em evaluate()
O Guardião Conservador SHALL calcular o swing low (mínimo) dos últimos 100 períodos e expor em `_last_indicators`.

#### Scenario: Swing low calculado com dados suficientes
- **WHEN** `evaluate()` com 100+ preços
- **THEN** `_last_indicators["swing_low"]` SHALL conter o menor preço dos últimos 100 candles

#### Scenario: Swing low com dados insuficientes
- **WHEN** `evaluate()` com < 100 preços
- **THEN** `_last_indicators["swing_low"]` SHALL ser o menor preço disponível

### Requirement: Propriedade name
O Guardião Conservador SHALL ter propriedade `name` com valor `"guardiao-conservador"`.

### Requirement: Indicadores expostos
O Guardião Conservador SHALL armazenar `_last_indicators` (dict com plus_di, minus_di, adx, volume_ratio, swing_low) após cada `evaluate()`.

> "O guardião observa o momentum e age no cruzamento" – made by Sky 🛡️
