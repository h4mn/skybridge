# Spec: Position View

Tela mostrando posições abertas/fechadas, lucro/prejuízo total e por ativo, com histórico de operações.

## ADDED Requirements

### Requirement: Cards de resumo

O sistema SHALL exibir cards de resumo com métricas gerais de posição.

#### Scenario: Exibição de lucro/prejuízo
- **GIVEN** o estado é POSITION
- **WHEN** a view é renderizada
- **THEN** dois cards são exibidos: "Lucro" e "Prejuízo"
- **AND** o card de Lucro mostra valor total (ex: R$ 110,00)
- **AND** o card de Prejuízo mostra valor total (ex: R$ 83,00)
- **AND** cards secundários mostram "Resultado", "Operações", "Vencedoras" (%)

### Requirement: Tabela de operações por ativo

O sistema SHALL listar todas as operações abertas/fechadas por ativo.

#### Scenario: Tabela de operações
- **GIVEN** o estado é POSITION
- **WHEN** a view é renderizada
- **THEN** uma tabela é exibida com as colunas: Ativo, Abriu, Fechou, Resultado, Corretora
- **AND** cada linha mostra uma operação diferente
- **AND** operações lucrativas são destacadas visualmente (cor verde)
- **AND** operações deficitárias são destacadas visualmente (cor vermelha)

### Requirement: Navegação

O sistema SHALL permitir navegação entre Position e outras telas.

#### Scenario: Retorno ao Dashboard
- **GIVEN** o estado é POSITION
- **WHEN** o usuário clica em "🏠 Home"
- **THEN** o estado muda para DASHBOARD
- **AND** a view é editada com conteúdo do Dashboard
