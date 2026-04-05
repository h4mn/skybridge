# paper-state Specification

## Purpose
TBD - created by archiving change paper-state-migration. Update Purpose after archive.
## Requirements
### Requirement: PaperStatePort provê interface unificada para persistência

O sistema SHALL expor uma porta `PaperStatePort` que define o contrato para
leitura e escrita do estado completo do paper trading.

#### Scenario: Carregar estado existente
- **WHEN** `PaperStatePort.carregar()` é chamado
- **THEN** retorna `PaperStateData` com saldo, ordens, posições e portfolios

#### Scenario: Salvar estado completo
- **WHEN** `PaperStatePort.salvar(data: PaperStateData)` é chamado
- **THEN** escreve arquivo JSON com schema v2 unificado

#### Scenario: Resetar para estado inicial
- **WHEN** `PaperStatePort.resetar(saldo_inicial: Decimal)` é chamado
- **THEN** limpa ordens, posições e portfolios; define saldo = saldo_inicial

---

### Requirement: JsonFilePaperState migra schema v1 para v2

O sistema SHALL detectar schema legado e migrar automaticamente.

#### Scenario: Arquivo inexistente cria estado vazio
- **WHEN** arquivo `paper_state.json` não existe
- **THEN** cria novo arquivo com saldo_inicial padrão de 100000.0

#### Scenario: Schema v1 migra para v2
- **WHEN** arquivo tem `version: 1` ou sem version
- **THEN** migra para schema v2 preservando todos os dados existentes
- **AND** cria backup em `paper_state.json.v1.bak`

#### Scenario: Schema v2 carrega diretamente
- **WHEN** arquivo tem `version: 2`
- **THEN** carrega sem modificação

---

### Requirement: PaperStateData representa estado completo

O sistema SHALL definir um dataclass `PaperStateData` que encapsula:
- `version: int` (sempre 2)
- `updated_at: datetime`
- `saldo: Decimal`
- `saldo_inicial: Decimal`
- `ordens: Dict[str, OrdemData]`
- `posicoes: Dict[str, PosicaoData]`
- `portfolios: Dict[str, PortfolioData]`

#### Scenario: Serialização JSON completa
- **WHEN** `PaperStateData` é serializado
- **THEN** produz JSON válido com todos os campos

#### Scenario: Deserialização preserva tipos
- **WHEN** JSON é deserializado para `PaperStateData`
- **THEN** Decimal permanece Decimal, datetime permanece datetime

---

### Requirement: JsonFilePaperBroker delega persistência

O adapter `JsonFilePaperBroker` SHALL delegar I/O para `PaperStatePort`.

#### Scenario: Broker não escreve diretamente no arquivo
- **WHEN** broker executa `enviar_ordem()`
- **THEN** chama `paper_state.salvar()` em vez de escrever JSON diretamente

#### Scenario: Broker lê via PaperState
- **WHEN** broker precisa ler saldo ou posições
- **THEN** chama `paper_state.carregar()`

---

### Requirement: JsonFilePortfolioRepository delega persistência

O adapter `JsonFilePortfolioRepository` SHALL delegar I/O para `PaperStatePort`.

#### Scenario: Repository não sobrescreve dados do broker
- **WHEN** repository salva um portfolio
- **THEN** preserva ordens e posições existentes no JSON

#### Scenario: Repository lê portfolios do estado unificado
- **WHEN** repository carrega portfolios
- **THEN** obtém dados de `paper_state.carregar().portfolios`

