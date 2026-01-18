# Feature Request: Portabilidade de Sessões entre Worktrees

## Título
**Ability to resume and clone sessions across git worktrees**

## Problema

Atualmente, sessões do Claude Code são isoladas por caminho completo do diretório de trabalho. Isso significa que conversas iniciadas em um worktree não podem ser continuadas em outro worktree do mesmo repositório.

### Estrutura Atual

```
C:\Users\hadst\.claude\projects\
├── B---repositorios-skybridge\
│   └── sessions\
│       └── abc123-...  ← Sessão da branch principal
└── B---repositorios-skybridge-worktrees-demo-feature\
    └── sessions\
        └── def456-...  ← Sessão do worktree (não acessa a outra)
```

## Impacto

Quando um desenvolvedor:
1. Trabalha em uma discussão detalhada na branch `main`
2. Cria um worktree para implementar uma feature (`git worktree add`)
3. Quer continuar o contexto da conversa anterior no novo worktree

**Resultado**: Perda total do contexto da conversa. O desenvolvedor precisa reexplicar tudo ou tentar lembrar do que foi discutido.

## Casos de Uso

### 1. Worktree para Continuação de Feature
```bash
# Branch principal: discussão sobre arquitetura
$ cd /path/to/skybridge
$ claude
> [discussão detalhada sobre implementação]

# Criar worktree para implementar
$ git worktree add ../skybridge-worktrees-feature-x -b feature/x
$ cd ../skybridge-worktrees-feature-x
$ claude --resume <session-id>
# ERRO: sessão não encontrada (está em outro namespace)
```

### 2. Code Review com Contexto
```bash
# Revisor no worktree do PR quer ver o contexto da discussão original
# que aconteceu no worktree de desenvolvimento
```

### 3. Experimentação Paralela
```bash
# Desenvolvedor quer testar duas abordagens diferentes
# mantendo o contexto da conversa original em ambos worktrees
```

## Soluções Propostas

### Opção 1: Flag `--clone-session` (Recomendado)

```bash
# No worktree filho, clonar uma sessão do worktree pai
$ claude --clone-session <session-id>@<project-path>

# Exemplo:
$ claude --clone-session 337c2b22-c543-4be8-ad3c-57b0860dee7e@B---repositorios-skybridge

# Ou inferir automaticamente a branch pai:
$ claude --clone-session-from-parent 337c2b22-c543-4be8-ad3c-57b0860dee7e
```

**Comportamento esperado:**
- Copia o histórico da sessão para o namespace do worktree atual
- Preserva mensagens, contexto e estado
- Permite continuar a conversa naturalmente

### Opção 2: Flag `--resume-from-parent`

```bash
# No worktree filho, continuar última sessão da branch pai
$ claude --resume-from-parent
```

**Comportamento esperado:**
- Detecta automaticamente o worktree/branch pai via Git
- Lista sessões disponíveis do worktree pai
- Permite selecionar qual continuar
- Clona para o worktree atual

### Opção 3: Namespace Compartilhado (Opção Avançada)

```bash
# Configurar namespace compartilhado para worktrees do mesmo repo
$ claude config set shared-namespace true
```

**Comportamento esperado:**
- Worktrees do mesmo repositório compartilham o namespace de sessões
- Sessões são acessíveis de qualquer worktree
- Requer cuidado com conflitos (mesma sessão aberta em múltiplos worktrees)

## Implementação Sugerida

### Backend (TypeScript)

```typescript
// src/core/session_manager.ts

interface SessionCloneOptions {
  sessionId: string;
  sourceProjectPath: string;
  targetProjectPath: string;
  mergeHistory?: boolean;
}

class SessionManager {
  async cloneSession(options: SessionCloneOptions): Promise<Session> {
    // 1. Carregar sessão do namespace fonte
    const sourceSession = await this.loadSession(
      options.sessionId,
      options.sourceProjectPath
    );

    // 2. Clonar para namespace destino
    const clonedSession = {
      ...sourceSession,
      id: generateNewSessionId(), // Novo ID para evitar conflitos
      projectPath: options.targetProjectPath,
      clonedFrom: options.sessionId,
      clonedAt: new Date().toISOString(),
    };

    // 3. Persistir no destino
    await this.saveSession(clonedSession);

    return clonedSession;
  }

  async detectParentWorktree(currentPath: string): Promise<string | null> {
    // Detectar worktree pai via .git files ou git worktree list
    const worktrees = await this.execGit('worktree list', { cwd: currentPath });
    // Analisar e retornar o worktree pai
  }
}
```

### CLI Interface

```typescript
// src/cli/commands/resume.ts

export const resumeCommand = {
  command: 'resume [session-id]',
  describe: 'Resume a previous conversation',
  builder: (yargs) => {
    yargs
      .option('clone-from', {
        describe: 'Clone session from another worktree',
        type: 'string',
      })
      .option('from-parent', {
        describe: 'Clone session from parent worktree',
        type: 'boolean',
        default: false,
      })
      .option('list-available', {
        describe: 'List available sessions from parent worktree',
        type: 'boolean',
        default: false,
      });
  },
  handler: async (argv) => {
    if (argv.fromParent) {
      await handleResumeFromParent(argv);
    } else if (argv.cloneFrom) {
      await handleCloneFromWorktree(argv);
    } else {
      await handleResume(argv);
    }
  },
};
```

## Alternativas Temporárias

Enquanto a feature não é implementada, usuários podem:

### Workaround 1: Link Simbólico (Windows)

```powershell
# No worktree filho
New-Item -ItemType SymbolicLink `
  -Path "C:\Users\hadst\.claude\projects\B---repositorios-skybridge-worktrees-current" `
  -Target "C:\Users\hadst\.claude\projects\B---repositorios-skybridge"
```

⚠️ **Problema**: Não funciona bem pois o Claude Code detecta o caminho real e cria novo namespace.

### Workaround 2: Documentação em Arquivos .md

```bash
# Criar arquivo de contexto no repositório
echo "## Contexto da Conversa
### Decisões tomadas:
1. Usar FileBasedJobQueue ao invés de Redis
2. Implementar retry com backoff exponencial

### Próximos passos:
- Implementar exists_by_delivery
- Adicionar testes de integração
" > CONTEXT.md

# O arquivo viaja com o código entre branches
git add CONTEXT.md
git commit -m "docs: adicionar contexto da conversa"
```

### Workaround 3: Cópia Manual de Sessão

```bash
# Copiar diretório da sessão manualmente
cp -r \
  "C:\Users\hadst\.claude\projects\B---repositorios-skybridge\sessions\337c2b22-..." \
  "C:\Users\hadst\.claude\projects\B---repositorios-skybridge-worktrees-current\sessions\"

# ⚠️ Não testado, pode não funcionar devido a validações internas
```

## Votação

- 👍 **Thumbs up** se você também precisa dessa feature
- 💬 **Comente** com seu caso de uso específico
- 🎯 **Reação** com a solução preferida (Opção 1, 2 ou 3)

## Referências

- Documentação de worktrees: https://git-scm.com/docs/git-worktree
- Issue relacionada (se houver): #[número]

---

**Priority**: Medium
**Complexity**: Medium
**Breaking Changes**: None
