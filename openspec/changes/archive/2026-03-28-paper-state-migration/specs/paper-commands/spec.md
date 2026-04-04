# Spec: paper-commands

## ADDED Requirements

### Requirement: CriarOrdemCommand encapsula dados de entrada

O sistema SHALL definir `CriarOrdemCommand` com campos:
- `ticker: str`
- `lado: str` ("compra" ou "venda")
- `quantidade: int`
- `preco_limite: Optional[Decimal]`

#### Scenario: Command válido para ordem a mercado
- **WHEN** command criado com ticker="BTC-USD", lado="compra", quantidade=1
- **THEN** command é válido com preco_limite=None

#### Scenario: Command válido para ordem limitada
- **WHEN** command criado com ticker="BTC-USD", lado="compra", quantidade=1, preco_limite=66000
- **THEN** command é válido

---

### Requirement: CriarOrdemHandler executa ordem via broker

O sistema SHALL definir `CriarOrdemHandler` que:
1. Valida command
2. Obtém cotação atual (se ordem a mercado)
3. Delega execução para `BrokerPort`
4. Persiste estado via `PaperStatePort`

#### Scenario: Ordem de compra a mercado executada
- **WHEN** handler processa command de compra BTC-USD quantidade=1
- **THEN** broker.executar_ordem() é chamado
- **AND** paper_state.salvar() é chamado
- **AND** resultado contém ordem_id e status="executada"

#### Scenario: Saldo insuficiente rejeita ordem
- **WHEN** saldo=1000 e ordem de compra BTC-USD quantidade=1 (preço > 1000)
- **THEN** ordem é rejeitada com status="rejeitada"
- **AND** motivo="saldo_insuficiente"

#### Scenario: Venda sem posição rejeita ordem
- **WHEN** portfólio não tem posição em ticker
- **THEN** ordem de venda é rejeitada com motivo="sem_posicao"

---

### Requirement: DepositarCommand adiciona fundos

O sistema SHALL definir `DepositarCommand` com:
- `valor: Decimal`

#### Scenario: Depósito aumenta saldo
- **WHEN** handler processa command com valor=10000
- **THEN** saldo aumenta em 10000
- **AND** paper_state é atualizado

---

### Requirement: ResetarCommand limpa posições

O sistema SHALL definir `ResetarCommand` que:
- Limpa todas as ordens
- Limpa todas as posições
- Restaura saldo para saldo_inicial

#### Scenario: Reset volta ao estado inicial
- **WHEN** handler processa ResetarCommand
- **THEN** saldo = saldo_inicial
- **AND** ordens = {}
- **AND** posicoes = {}
