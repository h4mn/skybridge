# Spec: State Snapshot

Captura do estado completo da UI em um momento específico, com comparação entre snapshots.

## ADDED Requirements

### Requirement: Capturar snapshot do estado atual

O sistema SHALL capturar o estado completo de todos os widgets registrados em um momento específico.

#### Scenario: Snapshot manual
- **WHEN** `SkyTextualDOM.snapshot()` é chamado
- **THEN** um `DOMSnapshot` é criado contendo:
  - Timestamp de captura
  - Estado de todos os `DOMNode`s
  - Todas as props reactive de todos os widgets
  - Estrutura hierárquica completa

#### Scenario: Snapshot inclui metadata
- **WHEN** um snapshot é capturado
- **THEN** o snapshot contém metadata:
  - `timestamp`: `datetime` com timezone
  - `widget_count`: Número total de widgets
  - `session_id`: Identificador da sessão atual
  - `git_commit`: Commit do código em execução (se disponível)

#### Scenario: Snapshot é imutável
- **WHEN** um snapshot é criado
- **THEN** seu conteúdo não pode ser modificado
- **AND** o snapshot é uma cópia profunda (deep copy) do estado

---

### Requirement: Snapshot com nome e descrição

O sistema SHALL permitir nomear snapshots e adicionar descrições para organização.

#### Scenario: Snapshot com nome
- **WHEN** `SkyTextualDOM.snapshot(name="antes-da-mudanca")` é chamado
- **THEN** o snapshot é salvo com esse nome
- **AND** pode ser recuperado via `SkyTextualDOM.get_snapshot("antes-da-mudanca")`

#### Scenario: Snapshot com descrição
- **WHEN** `snapshot(desc="Estado antes de aplicar o fix do bug")` é chamado
- **THEN** a descrição é anexada ao snapshot
- **AND** aparece na listagem de snapshots

#### Scenario: Snapshot sem nome usa timestamp
- **WHEN** `snapshot()` é chamado sem nome
- **THEN** o nome é gerado automaticamente: `snapshot_YYYYMMDD_HHMMSS`
- **EXAMPLE**: `snapshot_20250228_143201`

#### Scenario: Sobrescrever snapshot existente
- **WHEN** `snapshot(name="meu-snapshot", overwrite=True)` é chamado
- **THEN** o snapshot existente é substituído
- **AND** sem `overwrite=True`, um erro é lançado

---

### Requirement: Lista de snapshots

O sistema SHALL manter um registro de todos os snapshots capturados na sessão.

#### Scenario: Listar snapshots
- **WHEN** `SkyTextualDOM.list_snapshots()` é chamado
- **THEN** retorna lista de snapshots ordenados por timestamp (mais recente primeiro)
- **AND** cada entrada mostra:
  - `name`
  - `timestamp`
  - `desc` (se existir)
  - `size_bytes` (tamanho aproximado)

#### Scenario: Listar com limite
- **WHEN** `list_snapshots(limit=10)` é chamado
- **THEN** apenas os 10 snapshots mais recentes são retornados

#### Scenario: Filtrar snapshots por nome
- **WHEN** `list_snapshots(filter="bug-fix")` é chamado
- **THEN** apenas snapshots com "bug-fix" no nome são retornados

---

### Requirement: Diff entre snapshots

O sistema SHALL calcular diferenças entre dois snapshots, identificando mudanças de estado.

#### Scenario: Diff simples (adicional)
- **WHEN** um widget novo aparece no snapshot B
- **THEN** o diff marca como `+ADDED`
- **AND** mostra o estado completo do novo widget

#### Scenario: Diff simples (removido)
- **WHEN** um widget existe no snapshot A mas não no B
- **THEN** o diff marca como `-REMOVED`
- **AND** mostra o estado do widget removido

#### Scenario: Diff simples (modificado)
- **WHEN** uma prop reactive mudou entre A e B
- **THEN** o diff marca como `~MODIFIED`
- **AND** mostra `{prop: {old: valor_A, new: valor_B}}`

#### Scenario: Diff hierárquico
- **WHEN** widgets deep na árvore mudaram
- **THEN** o diff mostra o path completo até o widget modificado
- **EXAMPLE**: `ChatScreen > ChatHeader > AnimatedTitle > AnimatedVerb.estado`

#### Scenario: Diff com formatação colorida
- **WHEN** o diff é exibido na DevTools
- **THEN** adições são verdes, remoções são vermelhas, modificações são amarelas
- **AND** valores old/new são lado a lado para comparação

---

### Requirement: Diff focado em widget específico

O sistema SHALL permitir calcular diff para um único widget entre snapshots.

#### Scenario: Diff de único widget
- **WHEN** `diff(snapshot_a, snapshot_b, dom_id="AnimatedVerb_123")` é chamado
- **THEN** apenas mudanças desse widget são calculadas
- **AND** o resultado é mais rápido que diff completo

#### Scenario: Diff de prop específica
- **WHEN** `diff(..., prop="_offset")` é adicionalmente especificado
- **THEN** apenas mudanças dessa prop são retornadas
- **AND** o resultado mostra a linha do tempo da prop entre os snapshots

---

### Requirement: Persistência de snapshots

O sistema SHALL salvar snapshots em disco para recuperação entre sessões.

#### Scenario: Salvar snapshot em arquivo
- **WHEN** `snapshot.save(path="/tmp/snapshot.json")` é chamado
- **THEN** o snapshot é salvo como JSON comprimido
- **AND** o arquivo pode ser carregado em outra sessão

#### Scenario: Carregar snapshot do arquivo
- **WHEN** `SkyTextualDOM.load_snapshot("/tmp/snapshot.json")` é chamado
- **THEN** o snapshot é carregado e pode ser usado em diffs
- **AND** um erro é lançado se o arquivo for inválido

#### Scenario: Snapshots automáticos antes de ações
- **WHEN** uma ação destrutiva é executada (ex: limpar histórico)
- **THEN** um snapshot automático é capturado
- **AND** nomeado como `auto_snapshot_<action>_<timestamp>`

---

### Requirement: Exportação/importação de snapshots

O sistema SHALL permitir exportar snapshots para análise externa e importar de outras fontes.

#### Scenario: Exportar como JSON
- **WHEN** `snapshot.export(fmt="json")` é chamado
- **THEN** retorna string JSON com estado completo
- **AND** o JSON é legível e pode ser inspecionado manualmente

#### Scenario: Exportar como texto formatado
- **WHEN** `snapshot.export(fmt="txt")` é chamado
- **THEN** retorna string formatada com árvore de estado
- **AND** indentação e cores (se terminal suportar)

#### Scenario: Importar snapshot de outra sessão
- **WHEN** um snapshot JSON de outro computador é importado
- **THEN** o snapshot é válido para diffs
- **AND** metadados de origem são preservados

---

### Requirement: Timeline de snapshots

O sistema SHALL manter uma timeline visual de snapshots para facilitar comparações temporais.

#### Scenario: Timeline com múltiplos snapshots
- **WHEN** 5+ snapshots existem
- **THEN** uma timeline visual mostra pontos no tempo
- **AND** snapshots podem ser selecionados na timeline

#### Scenario: Timeline indica tipo de snapshot
- **WHEN** snapshots são exibidos na timeline
- **THEN** snapshots automáticos têm ícone diferente de manuais
- **AND** snapshots com erro são marcados em vermelho

#### Scenario: Navegar na timeline
- **WHEN** o usuário clica em um ponto da timeline
- **THEN** o snapshot correspondente é carregado
- **AND** o diff com o snapshot anterior é calculado automaticamente

---

### Requirement: Performance de snapshot

O sistema SHALL capturar snapshots com overhead mínimo.

#### Scenario: Snapshot rápido (< 100ms)
- **WHEN** `snapshot()` é chamado em uma UI com 50 widgets
- **THEN** a captura completa em menos de 100ms
- **AND** a UI não congela durante a captura

#### Scenario: Snapshot incremental
- **WHEN** snapshots frequentes são necessários
- **THEN** `snapshot(incremental=True)` captura apenas mudanças desde o último
- **AND** é significativamente mais rápido que snapshot completo

#### Scenario: Limitar tamanho do snapshot
- **WHEN** `snapshot(max_size_mb=1)` é chamado
- **THEN** se o snapshot exceder 1MB, apenas os widgets mais importantes são incluídos
- **AND** widgets visíveis têm prioridade sobre invisíveis

---

> "Um snapshot vale mil palavras de debugging" – made by Sky 📸
