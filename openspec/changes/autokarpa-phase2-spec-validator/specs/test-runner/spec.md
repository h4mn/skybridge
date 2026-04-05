## ADDED Requirements

### Requirement: Test Runner executa testes pytest em subprocess isolado
O sistema SHALL escrever o código do teste em um arquivo temporário e executar `pytest` via subprocess com timeout.

#### Scenario: Execução com sucesso
- **WHEN** o teste é executado e todos os asserts passam
- **THEN** o subprocess retorna código de saída 0 e o runner marca teste como `passed`

#### Scenario: Execução com falha
- **WHEN** o teste contém assert que falha
- **THEN** o subprocess retorna código de saída 1 e o runner captura a mensagem de erro

#### Scenario: Execução com erro de sintaxe
- **WHEN** o teste gerado tem erro de sintaxe Python
- **THEN** o subprocess retorna código diferente e o runner captura SyntaxError

### Requirement: Test Runner captura saída padrão e erro do pytest
O runner SHALL capturar stdout e stderr do subprocess para análise posterior pelo Solution Generator.

#### Scenario: Captura de AssertionError
- **WHEN** o teste falha com `assert X == Y`
- **THEN** o runner captura a linha `AssertionError` com valores de X e Y

#### Scenario: Captura de traceback completo
- **WHEN** o teste levanta exceção inesperada
- **THEN** o runner captura o traceback completo (linhas, arquivos, mensagens)

### Requirement: Test Runner impõe timeout para evitar travamentos
Cada execução de teste SHALL ter timeout máximo (configurável, padrão 30s).

#### Scenario: Timeout encerra execução
- **WHEN** o teste leva mais de 30 segundos para completar
- **THEN** o runner mata o subprocesso e marca resultado como `timeout`
