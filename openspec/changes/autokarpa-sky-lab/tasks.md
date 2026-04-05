# Tasks: Autokarpa Sky Lab

## Progresso: 94/114 tarefas (83%)

**Fases Completas:** 1-5
**Fases Pendentes:** 6 (Demo), 13-17 (parcial), 18-20

---

## 1. Setup Estrutura

- [x] 1.1 Criar diretório `src/core/autokarpa/programs/skylab/`
- [x] 1.2 Criar `src/core/autokarpa/programs/skylab/__init__.py` com entry point `run_skylab()`
- [x] 1.3 Criar subdiretórios: `core/`, `testing/`, `quality/`, `target/`
- [x] 1.4 Criar estrutura `target/` com DDD modular:
  - [x] 1.4.1 `target/__init__.py` (pacote Python)
  - [x] 1.4.2 `target/solution.py` (OBRIGATÓRIO - ponto de entrada/orquestração)
  - [x] 1.4.3 `target/domain.py` (SUGERIDO - entidades, VOs, regras de domínio)
  - [x] 1.4.4 `target/application.py` (SUGERIDO - casos de uso, handlers)
  - [x] 1.4.5 `target/infra.py` (SUGERIDO - implementações concretas)
- [x] 1.5 Adicionar `results/` e `diffs/` ao `.gitignore` (não versionar)
  - [x] 1.5.1 `results/results.tsv` - métricas principais (20 colunas)
  - [x] 1.5.2 `results/components/` - registros JSON de componentes
  - [x] 1.5.3 `results/drift/` - registros JSON de drift detectado
  - [x] 1.5.4 `results/review/` - registros markdown de diff estruturado
  - [x] 1.5.5 `results/state/` - persistência de estado (opcional)
  - [x] 1.5.6 `diffs/` - diffs estruturados (mesmo conteúdo que results/review/)
- [x] 1.6 Configurar integração com snapshot system existente em `src/runtime/observability/snapshot/`

## 2. Core - OpenSpec Integration

- [x] 2.1 Implementar `core/change_loader.py` - carrega proposal, specs, design, tasks da change
- [x] 2.2 Implementar `core/spec_parser.py` - parse requisitos e cenários, gera testes
- [x] 2.3 Implementar validação de change existente vs inexistente
- [⚠️] 2.4 Testar carregamento de change `autokarpa-sky-lab` (self-hosting) - LOOP RODOU MAS COM BUGS

## 3. Core - Test Runner

- [x] 3.1 Implementar `core/test_runner.py` - executa pytest e retorna resultados agregados
- [x] 3.2 Parse output do pytest: passed, failed, total
- [x] 3.3 Implementar retorno no formato: `{"passed": X, "failed": Y, "total": X+Y, "success": bool}`

## 4. Core - Metrics (Code Health)

- [x] 4.1 Implementar `core/metrics.py` - calculate_code_health() com pesos corretos
- [x] 4.2 Implementar cálculo de mutation score (50% weight)
- [x] 4.3 Implementar cálculo de unit score (20% weight)
- [x] 4.4 Implementar cálculo de PBT score (15% weight)
- [x] 4.5 Implementar cálculo de complexity score (15% weight)
- [⚠️] 4.6 Testar fórmula: code health = (mutation×0.5) + (unit×0.2) + (pbt×0.15) + (complexity×0.15) - IMPLEMENTADO, MAS UNIT=0, MUTATION=0 nos testes

## 5. Core - Evolution Loop

- [x] 5.1 Implementar `core/evolution.py` - loop principal de 100 iterações
- [x] 5.2 Implementar fluxo: Spec → TDD → Código → REFACTOR → PBT → Mutation → Medição → Repete
- [x] 5.3 Implementar decisão: keep se melhorou, discard se piorou
- [x] 5.4 Implementar git commit e git reset --hard baseado em code health
- [⚠️] 5.5 Testar loop com iteração única - LOOP RODOU VÁRIAS VEZES COM CRASHES E SCOPE VIOLATIONS
- [x] 5.6 **REFATORAR** `evolution.py` para coordenar registros independentes (components/, drift/, review) ANTES de implementar recorders.py - PRÉ-REQUISITO para task 15.1

## 6. Core - State Management

- [x] 6.1 Implementar `core/state.py` - gerencia `results.tsv`
- [x] 6.2 Implementar registro de 20 colunas organizadas em 6 grupos:
  - [x] 6.2.1 Score principal: `code_health`
  - [x] 6.2.2 Componentes (4): `mutation`, `unit`, `pbt`, `complexity`
  - [x] 6.2.3 Drift (3): `stagnation`, `decline`, `repetition`
  - [x] 6.2.4 Diff (7): `added_files`, `modified_files`, `removed_files`, `moved_files`, `added_dirs`, `removed_dirs`, `size_delta`
  - [x] 6.2.5 Metadata (3): `commit`, `memory_gb`, `status`
  - [x] 6.2.6 Descritores (2): `description`, `diff_path`
- [x] 6.3 Implementar status: "keep", "discard", "crash"
- [x] 6.4 Implementar valores booleanos para drift: `stagnation`, `decline`, `repetition`
- [x] 6.5 Testar escrita e leitura de `results.tsv` expandido - RESULTS.TSV GERADO COM 14 ITERAÇÕES

## 7. Core - Context Manager

- [x] 7.1 Implementar `core/context_manager.py` - previne overflow e drift
- [x] 7.2 Implementar re-injeção de prompt a cada 10 iterações
- [x] 7.3 Implementar compactação quando tokens > 80% da janela
- [x] 7.4 Implementar checkpoint a cada 25 iterações
- [⚠️] 7.5 Testar compactação mantendo: prompt original, melhor código, specs resumidas, últimas 20 iterações - IMPLEMENTADO, BUG: 'history' attribute

## 8. Testing - Property-Based Testing

- [x] 8.1 Implementar `testing/pbt.py` - integração com Hypothesis
- [x] 8.2 Configurar `@settings(max_examples=1000, derandomize=True)`
- [x] 8.3 Implementar estratégias para diferentes tipos de input
- [x] 8.4 Implementar parse de resultados: passed, failed, shrinks
- [⚠️] 8.5 Testar geração de 1000 casos - IMPLEMENTADO, NÃO TESTADO AINDA

## 9. Testing - Mutation Testing

- [x] 9.1 Implementar `testing/mutation.py` - Python puro (não wrapper mutmut)
- [x] 9.2 Definir constantes de orçamento fixo: `MUTATION_BUDGET = 50` e `MUTATION_TIMEOUT = 60` (análogo ao TIME_BUDGET do Karpathy — sem isso o loop fica cada vez mais lento)
- [x] 9.3 Executar mutmut com amostragem aleatória quando total > MUTATION_BUDGET
- [x] 9.4 Implementar cálculo de mutation score: killed / total
- [x] 9.5 Implementar classificação por tipo: Boundary, Arithmetic, Comparison, Logical
- [⚠️] 9.6 Testar com mutation score > 0.80 - MUTATION SCORE = 0 nos testes

## 10. Quality - Complexity Analysis

- [x] 10.1 Implementar `quality/complexity.py` - wrapper para radon
- [x] 10.2 Calcular complexidade ciclomática média
- [x] 10.3 Implementar complexity score: 1 - (avg_complexity / 20)
- [x] 10.4 Implementar threshold de 10 para exigir refactoring
- [⚠️] 10.5 Testar detecção de código acima do threshold - IMPLEMENTADO, COMPLEXITY=1.0 nos testes

## 11. Quality - Refactoring Automation

- [x] 11.1 Implementar `quality/refactor.py` - controle automático de complexidade (dentro de complexity.py)
- [x] 11.2 Implementar verificação OBRIGATÓRIA após Green, antes de PBT/Mutation
- [x] 11.3 Implementar bloqueio de loop se complexidade > 10
- [x] 11.4 Implementar alerta quando complexidade aumenta vs iteração anterior
- [⚠️] 11.5 Testar fluxo completo: TDD → Green → REFACTOR → PBT → Mutation - LOOP RODOU COM BUGS

## 12. Debug - Survivor Analysis

- [x] 12.1 Implementar `testing/debug.py` - análise estruturada de mutants sobreviventes
- [x] 12.2 Implementar padrões de correção por tipo de mutant
- [x] 12.3 Implementar sugestão de teste específico para cada tipo
- [x] 12.4 Implementar priorização por severidade (Boundary/Logical primeiro)
- [⚠️] 12.5 Testar sugestão de teste que mata mutant específico - IMPLEMENTADO, NÃO TESTADO AINDA

## 13. Snapshot + Diff Estruturado

- [x] 13.1 Implementar `core/snapshot_manager.py` - integração com snapshot system
- [x] 13.2 Implementar captura de snapshot antes de cada iteração (`capture_snapshot`)
- [x] 13.3 Implementar captura de snapshot depois de cada iteração
- [x] 13.4 Implementar comparação de snapshots (`compare_snapshots`)
- [x] 13.5 Implementar geração de diff em markdown/html (`render_diff`)
- [x] 13.6 Implementar salvamento de diff como artefato de auditoria
- [x] 13.7 Adicionar coluna `diff_path` ao `results.tsv`
- [x] 13.8 Testar fluxo completo: snapshot_before → agente → snapshot_after → diff → save - DIFS GERADOS EM results/review/

## 14. Validação de Escopo do Target

- [x] 14.1 Implementar validação de escopo via `git diff --name-only`
- [x] 14.2 Verificar que apenas arquivos dentro de `target/` foram modificados
- [x] 14.3 Rejeitar mudanças que violam escopo (modificam `core/`, `testing/`, `quality/`)
- [x] 14.4 Implementar notificação ao agente quando escopo é violado
- [x] 14.5 Implementar reset nuclear: `rm -rf target/` + restore do snapshot anterior
- [⚠️] 14.6 Testar validação com tentativa de modificação de arquivos do sistema - SCOPE VIOLATIONS OCORRENDO (agente modificando arquivos fora de target/)

## 15. Registros Independentes (Detalhamento)

- [x] 15.1 Implementar `core/recorders.py` - gerencia registros independentes
- [x] 15.2 Implementar `components/iteration_NNN.json` (sempre gera)
  - [x] 15.2.1 Detalhes granulares de mutation: mutants por tipo, survivors com sugestões
  - [x] 15.2.2 Detalhes de unit: coverage por arquivo, testes por módulo
  - [x] 15.2.3 Detalhes de PBT: shrinks, max_examples, falhas por estratégia
  - [x] 15.2.4 Detalhes de complexity: avg/max, worst_function, por arquivo
- [x] 15.3 Implementar `drift/iteration_NNN.json` (apenas se drift detectado)
  - [x] 15.3.1 Janela analisada, scores históricos
  - [x] 15.3.2 Ação tomada, razão, contexto completo
- [x] 15.4 Implementar `review/iteration_NNN.md` (sempre gera)
  - [x] 15.4.1 Diff estruturado em markdown (mesmo que `diffs/diff_NNN.md`)
  - [x] 15.4.2 Resumo de métricas, sobreviventes críticos
- [x] 15.5 Implementar consulta de registros: carregar por iteração, listar por tipo
- [x] 15.6 Criar diretórios `results/components/`, `results/drift/`, `results/review/`
- [x] 15.7 Testar geração completa de registros para uma iteração - REGISTROS GERADOS EM results/review/iteration_000.md

## 16. Git Integration - Branch Naming

- [⚠️] 16.1 Implementar criação de branch `autoresearch/<data><mes>-0` no início (ex: `autoresearch/abr05-0`) - NÃO IMPLEMENTADO (loop roda em branch atual)
- [⚠️] 16.2 **IMPORTANTE**: usar hífen, não colchetes — `[N]` causa glob expansion no bash e quebra em vários contextos - NÃO APLICÁVEL (16.1 não implementado)
- [⚠️] 16.3 Implementar renomeação de branch quando melhoria é encontrada: `-0` → `-42` - NÃO IMPLEMENTADO
- [x] 16.4 Implementar timing correto do `results.tsv`: gravar ANTES do `git reset` (hash do commit persiste mesmo após reset)
- [⚠️] 16.5 Testar padrão Karpathy completo: commit → métricas → tsv (20 colunas) → keep/discard - COMMIT HASH REGISTRADO NO TSV

## 17. Ralph Loop Integration (Opcional)

- [x] 17.1 Implementar persistência de estado para multi-sessão (session.py)
- [x] 17.2 Implementar checkpoint a cada iteração
- [x] 17.3 Implementar retomada de sessão após crash/pausa
- [⚠️] 17.4 Testar fluxo Ralph + Skylab (opcional) - IMPLEMENTADO, NÃO INTEGRADO AINDA

## 18. Demo - Todo List

- [ ] 18.1 Criar spec para Todo List em `openspec/changes/demo-todo-list/`
- [ ] 18.2 Implementar target/ com estrutura DDD modular
- [ ] 18.3 Gerar testes automaticamente da spec
- [ ] 18.4 Executar loop de evolução até code health aceitável
- [ ] 18.5 Validar mutation score > 0.80
- [ ] 18.6 Validar PBT com 1000 casos passando
- [ ] 18.7 Documentar `results.tsv` gerado com 20 colunas
- [ ] 18.8 Verificar isolamento: o agente deve ter modificado APENAS arquivos dentro de `target/` (nunca `core/`, `testing/`, `quality/`)
- [ ] 18.9 Validar que snapshots e diffs foram gerados corretamente para cada iteração
- [ ] 18.10 Validar que registros independentes em `results/` (components/, drift/, review/) foram gerados

## 19. Documentação

- [x] 19.1 Criar README.md em `src/core/autokarpa/programs/skylab/`
- [x] 19.2 Documentar uso: `run_skylab("change-name", iterations=100)`
- [x] 19.3 Documentar modo standalone vs Ralph vs Autogrind
- [x] 19.4 Documentar estrutura DDD modular de `target/` (SUGERIDA, EVOLUTIVA)
- [x] 19.5 Documentar results.tsv com 20 colunas organizadas em 6 grupos
- [x] 19.6 Documentar registros independentes em `results/`: components/, drift/, review/

## 20. Testes Finais

- [ ] 20.1 Executar demo todo-list até completion
- [ ] 20.2 Validar code health final > 0.80
- [ ] 20.3 Validar todas as specs cobertas (incluindo novos requisitos de snapshot/diff/registros)
- [ ] 20.4 Validar dependências instaladas (hypothesis, mutmut, radon)
- [ ] 20.5 Validar integração com snapshot system
- [ ] 20.6 Validar registros independentes em `results/` gerados corretamente
- [ ] 20.7 Self-host: executar skylab na change `autokarpa-sky-lab`

> "Spec → Teste → Código → REFACTOR → PBT → Mutation → Snapshot → Diff → Medição → Repita" – Sky 🔬
