# Spec: Meta-Gate

## ADDED Requirements

### Requirement: Validação de intenção explicita
O sistema SOMENTE PODERÁ permitir entrada em meta-modo quando a intenção for explicitamente declarada como uma das intenções válidas: "improve_evolution", "fix_bug", ou "refactor".

#### Scenario: Intenção válida é aceita
- **WHEN** usuário solicita meta-modo com intenção "improve_evolution"
- **THEN** sistema libera entrada em meta-modo

#### Scenario: Intenção inválida é rejeitada
- **WHEN** usuário solicita meta-modo com intenção "destroy_everything"
- **THEN** sistema bloqueia entrada com mensagem de erro listando intenções válidas

### Requirement: Snapshot baseline obrigatório
O sistema SOMENTE PODERÁ permitir entrada em meta-modo quando houver um snapshot baseline disponível (git commit existente).

#### Scenario: Sem snapshot baseline
- **WHEN** usuário solicita meta-modo sem commits baseline
- **THEN** sistema bloqueia entrada com mensagem instruindo criar commit baseline

#### Scenario: Com snapshot baseline
- **WHEN** usuário solicita meta-modo com commits baseline existentes
- **THEN** sistema permite entrada em meta-modo

### Requirement: Code Health mínimo
O sistema SOMENTE PODERÁ permitir entrada em meta-modo quando Code Health atual for maior que 0.5.

#### Scenario: Code Health insuficiente
- **WHEN** usuário solicita meta-modo com Code Health de 0.3
- **THEN** sistema bloqueia entrada informando que Code Health mínimo é 0.5

#### Scenario: Code Health suficiente
- **WHEN** usuário solicita meta-modo com Code Health de 0.8
- **THEN** sistema permite entrada em meta-modo

### Requirement: Self-hosting target validation
O sistema SOMENTE PODERÁ permitir entrada em meta-modo quando o target for o próprio Skylab (self-hosting).

#### Scenario: Target não é Skylab
- **WHEN** usuário solicita meta-modo para target "demo-todo-list"
- **THEN** sistema bloqueia entrada informando que meta-modo é apenas para self-hosting

#### Scenario: Target é Skylab
- **WHEN** usuário solicita meta-modo para target "skylab"
- **THEN** sistema permite entrada em meta-modo

### Requirement: Criação de sessão isolada
O sistema DEVERÁ criar uma sessão de meta-modo isolada em branch separado quando meta-modo for autorizado.

#### Scenario: Sessão criada com sucesso
- **WHEN** meta-gate autoriza entrada em meta-modo
- **THEN** sistema cria branch "skylab-meta-{timestamp}"
- **AND** captura commit baseline
- **AND** retorna MetaModeSession com session_id, branch_name e baseline_commit
