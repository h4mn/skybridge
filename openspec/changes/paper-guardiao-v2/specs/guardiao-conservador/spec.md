## ADDED Requirements

### Requirement: Swing low lookback em evaluate()
O Guardião Conservador SHALL calcular o swing low (mínimo) dos últimos 100 períodos e expor em `_last_indicators`.

#### Scenario: Swing low calculado com dados suficientes
- **WHEN** `evaluate()` com 100+ preços
- **THEN** `_last_indicators["swing_low"]` SHALL conter o menor preço dos últimos 100 candles

#### Scenario: Swing low com dados insuficientes
- **WHEN** `evaluate()` com < 100 preços
- **THEN** `_last_indicators["swing_low"]` SHALL ser o menor preço disponível

> "O guardião observa o momentum e age no cruzamento" – made by Sky 🛡️
