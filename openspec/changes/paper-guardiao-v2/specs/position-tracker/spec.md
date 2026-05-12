## ADDED Requirements

### Requirement: PositionTrackerPort (interface abstrata)
O sistema SHALL definir PositionTrackerPort como interface abstrata com nomenclatura MT5-compatible.

#### Scenario: Port define contrato do tracker
- **WHEN** criar qualquer implementação de PositionTrackerPort
- **THEN** SHALL implementar: `open_position()`, `close_position()`, `get_position()`, `check_price()`, `list_positions()`, `restore_positions()`, `set_reentry_state()`, `get_reentry_state()`, `tick_reentry()`, `clear_reentry_state()`

### Requirement: SimpleTracker (netting, 1 posição/ticker)
O SimpleTracker SHALL implementar PositionTrackerPort com modo netting — 1 posição por ticker.

#### Scenario: Abrir posição atribui ticket sequencial
- **WHEN** chamar `open_position("BTC-USD", Decimal("50000"))`
- **THEN** posição SHALL receber `ticket` (int auto-incrementado)

#### Scenario: Abrir posição duplicada substitui (netting)
- **WHEN** já existe posição para "BTC-USD" E chamar `open_position("BTC-USD", ...)`
- **THEN** SHALL substituir posição existente (netting mode)

#### Scenario: Position type derivado do contexto
- **WHEN** posição aberta via COMPRA
- **THEN** `position_type` SHALL ser "BUY"

### Requirement: Estado de re-entrada no SimpleTracker
O SimpleTracker SHALL manter estado de re-entrada em `_reentry` dict separado.

#### Scenario: Criar estado de re-entrada
- **WHEN** chamar `set_reentry_state("BTC-USD", crossover_price=Decimal("80830"), swing_low=Decimal("80279"))`
- **THEN** SHALL criar `_reentry["BTC-USD"]` com `crossover_price`, `swing_low`, `fib_level`, `ticks_since_signal=0`

#### Scenario: Obter estado de re-entrada
- **WHEN** chamar `get_reentry_state("BTC-USD")` com estado existente
- **THEN** SHALL retornar dict com `crossover_price`, `swing_low`, `fib_level`, `ticks_since_signal`

#### Scenario: Incrementar tick do re-entrada
- **WHEN** chamar `tick_reentry("BTC-USD")`
- **THEN** `ticks_since_signal` SHALL incrementar em 1

#### Scenario: Limpar estado de re-entrada
- **WHEN** chamar `clear_reentry_state("BTC-USD")`
- **THEN** `_reentry["BTC-USD"]` SHALL ser removido

#### Scenario: Expirar re-entrada após 200 ticks
- **WHEN** `ticks_since_signal` >= 200
- **THEN** estado SHALL ser automaticamente limpo

> "Stop loss é o paraquedas do trader" – made by Sky 🪂
