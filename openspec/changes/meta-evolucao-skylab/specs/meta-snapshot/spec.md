# Spec: Meta-Snapshot

## ADDED Requirements

### Requirement: Criação de snapshot via git
O sistema DEVERÁ criar snapshot do estado atual usando git commit quando solicitado.

#### Scenario: Snapshot criado com sucesso
- **WHEN** sistema solicita criação de snapshot
- **THEN** sistema executa `git add -A`
- **AND** sistema executa `git commit -m "<message>"`
- **AND** sistema retorna commit hash do snapshot criado

#### Scenario: Snapshot com mensagem customizada
- **WHEN** usuário solicita snapshot com mensagem "baseline: antes do meta-modo"
- **THEN** sistema cria commit com essa mensagem exata

### Requirement: Restore de snapshot via git
O sistema DEVERÁ restaurar snapshot anterior usando git reset quando solicitado.

#### Scenario: Restore com sucesso
- **WHEN** sistema solicita restore para snapshot hash "abc123"
- **THEN** sistema executa `git reset --hard abc123`
- **AND** sistema retorna True indicando sucesso

#### Scenario: Restore de snapshot inexistente
- **WHEN** sistema solicita restore para snapshot hash inexistente
- **THEN** sistema retorna False indicando falha
- **AND** sistema mantém estado atual

### Requirement: Snapshot atômico
O sistema DEVERÁ garantir que snapshot seja atômico (ou succeeds completamente ou fails sem mudanças).

#### Scenario: Snapshot atômico em falha parcial
- **WHEN** git add falha durante criação de snapshot
- **THEN** nenhum commit é criado
- **AND** sistema retorna erro
- **AND** estado do working directory permanece inalterado
