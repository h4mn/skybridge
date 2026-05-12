## ADDED Requirements

### Requirement: CQS — Queries granulares
O `SQLitePaperState` SHALL oferecer queries separadas por entidade (CQS: Command-Query Separation).

#### Scenario: get_position por ticker e estratégia
- **WHEN** chamar `get_position(ticker="BTC-USD", strategy_name="guardiao-conservador")`
- **THEN** SHALL retornar dict com dados da posição ou None

#### Scenario: list_orders com filtros
- **WHEN** chamar `list_orders(ticker="BTC-USD", status="EXECUTADA")`
- **THEN** SHALL retornar lista de ordens filtradas

#### Scenario: get_cashbook
- **WHEN** chamar `get_cashbook()`
- **THEN** SHALL retornar dict de currencies com amounts

#### Scenario: get_closed_pnl por ticker
- **WHEN** chamar `get_closed_pnl(ticker="BTC-USD")`
- **THEN** SHALL retornar lista de PnLs fechados para o ticker

### Requirement: CQS — Commands granulares
O `SQLitePaperState` SHALL oferecer commands que escrevem só a tabela afetada.

#### Scenario: save_order grava só tabela orders
- **WHEN** chamar `save_order(order_dict)`
- **THEN** SHALL inserir 1 row em orders sem tocar outras tabelas

#### Scenario: update_position grava só tabela positions
- **WHEN** chamar `update_position(ticker, strategy_name, data)`
- **THEN** SHALL atualizar/upsert 1 row em positions sem tocar outras tabelas

#### Scenario: save_pnl grava só tabela closed_pnl
- **WHEN** chamar `save_pnl(pnl_dict)`
- **THEN** SHALL inserir 1 row em closed_pnl sem tocar outras tabelas

#### Scenario: save_signal grava só tabela signals
- **WHEN** chamar `save_signal(signal_dict)`
- **THEN** SHALL inserir 1 row em signals sem tocar outras tabelas

#### Scenario: save_tick grava só tabela ticks_raw
- **WHEN** chamar `save_tick(tick_dict)`
- **THEN** SHALL inserir 1 row em ticks_raw sem tocar outras tabelas

#### Scenario: save_ohlcv grava só tabela ohlcv
- **WHEN** chamar `save_ohlcv(candle_dict)`
- **THEN** SHALL inserir 1 row em ohlcv sem tocar outras tabelas

### Requirement: Instanciação cria database
O `SQLitePaperState` SHALL criar o database com todas as tabelas na primeira vez.

#### Scenario: Database novo criado com WAL
- **WHEN** criar `SQLitePaperState("data/paper_state.db")`
- **THEN** SHALL criar arquivo com todas as tabelas e WAL ativo

#### Scenario: Carrega estado vazio
- **WHEN** chamar queries em database novo
- **THEN** SHALL retornar defaults (cashbook vazio, sem ordens, sem posições)

### Requirement: Atomicidade por operação
Cada command SHALL executar em sua própria transação.

#### Scenario: Falha em save_order não afeta save_pnl
- **WHEN** `save_order()` falha (constraint violation)
- **THEN** `save_pnl()` anterior SHALL permanecer gravado

### Requirement: Crash recovery via WAL
O SQLite SHALL sobreviver a crashes de processo sem corrupção.

#### Scenario: Dados intactos após kill
- **WHEN** gravar dados e matar processo sem graceful shutdown
- **THEN** reabrir database SHALL ter dados do último commit

### Requirement: Conexão única reutilizável
O `SQLitePaperState` SHALL manter uma única conexão SQLite reutilizada entre operações.

#### Scenario: Múltiplas queries sem reopen
- **WHEN** chamar `get_position()` 10 vezes seguidas
- **THEN** SHALL usar mesma conexão

### Requirement: Compatibilidade com PaperStatePort legado
O `carregar()` e `salvar(PaperStateData)` SHALL funcionar como fallback.

#### Scenario: carregar monta PaperStateData completo
- **WHEN** chamar `carregar()` em database com ordens e posições
- **THEN** SHALL retornar `PaperStateData` com todos os campos preenchidos

#### Scenario: salvar reescreve todas as tabelas
- **WHEN** chamar `salvar(PaperStateData)` com dados completos
- **THEN** SHALL sincronizar todas as tabelas em 1 transação

> "CQS: cada método faz uma coisa e faz bem" – made by Sky 🔌
