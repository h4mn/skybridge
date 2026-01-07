---
status: rascunho
data: 2026-01-06
---

# PRD012 - Estratégia de Versionamento (Semver + Conventional Commits)

## 1. Objetivo

Implementar a estratégia de versionamento definida na **ADR012**, utilizando **Semver** + **Conventional Commits** + **GitHub Workflows** para automatizar o versionamento e geração de documentação, estabelecendo um **single source of truth** para todas as versões do projeto Skybridge.

## 2. Problema

O projeto Skybridge possui múltiplas fontes de versionamento que evoluem de forma independente, resultando em:

- Versões duplicadas em múltiplos arquivos (`__init__.py`, OpenAPI YAML, specs)
- Desalinhamento automático entre componentes
- Changelogs manuais propensos a erros
- Falha de comunicação sobre breaking changes
- Dificuldade de rastrear mudanças que afetam múltiplos componentes

## 3. Escopo

### Dentro do escopo

- Fase de **descoberta e inventário** das versões atuais no codebase
- Criação do arquivo **VERSION** como single source of truth
- Implementação de **GitHub Workflows** para versionamento automatizado
- Configuração de **commitlint** para enforce de Conventional Commits
- Atualização de todos os pontos que leem versão para usar o arquivo VERSION
- Geração automática de **CHANGELOG.md**
- Sistema de **documentação versionada**

### Fora do escopo

- Migração de histórico de commits antigos para Conventional Commits
- Interface UI para gerenciamento de versões
- Sistema de releases com múltiplas linhas de suporte (LTS)

## 4. Usuários / Stakeholders

- **Desenvolvedores Skybridge** — Commitam com Conventional Commits e usam versões unificadas
- **Arquitetura** — Garantia de aderência ao ADR012
- **DevOps/SRE** — Gerenciam releases e documentação versionada
- **Consumidores da API** — Rastreiam mudanças e breaking changes via changelog

## 5. Requisitos

### Funcionais

#### Fase 1: Descoberta e Inventário

- [ ] **Inventário de versões atuais**
  - Mapear todos os arquivos que contêm versões hardcoded
  - Documentar cada versão encontrada com localização exata
  - Identificar discrepâncias entre as versões
  - Gerar relatório de estado atual (baseline)

- [ ] **Arquivos a inventariar** (lista preliminar):
  - `src/skybridge/__init__.py` — versão da aplicação
  - `src/skybridge/kernel/__init__.py` — versão do Kernel SDK
  - `openapi/v1/skybridge.yaml` — versão do contrato OpenAPI
  - `pyproject.toml` — versão do pacote Python
  - Quaisquer outros arquivos com versionamento

- [ ] **Relatório de inventário** (entregável)
  - Tabela com: Componente | Localização | Versão Atual | Formato
  - Lista de discrepâncias encontradas
  - Recomendação de versão inicial para cada componente

#### Fase 2: Single Source of Truth

- [ ] **Criar arquivo VERSION na raiz**
  - Formato multi-linha com key=value
  - Contém versões de todos os componentes
  - Servir como única fonte de verdade

- [ ] **Formato do arquivo VERSION:**
  ```
  SKYBRIDGE_VERSION=<versão_inicial>
  KERNEL_API_VERSION=<versão_inicial>
  OPENAPI_CONTRACT_VERSION=<versão_inicial>
  ```

- [ ] **Script de leitura de versão**
  - `scripts/version.py` ou similar
  - Função `get_version(component_name)`
  - Usado por todos os pontos que necessitam de versão

- [ ] **Atualizar pontos de consumo de versão**
  - `src/skybridge/__init__.py` — lê do VERSION
  - `openapi/v1/skybridge.yaml` — injetado via script
  - Qualquer outro arquivo identificado na fase 1

#### Fase 3: Conventional Commits

- [ ] **Configurar commitlint**
  - Instalar `@commitlint/cli` e `@commitlint/config-conventional`
  - Criar `.commitlintrc.yml` com configuração customizada
  - Definir tipos: feat, fix, docs, chore, test, refactor, BREAKING CHANGE
  - Definir escopos: app, kernel, openapi, auth, fileops, tasks

- [ ] **Husky (git hooks)**
  - Instalar e configurar husky
  - Hook `commit-msg` para validar commits
  - Integrar com commitlint

- [ ] **Configuração de escopos no commitlint:**
  ```yaml
  rules:
    scope-enum:
      - 2
      - always
      - app
      - kernel
      - openapi
      - auth
      - fileops
      - tasks
  ```

#### Fase 4: GitHub Workflows

- [ ] **Workflow de Release** (`.github/workflows/release.yml`)
  - Trigger: push para branch `main`
  - Parse commits com conventional-commits-parser
  - Determinar tipo de bump (MAJOR/MINOR/PATCH) por escopo
  - Atualizar arquivo VERSION
  - Gerar CHANGELOG.md do histórico de commits
  - Criar tag git no formato `v{version}`
  - Criar GitHub Release com changelog
  - Push da tag de volta para o repo

- [ ] **Workflow de Docs** (`.github/workflows/docs.yml`)
  - Trigger: push para branch `main` quando `docs/**` ou `VERSION` mudam
  - Injetar versão do VERSION no OpenAPI YAML
  - Atualizar referências de versão nos specs
  - Gerar documentação versionada
  - Deploy para GitHub Pages ou similar

- [ ] **Configuração de permissões**
  - GitHub token com permissão para criar releases
  - Permissão para escrever na branch (para atualizar VERSION e CHANGELOG)

#### Fase 5: Geração de Documentação

- [ ] **CHANGELOG.md automático**
  - Gerado pelo workflow de release
  - Formatado por tipo de mudança (Adicionado, Alterado, Corrigido, Removido)
  - Incluir links para commits e issues
  - Indexado por versão

- [ ] **Documentação versionada**
  - Specs indexados por versão: `/docs/v{version}/spec/...`
  - OpenAPI disponível por versão
  - Navegação entre versões

### Não funcionais

- [ ] **Backward compatibility** — Implementação não deve breaking changear nada
- [ ] **Performance** — Workflows devem completar em tempo razoável (< 5 min)
- [ ] **Idempotência** — Executar workflow múltiplas vezes não deve causar problemas
- [ ] **Validação** — Commits inválidos devem ser rejeitados no pre-commit
- [ ] **Rastreabilidade** — Cada versão deve ser rastreável ao commit que a gerou
- [ ] **Segurança** — Workflows devem usar permissões mínimas necessárias

## 6. Critérios de sucesso

### Fase de Descoberta
- [ ] Inventário completo de todas as versões no codebase
- [ ] Relatório com discrepâncias documentadas
- [ ] Recomendação de versões iniciais definidas

### Fase de Implementação
- [ ] Arquivo VERSION criado com versões iniciais
- [ ] commitlint configurado e funcional
- [ ] Workflows de release e docs criados e testados
- [ ] Todos os pontos de consumo atualizados para ler VERSION
- [ ] Primeiro release automatizado executado com sucesso
- [ ] CHANGELOG.md gerado automaticamente
- [ ] Documentação versionada acessível

### Qualidade
- [ ] Cobertura de testes para scripts de versionamento
- [ ] Documentação de uso atualizada
- [ ] Commits da própria implementação seguem Conventional Commits

## 7. Dependências e restrições

### Dependências

- **ADR012** — Estratégia de Versionamento (proposto)
- **ADR011** — Snapshot/Diff para Visão do Estado Atual (emendado)

### Restrições

- Versões iniciais devem respeitar o que já está no codebase (não iniciar de 0.0.0 arbitrariamente)
- Não deve breaking changear o sistema durante a implementação
- Workflows devem ser idempotentes
- Commits devem seguir Conventional Commits desde o início da implementação

## 8. Entregáveis

### Fase de Descoberta

- `docs/inventory/PRD012-version-inventory.md` — Relatório de inventário
  - Lista completa de arquivos com versão
  - Tabela de discrepâncias
  - Recomendação de versões iniciais

### Código

- `VERSION` — Single source of truth
- `scripts/version.py` — Script de leitura de versão
- `.commitlintrc.yml` — Configuração do commitlint
- `.github/workflows/release.yml` — Workflow de release
- `.github/workflows/docs.yml` — Workflow de documentação
- `CHANGELOG.md` — Changelog gerado (atualizado automaticamente)

### Configuração

- `package.json` — Com dependências de commitlint e husky
- `.husky/commit-msg` — Git hook para validar commits

### Testes

- `tests/version/test_version_script.py` — Testes do script de versão
- `tests/version/test_commitlint_config.py` — Testes de configuração

### Documentação

- `CONTRIBUTING.md` — Guia de contribuição com Conventional Commits
- `docs/adr/ADR012-estrategia-versionamento.md` — Atualizado com status "aceito"
- README do projeto com seção de versionamento

## 9. Próximos passos

### Fase 0: Pré-requisitos de Infraestrutura

1. [ ] **Verificar/criar repositório GitHub**
  - [ ] Verificar se repositório `skybridge` existe no GitHub
  - [ ] Se não existir, criar repositório via `gh repo create` ou interface web
  - [ ] Configurar branch `main` como padrão
  - [ ] Habilitar GitHub Actions (necessário para workflows)
  - [ ] Habilitar GitHub Pages (opcional, para documentação versionada)

### Fase 1: Descoberta (ANTES de implementar)

1. [ ] Criar diretório `docs/inventory/` se não existir
2. [ ] Buscar todos os arquivos que contêm "version" ou "VERSION"
3. [ ] Ler e documentar cada versão encontrada
4. [ ] Identificar discrepâncias entre versões
5. [ ] Definir versão inicial para cada componente baseado no estado atual
6. [ ] Gerar relatório `PRD012-version-inventory.md`
7. [ ] **APROVAÇÃO DO RELATÓRIO** antes de prosseguir para implementação

### Fase 2: Single Source of Truth

8. [ ] Criar arquivo `VERSION` na raiz com versões definidas na fase 1
9. [ ] Implementar `scripts/version.py` com função `get_version()`
10. [ ] Atualizar `src/skybridge/__init__.py` para ler do VERSION
11. [ ] Atualizar outros arquivos identificados no inventário

### Fase 3: Conventional Commits

12. [ ] Instalar commitlint e husky
13. [ ] Criar `.commitlintrc.yml` com escopos definidos
14. [ ] Configurar hook `commit-msg` via husky
15. [ ] Testar validação de commits (tentar commit inválido)
16. [ ] Documentar em `CONTRIBUTING.md`

### Fase 4: GitHub Workflows

17. [ ] Criar `.github/workflows/release.yml`
18. [ ] Implementar lógica de parse de commits
19. [ ] Implementar lógica de bump de versão
20. [ ] Implementar geração de CHANGELOG
21. [ ] Criar `.github/workflows/docs.yml`
22. [ ] Testar workflows manualmente (trigger manual)
23. [ ] Validar permissões do GitHub token

### Fase 5: Primeiro Release

24. [ ] Fazer commit follow Conventional Commits
25. [ ] Merge para main
26. [ ] Observar workflow executar
27. [ ] Validar release criada
28. [ ] Validar CHANGELOG gerado
29. [ ] Validar documentação versionada
30. [ ] Atualizar ADR012 para status "aceito"

---

## A) Inventário Preliminar (A ser preenchido na Fase 1)

| Componente | Localização | Versão Atual | Formato | Observações |
|------------|-------------|--------------|---------|-------------|
| App Skybridge | `src/skybridge/__init__.py` | ? | string | A descobrir |
| Kernel API | `src/skybridge/kernel/__init__.py` | ? | string | A descobrir |
| OpenAPI | `openapi/v1/skybridge.yaml` | ? | string | A descobrir |
| Pacote Python | `pyproject.toml` | ? | string | A descobrir |
| ... | ... | ... | ... | ... |

---

> "Versionamento sem caos é a base de confiança em evolução."
> — ADR012

> "Para versionar o futuro, primeiro precisamos entender o presente."
> — made by Sky 🔢✨
