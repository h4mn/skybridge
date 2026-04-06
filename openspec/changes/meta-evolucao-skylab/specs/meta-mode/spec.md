# Spec: Meta-Mode

## ADDED Requirements

### Requirement: Scope validator respeita meta-mode
O sistema DEVERÁ permitir modificações em `core/` quando meta-mode estiver ativo, mas bloquear quando inativo.

#### Scenario: Meta-mode inativo bloqueia core/
- **WHEN** agente tenta modificar `core/evolution.py` com meta-mode=False
- **THEN** scope validator bloqueia modificação
- **AND** sistema levanta ScopeViolation error

#### Scenario: Meta-mode ativo permite core/
- **WHEN** agente modifica `core/evolution.py` com meta-mode=True
- **THEN** scope validator permite modificação
- **AND** mudança é aplicada

### Requirement: Meta-mode requer snapshot prévio
O sistema DEVERÁ exigir snapshot baseline antes de permitir modificações em meta-mode.

#### Scenario: Modificação sem snapshot é bloqueada
- **WHEN** agente tenta modificar `core/` sem snapshot baseline
- **THEN** meta-mode não é ativado
- **AND** sistema retorna erro exigindo snapshot

#### Scenario: Modificação com snapshot é permitida
- **WHEN** agente tenta modificar `core/` com snapshot baseline existente
- **THEN** meta-mode é ativado
- **AND** modificação é permitida

### Requirement: Meta-mode nunca permite testing/ ou quality/
O sistema SOMENTE PODERÁ permitir `core/` e `target/` em meta-mode, nunca `testing/` ou `quality/`.

#### Scenario: Testing é bloqueado mesmo em meta-mode
- **WHEN** agente tenta modificar `testing/test_runner.py` com meta-mode=True
- **THEN** scope validator bloqueia modificação
- **AND** sistema levanta ScopeViolation error

#### Scenario: Quality é bloqueado mesmo em meta-mode
- **WHEN** agente tenta modificar `quality/mutation.py` com meta-mode=True
- **THEN** scope validator bloqueia modificação
- **AND** sistema levanta ScopeViolation error

### Requirement: Teste duplo após modificação em core/
O sistema DEVERÁ executar testes duplos (target + sistema) após qualquer modificação em `core/`.

#### Scenario: Teste duplo passa
- **WHEN** agente modifica `core/evolution.py`
- **THEN** sistema executa testes do target
- **AND** sistema executa testes do evolution loop
- **AND** ambos passam
- **AND** mudança é mantida

#### Scenario: Teste do sistema falha
- **WHEN** agente modifica `core/evolution.py`
- **AND** testes do target passam
- **BUT** testes do evolution loop falham
- **THEN** sistema descarta mudança
- **AND** restore snapshot baseline
