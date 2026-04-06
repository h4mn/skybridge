# Tasks: Meta-Evolução do Skylab

## 1. Camada 0 - Meta-Gate (Inviolável)

- [x] 1.1 Criar `programs/skylab/core/meta_gate.py` com classe `MetaGate`
- [x] 1.2 Implementar `check_meta_mode_permission()` com validação de intenção, baseline, Code Health
- [x] 1.3 Implementar `create_meta_mode_session()` com criação de branch isolado
- [x] 1.4 Implementar `close_meta_mode_session()` com commit ou descarte
- [x] 1.5 Adicionar git helpers: `_has_baseline_snapshot()`, `_is_self_hosting_target()`, `_git_create_branch()`, `_git_get_current_commit()`, `_git_commit_all()`

## 2. Camada 0 - Snapshot Engine (Git Wrapper)

- [x] 2.1 Criar `programs/skylab/core/snapshot_engine.py` com classe `GitSnapshotEngine`
- [x] 2.2 Implementar `create_snapshot(message)` usando `git add -A` + `git commit`
- [x] 2.3 Implementar `restore_snapshot(snapshot_hash)` usando `git reset --hard`
- [x] 2.4 Adicionar tratamento de erros para falhas de git

## 3. Camada 1 - Scope Validator com Meta-Mode

- [x] 3.1 Modificar `programs/skylab/core/scope_validator.py`
- [x] 3.2 Adicionar parâmetro `meta_mode: bool = False` em `validate_scope()`
- [x] 3.3 Implementar lógica: quando `meta_mode=True`, permitir `core/` mas bloquear `testing/` e `quality/`
- [x] 3.4 Mantem lógica original quando `meta_mode=False` (apenas `target/`)

## 4. Camada 1 - Evolution Loop Integration

- [x] 4.1 Modificar `programs/skylab/core/evolution.py`
- [x] 4.2 Integrar com `MetaGate` para validar permissão antes de meta-mode
- [x] 4.3 Adicionar parâmetro `meta_mode` em `run_evolution()`
- [x] 4.4 Implementar teste duplo: rodar testes do target + testes do sistema após mudanças em `core/`
- [x] 4.5 Adicionar rollback via `GitSnapshotEngine` se teste duplo falhar

## 5. Camada 2 - Self-Hosting Agent

- [x] 5.1 Criar `programs/skylab/core/self_hosting_agent.py` com classe `SelfHostingAgent`
- [x] 5.2 Implementar `evolve_skylab(spec, iterations)` com fluxo de meta-evolução
- [x] 5.3 Implementar loop: criar sessão → meta-gate → snapshot → agente propõe → teste duplo → keep/discard
- [x] 5.4 Adicionar limite de recursão (N≤3) com verificação explícita

## 6. Testes - Meta-Mode

- [x] 6.1 Criar `tests/core/autokarpa/programs/skylab/test_meta_gate.py`
- [x] 6.2 Testar `check_meta_mode_permission()` rejeita intenção inválida
- [x] 6.3 Testar `check_meta_mode_permission()` exige Code Health mínimo
- [x] 6.4 Testar `check_meta_mode_permission()` exige baseline snapshot
- [x] 6.5 Testar `check_meta_mode_permission()` valida self-hosting target

## 7. Testes - Snapshot Engine

- [x] 7.1 Adicionar testes em `test_snapshot_engine.py`
- [x] 7.2 Testar `create_snapshot()` cria commit com mensagem correta
- [x] 7.3 Testar `restore_snapshot()` restaura estado corretamente
- [x] 7.4 Testar snapshot atômico (falha parcial não deixa estado inconsistente)

## 8. Testes - Scope Validator Meta-Mode

- [x] 8.1 Criar `tests/core/autokarpa/programs/skylab/test_scope_validator_meta_mode.py`
- [x] 8.2 Testar `validate_scope()` bloqueia `core/` quando `meta_mode=False`
- [x] 8.3 Testar `validate_scope()` permite `core/` quando `meta_mode=True`
- [x] 8.4 Testar `validate_scope()` SEMPRE bloqueia `testing/` e `quality/` (mesmo em meta-mode)
- [x] 8.5 Testar `validate_scope()` exige snapshot baseline para meta-mode

## 9. Testes - Teste Duplo

- [x] 9.1 Adicionar testes em `test_evolution_meta_mode.py`
- [x] 9.2 Testar teste duplo passa quando ambos target e sistema funcionam
- [x] 9.3 Testar teste duplo falha quando sistema falha (rollback executado)
- [x] 9.4 Testar teste duplo detecta quebras em `evolution.py`

## 10. Testes - Self-Hosting Session

- [ ] 10.1 Adicionar testes em `test_self_hosting_session.py` (parcial - imports problemáticos)
- [x] 10.2 Testar criação de branch isolado
- [x] 10.3 Testar baseline capture
- [x] 10.4 Testar limite de recursão (N=1, N=2, N=3 permitidos, N=4 bloqueado)
- [x] 10.5 Testar fechamento de sessão com sucesso e falha

## 11. Documentação

- [ ] 11.1 Criar `doc/skylab/META-EVOLUÇÃO.md` com guia completo
- [ ] 11.2 Documentar arquitetura em 3 camadas
- [ ] 11.3 Documentar fluxo de meta-evolução passo a passo
- [ ] 11.4 Documentar critérios de entrada (intenção, baseline, Code Health)
- [ ] 11.5 Documentar mecanismos de segurança (recursão limitada, teste duplo, rollback)
- [ ] 11.6 Adicionar exemplos de uso

## 12. Integração e E2E

- [ ] 12.1 Executar meta-evolução em sandbox (N=1)
- [ ] 12.2 Executar meta-evolução em main (N=2)
- [ ] 12.3 Verificar que Skylab continua funcionando após meta-evolução
- [ ] 12.4 Verificar rollback funciona quando meta-evolução falha
- [ ] 12.5 Documentar resultados e aprendizados

---

**Progresso: 45/56 tasks (80%)**

### Status dos Issues Críticos:

- ✅ CRITICAL #1: Branch creation via git checkout -b
- ✅ CRITICAL #3: Snapshot Engine em arquivo separado
- ✅ CRITICAL #4: Evolution.py integrado com Meta-Gate
- ✅ CRITICAL #5: Teste Duplo implementado
- ⚠️ CRITICAL #6: Self-Hosting Agent (parcial - imports relativos)
- ✅ CRITICAL #7: testing/quality/ bloqueados em meta-mode
- ✅ CRITICAL #8: Limite de recursão N≤3

### Pendências:

1. Corrigir imports relativos em self_hosting_agent.py (CRITICAL #6)
2. Criar documentação (tasks 11.1-11.6)
3. Executar testes E2E (tasks 12.1-12.5)
4. Investigar code_health estagnado/variando (task #2)
5. Verificar description hardcodado no results.tsv (task #1)
6. Investigar métricas zeradas no results.tsv (task #3)
