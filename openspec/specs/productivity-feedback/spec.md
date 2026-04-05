# productivity-feedback Specification

## Purpose
TBD - created by archiving change document-track-productivity-system. Update Purpose after archive.
## Requirements
### Requirement: Calculadora de cotas
O sistema SHALL calcular cotas de produtividade baseadas em tempo trabalhado.

#### Scenario: Cálculo por hora
- **WHEN** usuário trabalha 1 hora
- **THEN** sistema calcula 0.625 cotas
- **AND** exibe: "1 hora = 0.625 cotas"

#### Scenario: Meta diária
- **WHEN** usuário trabalha 8 horas (480 min)
- **THEN** sistema calcula 5 cotas
- **AND** exibe: "Meta diária atingida! 5 cotas"

#### Scenario: Meta mensal
- **WHEN** mês tem 20 dias úteis
- **THEN** meta é 100 cotas
- **AND** exibe progresso: "X/100 cotas (Y%)"

#### Scenario: Custo do tempo
- **WHEN** usuário pergunta quanto custou 2h de trabalho
- **THEN** sistema calcula: 2 × 0.625 = 1.25 cotas
- **AND** exibe: "1.25% do salário mensal"

### Requirement: Feedback estruturado em intervalos
O sistema SHALL fornecer feedback ao final de cada ciclo Pomodoro.

#### Scenario: Feedback após 50min
- **WHEN** timer para após 50min de trabalho
- **THEN** sistema exibe:
  - Duração: 50min
  - Cotas: 0.52 cotas
  - Progresso diário: X/5 cotas

#### Scenario: Feedback durante pausa
- **WHEN** break de 10min está em andamento
- **THEN** sistema exibe countdown
- **AND** sugere: "Aproveite para descansar e hidratar"

#### Scenario: Resumo do dia
- **WHEN** usuário solicita resumo diário
- **THEN** sistema soma todas entries do dia
- **AND** exibe: total horas, cotas, progresso vs meta

### Requirement: Integração RescueTime (futura)
O sistema SHALL integrar com RescueTime para métricas de produtividade.

#### Scenario: Score de produtividade
- **WHEN** usuário solicita score do dia
- **THEN** sistema chama `get_productivity_score` via MCP RescueTime
- **AND** exibe: productive_time vs distracting_time

#### Scenario: Destaques do dia
- **WHEN** RescueTime tem highlights registrados
- **THEN** sistema exibe top 3 atividades produtivas
- **AND** sugere: "Continue focado no que gera valor"

#### Scenario: API RescueTime indisponível
- **WHEN** RescueTime MCP falha
- **THEN** sistema degrada graciosamente
- **AND** continua funcionando sem métricas de produtividade

### Requirement: Padrões de produtividade
O sistema SHALL identificar padrões que afetam produtividade.

#### Scenario: Alpha patterns
- **WHEN** tags como "implementacao" correlacionam com alta produtividade
- **THEN** sistema identifica: "Implementação = -30% tempo estimado"
- **AND** sugere: "Priorize tarefas de implementação"

#### Scenario: Beta patterns
- **WHEN** tags como "sem-specs" correlacionam com baixa produtividade
- **THEN** sistema identifica: "Sem specs = +50% tempo estimado"
- **AND** sugere: "Especifique antes de implementar"

#### Scenario: Alerta de estagnação
- **WHEN** tarefa está parada > 4h
- **THEN** sistema alerta: "Tarefa X estagnada há 4h"
- **AND** sugere: "Está bloqueado? Considere pedir ajuda"

### Requirement: Precisão de estimativa
O sistema SHALL rastrear precisão de estimativas vs realidade.

#### Scenario: Estimativa precisa
- **WHEN** tarefa estimada em 2 cotas leva 2 cotas
- **THEN** precisão = 100%
- **AND** sistema registra em history.json: "precisao": 100

#### Scenario: Estimativa registrada
- **WHEN** tarefa é concluída
- **THEN** history.json armazena: estimativa_cotas, real_cotas, precisao%
- **AND** dados são persistidos para análise de padrões futuros

#### Scenario: Meta de precisão
- **WHEN** precisão média < 80%
- **THEN** sistema sugere: "Revise método de estimativa"
- **AND** recomenda: "Use referências históricas de history.json"

#### Scenario: Estimativa otimista
- **WHEN** tarefa estimada em 2 cotas leva 4 cotas
- **THEN** precisão = 50%
- **AND** sistema alerta: "Estimativa foi otimista"
- **AND** sugere: "Adicione 50% de buffer para próximas estimativas"

#### Scenario: Meta de precisão
- **WHEN** precisão média < 80%
- **THEN** sistema sugere: "Revise método de estimativa"
- **AND** recomenda: "Use referências históricas"

---

> "Cotas são a moeda do seu tempo. Gaste com sabedoria" – made by Sky [feedback]

