# Spec: TDD Core

**Contexto:** Esta spec define o comportamento do **Skylab** - composto por:
- **Sistema** (framework fixo): `core/`, `testing/`, `quality/` - coordena e valida
- **Agente** (autônomo): modifica apenas `target/` - implementa código

## ADDED Requirements

### Requirement: Load OpenSpec change
O **Skylab** DEVE carregar os artefatos de uma change OpenSpec pelo nome.

#### Scenario: Change existe
- **WHEN** usuário chama `run_skylab("autokarpa-sky-lab")`
- **THEN** Skylab lê `proposal.md` da change
- **AND** Skylab lê todos os specs em `specs/**/*.md`
- **AND** Skylab lê `design.md` da change
- **AND** Skylab lê `tasks.md` da change

#### Scenario: Change não encontrada
- **WHEN** usuário chama `run_skylab("nonexistent")`
- **THEN** Skylab levanta `FileNotFoundError`
- **AND** mensagem inclui o caminho buscado

### Requirement: Parse specs e gerar testes
O **Sistema** DEVE gerar código de testes automaticamente a partir dos requisitos das specs.

### Requirement: Separação de responsabilidades
O **Skylab** DEVE manter separação clara entre Sistema (fixo) e Agente (variável).

#### Scenario: Arquivos fixos do Sistema
- **WHEN** definindo Skylab
- **THEN** `core/`, `testing/`, `quality/` são FIXOS (Sistema coordena e valida)
- **AND** `program.md` contém instruções para o Agente
- **AND** `prepare.py` NÃO existe (a change OpenSpec é o prepare)

#### Scenario: Arquivos variáveis do Agente
- **WHEN** Agente atua
- **THEN** `target/` contém código que Agente modifica
- **AND** `target/` é uma pasta com estrutura DDD modular (SUGERIDA, não obrigatória)
- **AND** `target/solution.py` é o ponto de entrada/orquestração
- **AND** `target/` pode conter: `domain.py`, `application.py`, `infra.py` (DDD modular)
- **AND** Agente NÃO pode modificar `core/`, `testing/`, `quality/`

#### Scenario: Comunicação Sistema → Agente
- **WHEN** Sistema solicita ação ao Agente
- **THEN** Sistema fornece contexto: testes falhando, code health atual
- **AND** Agente propõe mudança com justificativa
- **AND** Sistema valida antes de aceitar

#### Scenario: Gera testes a partir de requisitos
- **WHEN** specs contêm requisitos com "### Requirement:"
- **THEN** Skylab gera função `test_<requirement_name>()` para cada requisito
- **AND** função contém docstring com descrição do requisito
- **AND** função inicialmente levanta `NotImplementedError` (RED)

#### Scenario: Gera asserts a partir de cenários
- **WHEN** requisito contém cenários com WHEN/THEN
- **THEN** Skylab gera asserts baseados no THEN
- **AND** Skylab setup o estado descrito no WHEN

### Requirement: Executar testes unitários
Skylab DEVE executar testes unitários com pytest e retornar resultados agregados.

#### Scenario: Todos os testes passam
- **WHEN** pytest executa com todos os testes passando
- **THEN** retorna `{"passed": N, "failed": 0, "total": N, "success": true}`

#### Scenario: Alguns testes falham
- **WHEN** pytest executa com testes falhando
- **THEN** retorna `{"passed": X, "failed": Y, "total": X+Y, "success": false}`
- **AND** falhas são capturadas no resultado

### Requirement: Calcular Code Health Score
Skylab DEVE calcular métrica composta de saúde do código que previne overfitting.

#### Scenario: Calcula com todos os componentes
- **WHEN** mutation score = 0.85, unit score = 1.0, PBT score = 1.0, complexity score = 0.9
- **THEN** code health = (0.85 × 0.5) + (1.0 × 0.2) + (1.0 × 0.15) + (0.9 × 0.15) = 0.91

#### Scenario: Mutation score domina
- **WHEN** mutation score = 0.0 (testes ruins)
- **THEN** code health máximo = 0.5 (mesmo com unit/PBT perfeitos)
- **AND** Skylab penaliza fortemente testes que não matam mutants

### Requirement: Mutation Testing Windows-Friendly
O **Sistema** DEVE implementar mutation testing que funciona nativamente em Windows sem dependências externas (mutmut, WSL2, Docker).

#### Scenario: Implementação em Python puro
- **WHEN** mutation testing é executado
- **THEN** Sistema usa implementação em Python puro (sem mutmut)
- **AND** Suporta tipos: Arithmetic, Comparison, Logical, Boundary
- **AND** Funciona em Windows, Linux, Mac sem configuração adicional

#### Scenario: Orçamento fixo de mutants
- **WHEN** total de mutants > 50 (MUTATION_BUDGET)
- **THEN** Sistema amostra aleatoriamente 50 mutants
- **AND** Previne degeneração de performance ao longo do loop
- **AND** Timeout de 60 segundos por execution (MUTATION_TIMEOUT)

#### Scenario: Cálculo de mutation score
- **WHEN** mutation testing completa
- **THEN** mutation score = mutants_killed / mutants_total
- **AND** Classificação por tipo é registrada em results/components/*.json

### Requirement: Loop de evolução
O **Sistema** DEVE coordenar o loop de evolução: Spec → TDD → Agente → Refactor → PBT → Mutation → Medição → Repete.

#### Scenario: Uma iteração do loop
- **WHEN** iteração inicia
- **THEN** Sistema gera testes das specs (RED)
- **AND** Sistema solicita ao Agente: "implemente mínimo para passar"
- **AND** Agente modifica `target/train.py`
- **AND** Sistema roda pytest (GREEN)
- **AND** Sistema exige refactoring se complexidade > 10
- **AND** Sistema roda PBT e Mutation
- **AND** Sistema calcula code health
- **AND** Sistema decide: keep (git commit) ou discard (git reset)

#### Scenario: Iteração única melhora
- **WHEN** code health before = 0.5, after = 0.6
- **THEN** Sistema executa `git commit` (mantém mudança)
- **AND** Sistema registra melhoria em `results.tsv` com status "keep"

#### Scenario: Iteração única piora
- **WHEN** code health before = 0.6, after = 0.5
- **THEN** Skylab executa `git reset --hard HEAD~1` (descarta)
- **AND** retorna ao estado anterior
- **AND** registra em `results.tsv` com status "discard"

#### Scenario: Crash durante execução
- **WHEN** execução resulta em crash (OOM, exception)
- **THEN** Skylab executa `git reset --hard HEAD~1`
- **AND** registra em `results.tsv` com status "crash"
- **AND** continuação do loop é possível

### Requirement: Gerenciar contexto e drift
Skylab DEVE prevenir context overflow e drift durante loops longos.

#### Scenario: Re-injeta prompt periodicamente
- **WHEN** iteração atinge múltiplo de 10
- **THEN** Skylab re-injeta prompt original
- **AND** mantém foco no objetivo

#### Scenario: Compacta contexto quando necessário
- **WHEN** tokens atuais > 80% da janela máxima
- **THEN** Skylab compacta mantendo: prompt original, melhor código, specs resumidas, últimas 20 iterações
- **AND** descarta iterações antigas

#### Scenario: Checkpoint a cada 25 iterações
- **WHEN** iteração é múltiplo de 25
- **THEN** Skylab salva checkpoint em `results.tsv`
- **AND** reseta contexto de iterações

### Requirement: Registrar resultados em TSV
Skylab DEVE registrar cada iteração em arquivo `results.tsv` formato tab-separated.

#### Scenario: Registro bem-sucedido
- **WHEN** iteração completa com sucesso
- **THEN** Skylab adiciona linha em `results.tsv` com 20 colunas organizadas em 6 grupos:
  - Score principal: `code_health`
  - Componentes (4): `mutation`, `unit`, `pbt`, `complexity`
  - Drift (3): `stagnation`, `decline`, `repetition`
  - Diff (7): `added_files`, `modified_files`, `removed_files`, `moved_files`, `added_dirs`, `removed_dirs`, `size_delta`
  - Metadata (3): `commit`, `memory_gb`, `status`
  - Descritores (2): `description`, `diff_path`

#### Scenario: Arquivo não versionado
- **WHEN** `results.tsv` é criado
- **THEN** arquivo NÃO deve ser versionado (adicionar ao `.gitignore`)

### Requirement: Integração com Ralph Loop
Skylab DEVE suportar coordenação opcional via Ralph Loop para multi-sessão.

#### Scenario: Modo standalone (padrão)
- **WHEN** usuário chama `run_skylab("change", iterations=100)`
- **THEN** Skylab executa com loop próprio
- **AND** não depende de Ralph Loop

#### Scenario: Modo Ralph (opcional)
- **WHEN** usuário chama via Ralph com `persist_state=True`
- **THEN** Skylab salva estado a cada iteração
- **AND** permite retomar após crash/pausa

### Requirement: Entry point por nome da change
Skylab DEVE aceitar apenas o nome da change OpenSpec como entrada.

#### Scenario: Input é nome da change
- **WHEN** usuário chama `run_skylab("autokarpa-sky-lab")`
- **THEN** Skylab carrega artefatos de `openspec/changes/autokarpa-sky-lab/`
- **AND** não usa `prepare.py` estático

### Requirement: Branch naming padrão Karpathy
Skylab DEVE seguir padrão de branch naming do Autoresearch.

#### Scenario: Cria branch inicial
- **WHEN** loop de evolução inicia
- **THEN** Skylab cria branch `autoresearch/<data>[0]` (ex: `autoresearch/abr05[0]`)

#### Scenario: Renomeia branch quando melhora
- **WHEN** iteração 42 produz melhor code health
- **THEN** Skylab renomeia branch para `autoresearch/abr05[42]`

### Requirement: Estrutura DDD modular do target
O **target/** DEVE seguir estrutura DDD modular (SUGERIDA, evolutiva).

#### Scenario: Estrutura inicial sugerida
- **WHEN** `target/` é criado
- **THEN** DEVE conter `solution.py` (ponto de entrada/orquestração)
- **AND** PODE conter `domain.py` (entidades, VOs, regras de domínio)
- **AND** PODE conter `application.py` (casos de uso, handlers)
- **AND** PODE conter `infra.py` (implementações concretas)

#### Scenario: Arquitetura evolutiva
- **WHEN** experimentos revelam que estrutura DDD não é ótima
- **THEN** Skylab DEVE registrar aprendizado em `meta-results.md`
- **AND** ajustes na arquitetura SÃO FATORES DE MEDIÇÃO para melhoria
- **AND** arquitetura está ABERTA a mudanças baseadas em evidência

### Requirement: Snapshot antes/depois de cada iteração
O **Sistema** DEVE capturar snapshots estruturais de `target/` antes e depois de cada iteração.

#### Scenario: Captura snapshot antes da iteração
- **WHEN** iteração do loop inicia
- **THEN** Sistema captura snapshot de `target/` via `capture_snapshot("skylab", target="target/")`
- **AND** snapshot armazena estrutura, arquivos, métricas

#### Scenario: Captura snapshot depois da iteração
- **WHEN** Agente finaliza mudanças em `target/`
- **THEN** Sistema captura novo snapshot de `target/`
- **AND** Sistema compara snapshots via `compare_snapshots(before, after)`

### Requirement: Diff estruturado como mecanismo de review
O **Sistema** DEVE gerar diff estruturado navegável para review de cada iteração.

#### Scenario: Gera diff estruturado
- **WHEN** snapshots são comparados
- **THEN** Sistema gera diff com: arquivos adicionados, modificados, removidos
- **AND** diff contém summary com contagens e delta de tamanho
- **AND** diff é renderizado em markdown/html para review humano

#### Scenario: Diff substitui git diff verboso
- **WHEN** review de iteração é necessário
- **THEN** diff estruturado mostra "o que mudou de verdade" em alto nível
- **AND** não depende de `git diff` verboso de pasta multi-arquivo
- **AND** diff pode ser salvo como artefato de auditoria

### Requirement: Validação de escopo do target
O **Sistema** DEVE validar que apenas arquivos dentro de `target/` foram modificados.

#### Scenario: Validação de escopo
- **WHEN** Agente propõe mudança
- **THEN** Sistema verifica com `git diff --name-only HEAD~1 | grep -v "^target/"`
- **AND** se algum arquivo fora de `target/` foi modificado, mudança é rejeitada
- **AND** Agente é notificado para refazer proposta respeitando escopo

#### Scenario: Reset de iteração
- **WHEN** iteração precisa ser descartada
- **THEN** Sistema pode fazer `rm -rf target/` e restore do snapshot anterior
- **AND** garante estado limpo para próxima iteração

### Requirement: Registro expandido em results.tsv
O **Sistema** DEVE registrar 20 métricas organizadas em 6 grupos no `results.tsv`.

#### Scenario: Colunas organizadas por grupo
- **WHEN** registrando iteração em `results.tsv`
- **THEN** DEVE conter 6 grupos de colunas:
  - **Score principal** (1): `code_health`
  - **Componentes** (4): `mutation`, `unit`, `pbt`, `complexity`
  - **Drift** (3): `stagnation`, `decline`, `repetition`
  - **Diff** (7): `added_files`, `modified_files`, `removed_files`, `moved_files`, `added_dirs`, `removed_dirs`, `size_delta`
  - **Metadata** (3): `commit`, `memory_gb`, `status`
  - **Descritores** (2): `description`, `diff_path`

#### Scenario: Valores de drift indicam estado do loop
- **WHEN** calculando indicadores de drift
- **THEN** `stagnation` = `true` se variância < 0.01 nas últimas N iterações
- **AND** `decline` = `true` se segunda metade da janela 10% pior que a primeira
- **AND** `repetition` = `true` se similaridade > 0.9 nos últimos snippets

### Requirement: Registros independentes para detalhamento
O **Sistema** DEVE gerar registros independentes quando `results.tsv` não é suficiente para análise.

#### Scenario: Registro de componentes detalhado
- **WHEN** iteração completa
- **THEN** Sistema DEVE gerar `results/components/iteration_NNN.json`
- **AND** arquivo DEVE conter detalhes granulares: mutants por tipo, cobertura por arquivo, survivors com sugestões
- **AND** formato DEVE ser JSON para análise programática

#### Scenario: Registro de drift apenas quando detectado
- **WHEN** drift é detectado (stagnation, decline, ou repetition)
- **THEN** Sistema DEVE gerar `results/drift/iteration_NNN.json`
- **AND** arquivo DEVE conter: janela analisada, scores históricos, ação tomada, razão
- **AND** arquivo NÃO é gerado se nenhum drift foi detectado

#### Scenario: Registro de review com diff estruturado
- **WHEN** iteração completa
- **THEN** Sistema DEVE gerar `results/review/iteration_NNN.md`
- **AND** arquivo DEVE conter diff estruturado navegável
- **AND** formato DEVE ser markdown para leitura humana

#### Scenario: Consulta de registros independentes
- **WHEN** análise profunda é necessária
- **THEN** Sistema DEVE permitir carregar detalhes de iteração específica
- **AND** Sistema DEVE permitir listar iterações com drift detectado
- **AND** Sistema DEVE permitir filtrar registros por tipo (components, drift, review)

> "Spec → Teste → Código → REFACTOR → PBT → Mutation → Snapshot → Diff → Medição → Repita" – Sky 🔬
