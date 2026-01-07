# My First Plugin

Plugin tutorial para aprender a criar componentes Claude Code.

## Estrutura

```
my-first-plugin/
├── .claude-plugin/
│   └── plugin.json          # Manifest do plugin
├── commands/
│   └── hello.md             # Comando /hello
├── agents/
│   └── motivator.md         # Agente motivador
├── skills/
│   └── hello-world/
│       └── SKILL.md         # Skill demonstrativa
├── hooks/
│   └── hooks.json           # Hooks de evento
└── README.md
```

## Componentes

### Command: `/hello`

Execute `/hello` para receber uma saudação personalizada.

### Agent: `motivator`

Agente que motiva e inspira durante sessões de código.

### Skill: `hello-world`

Skill demonstrativa que se ativa automaticamente.

### Hooks

- **PostToolUse**: Log após Write/Edit
- **SessionStart**: Mensagem ao iniciar sessão

## Próximos Passos

1. Instalar o plugin no Claude Code
2. Testar cada componente
3. Modificar e extender
4. Criar seus próprios componentes

## Referências

- [Claude Code Plugins](https://github.com/anthropics/claude-plugins-official)
- Documentação em `.agents/repos/claude-code/`

---

> "The best way to learn is by doing" – made by Sky [🚀]
