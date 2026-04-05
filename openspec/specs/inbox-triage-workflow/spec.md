# Spec: Inbox Triage Workflow

## ADDED Requirements

### Requirement: Listar entradas por antiguidade

O sistema SHALL permitir listar entradas do Inbox ordenadas por data de criação (mais antigas primeiro).

#### Scenario: Listar todas as entradas

- **WHEN** usuário solicita triagem do Inbox
- **THEN** sistema lista issues do projeto "Inbox" com status "Inbox Entry"
- **AND** issues são ordenadas por createdAt (ascendente)
- **AND** cada entrada mostra título, idade em dias, labels

#### Scenario: Filtrar por label

- **WHEN** usuário solicita triagem filtrada por label `fonte:discord`
- **THEN** sistema lista apenas issues com label `fonte:discord`
- **AND** ordenação por antiguidade é mantida

### Requirement: Processar entrada - Implementar

O sistema SHALL mover ou transformar issue quando ação decidida é "Implementar".

#### Scenario: Mover para projeto existente

- **WHEN** usuário decide implementar ideia e mover para projeto "Paper Trading"
- **THEN** issue é movida do projeto "Inbox" para "Paper Trading"
- **AND** status é alterado de "Inbox Entry" para "Backlog"
- **AND** label `ação:implementar` é removido
- **AND** comentário é adicionado com contexto da triagem

#### Scenario: Criar nova issue com escopo

- **WHEN** usuário decide implementar mas requer escopo mais detalhado
- **THEN** nova issue é criada no projeto apropriado
- **AND** issue original do Inbox é movida para status "Done"
- **AND** link entre issues é criado (relação "superseded by")

### Requirement: Processar entrada - Pesquisar

O sistema SHALL criar documentação quando ação decidida é "Pesquisar".

#### Scenario: Criar doc de research

- **WHEN** usuário decide pesquisar tópico
- **THEN** arquivo markdown é criado em `docs/research/<topic>.md`
- **AND** arquivo contém título da ideia, contexto, referências
- **AND** issue do Inbox é movida para status "Done"
- **AND** comentário é adicionado com link para o doc criado

#### Scenario: Criar reference em memory

- **WHEN** usuário decide apenas registrar referência
- **THEN** entrada é adicionada em `memory/reference-<topic>.md`
- **AND** issue do Inbox é movida para status "Done"

### Requirement: Processar entrada - Arquivar

O sistema SHALL arquivar entrada quando ação decidida é "Arquivar".

#### Scenario: Arquivar manualmente

- **WHEN** usuário decide arquivar ideia para mais tarde
- **THEN** issue é movida para status "Archived"
- **AND** issue permanece no projeto "Inbox"
- **AND** label `ação:arquivar` é adicionado para futura busca

#### Scenario: Auto-arquivar por expiração

- **WHEN** entrada tem `**Expires:**` < data atual
- **THEN** sistema sugere ação ao usuário durante triagem
- **AND** usuário decide: arquivar, descartar ou renovar expires

### Requirement: Processar entrada - Descartar

O sistema SHALL descartar (deletar) entrada quando ação decidida é "Descartar".

#### Scenario: Descartar entrada

- **WHEN** usuário decide descartar ideia
- **THEN** issue é deletada do Linear
- **AND** confirmação é solicitada antes de deletar
- **AND** log de deleção é registrado para auditoria

### Requirement: Rastrear tempo de triagem

O sistema SHALL permitir rastrear tempo gasto na sessão de triagem via Toggl.

#### Scenario: Iniciar tracking manual

- **WHEN** usuário inicia sessão de triagem
- **THEN** usuário pode executar `/track inbox-triagem`
- **AND** timer Toggl é iniciado com descrição "Inbox Triage"

#### Scenario: Parar tracking

- **WHEN** usuário finaliza sessão de triagem
- **THEN** usuário executa `/track` sem argumentos
- **AND** timer Toggl é parado
- **AND** tempo total é registrado para métricas

### Requirement: Adicionar comentário durante triagem

O sistema SHALL permitir adicionar comentário à issue durante triagem para documentar decisão.

#### Scenario: Comentar ao mover

- **WHEN** usuário move issue para outro projeto
- **THEN** sistema adiciona comentário automático:

```markdown
Triagem em <data>: movido para <projeto>.
Motivo: <decisão do usuário>
```

#### Scenario: Comentário manual

- **WHEN** usuário adiciona comentário manual durante triagem
- **THEN** comentário é preservado na issue
- **AND** comentário sincroniza com Liner (nativo)
