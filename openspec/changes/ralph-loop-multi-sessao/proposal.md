# Proposal: Ralph Loop Multi-Sessão

## Why

O Ralph Loop atual usa um arquivo de estado compartilhado (`.claude/ralph-loop.local.md`) que todas as sessões do Claude Code no mesmo projeto acessam. Isso causa confusão quando múltiplas sessões estão ativas simultaneamente, pois cada sessão pode ler informações de loops de outras sessões.

## What Changes

- **Mudança no nome do arquivo de estado**: De `ralph-loop.local.md` (fixo) para `ralph-loop.{session_id}.md` (único por sessão)
- **Atualização do stop hook**: Modificar lógica para identificar arquivo da sessão atual
- **Atualização do setup script**: Modificar criação de arquivo para usar session_id no nome
- **Atualização do cancel skill**: Modificar remoção de arquivo para considerar session_id

## Capabilities

### New Capabilities
- `ralph-multi-session`: Isolamento completo entre sessões do Ralph Loop através de arquivos dedicados por session_id

### Modified Capabilities
Nenhuma (o comportamento do Ralph Loop não muda, apenas o isolamento entre sessões)

## Impact

**Arquivos afetados:**
- `.claude/plugins/ralph-loop/scripts/setup-ralph-loop.sh`
- `.claude/plugins/ralph-loop/hooks/stop-hook.sh`
- `.claude/plugins/ralph-loop/commands/cancel-ralph.md`

**Sistemas afetados:**
- Ralph Loop plugin (CLAUDE_CONFIG_DIR/plugins/)
- Funcionamento multi-sessão do Claude Code

**Benefícios:**
- Múltiplas sessões podem executar Ralph Loop simultaneamente sem interferência
- Cada sessão tem seu próprio estado e contagem de iterações
- Mais claro visualmente qual loop pertence a qual sessão
