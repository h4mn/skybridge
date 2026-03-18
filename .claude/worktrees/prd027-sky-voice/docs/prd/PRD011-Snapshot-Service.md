---
status: rascunho
data: 2025-12-28
---

# PRD011 - Snapshot Service como Serviço de Observabilidade da Plataforma

## 1. Objetivo

Implementar o **Snapshot Service** como serviço transversal de observabilidade estrutural da plataforma Skybridge, sob `platform/observability/snapshot`, conforme definido no **ADR015**, especificado no **SPEC007** e com armazenamento em **workspace** conforme **ADR017**.

## 2. Problema

O conceito de snapshot/diff estava originalmente limitado ao domínio de fileops/Skybridge (ADR011). Com a evolução da arquitetura e da Sky-RPC, tornou-se necessário elevar esta capacidade a um **serviço da plataforma**, aplicável a múltiplos domínios observáveis (arquivos, tarefas, saúde do sistema, etc.) sem acoplamento direto entre eles.

## 3. Escopo

### Dentro do escopo

- Implementação do core do Snapshot Service em `platform/observability/snapshot/`
- Registro de extratores de estado por domínio (fileops, tasks, health)
- Contrato RPC via Sky-RPC v0.3 (`snapshot.capture`, `snapshot.compare`)
- Sistema de armazenamento e retenção de snapshots
- Modelos de dados Pydantic (Snapshot, Diff)
- Interface base `StateExtractor` para extensibilidade
- Documentação e exemplos de uso

### Fora do escopo

- Implementação de extratores específicos (exceto fileops como referência)
- Interface UI/CLI para snapshots (planejado para fase posterior)
- Sistema de alertas baseado em diffs
- Integração com ferramentas externas

## 4. Usuários / Stakeholders

- **Desenvolvedores Skybridge** — Acesso via RPC para observação de domínios
- **Agentes IA** — Uso automatizado para discovery e comparações estruturais
- **Arquitetura** — Garantia de aderência ao ADR015 e SPEC007
- **DevOps/SRE** — Monitoramento de saúde e evolução da infraestrutura

## 5. Requisitos

### Funcionais

- [ ] **Base legado Pyro** — O código existente em `B:\_repositorios\pyro\src\snapshot` deve ser analisado e servir como padrão e/ou ser portado para esta implementação.

- [ ] **Configuração de workspace** (conforme ADR017)
  - Auto-criação de diretórios `workspace/skybridge/snapshots/` e `workspace/skybridge/diffs/`
  - Suporte a variável de ambiente `SKYBRIDGE_WORKSPACE` para override
  - Validação de permissões de escrita ao inicializar

- [ ] **Captura de snapshot** (`snapshot.capture`)
  - Suporte a múltiplos domínios: fileops, tasks, health
  - Configuração de profundidade, filtros de inclusão/exclusão
  - Geração de ID único com timestamp
  - Coleta de metadados (git hash, branch, tags)

- [ ] **Comparação de snapshots** (`snapshot.compare`)
  - Identificação de mudanças: added, removed, modified, moved
  - Suporte a múltiplos formatos de saída: JSON, Markdown, HTML
  - Geração de resumo estatístico (contagens, delta de tamanho)

- [ ] **Registro de extratores** (`ExtractorRegistry`)
  - Interface base `StateExtractor` com métodos `capture()` e `compare()`
  - Registro dinâmico de extratores por domínio
  - Validação de domínios suportados

- [ ] **Armazenamento e retenção** (conforme ADR017)
  - Diretório base: `workspace/skybridge/snapshots/[subject]/`
  - Diretório de diffs: `workspace/skybridge/diffs/[subject]/`
  - Função `ensure_workspace()` para auto-criação de estrutura
  - Persistência de snapshots em formato JSON
  - Política de retenção configurável (padrão: 30-365 dias)
  - Organização por domínio e data
  - Suporte a snapshots marcados (tagged) para retenção estendida
  - Variável de ambiente `SKYBRIDGE_WORKSPACE` para override de caminho

- [ ] **Contrato RPC Sky-RPC v0.3**
  - Handler `snapshot.capture` com envelope estruturado
  - Handler `snapshot.compare` com envelope estruturado
  - Respostas com ticket_id e resultado padronizado

- [ ] **Modelos de dados Pydantic**
  - `SnapshotSubject` (enum: fileops, tasks, health, custom)
  - `SnapshotMetadata` com ID, timestamp, subject, target
  - `SnapshotStats` com contagens e agregações
  - `DiffChange` (enum: added, removed, modified, moved)
  - `DiffSummary` e `DiffItem` para representação de mudanças

### Não funcionais

- [ ] **Imutabilidade** — Snapshots nunca são alterados após criação
- [ ] **Comparabilidade** — Snapshots podem ser comparados entre si
- [ ] **Reprodutibilidade** — Parâmetros iguais = snapshot idêntico
- [ ] **Leveza** — Captura estrutural, sem conteúdo dos arquivos
- [ ] **Desacoplamento** — Nenhum domínio depende diretamente de outro
- [ ] **Performance** — Captura de snapshots deve completar em tempo razoável (< 30s para projetos médios)
- [ ] **Testabilidade** — Cobertura de testes unitários para core e extratores

## 6. Critérios de sucesso

- [ ] Snapshot Service operacional via RPC com handlers registrados
- [ ] Pelo menos 2 extratores implementados (fileops e tasks/health)
- [ ] Snapshots persistidos e recuperáveis por ID
- [ ] Diffs gerados corretamente entre snapshots de mesmo domínio
- [ ] Documentação de API e exemplos de uso disponíveis
- [ ] Cobertura de testes >= 80% para core do serviço

## 7. Dependências e restrições

### Dependências

- **ADR015** — Adoção de Snapshot como Serviço da Plataforma (aprovado)
- **ADR017** — Estrutura de Workspace para Dados Gerados
- **SPEC007** — Snapshot Service (especificação técnica)
- **ADR010** — Adoção do Sky-RPC
- **SPEC004** — Sky-RPC v0.3 (contrato de envelope)
- **PRD009** — Sky-RPC v0.3 RPC-first Semântico

### Restrições

- Deve aderir ao padrão Sky-RPC v0.3 para envelope e ticket
- Deve seguir estrutura de diretórios definida no SPEC007
- Armazenamento deve utilizar `workspace/skybridge/snapshots/` conforme ADR017
- `workspace/` deve ser adicionado ao `.gitignore`
- Não pode introduzir dependências síncronas entre domínios
- Política de retenção deve respeitar limites de armazenamento

## 8. Entregáveis

### Código

- `platform/observability/snapshot/__init__.py` — Inicialização e registro RPC
- `platform/observability/snapshot/capture.py` — Lógica de captura
- `platform/observability/snapshot/diff.py` — Lógica de comparação
- `platform/observability/snapshot/registry.py` — Registro de extratores
- `platform/observability/snapshot/storage.py` — Persistência em workspace
- `platform/observability/snapshot/workspace.py` — Configuração e `ensure_workspace()`
- `platform/observability/snapshot/models.py` — Modelos Pydantic
- `platform/observability/snapshot/extractors/` — Extratores de domínio
  - `base.py` — Interface `StateExtractor`
  - `fileops_extractor.py` — Implementação de referência

### Configuração

- `.gitignore` atualizado com `workspace/`
- `workspace/.gitkeep` para preservar estrutura no git
- `workspace/README.md` documentando a estrutura

### Testes

- `tests/platform/observability/snapshot/test_capture.py`
- `tests/platform/observability/snapshot/test_diff.py`
- `tests/platform/observability/snapshot/test_registry.py`
- `tests/platform/observability/snapshot/test_extractors.py`

### Documentação

- README do serviço com exemplos de uso
- Especificação de contratos RPC
- Guia de implementação de extratores customizados

## 9. Próximos passos

### Setup de Workspace (ADR017)

1. [ ] Adicionar `workspace/` ao `.gitignore` (com exceção de `.gitkeep`)
2. [ ] Criar `workspace/.gitkeep` para preservar estrutura
3. [ ] Criar `workspace/README.md` com documentação da estrutura
4. [ ] Implementar `workspace.py` com função `ensure_workspace()`
5. [ ] Adicionar suporte a `SKYBRIDGE_WORKSPACE` env var

### Implementação Core

6. [ ] Criar estrutura de diretórios em `platform/observability/snapshot/`
7. [ ] Implementar modelos Pydantic (Snapshot, Diff)
8. [ ] Implementar interface `StateExtractor` e `ExtractorRegistry`
9. [ ] Implementar core de captura e comparação
10. [ ] Implementar extrator de referência (FileOpsExtractor)
11. [ ] Implementar camada de persistência usando `workspace/skybridge/snapshots/`
12. [ ] Registrar handlers RPC (`snapshot.capture`, `snapshot.compare`)

### Testes e Documentação

13. [ ] Escrever testes unitários
14. [ ] Documentar API e exemplos de uso
15. [ ] Atualizar ADR015 marcando implementação como concluída
16. [ ] Atualizar ADR017 marcando integração como concluída

---

> "A observabilidade estrutural é o alicerce da evolução consciente de qualquer sistema."
> — made by Sky 👁️✨
