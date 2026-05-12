## ADDED Requirements

### Requirement: Auto-detecção JSON existente
O `SQLitePaperState` SHALL detectar `paper_state.json` quando `.db` não existe e migrar automaticamente.

#### Scenario: JSON encontrado, DB não existe
- **WHEN** `SQLitePaperState("data/paper_state.db")` e `.db` não existe mas `.json` existe
- **THEN** SHALL importar dados do JSON para SQLite
- **AND** SHALL renomear JSON para `paper_state.v3.migrated.json`

#### Scenario: DB já existe
- **WHEN** `.db` já existe
- **THEN** SHALL abrir normalmente sem migrar

#### Scenario: Nenhum arquivo existe
- **WHEN** nem `.db` nem `.json` existem
- **THEN** SHALL criar database novo com defaults

### Requirement: Importar JSON v3 completo
A migração SHALL importar todos os campos do `paper_state.json` v3.

#### Scenario: Cashbook importado
- **WHEN** JSON tem cashbook com BRL=100000 e USD=2500
- **THEN** `cashbook_entries` SHALL conter 2 rows com valores exatos

#### Scenario: Ordens importadas
- **WHEN** JSON tem 3 ordens
- **THEN** `orders` SHALL conter 3 rows

#### Scenario: Posições importadas com strategy_name
- **WHEN** JSON tem posição BTC-USD
- **THEN** `positions` SHALL conter a posição com strategy_name default

### Requirement: Importar guardiao-state.json
A migração SHALL importar `guardiao-state.json` quando existir.

#### Scenario: Posições do tracker importadas
- **WHEN** `guardiao-state.json` tem posição com take_profit_pct=0.004
- **THEN** `strategy_positions` SHALL conter a posição com TP preservado

#### Scenario: Closed PnL importado
- **WHEN** `guardiao-state.json` tem closed_pnl = [50.0, -20.0, 30.0]
- **THEN** `closed_pnl` SHALL conter 3 registros

### Requirement: Migração idempotente
Rodar migração 2 vezes SHALL não duplicar dados.

#### Scenario: Dupla migração
- **WHEN** migração rodar 2 vezes contra mesmo JSON
- **THEN** database SHALL ter mesmos dados (não duplicados)

### Requirement: JSON preservado após migração
O arquivo JSON original SHALL ser preservado.

#### Scenario: JSON renomeado
- **WHEN** migração completa com sucesso
- **THEN** `paper_state.json` SHALL ser renomeado para `paper_state.v3.migrated.json`

### Requirement: Backup temporal mensal
O sistema SHALL criar backup mensal automático do database.

#### Scenario: Backup mensal criado
- **WHEN** iniciar sistema e backup do mês atual não existe
- **THEN** SHALL copiar `.db` para `backups/paper_state-YYYY-MM.db`

#### Scenario: Backup não duplica no mesmo mês
- **WHEN** backup de 2026-05 já existe
- **THEN** SHALL pular backup para este mês

> "Migrar é ponte, não queimadura" – made by Sky 🌉
