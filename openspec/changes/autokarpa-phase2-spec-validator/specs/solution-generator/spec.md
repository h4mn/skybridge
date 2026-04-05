## ADDED Requirements

### Requirement: Solution Generator propõe correção quando teste falha
O sistema SHALL enviar para a LLM: o código que falhou, o teste que falhou, o erro capturado, e a spec original; e receber código corrigido.

#### Scenario: Gera correção para assert falho
- **WHEN** teste falha com `assert result[0].text == "C", got "A"`
- **THEN** o gerador propõe correção no código que inverte a ordem

#### Scenario: Gera correção mínima (sem refatoração)
- **WHEN** o teste falha e múltiplas correções são possíveis
- **THEN** o gerador propõe a correção MÍNIMA para passar no teste (não refatora código inteiro)

### Requirement: Solution Generator recebe código puro como resposta
A LLM SHALL retornar apenas a função ou método corrigido, não o arquivo inteiro.

#### Scenario: Retorno é função única
- **WHEN** a correção afeta apenas `get_chat_history`
- **THEN** a LLM retorna apenas `def get_chat_history(...):` corrigida

### Requirement: Solution Generator valida sintaxe antes de retornar
O código proposto SHALL ser validado (AST parse) antes de ser considerado válido.

#### Scenario: Validação de sintaxe Python
- **WHEN** a LLM retorna código corrigido
- **THEN** o gerador faz parse com `ast.parse()` e rejeita se houver SyntaxError
