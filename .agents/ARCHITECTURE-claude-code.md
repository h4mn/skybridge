# Claude Code - Mapa Arquitetural

> Repositório analisado: [anthropics/claude-code](https://github.com/anthropics/claude-code)
> Data da análise: 2025-12-25

---

## 1. Arquitetura de Alto Nível

Claude Code segue uma **arquitetura baseada em plugins, orientada a eventos**:

| Princípio | Descrição |
|-----------|-----------|
| **Agent-first** | Sistema construído ao redor de agentes AI especializados |
| **Plugin extensibility** | Toda funcionalidade é implementada como plugins |
| **Event-driven hooks** | Sistema responde a eventos de ciclo de vida |
| **Natural language interface** | Comandos via processamento de linguagem natural |
| **Tool integration** | Integração via MCP (Model Context Protocol) |

---

## 2. Estrutura de Diretórios

```
claude-code/
├── .claude/                           # Configuração core
│   ├── commands/                      # Comandos embutidos
│   └── ...
├── .claude-plugin/                    # Marketplace de plugins
│   └── marketplace.json              # Registry de plugins
├── .devcontainer/                     # Container de desenvolvimento
│   └── devcontainer.json
├── .github/
│   └── workflows/                      # CI/CD
├── .vscode/
│   └── extensions.json
├── plugins/                           # 🧩 Ecosystem de Plugins
│   ├── agent-sdk-dev/                 # Dev tools para Agent SDK
│   ├── commit-commands/               # Git workflow
│   ├── feature-dev/                    # Desenvolvimento de features
│   ├── plugin-dev/                    # Plugin development toolkit
│   ├── pr-review-toolkit/             # Pull review tools
│   └── ... (12+ plugins oficiais)
├── scripts/                           # Scripts utilitários
│   ├── auto-close-duplicates.ts
│   └── backfill-duplicate-comments.ts
└── examples/                          # Exemplos de implementação
```

---

## 3. Componentes Principais

### Plugin System

```
┌─────────────────────────────────────────────────────────┐
│                    Plugin System                        │
├─────────────────────────────────────────────────────────┤
│  Auto-discovery → Manifest → Component Registration    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐  │
│  │ Commands │  │  Agents  │  │  Skills  │  │ Hooks │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────┘  │
│       │             │              │            │      │
│       ▼             ▼              ▼            ▼      │
│  Slash-cmd    Special-AI   Context-Auto    Events     │
└─────────────────────────────────────────────────────────┘
```

### Tipos de Componentes

| Tipo | Finalidade | Exemplo |
|------|-----------|---------|
| **Commands** | Comandos do usuário `/nome` | `/commit`, `/review-pr` |
| **Agents** | Sub-agentes especializados | code-reviewer, code-explorer |
| **Skills** | Ativação automática por contexto | pdf, commit |
| **Hooks** | Event handlers de lifecycle | PreToolUse, PostToolUse |
| **MCP Servers** | Integração com tools externas | GitHub, APIs |

---

## 4. Estrutura de Plugin

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # ⭐ Metadata (obrigatório)
├── commands/                # Slash commands (opcional)
│   └── command-name.md     # YAML frontmatter + implementação
├── agents/                  # Agentes especializados
│   └── agent-name.md       # Declaração de capacidades
├── skills/                  # Skills auto-ativáveis
│   └── skill-name/
│       └── SKILL.md
├── hooks/                   # Event handlers
│   └── hooks.json
├── .mcp.json                # Servidores MCP
└── README.md
```

---

## 5. Fluxo de Dados

```
┌─────────────┐
│ User Input  │ (Natural Language)
└──────┬──────┘
       ▼
┌─────────────────┐
│ Command Parsing │
│ Pattern Match   │
└────────┬────────┘
         ▼
┌──────────────────┐
│ Component Select │ (Command/Agent/Skill)
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Context Gather   │ (git, files, etc)
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Execute + Tools  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Output Response  │
└──────────────────┘
```

---

## 6. Stack Tecnológico

| Categoria | Tecnologias |
|-----------|-------------|
| **Runtime** | Node.js 18+, Bun |
| **Config** | JSON, YAML frontmatter |
| **Scripting** | TypeScript, Bash |
| **Container** | Docker |
| **CI/CD** | GitHub Actions |
| **Integração** | MCP (SSE, stdio, HTTP, WebSocket) |

---

## 7. Pontos de Extensão

| Extensão | Como |
|----------|------|
| Commands | Criar `.md` com frontmatter em `commands/` |
| Agents | Declarar capacidades em `agents/*.md` |
| Skills | Criar `skills/*/SKILL.md` com regras de ativação |
| Hooks | Configurar em `hooks/hooks.json` |
| MCP Servers | Definir em `.mcp.json` |

---

## 8. Eventos do Sistema (Hooks)

| Evento | Quando Dispara |
|--------|----------------|
| `PreToolUse` | Antes de usar uma tool |
| `PostToolUse` | Depois de usar uma tool |
| `Stop` | Ao parar sessão |
| `SessionStart` | Ao iniciar sessão |
| `SessionEnd` | Ao encerrar sessão |
| `UserPromptSubmit` | Ao submeter prompt |
| `SubagentStop` | Ao parar sub-agente |

---

## 9. Plugins Oficiais

| Plugin | Propósito |
|--------|-----------|
| `agent-sdk-dev` | Desenvolvimento de agentes |
| `commit-commands` | Workflows Git |
| `feature-dev` | Desenvolvimento de features |
| `plugin-dev` | Toolkit para plugins |
| `pr-review-toolkit` | Revisão de PRs |
| `claude-code-guide` | Documentação Claude Code |

---

## 10. Insights Arquiteturais

1. **Modularidade extrema** - Tudo é plugin
2. **Convention over configuration** - Auto-discovery reduz boilerplate
3. **Event-driven** - Hooks permitem customização profunda
4. **Tool integration** - MCP protocol para tools externas
5. **Multi-platform** - Containerização garante consistência
6. **Natural language first** - Interface humana legível

---

> "Architecture is frozen conversation" – made by Sky [🏗️]
