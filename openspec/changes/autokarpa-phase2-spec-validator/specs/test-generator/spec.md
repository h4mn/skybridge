## ADDED Requirements

### Requirement: Test Generator usa LLM para gerar testes pytest a partir de specs
O sistema SHALL enviar para a LLM um prompt contendo: spec (requisito + cenário), código alvo atual, e instrução de gerar teste pytest.

#### Scenario: Gerar teste para requisito simples
- **WHEN** recebido SpecRequirement com descrição "função X retorna Y"
- **THEN** o gerador invoca LLM e retorna código de teste pytest com assert validando o comportamento

#### Scenario: Teste gerado segue padrão pytest
- **WHEN** a LLM gera código de teste
- **THEN** o código contém `def test_<nome>()` e usa assert padrão pytest

### Requirement: Test Generator inclui setup e teardown nos testes gerados
O teste gerado SHALL incluir código de setup (criação de fixtures/dados) e o código de execução do sistema sob teste.

#### Scenario: Teste com setup de dados
- **WHEN** o cenário requer mensagens de teste no banco
- **THEN** o teste gerado inclui criação de objetos Message e salvamento no banco antes do assert

### Requirement: Test Generator retorna código puro (sem execução)
O gerador SHALL retornar APENAS o string do código Python, sem executá-lo. A execução é responsabilidade do Test Runner.

#### Scenario: Retorno é string Python
- **WHEN** a LLM retorna código gerado
- **THEN** o gerador retorna o código como string, não executa pytest
