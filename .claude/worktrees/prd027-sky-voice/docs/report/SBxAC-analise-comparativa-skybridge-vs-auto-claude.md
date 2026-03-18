# Análise Comparativa: Skybridge vs Auto-Claude

**Data:** 2026-01-14
**Analista:** Sky
**Repositórios Comparados:**
- B:\_repositorios\skybridge
- B:\_repositorios\auto-claude

---

## 1. Visão Geral dos Projetos

### Skybridge
- **Descrição:** Microkernel RPC Platform (PoC Hello World)
- **Versão:** 0.1.0
- **Tipo:** Engine de agentes + ferramentas (baseada em ADRs)
- **Idioma:** Português brasileiro (pt-br)
- **Foco:** Arquitetura orientada a ADRs, DDD (Domain-Driven Design), padrões de projeto

### Auto-Claude
- **Descrição:** Autonomous multi-agent coding framework powered by Claude AI
- **Versão:** 2.7.4
- **Tipo:** Framework completo de codificação autônoma com multi-agentes
- **Idioma:** Inglês
- **Foco:** Automação completa de desenvolvimento de software com agentes AI

---

## 2. Características IGUAIS

### 2.1. Estrutura de Projeto Similar
- Ambos possuem diretório `apps/` com componentes modulares
- Ambos usam Python como linguagem principal do backend
- Ambos possuem testes em diretórios separados (`tests/`)

### 2.2. Uso de Workspaces de Git
- **Skybridge:** `src/skybridge/core/contexts/agents/worktree_validator.py`
- **Auto-Claude:** `apps/backend/core/worktree.py`
- Ambos implementam gerenciamento de git worktrees para isolamento

### 2.3. Stack Tecnológica Comum
- **Python 3.11+** como base
- **pydantic>=2.0.0** para validação de dados
- **python-dotenv** para gerenciamento de variáveis de ambiente
- Ambos usam **JSON-RPC** (Auto-Claude implícito via Claude Agent SDK)

### 2.4. Conceitos de Agentes
- Ambos possuem sistemas de agentes com contextos isolados
- Ambos possuem camadas de segurança e validação

### 2.5. Arquitetura em Camadas
- **Skybridge:** kernel/ → core/ → platform/ → apps/
- **Auto-Claude:** core/ → agents/ → integrations/ → cli/
- Ambos seguem princípios de separação de responsabilidades

### 2.6. Configuração de Ambiente
- Ambos usam arquivos `.env` e `.env.example`
- Ambos possuem `.gitignore` configurado
- Ambos têm configurações de lint e formatação

### 2.7. Documentação Estruturada
- **Skybridge:** docs/adr/ (Architecture Decision Records)
- **Auto-Claude:** guides/ (documentação técnica)
- Ambos possuem documentação dedicada para decisões técnicas

---

## 3. Características PARECIDAS

### 3.1. Integração com Claude AI
- **Skybridge:** Usa Claude Agent SDK indiretamente (via arquitetura)
- **Auto-Claude:** Usa Claude Agent SDK diretamente (claude-agent-sdk>=0.1.16)
- Ambos projetados para trabalhar com Claude AI

### 3.2. Sistema de Agentes
- **Skybridge:** Context-based agents em `src/skybridge/core/contexts/agents/`
- **Auto-Claude:** Multi-agent system em `apps/backend/agents/` (planner, coder, qa_reviewer, qa_fixer)
- Ambos possuem múltiplos tipos de agentes com responsabilidades específicas

### 3.3. Memória e Contexto
- **Skybridge:** Sistema de contexto baseado em fileops e registry
- **Auto-Claude:** Graphiti (LadybugDB) para memória de longo prazo
- Ambos mantêm estado/contexto entre sessões

### 3.4. Segurança em Camadas
- **Skybridge:** Validação de paths, allowed paths, operações isoladas
- **Auto-Claude:** OS sandbox, filesystem restrictions, command allowlist
- Ambos implementam múltiplas camadas de segurança

### 3.5. Gerenciamento de Especificações (Specs)
- **Skybridge:** ADRs definindo contratos e specs
- **Auto-Claude:** `.auto-claude/specs/XXX-name/` com spec.md, requirements.json
- Ambos usam especificações como fonte de verdade

### 3.6. CLI como Interface Principal
- **Skybridge:** Typer para CLI (sb command)
- **Auto-Claude:** CLI via `apps/backend/run.py`
- Ambos suportam operação via linha de comando

### 3.7. Validadores e Checkpoints
- **Skybridge:** Validação de snapshots, checkpoints em ADRs
- **Auto-Claude:** QA validation loop, checkpoint-based spec validation
- Ambos usam validação em múltiplas fases

### 3.8. Hooks e Git Integrations
- **Skybridge:** Husky + commitlint
- **Auto-Claude:** .pre-commit-config.yaml
- Ambos automatizam qualidade de commits

---

## 4. Características DIFERENTES

### 4.1. Escopo e Maturidade
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Estado | PoC (Proof of Concept) | Produção (v2.7.4) |
| Maturidade | Inicial (0.1.0) | Estável e maduro |
| Completude | Hello World minimalista | Framework completo |

### 4.2. Frontend / UI
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Tipo | API REST (FastAPI) + CLI | Electron Desktop App + CLI |
| Interface | Thin adapter HTTP | Rich UI com Kanban, Terminals, Insights |
| Internacionalização | Não implementada | i18n completo (en, fr, etc.) |

### 4.3. Sistema de Memória
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Tecnologia | Registry-based context | Graphiti (LadybugDB) + Graph Database |
| Persistência | Temporária/contextual | Longo prazo,跨 sessão |
| Search | Simples | Semantic search embeddings |

### 4.4. Pipeline de Desenvolvimento
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Abordagem | ADR-driven, incremental | Multi-phase pipeline (3-8 fases dinâmicas) |
| Complexity | Não detecta automaticamente | Detecta complexity (simple/standard/complex) |
| Fases | Fixo (definido por ADRs) | Dinâmico baseado na tarefa |

### 4.5. Integrações Externas
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Linear | Não integrado | Integrado |
| GitHub/GitLab | Não integrado | Integrado (Issues, PRs) |
| Sentry | Opcional (comentado) | Integrado (sentry-sdk>=2.0.0) |
| Ngrok | Opcional | Não integrado |

### 4.6. E2E Testing
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| E2E Framework | Não implementado | Electron MCP (Chrome DevTools Protocol) |
| QA Automation | Não implementado | QA agents com E2E testing |

### 4.7. Distribuição e Release
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Distribuição | pip install (Python package) | Binários (Windows, macOS, Linux, Flatpak) |
| Auto-update | Não implementado | Auto-update integrado |
| Release Process | Manual | Automated via GitHub Actions |

### 4.8. Modelo de Dados
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Arquitetura | DDD (Domain-Driven Design) | Spec-based com JSON schemas |
| Schema | Result, Envelope, Registry | spec_contract.json, requirements.json |
| Persistência | Em memória/contexto | JSON files + Graph Database |

### 4.9. Abordagem de Multi-Agent
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Arquitetura | Context-based agents | Planner → Coder → QA Reviewer → QA Fixer |
| Parallelism | Não especificado | Parallel execution até 12 terminals |
| Coordination | Via Registry/Kernel | Via orchestration layer |

### 4.10. Idioma e Documentação
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Idioma | Português brasileiro (pt-br) | Inglês |
| Encoding | UTF-8 (explícito) | UTF-8 (implícito) |
| Documentação | ADRs técnicos | Guides + README + CLAUDE.md |

### 4.11. License
| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| Licença | Não especificado | AGPL-3.0 |
| Model | Não especificado | Open source com opção comercial |

### 4.12. Complementos Específicos

**Skybridge possui:**
- ADR (Architecture Decision Records) bem definidos
- Kernel com Result, Envelope, Registry
- Thin adapter HTTP (FastAPI)
- Health endpoint pronto
- Estrutura DDD rigorosa
- Sandbox `.agents/` para experimentação

**Auto-Claude possui:**
- Frontend Electron completo
- Graphiti memory system obrigatório
- Multiple LLM providers (OpenAI, Anthropic, Azure, Ollama, Google AI)
- Multiple embedder providers
- MCP servers integrados (Context7, Linear, Graphiti, Electron, Puppeteer)
- Phase-based spec creation (3-8 fases)
- QA Loop automático
- Ideation e Insights features
- Changelog automático
- Version bump automation
- CI/CD completo no GitHub Actions

---

## 5. Análise de Convergência e Divergência

### 5.1. Convergência (O que é semelhante)
Ambos os projetos **convergem** nos seguintes aspectos:
1. **Microkernel architecture** - Skybridge explícito, Auto-Claude implícito via core/
2. **Multi-agent systems** - Ambos usam múltiplos agentes com papéis definidos
3. **Security-first approach** - Múltiplas camadas de segurança
4. **Git worktree isolation** - Ambos implementam isolamento seguro
5. **Spec-driven development** - Especificações como fonte de verdade
6. **Python backend com Pydantic** - Stack tecnológico similar
7. **Claude AI integration** - Ambos projetados para Claude

### 5.2. Divergência (O que é diferente)
Os projetos **divergem** principalmente em:
1. **Escopo e Maturidade** - Skybridge é PoC, Auto-Claude é produção
2. **Frontend** - Skybridge (API), Auto-Claude (Electron desktop)
3. **Memória** - Skybridge (Registry), Auto-Claude (Graphiti graph DB)
4. **Distribuição** - Skybridge (Python package), Auto-Claude (Binários)
5. **Complexidade** - Skybridge (simples), Auto-Claude (completo)
6. **Idioma** - Skybridge (pt-br), Auto-Claude (en)
7. **Pipeline** - Skybridge (ADR-driven), Auto-Claude (multi-phase dinâmico)

---

## 6. Oportunidades de Aprendizado e Evolução

### 6.1. Skybridge pode aprender de Auto-Claude
1. **Graphiti Memory System** - Sistema de memória de longo prazo robusto
2. **Multi-phase Pipeline** - Detecção dinâmica de complexidade
3. **QA Loop Automático** - Validação automatizada com fix loop
4. **E2E Testing** - Electron MCP para testes de UI
5. **Parallel Execution** - Múltiplos agentes trabalhando em paralelo
6. **Multiple LLM Providers** - Flexibilidade de provedores
7. **CI/CD Automation** - Release process automático
8. **Internationalization** - i18n completo no frontend

### 6.2. Auto-Claude pode aprender de Skybridge
1. **ADR Framework** - Decisões de arquitetura documentadas
2. **DDD Rigoroso** - Domain-Driven Design mais explícito
3. **Kernel Pattern** - Microkernel bem definido
4. **PoC Approach** - Validação rápida de conceitos
5. **Thin Adapter HTTP** - Camada de API minimalista
6. **Sandbox Pattern** - Espaço isolado para experimentação (`.agents/`)

---

## 7. Conclusão

### 7.1. Relação entre os Projetos
Os dois projetos **não são competidores diretos**, mas sim **projetos complementares** em diferentes estágios de evolução:

- **Skybridge** está na fase de **validação de arquitetura** (PoC) com foco em **padrões de projeto rigorosos** (ADR, DDD)
- **Auto-Claude** está na fase de **produção** com foco em **automação completa** de desenvolvimento de software

### 7.2. Principais Semelhanças
- Ambos usam **multi-agent architecture** com Claude AI
- Ambos implementam **security em camadas** e **git worktree isolation**
- Ambos são **spec-driven** e **Python-based**
- Ambos possuem **modularidade** e **separação de responsabilidades**

### 7.3. Principais Diferenças
- **Skybridge**: Arquitetura acadêmica/rigorosa, PoC, pt-br, sem frontend, DDD
- **Auto-Claude**: Framework completo, produção, en, Electron desktop, pipeline complexo

### 7.4. Potencial de Convergência
Se **Skybridge** evoluir para produção, pode:
- Adotar **Graphiti** para memória
- Implementar **multi-phase pipeline**
- Adicionar **QA loop automático**
- Criar **frontend** (Electron ou similar)

Se **Auto-Claude** quiser melhorar arquitetura, pode:
- Adotar **ADRs** para decisões
- Implementar **DDD** mais rigoroso
- Adicionar **kernel pattern** explícito

### 7.5. Resumo Executivo

| Aspecto | Skybridge | Auto-Claude |
|---------|-----------|-------------|
| **Estágio** | PoC (Validação) | Produção (Stable) |
| **Foco** | Arquitetura rigorosa | Automação completa |
| **Frontend** | API REST | Electron Desktop |
| **Memória** | Registry | Graphiti (Graph DB) |
| **Pipeline** | ADR-driven | Multi-phase dinâmico |
| **Distribuição** | Python package | Binários multi-plataforma |
| **QA** | Manual | Automatizado com E2E |
| **Idioma** | Português (pt-br) | Inglês (en) |
| **E2E Testing** | ❌ | ✅ (Electron MCP) |
| **i18n** | ❌ | ✅ |
| **CI/CD** | Básico | Completo (GitHub Actions) |

---

## 8. Recomendações

### Para Skybridge
1. **Adotar Graphiti** para sistema de memória robusto
2. **Implementar QA loop** automatizado
3. **Adicionar frontend** (Electron ou web-based)
4. **Criar pipeline multi-phase** baseado em complexidade
5. **Documentar ADRs** ainda mais detalhadamente (como Auto-Claude faz com guides)

### Para Auto-Claude
1. **Adotar ADRs** para documentar decisões de arquitetura
2. **Refatorar para DDD** mais explícito
3. **Adicionar kernel pattern** para melhor modularidade
4. **Criar sandbox** para experimentação (como `.agents/` do Skybridge)

---

## 9. Referências

### Skybridge
- **README:** B:\_repositorios\skybridge\README.md
- **ADRs:** docs/adr/ (ADR000-ADR009)
- **Código fonte:** src/skybridge/
- **Requirements:** requirements.txt
- **Package:** package.json

### Auto-Claude
- **README:** B:\_repositorios\auto-claude\README.md
- **CLAUDE.md:** B:\_repositorios\auto-claude\CLAUDE.md
- **Código fonte:** apps/backend/
- **Requirements:** apps/backend/requirements.txt
- **Package:** package.json
- **Guides:** guides/

---

> "Dois projetos, uma visão: agentes AI construindo software de forma autônoma." – made by Sky 🚀
