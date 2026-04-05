# Spec: Optimistic Start

Capability para modo otimista de iniciar timer, melhorando perceived performance em 50% via verificação assíncrona.

## ADDED Requirements

### Requirement: Início otimista
O sistema SHALL iniciar timer imediatamente antes de verificar, reduzindo perceived latency.

#### Scenario: Início otimista bem-sucedido
- **WHEN** usuário solicita iniciar com modo optimistic
- **THEN** sistema retorna `{"action": "start_optimistic", "verify_after": true}`
- **AND** `toggl_start_timer` é chamado imediatamente
- **AND** usuário vê confirmação em ~25s (vs 50s verify-first)

#### Scenario: Verificação em background
- **WHEN** `verify_after: true` no response
- **THEN** skill chama `toggl_get_current_entry` após start
- **AND** verificação não bloqueia resposta ao usuário

#### Scenario: Rollback em erro
- **WHEN** verificação background detecta erro
- **THEN** sistema chama `toggl_stop_timer` para rollback
- **AND** notifica usuário sobre falha

### Requirement: Modo verify-first (fallback)
O sistema SHALL suportar modo verify-first para máxima segurança.

#### Scenario: Verify-first padrão
- **WHEN** usuário não especifica modo optimistic
- **THEN** sistema usa verify-first (mais seguro)
- **AND** retorna `{"action": "start"}` sem optimistic flags

#### Scenario: Toggle por flag
- **WHEN** `--optimistic` flag é passada ao orchestrator
- **THEN** sistema ativa modo optimistic-start
- **AND** inclui `verify_after: true` e `rollback_on_error: true`

### Requirement: Test suite de performance
O sistema SHALL incluir testes para medir perceived performance.

#### Scenario: Teste mock (100ms latência)
- **WHEN** `test_performance.py --mode mock` é executado
- **THEN** mede verify-first vs optimistic com latência simulada
- **AND** reporta melhoria percebida (ex: 50%)

#### Scenario: Teste real (MCP)
- **WHEN** `test_performance.py --mode real` é executado
- **THEN** mede latência real das chamadas MCP Toggl
- **AND** reporta tempo perceived vs total

#### Scenario: Teste E2E bash
- **WHEN** `test_performance_e2e.sh` é executado
- **THEN** mede tempo total do orchestrator + estimativa MCP
- **AND** exibe comparação verify-first vs optimistic

### Requirement: Métricas de melhoria
O sistema SHALL documentar melhoria de perceived performance.

#### Scenario: 50% melhoria percebida
- **WHEN** comparando verify-first (50s) vs optimistic (25s)
- **THEN** perceived melhoria = 50%
- **AND** usuário recebe resposta 2x mais rápido

#### Scenario: Latência MCP variável
- **WHEN** latência MCP muda (25s real vs 100ms mock)
- **THEN** melhoria percentual se mantém constante
- **AND** perceived time = start_timer apenas (sem verify)

### Requirement: Integração com orchestrator
O sistema SHALL integrar modo optimistic com comandos existentes.

#### Scenario: Comando start optimistic
- **WHEN** `orchestrator.py start --optimistic` é executado
- **THEN** retorna `action: "start_optimistic"` com params completos
- **AND** inclui `project_id`, `tags`, `description` do contexto

#### Scenario: Comando resume optimistic
- **WHEN** `orchestrator.py resume --optimistic` é executado
- **THEN** verifica se deve retomar via `should_resume()`
- **AND** retorna `action: "start_optimistic"` se conditions met

#### Scenario: Consistency check mantido
- **WHEN** modo optimistic está ativo
- **THEN** `consistency_check()` ainda é executado se `--toggl-running` fornecido
- **AND** auto-restart tem prioridade sobre optimistic

---

## Performance Metrics

| Abordagem | Verify Time | Start Time | Perceived | Total | Melhoria |
|-----------|-------------|------------|-----------|-------|----------|
| Verify-first | 25s | 25s | 50s | 50s | baseline |
| Optimistic | 0s (bg) | 25s | 25s | 50s | **50%** |

> "Perceived performance é perceived value. Usuário não espera 50s em silêncio quando pode começar em 25s" – made by Sky [optimistic]
