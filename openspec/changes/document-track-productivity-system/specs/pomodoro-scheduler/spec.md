# Spec: Pomodoro Scheduler

Capability para gerenciamento de ciclos Pomodoro 50+10 (trabalho + pausa) otimizado para trabalho com IA.

## ADDED Requirements

### Requirement: Lógica de retomada
O sistema SHALL retomar timer automaticamente quando break terminou E ciclo completo foi trabalhado.

#### Scenario: Retoma bem-sucedida
- **WHEN** break ≥ 10min E último trabalho ≥ 50min (3000s)
- **THEN** sistema retorna ação `start` com parâmetros do último timer
- **AND** usuário é notificado: "Timer retomado!"

#### Scenario: Break não terminado
- **WHEN** break < 10min desde last_stop
- **THEN** sistema retorna ação `wait`
- **AND** mensagem: "Break não terminou ou ciclo incompleto"

#### Scenario: Ciclo incompleto
- **WHEN** último trabalho < 50min
- **THEN** sistema não retoma automaticamente
- **AND** sugere iniciar novo timer manualmente

### Requirement: Rastreamento de estado
O sistema SHALL persistir informações do último ciclo para retomada inteligente.

#### Scenario: Persistência ao iniciar
- **WHEN** timer é iniciado
- **THEN** state.json registra `last_start` e contexto atual

#### Scenario: Persistência ao parar
- **WHEN** timer é parado
- **THEN** state.json registra `last_stop`, `last_duration`, `last_timer`
- **AND** `running` é definido como `false`

#### Scenario: Recuperação de contexto
- **WHEN** usuário solicita retomada
- **THEN** sistema recupera `last_timer` de state.json
- **AND** usa mesmos project, tags, description

### Requirement: Ciclo 50+10 otimizado para IA
O sistema SHALL implementar ciclo de 50min trabalho + 10min pausa.

#### Scenario: Trabalho profundo
- **WHEN** timer está rodando
- **THEN** 50min permite: 2min setup + 35min execução + 3min review + 10min pausa
- **AND** usuário recebe lembrete após 50min

#### Scenario: Pausa produtiva
- **WHEN** timer para após 50min
- **THEN** sistema aguarda 10min de break
- **AND** break permite digestão + planejamento próximo ciclo

#### Scenario: Diferença de 25+5
- **WHEN** usuário questiona por que não 25+5
- **THEN** sistema explica: IA precisa de contexto, 50min é mais eficiente para trabalho colaborativo

### Requirement: Cálculo de cotas
O sistema SHALL calcular cotas de produtividade baseadas em tempo trabalhado.

#### Scenario: Cotas por hora
- **WHEN** usuário trabalha 1 hora
- **THEN** sistema calcula 0.625 cotas
- **AND** exibe: "Você produziu 0.625 cotas nesta sessão"

#### Scenario: Meta diária
- **WHEN** usuário trabalha 8 horas
- **THEN** sistema calcula 5 cotas (meta diária)
- **AND** exibe: "Meta atingida! 5 cotas = 1 dia de trabalho"

#### Scenario: Meta mensal
- **WHEN** mês tem 20 dias úteis
- **THEN** meta é 100 cotas = salário completo
- **AND** progresso é rastreado em state.json

---

> "Contexto é caro, então estica o ciclo. 50+10 > 25+5 com IA" – made by Sky [pomodoro]
