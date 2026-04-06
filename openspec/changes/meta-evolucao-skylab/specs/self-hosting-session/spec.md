# Spec: Self-Hosting Session

## ADDED Requirements

### Requirement: Isolamento por branch
O sistema DEVERÁ criar branch git isolado para cada sessão de self-hosting.

#### Scenario: Branch criado com nome único
- **WHEN** meta-gate cria sessão de self-hosting
- **THEN** branch "skylab-meta-{timestamp}" é criado via `git checkout -b`
- **AND** branch nome contém timestamp único

#### Scenario: Branch isolado não afeta main
- **WHEN** sessão de self-hosting modifica arquivos em branch isolado
- **THEN** branch main permanece inalterado
- **AND** mudanças não são visíveis em main até merge manual

### Requirement: Baseline capture
O sistema DEVERÁ capturar commit baseline antes de qualquer modificação em meta-mode.

#### Scenario: Baseline capturado na criação da sessão
- **WHEN** meta-gate cria MetaModeSession
- **THEN** commit hash atual é capturado como baseline
- **AND** baseline_commit é registrado na sessão

#### Scenario: Baseline usado para rollback
- **WHEN** meta-evolução falha
- **THEN** sistema usa baseline_commit para restore
- **AND** estado é revertido para baseline

### Requirement: Limite de recursão
O sistema DEVERÁ limitar recursão de meta-evolução a máximo 3 níveis (N≤3).

#### Scenario: Nível 1 - Sandbox
- **WHEN** Skylab principal evolui Skylab sandbox (cópia)
- **THEN** recursão nível = 1
- **AND** é permitido sem limites adicionais

#### Scenario: Nível 2 - Meta-mode em main
- **WHEN** Skylab evolui a si mesmo no main branch
- **THEN** recursão nível = 2
- **AND** requer meta-gate approval
- **AND** requer snapshot baseline

#### Scenario: Nível 3 - Meta-gate evolui meta-gate
- **WHEN** Skylab constrói novo meta-gate
- **THEN** recursão nível = 3
- **AND** é nível máximo permitido
- **AND** qualquer tentativa de N=4 é bloqueada

### Requirement: Fechamento de sessão
O sistema DEVERÁ fornecer mecanismo para fechar sessão de meta-mode com sucesso ou falha.

#### Scenario: Sessão fechada com sucesso
- **WHEN** meta-evolução é bem-sucedida
- **THEN** mudanças são commitadas
- **AND** branch é mantido para merge manual
- **AND** sessão retorna status "success"

#### Scenario: Sessão fechada com falha
- **WHEN** meta-evolução falha
- **THEN** branch é mantido para inspeção
- **AND** sessão retorna status "failed"
- **AND** usuário decide manualmente entre keep ou discard

### Requirement: Intention tracking
O sistema DEVERÁ rastrear intenção da meta-evolução na sessão.

#### Scenario: Intenção registrada
- **WHEN** sessão é criada com intenção "improve_evolution"
- **THEN** MetaModeSession.intention = "improve_evolution"
- **AND** intenção é usada para validação e auditoria

#### Scenario: Intenção inválida rejeitada
- **WHEN** usuário tenta criar sessão com intenção "destroy_everything"
- **THEN** meta-gate rejeita criação
- **AND** nenhuma sessão é criada
