# Tasks Context — Gerenciamento de Tarefas e Wiki

## O que é

Bounded Context para gerenciamento de tarefas com entidades Task/Note/Group/List e funcionalidade wiki.

## Linguagem e Limites

### Responsabilidades (dentro)
- Gerenciamento de tarefas: criar, editar, promover, arquivar
- Entidades: Task, Note, Group, List
- Histórico com Event Sourcing
- Estados e transições de tarefas
- Wiki e documentação vinculada

### Responsabilidades (fora)
- Sync com Trello/Discord (infra/integrations)
- UI de gestão (apps)
- Automação complexa (plugins)

## Entidades e Invariantes

- **Task**: tarefa individual com título, descrição, estado, metadata
- **Note**: nota rápida vinculada a tarefas ou independente
- **Group**: agrupamento de tarefas/notes
- **List**: lista ordenada de itens

## Eventos Emitidos (Event Sourcing)

- `TaskCreated` — nova tarefa criada
- `TaskUpdated` — tarefa modificada
- `TaskPromoted` — tarefa promovida (ex: para backlog)
- `TaskArchived` — tarefa arquivada
- `NoteCreated` — nota criada
- `GroupCreated` — grupo criado

## Dependências Permitidas

### Ports (interfaces)
- `EventStorePort` — persistência de eventos
- `ProjectionPort` — leituras materializadas
- `TaskRepositoryPort` — consultas de tarefas

### Adapters
- Implementações concretas vivem em `infra/contexts/tasks/`
- Event store em JSON (inicialmente)

---

> "Tarefas são a unidade mínima de progresso." – made by Sky ✨
