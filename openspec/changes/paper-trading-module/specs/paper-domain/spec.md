# Spec: paper-domain

Entidades e value objects do domínio de paper trading.

## ADDED Requirements

### Requirement: Entidade Portfolio
O sistema SHALL manter uma entidade Portfolio que representa o agregado raiz do paper trading.

#### Scenario: Criar portfolio padrão
- **WHEN** um novo Portfolio é criado sem parâmetros
- **THEN** o sistema SHALL gerar UUID único, saldo inicial de R$ 100.000, e data de criação atual

#### Scenario: Depositar valor no portfolio
- **WHEN** o método `depositar(valor)` é chamado com valor positivo
- **THEN** o sistema SHALL incrementar o saldo_atual

#### Scenario: Retirar valor do portfolio
- **WHEN** o método `retirar(valor)` é chamado com valor positivo e menor ou igual ao saldo
- **THEN** o sistema SHALL decrementar o saldo_atual

#### Scenario: Retirada com saldo insuficiente
- **WHEN** o método `retirar(valor)` é chamado com valor maior que o saldo
- **THEN** o sistema SHALL lançar ValueError com mensagem "Saldo insuficiente"

#### Scenario: Calcular PnL
- **WHEN** o método `pnl()` é chamado
- **THEN** o sistema SHALL retornar a diferença entre saldo_atual e saldo_inicial

#### Scenario: Calcular PnL percentual
- **WHEN** o método `pnl_percentual()` é chamado
- **THEN** o sistema SHALL retornar o PnL como porcentagem do saldo_inicial

### Requirement: Value Object Ticker
O sistema SHALL fornecer um Value Object Ticker imutável para representar símbolos de ativos.

#### Scenario: Criar ticker
- **WHEN** um Ticker é criado com símbolo "petr4"
- **THEN** o sistema SHALL normalizar para "PETR4" (maiúsculas)

#### Scenario: Ticker imutável
- **WHEN** uma tentativa de modificar o símbolo é feita
- **THEN** o sistema SHALL impedir a modificação (frozen dataclass)

#### Scenario: String representation
- **WHEN** `str(ticker)` é chamado
- **THEN** o sistema SHALL retornar o símbolo normalizado
