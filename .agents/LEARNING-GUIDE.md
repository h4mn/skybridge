# Guia de Aprendizado - Criando Plugins Claude Code

## Plugin Criado: `.agents/my-first-plugin/`

Seu primeiro plugin está pronto! Vamos entender cada componente.

---

## 1. Estrutura do Plugin

```
my-first-plugin/
├── .claude-plugin/plugin.json    # Manifest (obrigatório)
├── commands/hello.md             # Slash command
├── agents/motivator.md           # Sub-agente especializado
├── skills/hello-world/SKILL.md   # Skill auto-ativável
├── hooks/hooks.json              # Event handlers
└── README.md                     # Documentação
```

---

## 2. Componentes Explicados

### Commands (`commands/*.md`)

**O que são**: Comandos que o usuário invoca com `/nome`

**Estrutura**:
```markdown
---
name: hello
description: O que este comando faz
allowed-tools: []  # Tools que pode usar
---

Instruções para o IA executar este comando...
```

**Como usar**: Digite `/hello` no chat

---

### Agents (`agents/*.md`)

**O que são**: Sub-agentes com especialidade específica

**Estrutura**:
```markdown
---
description: Papel do agente
capabilities:
  - Capacidade 1
  - Capacidade 2
---

Instruções detalhadas do agente...
```

**Como usar**: Claude Code invoca automaticamente baseado no contexto

---

### Skills (`skills/*/SKILL.md`)

**O que são**: Capacidades auto-ativadas por contexto

**Estrutura**:
```markdown
---
name: skill-name
description: Quando ativar
version: 1.0.0
---

Definição da skill...
```

**Como usar**: Ativa automaticamente quando o contexto bate com `description`

---

### Hooks (`hooks/hooks.json`)

**O que são**: Respondem a eventos do sistema

**Eventos disponíveis**:
| Evento | Quando Dispara |
|--------|----------------|
| `PreToolUse` | Antes de usar uma tool |
| `PostToolUse` | Depois de usar uma tool |
| `SessionStart` | Ao iniciar sessão |
| `SessionEnd` | Ao encerrar sessão |
| `Stop` | Ao parar |

**Estrutura**:
```json
{
  "SessionStart": [{
    "hooks": [{
      "type": "command",
      "command": "echo 'Sessão iniciada!'",
      "timeout": 5
    }]
  }]
}
```

---

## 3. Como Instalar e Testar

### Método 1: Local (para desenvolvimento)

```bash
# Copiar para diretório de plugins local
# Windows: C:\Users\SEU_USUARIO\.claude\plugins\
# Mac/Linux: ~/.claude/plugins/
```

### Método 2: Marketplace

Publicar no GitHub e adicionar ao marketplace oficial.

---

## 4. Extraindo Valor do Claude Code

### Ideias de Fluxos Úteis

#### Fluxo 1: Code Review Automático
```
commands/
├── review-pr.md        # /review-pr
agents/
├── code-reviewer.md    # Analisa código
├── security-checker.md # Verifica segurança
hooks/
└── hooks.json          # Roda antes de commit
```

#### Fluxo 2: Deploy Automatizado
```
commands/
├── deploy.md           # /deploy
├── rollback.md         # /rollback
skills/
└── deployment/
    └── SKILL.md        # Detecta padrões de deploy
```

#### Fluxo 3: Documentação
```
commands/
├── docs.md             # /docs
agents/
├── doc-writer.md       # Escreve documentação
skills/
└── api-docs/
    └── SKILL.md        # Gera docs de APIs
```

---

## 5. Referência Rápida - Variáveis Úteis

| Variável | O que é | Uso |
|----------|---------|-----|
| `${CLAUDE_PLUGIN_ROOT}` | Caminho do plugin | Hooks, MCP servers |
| `allowed-tools` | Tools disponíveis | No frontmatter do command |
| `matcher` | Pattern matching | Em hooks para filtrar tools |

---

## 6. Próximos Passos para Aprender Mais

### Skills Úteis do Claude Code

Use estes skills para aprender mais:

- `/plugin-dev:plugin-structure` - Estrutura de plugins
- `/plugin-dev:command-development` - Criar commands
- `/plugin-dev:agent-development` - Criar agents
- `/plugin-dev:skill-development` - Criar skills
- `/plugin-dev:hook-development` - Criar hooks
- `/plugin-dev:mcp-integration` - Integrar MCP servers

### Estudar o Código Fonte

```bash
# Plugins oficiais para estudar
.agents/repos/claude-code/plugins/commit-commands/
.agents/repos/claude-code/plugins/feature-dev/
.agents/repos/claude-code/plugins/plugin-dev/
```

---

## 7. Exercícios Práticos

### Fácil
1. Modificar `/hello` para incluir seu nome
2. Criar um comando `/data` que mostra data/hora

### Médio
1. Criar agente `code-explainer` que explica código
2. Criar skill `debug-helper` que ativa ao falar de bugs

### Avançado
1. Criar hook que valida código antes de Write
2. Integrar MCP server para API externa
3. Criar workflow completo de PR review

---

## 8. Diagrama de Fluxo

```
┌─────────────┐
│  Usuário    │
│  /comando   │
└──────┬──────┘
       ▼
┌─────────────────┐
│ Command Parser  │
│ (frontmatter)   │
└────────┬────────┘
         ▼
┌──────────────────┐
│ Claude Code      │
│ + allowed-tools  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Executa          │
│ (Bash, Files,    │
│  Git, etc)       │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Hooks            │
│ (PostToolUse)    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Resposta ao      │
│ Usuário          │
└──────────────────┘
```

---

## 9. Troubleshooting

| Problema | Solução |
|----------|---------|
| Command não aparece | Verifique se está em `commands/` com extensão `.md` |
| Hook não executa | Verifique sintaxe JSON em `hooks.json` |
| Skill não ativa | Ajuste `description` para ser mais específico |
| Path errors | Use `${CLAUDE_PLUGIN_ROOT}` para caminhos relativos |

---

## 10. Recursos

- [Claude Code GitHub](https://github.com/anthropics/claude-code)
- [Plugins Oficiais](https://github.com/anthropics/claude-plugins-official)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)

---

> "Learning is a journey, not a destination" – made by Sky [📚]
